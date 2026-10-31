"""Generates a small synthesized demo project from scratch (optional).
Everything is synthesized here (tones, noise, gradients) so there are no licence issues.
The output goes to synthetic_demo/sample_project and synthetic_demo/sample_libraries,
so it never touches the real demo in sample_project/.
Needs: numpy, Pillow and an `ffmpeg` on PATH (or imageio-ffmpeg installed).
Run from the repository root:  python tools/make_sample_project.py
"""
import json
import os
import shutil
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESS = os.path.join(ROOT, "synthetic_demo", "sample_project")
LIBS = os.path.join(ROOT, "synthetic_demo", "sample_libraries")
SR = 22050
rng = np.random.default_rng(7)


def ffmpeg_exe():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def save_ogg(path, samples):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    s = np.clip(samples, -1, 1)
    pcm = (s * 32767).astype(np.int16)
    tmp = path + ".wav"
    with wave.open(tmp, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    subprocess.run([ffmpeg_exe(), "-y", "-v", "quiet", "-i", tmp, "-c:a", "libvorbis", "-q:a", "3", path],
                   check=True)
    os.remove(tmp)


def t(sec):
    return np.arange(int(SR * sec)) / SR


def env(n, a=0.02, r=0.3):
    e = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    e[:na] = np.linspace(0, 1, na)
    e[-nr:] = np.linspace(1, 0, nr)
    return e


def note(freq, sec, vol=0.3, harm=(1, .5, .25)):
    x = t(sec)
    y = sum(h * np.sin(2 * np.pi * freq * (i + 1) * x) for i, h in enumerate(harm))
    return vol * y / max(harm) * env(len(x), 0.01, min(0.25, sec / 2))


def melody(notes, step, loops=1, vol=0.3):
    out = []
    for f, d in notes * loops:
        out.append(note(f, d, vol) if f else np.zeros(int(SR * d)))
    return np.concatenate(out)


def pad(freqs, sec, vol=0.12):
    x = t(sec)
    y = sum(np.sin(2 * np.pi * f * x) + .4 * np.sin(2 * np.pi * f * 2.003 * x) for f in freqs)
    return vol * y / len(freqs) * env(len(x), 1.0, 1.0)


def noise(sec, lp=0.05, vol=0.4):
    n = rng.standard_normal(int(SR * sec))
    out = np.zeros_like(n)
    a = lp
    for i in range(1, len(n)):          # one-pole low-pass
        out[i] = out[i - 1] + a * (n[i] - out[i - 1])
    return vol * out / np.max(np.abs(out))


# ------------------------------------------------------------------ audio
A, B, C, D, E, F, G = 220, 246.94, 261.63, 293.66, 329.63, 349.23, 392.0
tavern = melody([(A, .25), (C * 1.0, .25), (E, .25), (C, .25), (D, .25), (F, .25), (A, .25), (F, .25)] * 2, 0, loops=2, vol=.28)
road = melody([(C, .5), (E, .5), (G, .5), (E, .5), (D, .5), (F, .5), (A, .5), (0, .5)], 0, loops=2, vol=.28)
save_ogg(os.path.join(SESS, "Demo Session", "The Tavern", "music", "Tavern Fiddle.ogg"), tavern)
save_ogg(os.path.join(SESS, "Demo Session", "The Tavern", "music", "Warm Hearth.ogg"), pad([110, 165, 220], 10))
save_ogg(os.path.join(SESS, "Demo Session", "Forest Road", "music", "Road Theme.ogg"), road)

knock = np.concatenate([noise(0.08, .4, .9) * env(int(SR * .08), .001, .06), np.zeros(int(SR * .15))] * 3)
save_ogg(os.path.join(SESS, "Demo Session", "The Tavern", "sfx", "Door Knock.ogg"), knock)
save_ogg(os.path.join(SESS, "Demo Session", "The Tavern", "sfx", "Crowd Murmur.ogg"), noise(8, .02, .5))
save_ogg(os.path.join(SESS, "Demo Session", "Forest Road", "sfx", "Wind In Trees.ogg"), noise(8, .01, .55))
x = t(1.2)
save_ogg(os.path.join(SESS, "Demo Session", "The Tavern", "quickfire", "Sword Clang.ogg"),
         .5 * (np.sin(2 * np.pi * 1760 * x) + .6 * np.sin(2 * np.pi * 2637 * x)) * np.exp(-5 * x))
x = t(1.5)
save_ogg(os.path.join(SESS, "Demo Session", "The Tavern", "quickfire", "Dramatic Hit.ogg"),
         .8 * (np.sin(2 * np.pi * 55 * x) + .5 * noise(1.5, .05, 1)) * np.exp(-3 * x))
x = t(1.0)
save_ogg(os.path.join(SESS, "Demo Session", "The Tavern", "quickfire", "Whoosh.ogg"),
         noise(1.0, .15, .8) * np.sin(np.pi * x) ** 2)

save_ogg(os.path.join(LIBS, "music", "Ambient", "Calm Pad.ogg"), pad([130.81, 196, 261.63], 12))
save_ogg(os.path.join(LIBS, "music", "Ambient", "Night Wind.ogg"), noise(10, .008, .5))
beat = np.zeros(int(SR * 8))
for k in range(16):
    s0 = int(k * .5 * SR)
    kick = np.sin(2 * np.pi * 60 * t(.3)) * np.exp(-12 * t(.3)) * .9
    beat[s0:s0 + len(kick)] += kick
    if k % 2:
        beat[s0:s0 + int(.15 * SR)] += noise(.15, .4, .4)
save_ogg(os.path.join(LIBS, "music", "Combat", "Battle Pulse.ogg"), beat)
save_ogg(os.path.join(LIBS, "music", "Combat", "Boss", "Final Drone.ogg"), pad([55, 58.27, 82.4], 12, .25))
save_ogg(os.path.join(LIBS, "sfx", "Weather", "Rain Loop.ogg"), noise(8, .3, .5))
save_ogg(os.path.join(LIBS, "sfx", "Weather", "Thunder.ogg"), noise(4, .02, .9) * np.exp(-1.2 * t(4)))
save_ogg(os.path.join(LIBS, "sfx", "Dungeon", "Dripping.ogg"),
         np.concatenate([note(900, .06, .4, (1,)) * np.exp(-30 * t(.06)), np.zeros(int(SR * 1.2))] * 5))


# ------------------------------------------------------------------ images
def font(size):
    try:
        return ImageFont.load_default(size)
    except TypeError:
        return ImageFont.load_default()


def backdrop(path, top, bottom, title, shapes):
    w, h = 1280, 720
    im = Image.new("RGB", (w, h))
    px = im.load()
    for yy in range(h):
        k = yy / h
        c = tuple(int(top[i] * (1 - k) + bottom[i] * k) for i in range(3))
        for xx in range(w):
            px[xx, yy] = c
    d = ImageDraw.Draw(im)
    for kind, box, col in shapes:
        (d.ellipse if kind == "e" else d.rectangle)(box, fill=col)
    im = im.filter(ImageFilter.GaussianBlur(2))
    d = ImageDraw.Draw(im)
    d.text((w // 2, 90), title, font=font(64), fill=(245, 235, 210), anchor="mm")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path, quality=82)


tav = os.path.join(SESS, "Demo Session", "The Tavern", "visuals")
road_v = os.path.join(SESS, "Demo Session", "Forest Road", "visuals")
backdrop(os.path.join(tav, "Tavern Interior.jpg"), (60, 30, 18), (20, 10, 6), "The Rusty Flagon",
         [("r", (180, 420, 1100, 470), (92, 58, 30)), ("e", (560, 120, 720, 280), (255, 190, 90)),
          ("r", (100, 500, 1180, 720), (40, 24, 14))])
backdrop(os.path.join(tav, "Cellar.jpg"), (25, 28, 40), (8, 8, 14), "The Cellar",
         [("r", (150, 300, 330, 600), (60, 45, 35)), ("r", (900, 280, 1100, 620), (60, 45, 35))])
backdrop(os.path.join(road_v, "Forest Road.jpg"), (90, 140, 170), (24, 52, 28), "The Forest Road",
         [("e", (900, 80, 1100, 280), (250, 240, 190)), ("r", (0, 520, 1280, 720), (50, 36, 22))])
tok = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
dd = ImageDraw.Draw(tok)
dd.ellipse((8, 8, 192, 192), fill=(200, 40, 40, 255), outline=(255, 230, 200, 255), width=8)
dd.text((100, 100), "NPC", font=font(56), fill=(255, 255, 255, 255), anchor="mm")
os.makedirs(tav, exist_ok=True)
tok.save(os.path.join(tav, "Token Red.png"))


# ------------------------------------------------------------------ project files
SX, SY = (5000 - 1920) // 2, (5000 - 1080) // 2          # stage origin used by the app
R = "{ROOT}/Demo Session"


def layout(name, scene, items):
    path = os.path.join(SESS, "Demo Session", scene, "layouts", name + ".json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    vis = []
    for z, (file, folder_scene, x, y, sc, op) in enumerate(items, 1):
        vis.append({"file": file, "x": SX + x, "y": SY + y, "scale": sc, "z": z, "opacity": op,
                    "path": f"{R}/{folder_scene}/visuals/{file}"})
    json.dump({"visuals": vis, "blanking": []}, open(path, "w", encoding="utf-8"), indent=2)


layout("Tavern", "The Tavern", [("Tavern Interior.jpg", "The Tavern", 0, 0, 1.5, 1.0)])
layout("Tavern + NPC", "The Tavern", [("Tavern Interior.jpg", "The Tavern", 0, 0, 1.5, 1.0),
                                      ("Token Red.png", "The Tavern", 800, 600, 1.0, 1.0)])
layout("Cellar", "The Tavern", [("Cellar.jpg", "The Tavern", 0, 0, 1.5, 1.0)])
layout("Road", "Forest Road", [("Forest Road.jpg", "Forest Road", 0, 0, 1.5, 1.0)])


def settings(scene, linked, playlist=None):
    d = {"use_scene_music": True, "use_scene_visuals": True, "use_scene_sfx": True,
         "improv_category": "", "use_playlist": False, "is_shuffle": False, "fade_duration": 1.0,
         "music_volume": 70, "sfx_volume": 70, "collapsed_sections": {},
         "linked_assets": linked, "music_orders": {}, "music_playlist": playlist or [],
         "music_playlist_name": "", "music_playlist_source": "", "orders": {}}
    if scene == "The Tavern":
        d.update({"quickfire_path": f"{R}/The Tavern/quickfire", "quickfire_enabled": True})
    p = os.path.join(SESS, "Demo Session", scene, "scene_settings.json")
    json.dump(d, open(p, "w", encoding="utf-8"), indent=2)


settings("The Tavern", {"music": {}, "sfx": {}, "visuals": {}, "layouts": {}},
         [{"name": "Tavern Fiddle.ogg", "path": f"{R}/The Tavern/music/Tavern Fiddle.ogg"},
          {"name": "Battle Pulse.ogg", "path": "{MUSIC}/Combat/Battle Pulse.ogg"}])
settings("Forest Road", {
    "music": {"Tavern Fiddle.ogg": f"{R}/The Tavern/music/Tavern Fiddle.ogg"},
    "sfx": {"Door Knock.ogg": f"{R}/The Tavern/sfx/Door Knock.ogg"},
    "visuals": {"Tavern Interior.jpg": f"{R}/The Tavern/visuals/Tavern Interior.jpg"},
    "layouts": {}})
pl = os.path.join(SESS, "Demo Session", "The Tavern", "playlists", "Demo Mix.json")
os.makedirs(os.path.dirname(pl), exist_ok=True)
json.dump({"name": "Demo Mix", "version": 1, "tracks": [
    {"name": "Tavern Fiddle.ogg", "path": f"{R}/The Tavern/music/Tavern Fiddle.ogg"},
    {"name": "Calm Pad.ogg", "path": "{MUSIC}/Ambient/Calm Pad.ogg"},
    {"name": "Battle Pulse.ogg", "path": "{MUSIC}/Combat/Battle Pulse.ogg"},
    {"name": "Final Drone.ogg", "path": "{MUSIC}/Combat/Boss/Final Drone.ogg"}]},
    open(pl, "w", encoding="utf-8"), indent=2)
print("sample project written")
