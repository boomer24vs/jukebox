# Changelog

## [0.2.0] - 2026-10-04

### Added
- Disc chest: a small chest next to the jukebox, with a bouncing indicator arrow. Click it to open a
  Minecraft chest GUI on the right with every track as a music disc (27 per page, `<` `>` to change page).
  Hover a disc for the in-game tooltip, click it to play that track; the chest closes.
- Tracks without an official disc get their own label colour, as a rainbow gradient.
- Autoplay: when a track ends, another random one starts (`"autoplay"` in `PRESET`).

### Fixed
- Black square around the jukebox when the machine's hostname changed after login
  (python-xlib could not use the X cookie, so transparency was turned off).

## [0.1.0] - 2026-10-04

First release.

- Isometric pixel-art jukebox on the desktop, drawn by code (no game texture included).
- Click: random C418 track, never the same twice in a row; the disc rises out of the jukebox.
- "Now Playing" message in the Minecraft font with the in-game rainbow fade.
- Music notes while playing, bigger and more frequent when the volume is louder.
- Mouse wheel on the jukebox: volume.
- Drag to move it anywhere on the desktop, smoothly.
- Stays under your apps, like a desktop widget.
- Compact mode after 10 s idle: small jukebox, title and an experience-style progress bar.
- Clicks on transparent areas go through to what is below.
- `install.sh`: virtual environment, music extraction from your Minecraft install, app menu shortcut.

[0.2.0]: https://github.com/boomer24vs/jukebox/compare/v0.1.0...main
[0.1.0]: https://github.com/boomer24vs/jukebox/releases/tag/v0.1.0
