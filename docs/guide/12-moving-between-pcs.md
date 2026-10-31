# Moving to another PC

You prepared your campaign at home and want to run it at a friend's table? Good news: it's built for that.

## What to copy

Just copy your **whole sessions folder** (the one you choose with 📁 Browse…). Music, sounds, visuals, layouts and playlists
inside it come along, and the project files refer to them with **relative paths**.
Under the hood, the files use short placeholders like `{ROOT}` (your sessions folder) instead of `D:\Campaigns\...`.

## On the new PC

1. Start the tool and click **📁 Browse…**. Choose the copied sessions folder.
2. If you use big libraries (a genre music folder, an SFX folder), set their folders once with the **…** buttons.
   These settings are about the PC, not the campaign. They live in `director_config.json` next to the program.
3. Done! Layouts find their pictures, playlists find their tracks.

## Files from outside your sessions folder

If a scene points at a file that lives *outside* your sessions folder and *outside* your libraries (say, `C:\Users\Me\Desktop\boom.wav`),
that path can't travel. Move the file into the scene's folders, or into one of your libraries.

## 🧳 Make a project portable

Projects made with older versions stored full paths. Press **🧳** next to *Browse…* to convert the whole project.
The tool asks first, **makes a backup** (a `portable_backup_…` folder next to the program), converts everything,
and shows you a list of the few files that point outside the project.
Old projects also keep working without the conversion, as the tool tries to find files again under your sessions folder.
