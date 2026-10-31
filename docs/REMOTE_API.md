# Director remote-control command reference (all fields optional, combine freely)

The Session Manager writes ONE json object to `director_remote_command.json` (next to main.py / the exe).
The Director polls it every 0.75 s and applies it when the file's modified time changes.

## Scene / layout
| field | meaning |
|---|---|
| `session`, `scene` | switch to that scene (same as clicking it; starts layout, music, sfx) |
| `layout` | load that layout file (e.g. `"Tavern.json"`) |
| `switch_scene: false` | with session+scene: do NOT switch. `music`, `sfx`, `quickfire` are looked up in THAT scene's own settings and played immediately. (`playlist` / genre select are ignored in this mode: they change the active scene's panel.) |

## Music
| field | meaning |
|---|---|
| `music: "track.mp3"` | track from the active scene's current music list (as before) |
| `music: "C:/full/path/track.mp3"` | any audio file by absolute path |
| `music_genre: "Jazz/Bebop"` + `music: "x.mp3"` | play x.mp3 from that genre folder (path relative to the music root, `/` for sub-levels, any depth). Does not change the UI or scene settings |
| `music_genre: "Jazz"` (without `music`) | select that genre in the music panel (leaves folder/playlist mode). Add `play: true` to start it |
| `playlist: "Name"` | load a saved playlist and switch the music panel to "Use Playlist". Accepts the playlist name, the label `"Session / Scene  —  Name"`, a file name (`Name.json`) or the full path. On duplicates, the target/active scene's playlist wins. Add `music: "track.mp3"` to start a track of it, or `play: true` to start it |
| `playlist_off: true` | leave playlist mode (back to the genre list) |

## SFX (loops, like the Play button)
| field | meaning |
|---|---|
| `sfx: "door.wav"` | file from the active scene's SFX list |
| `sfx_category: "Rain"` + `sfx: "x.wav"` | file from that folder of the SFX library (`""` or `"--- Root Folder ---"` = library root). Does not change the UI |
| `sfx: "C:/full/path/x.wav"` | any file by absolute path |
| `sfx_stop: true` | stop the SFX |

## Quickfire
`quickfire: "file.wav"` selects it, `quickfire_fire: true` fires it (with `switch_scene:false` it fires from that scene's quickfire folder; a file name is required then).

## Where the data lives (for listing)
* Music library root: `improv_music_path` in `director_config.json`. Genres = every sub-folder at any depth; ID = relative path with `/` (e.g. `Jazz/Bebop`). Audio: mp3 flac wav ogg m4a aac wma opus.
* SFX library root: `improv_sfx_path` in `director_config.json`. Categories = its direct sub-folders (+ the root itself).
* A scene's own files: `<root>/<session>/<scene>/music|sfx|visuals|layouts|scripts` + links in `scene_settings.json` -> `linked_assets.music|sfx|...` (name -> path, may start with a `{ROOT}`-style token, see "Path tokens" below).
* Scene state: `<scene>/scene_settings.json`: `use_scene_music`, `improv_category` (genre), `use_playlist`, `music_playlist` (working playlist, `[{name,path}]`), `use_scene_sfx`, `improv_sfx_category`, `quickfire_path`.
* Saved playlists (GLOBAL list = scan all): `<root>/<session>/<scene>/playlists/<Name>.json` with `{"name": "...", "tracks": [{"name": "...", "path": "..."}]}`. The list of every playlist = every `playlists/*.json` under every session/scene.

## Path tokens in the project files (since the portable-paths update)
Paths that the app saves into `scene_settings.json` (`linked_assets`, `quickfire_path`, `music_playlist`, `music_playlist_source`), into
`playlists/*.json` (track `path`) and into layout files (visual `path`) are stored with a leading token instead of a machine-specific folder:

| token | means |
|---|---|
| `{ROOT}` | the sessions folder (`root_path` in `director_config.json`) |
| `{MUSIC}` | `improv_music_path` in `director_config.json` |
| `{SFX}` | `improv_sfx_path` in `director_config.json` |
| `{VISUALS}` | `improv_visuals_path` in `director_config.json` |

Example: `{ROOT}/Demo Session/The Tavern/visuals/Cellar.jpg` -> `<root_path>/Demo Session/The Tavern/visuals/Cellar.jpg`.
A tool that reads these files directly must replace the token with the matching folder (forward or back slashes both work). Older absolute
paths may still appear in projects that were not converted yet, so accept both forms. The remote command fields above (`music`, `sfx`, `playlist`, ...)
are resolved by the app itself, so a tool that only writes `director_remote_command.json` needs no change.

## Where the files are
`director_remote_command.json` and `director_config.json` sit **next to the program** (next to `main.py`, or next to the `.exe`). They are the same
place as in earlier versions. A new download or a moved `.exe` is a new location, so point the session tool at the folder of the version you actually run.
