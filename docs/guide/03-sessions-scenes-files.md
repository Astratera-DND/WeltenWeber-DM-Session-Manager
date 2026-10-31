# Sessions, scenes and your files

## The idea

* A **session** is one game evening (or one chapter, up to you).
* A **scene** is a place or moment inside it: *The Tavern*, *Forest Road*, *Boss Fight*.
* Each scene has its own music, sounds, pictures, layouts, volumes and settings. Switching scenes switches all of that.

## How it looks on disk

```
Sessions folder
└── Session
    └── Scene
        ├── music/      sfx/      visuals/     layouts/
        ├── scripts/    quickfire/    playlists/
        └── scene_settings.json
```

You never have to create these by hand. Press **+** next to *Sessions* or *Scenes*, type a name, done.
You can also drop files straight into a scene's folders with Windows Explorer and press **🔄 RELOAD (Ctrl+R)**.

## Opening a scene

Click a session, then a scene. The panels fill up. Nothing starts playing yet. You decide when, with **START ALL**,
the Play buttons, or double-clicks. (If you are recording, the scene change is written into the recording markers.)

## Sharing one file with many scenes (linking)

Got a great battle track you want in five scenes? Don't copy it five times. **Link** it:

* **Right-click** a track, SFX or visual → **🔗 Link to…**, then tick the scenes that should get it.
  The file stays where it is. The other scenes just point at it.
* **Right-click a scene** → **➕ Add from scene: music / sfx / visuals / layouts** pulls everything of that kind from the
  scene you clicked into the current scene.
* The **🔗** button in a panel header lets you pick any files from your PC and add them to the scene as links.
* To undo a link: right-click the item → **🔗 Remove Link (Keep File)**. The file itself is not deleted.

## Reordering

Drag items in any list to put them in your order. The order is saved per scene.

## Where is everything saved?

Per scene in `scene_settings.json` (volumes, shuffle, the chosen genre or playlist, links, folded panels, fade time),
plus your layouts and playlists as small files in the scene folders. All of it uses relative paths,
so you can copy the whole campaign to another PC. See [Moving to another PC](12-moving-between-pcs.md).
