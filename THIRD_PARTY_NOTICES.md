# Third-party software

The WeltenWeber DM Tool **source code** is MIT-licensed (see `LICENSE`).

The **Windows download** is a PyInstaller build that bundles the components below. They keep their own licenses.
Because the bundle includes PyQt6, which is available under GPL-3.0 (or a commercial license from Riverbank Computing),
the bundled Windows binaries are distributed under the terms of the GPL-3.0. The corresponding source code of this
program is available at <https://github.com/Astratera-DND/WeltenWeber-DM-Tool>.

| Component | License | Where to get it / its source |
|---|---|---|
| PyQt6 | GPL-3.0 or commercial (Riverbank Computing) | <https://www.riverbankcomputing.com/software/pyqt/> |
| Qt 6 (shipped with PyQt6) | LGPL-3.0 / GPL-3.0 | <https://www.qt.io/> |
| python-vlc | LGPL-2.1-or-later | <https://github.com/oaubert/python-vlc> |
| VLC / libVLC 3.0.21 | libVLC and libVLCcore: LGPL-2.1-or-later. The VLC player and some of the bundled plugins (for example the x264 and x265 codec plugins) are GPL. | <https://www.videolan.org/> — source: <https://download.videolan.org/pub/videolan/vlc/3.0.21/> |
| FFmpeg (via imageio-ffmpeg) | LGPL-2.1-or-later / GPL-2.0-or-later, depending on the build | <https://ffmpeg.org/> — wrapper `imageio-ffmpeg` (BSD-2-Clause): <https://github.com/imageio/imageio-ffmpeg> |
| sounddevice, PortAudio | MIT | <https://github.com/spatialaudio/python-sounddevice> |
| soundfile, libsndfile | BSD-3-Clause, LGPL-2.1-or-later | <https://github.com/bastibe/python-soundfile> |
| NumPy | BSD-3-Clause | <https://numpy.org/> |
| PyInstaller (build tool) | GPL-2.0-or-later with a bootloader exception | <https://pyinstaller.org/> |

The release zip also contains the full VLC license text as `VLC-COPYING.txt`.

This list is a good-faith summary, not legal advice. Each project's own license file is the authoritative text.
