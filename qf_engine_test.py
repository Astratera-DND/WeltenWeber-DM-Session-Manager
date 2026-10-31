"""
Try the fast Quick Fire engine on THIS computer, without starting the whole program.

    python tools/qf_engine_test.py                      -> opens the output, beeps once per speaker
    python tools/qf_engine_test.py clip1.mkv clip2.mp4  -> also loads your files and plays each one

It prints what the output device offers, how many channels ffmpeg really decodes from each of your
files (a Dolby Digital Plus 7.1 file may come out as 5.1 here, and that is good to know), how long
loading took, and plays the files straight from memory.
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import sounddevice as sd
import quickfire_engine as qe


def find_ffmpeg():
    import shutil
    here = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    for name in ("ffmpeg.exe", "ffmpeg"):
        p = os.path.join(here, name)
        if os.path.isfile(p):
            return p
    found = shutil.which("ffmpeg")
    if found:
        return found
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def main(files):
    ffmpeg = find_ffmpeg()
    print("ffmpeg:", ffmpeg or "NOT FOUND")
    print("\nHost APIs / default outputs:")
    for a in sd.query_hostapis():
        d = a.get("default_output_device", -1)
        if d >= 0:
            info = sd.query_devices(d)
            print(f"  {a['name']:22s} -> {info['name']}  ({info['max_output_channels']} channels, {int(info['default_samplerate'])} Hz)")
    eng = qe.QuickFireEngine(sd, ffmpeg)
    t = time.time()
    if not eng.open():
        print("\nCould not open the output:", eng.error)
        return
    print(f"\nOpened in {time.time() - t:.2f} s -> {eng.describe()}")

    for f in files:
        print("\n" + f)
        info = qe.probe_audio(ffmpeg, f)
        print(f"  ffmpeg sees: codec={info['codec']}, {info['rate']} Hz, layout={info['layout']} ({info['channels']} channels), "
              f"duration={info['duration']}")
        t = time.time()
        try:
            data = qe.decode_clip(ffmpeg, f, eng.channels, eng.rate)
        except Exception as e:
            print("  could not decode:", e)
            continue
        print(f"  decoded in {time.time() - t:.2f} s -> {len(data) / eng.rate:.2f} s of audio, "
              f"{data.nbytes / 1048576:.1f} MB in memory")
        eng.preload([f])
        t0 = time.time()
        while not eng.is_ready(f) and time.time() - t0 < 60:
            time.sleep(0.05)

    print("\nSpeaker test, in this order:", "  ->  ".join(qe.SPEAKER_NAMES.get(eng.channels, [])))
    eng.speaker_test()
    time.sleep(eng.channels * 0.7 + 0.5)

    for f in files:
        if eng.is_ready(f):
            print("Playing from memory:", os.path.basename(f))
            eng.set_gain(0.8)
            t = time.perf_counter()
            eng.fire(f)
            print(f"  fire() returned after {(time.perf_counter() - t) * 1000:.2f} ms "
                  f"(sound starts within about {eng.latency_ms:.0f} ms of that)")
            while eng.playback_state()[0]:
                time.sleep(0.05)
            time.sleep(0.3)
    eng.close()
    print("\nDone.")


if __name__ == "__main__":
    main(sys.argv[1:])
