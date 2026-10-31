"""
Fast Quick Fire engine (optional, experimental).

Why: playing a Quick Fire sound through VLC means opening the file, starting a decoder and
(re)starting the audio output every single time. With 7.1 over HDMI that takes a while and the
receiver may swallow the first moments of the sound.

How this works instead:
  * every Quick Fire file is decoded ONCE, in the background, with ffmpeg into memory
    (all channels are kept: 7.1 stays 7.1),
  * one audio output stream stays open and plays silence while nothing is fired,
  * FIRE only starts mixing the clip that is already in memory, so the sound starts as soon as the
    output buffer is refilled (typically 10-30 ms) and it always starts at the same, predictable moment,
  * the volume slider is simply a gain factor.

Nothing in here is allowed to take the program down: every public method catches its errors, and the
main program falls back to the normal VLC playback whenever this engine is not ready.
"""
import collections
import logging
import os
import re
import subprocess
import threading
import time

import numpy as np

MAX_CLIP_SECONDS = 120               # longer files are not preloaded (they play through VLC as before)
MAX_CACHE_BYTES = 768 * 1024 * 1024  # decoded sound kept in memory; oldest unused clips are dropped first
STREAM_LATENCY = 0.04                # seconds of output buffer: small enough to feel instant, big enough to stay
                                     # glitch-free while the window is busy (video, projector)
FADE_SAMPLES = 480                   # ~10 ms fade when a new sound replaces the one that is still playing

SPEAKER_NAMES = {
    8: ["Front left", "Front right", "Center", "Subwoofer (LFE)",
        "Back left", "Back right", "Side left", "Side right"],
    6: ["Front left", "Front right", "Center", "Subwoofer (LFE)", "Surround left", "Surround right"],
    2: ["Left", "Right"],
    1: ["Mono"],
}

_LAYOUT_CHANNELS = {"mono": 1, "stereo": 2, "downmix": 2, "2.1": 3, "3.0": 3, "quad": 4, "4.0": 4,
                    "4.1": 5, "5.0": 5, "5.1": 6, "6.0": 6, "6.1": 7, "7.0": 7, "7.1": 8}


def _no_window():
    try:
        return subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    except Exception:
        return 0


def layout_to_channels(layout):
    """'5.1(side)' -> 6, '7.1' -> 8, 'stereo' -> 2, '6 channels' -> 6. 0 when unknown."""
    if not layout:
        return 0
    m = re.match(r"\s*(\d+)\s+channels?", layout)
    if m:
        return int(m.group(1))
    base = re.split(r"[(\[]", layout.strip().lower())[0].strip()
    if base in _LAYOUT_CHANNELS:
        return _LAYOUT_CHANNELS[base]
    m = re.match(r"(\d+)\.(\d)", base)
    if m:
        return int(m.group(1)) + int(m.group(2))
    return 0


def probe_audio(ffmpeg, path, timeout=20):
    """What does ffmpeg see in the first audio stream of this file?
    Returns {'codec','rate','layout','channels','duration'} (missing pieces are None / 0)."""
    info = {"codec": None, "rate": None, "layout": None, "channels": 0, "duration": None}
    try:
        proc = subprocess.run([ffmpeg, "-hide_banner", "-nostdin", "-i", path],
                              stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=timeout,
                              creationflags=_no_window())
        text = proc.stderr.decode("utf-8", "replace")
    except Exception as e:
        logging.warning(f"Quick Fire engine: probe failed for {path}: {e}")
        return info
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", text)
    if m:
        info["duration"] = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    for line in text.splitlines():
        if "Audio:" in line and "Stream #" in line:
            parts = [p.strip() for p in line.split("Audio:", 1)[1].split(",")]
            if parts:
                info["codec"] = parts[0].split(" ")[0]
            for p in parts[1:]:
                mr = re.match(r"(\d+)\s*Hz", p)
                if mr:
                    info["rate"] = int(mr.group(1))
                    continue
                n = layout_to_channels(p)
                if n and not info["layout"]:
                    info["layout"] = p
                    info["channels"] = n
            break
    return info


def decode_clip(ffmpeg, path, channels, rate, max_seconds=MAX_CLIP_SECONDS, timeout=90):
    """Decodes the first audio stream to float32 (frames, channels) at the output rate.
    ffmpeg maps the channels onto the requested layout (7.1 -> 7.1 unchanged)."""
    cmd = [ffmpeg, "-v", "error", "-nostdin", "-t", str(max_seconds), "-i", path,
           "-map", "0:a:0", "-vn", "-sn", "-dn",
           "-ac", str(channels), "-ar", str(rate), "-f", "f32le", "-"]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout,
                          creationflags=_no_window())
    raw = proc.stdout
    if not raw:
        err = proc.stderr.decode("utf-8", "replace").strip().splitlines()
        raise RuntimeError(err[-1] if err else "no audio decoded")
    arr = np.frombuffer(raw, dtype=np.float32)
    usable = (len(arr) // channels) * channels
    if usable == 0:
        raise RuntimeError("no audio decoded")
    return np.ascontiguousarray(arr[:usable].reshape(-1, channels))


def make_speaker_test(channels, rate):
    """One short beep per speaker, one after the other (the subwoofer channel gets a low tone)."""
    seg = int(rate * 0.4)
    gap = int(rate * 0.3)
    total = channels * (seg + gap)
    data = np.zeros((total, channels), dtype=np.float32)
    t = np.arange(seg) / float(rate)
    env = np.minimum(1.0, np.minimum(np.arange(seg), seg - np.arange(seg)) / (0.02 * rate))
    for ch in range(channels):
        freq = 70.0 if (channels in (6, 8) and ch == 3) else 440.0 + 80.0 * ch
        tone = (0.25 * np.sin(2 * np.pi * freq * t) * env).astype(np.float32)
        start = ch * (seg + gap)
        data[start:start + seg, ch] = tone
    return data


class _Voice(object):
    __slots__ = ("data", "pos", "key", "fade_pos")

    def __init__(self, data, key):
        self.data = data
        self.pos = 0
        self.key = key
        self.fade_pos = -1          # -1 = not fading; otherwise samples already faded


class QuickFireEngine(object):
    def __init__(self, sd_module, ffmpeg_path, notify=None):
        self._sd = sd_module
        self._ffmpeg = ffmpeg_path
        self.notify = notify                # callable(kind) - called from helper threads, must be thread-safe
        self._lock = threading.Lock()       # protects the playing voices
        self._voices = []
        self._last_voice = None
        self._gain = 0.8
        self._stream = None
        self._dead = False
        self._closing = False
        self._opening = False
        self._last_open_try = 0.0
        # stream facts
        self.channels = 0
        self.rate = 0
        self.host = ""
        self.device_name = ""
        self.latency_ms = 0.0
        self.error = ""
        # preloaded clips
        self._clips = collections.OrderedDict()   # path -> dict(data, info, bytes, seconds)
        self._failed = {}                         # path -> reason
        self._queue = collections.deque()
        self._queued = set()
        self._cond = threading.Condition()
        self._worker = None
        self._worker_running = False
        self._op_lock = threading.RLock()         # open() and close() never run at the same time
        self._cache_lock = threading.Lock()
        self._fmt = None

    # ---------- state ----------
    @property
    def active(self):
        s = self._stream
        if s is None or self._dead or self._closing:
            return False
        try:
            return bool(s.active)
        except Exception:
            return False

    @property
    def opening(self):
        return self._opening

    def _emit(self, kind):
        try:
            if self.notify:
                self.notify(kind)
        except Exception:
            pass

    def set_gain(self, gain):
        try:
            self._gain = max(0.0, min(2.0, float(gain)))
        except Exception:
            pass

    def ready_count(self):
        with self._cache_lock:
            return len(self._clips)

    def failed_reason(self, path):
        return self._failed.get(os.path.normcase(os.path.normpath(path)))

    def clip_info(self, path):
        with self._cache_lock:
            c = self._clips.get(self._key(path))
        return dict(c["info"], seconds=c["seconds"], decode_s=c["decode_s"]) if c else None

    def failed_count(self):
        return len(self._failed)

    def pending_count(self):
        with self._cond:
            return len(self._queue) + (1 if self._loading_now else 0)

    _loading_now = None

    @staticmethod
    def _key(path):
        return os.path.normcase(os.path.normpath(path))

    def describe(self):
        """One line for the settings dialog."""
        if self.active:
            names = {8: "7.1", 6: "5.1", 2: "stereo", 1: "mono"}
            lay = names.get(self.channels, f"{self.channels} channels")
            return (f"Ready: {lay} ({self.channels} channels), {self.rate} Hz, {self.host}, "
                    f"about {self.latency_ms:.0f} ms latency. {self.device_name}")
        if self._opening:
            return "Starting the audio output..."
        if self.error:
            return f"Not available: {self.error}"
        return "Off"

    # ---------- output stream ----------
    def _candidates(self):
        sd = self._sd
        out, seen = [], set()
        try:
            apis = sd.query_hostapis()
        except Exception:
            apis = []
        for want in ("Windows WASAPI", "Windows DirectSound", "MME"):
            for a in apis:
                try:
                    if a.get("name") == want and a.get("default_output_device", -1) >= 0:
                        dev = a["default_output_device"]
                        if dev not in seen:
                            seen.add(dev)
                            out.append((want, dev))
                except Exception:
                    continue
        if not out:
            try:
                dev = sd.default.device[1]
                if dev is not None and dev >= 0:
                    out.append(("default", dev))
            except Exception:
                pass
        return out

    def open(self):
        """Opens the output stream (blocking: call from a helper thread). True on success."""
        with self._op_lock:
            return self._open_locked()

    def _open_locked(self):
        if self._opening:
            return False
        self._opening = True
        self._closing = False
        self.error = ""
        self._last_open_try = time.time()
        self._emit("opening")
        try:
            if self._ffmpeg is None:
                raise RuntimeError("ffmpeg was not found")
            if self._stream is not None:
                self._close_stream()
            sd = self._sd
            tried = []
            for host, dev in self._candidates():
                try:
                    info = sd.query_devices(dev)
                except Exception:
                    continue
                max_ch = int(info.get("max_output_channels", 0))
                for ch in (8, 6, 2):
                    if ch > max_ch:
                        continue
                    rate = int(info.get("default_samplerate") or 48000)
                    extra = None
                    if host == "Windows WASAPI":
                        try:
                            extra = sd.WasapiSettings(auto_convert=True)
                        except Exception:
                            extra = None
                    try:
                        self._dead = False
                        stream = sd.OutputStream(
                            samplerate=rate, device=dev, channels=ch, dtype="float32", latency=STREAM_LATENCY,
                            callback=self._callback, finished_callback=self._on_finished,
                            extra_settings=extra)
                        stream.start()
                    except Exception as e:
                        tried.append(f"{host} {ch}ch: {e}")
                        continue
                    self._stream = stream
                    self.channels, self.rate, self.host = ch, rate, host
                    self.device_name = str(info.get("name", ""))
                    try:
                        self.latency_ms = float(stream.latency) * 1000.0
                    except Exception:
                        self.latency_ms = 0.0
                    fmt = (ch, rate)
                    if self._fmt != fmt:          # clips are decoded for one exact format
                        with self._cache_lock:
                            self._clips.clear()
                            self._failed.clear()
                        self._fmt = fmt
                    return True
            raise RuntimeError(tried[-1] if tried else "no audio output device found")
        except Exception as e:
            self.error = str(e)
            logging.warning(f"Quick Fire engine: could not open audio output: {e}")
            return False
        finally:
            self._opening = False
            self._emit("opened" if self.active else "failed")

    def can_retry_open(self):
        return (not self._opening) and (time.time() - self._last_open_try) > 8.0

    def _on_finished(self):
        if not self._closing:
            self._dead = True
            self.error = "the audio output stopped (device removed or changed?)"
            self._emit("failed")

    def _close_stream(self):
        s, self._stream = self._stream, None
        with self._lock:
            self._voices = []
            self._last_voice = None
        if s is not None:
            try:
                s.stop()
            except Exception:
                pass
            try:
                s.close()
            except Exception:
                pass

    def close(self):
        self._closing = True              # from this moment on the engine counts as inactive
        with self._op_lock:
            self._close_locked()

    def begin_close(self):
        """Closes on a helper thread; the engine is inactive immediately."""
        self._closing = True
        threading.Thread(target=self.close, name="qf-close", daemon=True).start()

    def _close_locked(self):
        self._closing = True
        try:
            with self._cond:
                self._queue.clear()
                self._queued.clear()
            self._close_stream()
        except Exception as e:
            logging.warning(f"Quick Fire engine: close failed: {e}")
        self._dead = False
        self._closing = False
        self.error = ""
        self._emit("closed")

    # ---------- audio callback (runs on the audio thread: keep it short and never raise) ----------
    def _callback(self, outdata, frames, time_info, status):
        try:
            outdata.fill(0)
            with self._lock:
                if not self._voices:
                    return
                gain = self._gain
                done = []
                for v in self._voices:
                    n = min(frames, len(v.data) - v.pos)
                    if n > 0:
                        seg = v.data[v.pos:v.pos + n] * gain
                        if v.fade_pos >= 0:
                            idx = v.fade_pos + np.arange(n)
                            ramp = np.clip(1.0 - idx / float(FADE_SAMPLES), 0.0, 1.0).astype(np.float32)
                            seg = seg * ramp[:, None]
                            v.fade_pos += n
                        outdata[:n] += seg
                        v.pos += n
                    if v.pos >= len(v.data) or (v.fade_pos >= FADE_SAMPLES):
                        done.append(v)
                if done:
                    self._voices = [v for v in self._voices if v not in done]
            np.clip(outdata, -1.0, 1.0, out=outdata)
        except Exception:
            try:
                outdata.fill(0)
            except Exception:
                pass

    # ---------- preloading ----------
    def preload(self, paths, first=False):
        """Queue files for background decoding. first=True puts them in front of the queue."""
        if not self.active or not paths:
            return
        with self._cond:
            items = []
            for p in paths:
                k = self._key(p)
                with self._cache_lock:
                    have = k in self._clips
                if have or k in self._queued or k in self._failed:
                    continue
                items.append((k, p))
            if first:
                for k, p in reversed(items):
                    self._queue.appendleft((k, p))
                    self._queued.add(k)
            else:
                for k, p in items:
                    self._queue.append((k, p))
                    self._queued.add(k)
            if items and not self._worker_running:
                self._worker_running = True       # decided under the lock, so the worker can never miss work
                self._worker = threading.Thread(target=self._work, name="qf-preload", daemon=True)
                self._worker.start()
            self._cond.notify()

    def _work(self):
        while True:
            with self._cond:
                if not self._queue:
                    self._cond.wait(timeout=5.0)
                    if not self._queue:
                        self._loading_now = None
                        self._worker_running = False
                        return
                k, p = self._queue.popleft()
                self._queued.discard(k)
                self._loading_now = k
            if not self.active:
                continue
            fmt = self._fmt
            t0 = time.time()
            try:
                info = probe_audio(self._ffmpeg, p)
                dur = info.get("duration")
                if dur and dur > MAX_CLIP_SECONDS:
                    raise RuntimeError(f"longer than {MAX_CLIP_SECONDS} s (plays through VLC)")
                data = decode_clip(self._ffmpeg, p, fmt[0], fmt[1])
                if fmt != self._fmt:          # output was re-opened in another format meanwhile
                    continue
                size = data.nbytes
                with self._cache_lock:
                    self._clips[k] = {"data": data, "info": info, "bytes": size,
                                      "seconds": len(data) / float(fmt[1]), "decode_s": time.time() - t0}
                    total = sum(c["bytes"] for c in self._clips.values())
                    while total > MAX_CACHE_BYTES and len(self._clips) > 1:
                        _, old = self._clips.popitem(last=False)
                        total -= old["bytes"]
            except Exception as e:
                self._failed[k] = str(e)
                logging.warning(f"Quick Fire engine: could not preload {p}: {e}")
            self._emit("progress")

    def retain(self, paths):
        """Forget everything that is not in `paths` (a scene change must not keep the old scene's sounds)."""
        keep = {self._key(p) for p in paths}
        playing = set()
        try:
            with self._lock:
                playing = {v.key for v in self._voices}
        except Exception:
            pass
        with self._cond:
            self._queue = collections.deque([(k, p) for (k, p) in self._queue if k in keep])
            self._queued = {k for (k, _) in self._queue}
        with self._cache_lock:
            for k in [k for k in self._clips if k not in keep and k not in playing]:
                del self._clips[k]
            for k in [k for k in self._failed if k not in keep]:
                del self._failed[k]

    def is_ready(self, path):
        with self._cache_lock:
            return self._key(path) in self._clips

    # ---------- playing ----------
    def fire(self, path, gain=None):
        """Starts a preloaded clip right now. False = not possible (caller uses VLC instead)."""
        try:
            if not self.active:
                return False
            k = self._key(path)
            with self._cache_lock:
                clip = self._clips.get(k)
                if clip is None:
                    return False
                self._clips.move_to_end(k)
                data = clip["data"]
            if gain is not None:
                self.set_gain(gain)
            self._start(data, k)
            return True
        except Exception as e:
            logging.warning(f"Quick Fire engine: fire failed: {e}")
            return False

    def play_array(self, data, key="__test__"):
        try:
            if not self.active:
                return False
            self._start(data, key)
            return True
        except Exception as e:
            logging.warning(f"Quick Fire engine: play failed: {e}")
            return False

    def _start(self, data, key):
        v = _Voice(data, key)
        with self._lock:
            for old in self._voices:          # a new sound replaces the one that is still playing
                if old.fade_pos < 0:
                    old.fade_pos = 0
            self._voices.append(v)
            self._last_voice = v

    def stop_all(self):
        try:
            with self._lock:
                for v in self._voices:
                    if v.fade_pos < 0:
                        v.fade_pos = 0
        except Exception:
            pass

    def playback_state(self):
        """(is_playing, fraction 0..1) of the newest sound; the output delay is subtracted."""
        try:
            with self._lock:
                v = self._last_voice
                if v is None or v not in self._voices:
                    return False, 0.0
                lat = int(self.latency_ms / 1000.0 * self.rate)
                return True, max(0.0, min(1.0, (v.pos - lat) / float(max(1, len(v.data)))))
        except Exception:
            return False, 0.0

    def speaker_test(self):
        if not self.active:
            return False
        return self.play_array(make_speaker_test(self.channels, self.rate), "__speaker_test__")
