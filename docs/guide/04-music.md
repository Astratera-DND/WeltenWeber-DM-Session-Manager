# Music

The **Music** panel on the left decides *what* plays. The **Audio mixer** on the right decides *how* it plays.

## Three places to take music from

Under the *Music* title you pick the source:

| Setting | What you get |
|---|---|
| **Use Music from Folder** (ticked) | The tracks in this scene's own `music` folder, plus anything you linked. |
| Untick it → **genre library** | A big shared music folder, sorted into genre folders (*Ambient*, *Combat*, *Combat/Boss*). Choose the genre from the dropdown. Folders inside folders work and show up as `Parent/Child`. Set the library folder with the **…** button. |
| **Use Playlist** | A playlist you built (see below). A dropdown lists every saved playlist in your campaign. **↻** rescans for new ones. |

Each scene remembers its choice. Your scene can start with "Tavern music" and the next one with the "Combat" genre.

## Playing

* **Double-click** a track to play it, or select it and press **🎵 Play** in the mixer.
* **Next / Prev** jump through the list. When a track ends, the next one starts on its own.
* **In Order** plays top to bottom. **Shuffle** picks a random track (never the same one twice in a row).
* Changing tracks fades the old one out first, so it never cuts off harshly.
* **Music volume** is the slider under the buttons. It is saved per scene.
* The mixer shows what is **Now** playing, how much time is left, and what comes **Next**.

## Preview waveform

Tick **〰️ Preview Waveform** to see the shape of the current track with a red line for the playhead. It is handy for finding
the loud part of a battle song. It is only a display. You can't click it to jump around.

## Reorder, filter and playlists (the ☰ button)

Press **☰ Reorder / Filter / Playlist** for the big window.

![Playlist window](../images/playlist-manager.png)

When you use the scene folder, you get a simple list where you can:

* **Drag** tracks into the order you like.
* **Search** by typing part of a file name. This only hides rows, it never deletes anything.
* **🚫 Blacklist** tracks you never want played automatically (shown red).
* **✅ Whitelist** tracks to restrict automatic playing to only those (shown green).
* **💾 Save Current Order as Playlist…** turns the list into a playlist.

Pressing **Blacklist** or **Whitelist** a second time on tracks that already have that mark takes it off again (back to normal).

Blacklisting only affects *automatic* playing (Next, Shuffle, auto-advance). You can still double-click a blacklisted track.

In the bigger genre/playlist window, **🚫 Blacklist / ✅ Whitelist / Clear Filter** buttons sit under **both** lists. The top list (genre tracks) works on its own, so you do not need a playlist. The bottom list (your playlist) works too. Red and green show in both lists and in the main music list. Filters are remembered per scene and go by file name, so two files with the same name in different genres share one setting.

When you use the genre library or a playlist, you get the bigger playlist window:

1. Pick a genre on the left. Its tracks appear in the middle.
   Tick **Include subfolders** to see the tracks of sub-genres too, or **Search all genres** to search everything.
2. **Double-click** a track to preview it. Select tracks and press **➕ Add Selected to Playlist**.
3. In the lower half, drag the playlist into order, remove tracks, or mark black or white.
4. Type a name and press **💾 Save**. The playlist is stored in this scene's `playlists` folder.
5. **📂 Load into editor** brings a saved playlist back (from any scene), either replacing or merging.
6. Tick **Play from this playlist** to use it, which does the same as **Use Playlist** in the panel.

Grey playlist entries mean the file is missing on this PC.
