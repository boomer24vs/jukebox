#!/usr/bin/env bash
# Jukebox installer: Python environment, C418 music from your Minecraft install, app menu shortcut.
# Usage: ./install.sh [path/to/minecraft/assets]
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

step() { printf '\n\033[1;32m==>\033[0m %s\n' "$1"; }
warn() { printf '\033[1;33m!!\033[0m %s\n' "$1"; }

step "Checking Python"
if ! command -v python3 >/dev/null; then
    echo "python3 not found: install Python 3.10 or newer with your package manager." >&2
    exit 1
fi
python3 -c 'import sys; sys.exit(sys.version_info < (3, 10))' || {
    echo "Python 3.10 or newer is required (found $(python3 --version))." >&2
    exit 1
}
python3 --version

step "Creating the virtual environment (.venv) and installing dependencies"
python3 -m venv .venv || {
    echo "Could not create the venv. On Debian/Ubuntu: sudo apt install python3-venv" >&2
    exit 1
}
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r requirements.txt

step "Copying the C418 music from your Minecraft install"
if compgen -G "sounds/*.ogg" >/dev/null; then
    echo "Music already in sounds/, skipped (run .venv/bin/python extract_music.py to refresh it)."
else
    .venv/bin/python extract_music.py "$@"
fi

step "Checking the Minecraftia font"
FONT_OK=1
if [ ! -f fonts/Minecraftia-Regular.ttf ]; then
    FONT_OK=0
    warn "Font missing. Download Minecraftia from https://www.dafont.com/minecraftia.font"
    warn "and put Minecraftia-Regular.ttf in $DIR/fonts/"
fi

step "Adding Jukebox to the application menu"
APPS="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
mkdir -p "$APPS"
cat > "$APPS/jukebox.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=Jukebox
Comment=Minecraft jukebox desktop widget (C418 music)
Exec="$DIR/.venv/bin/python" "$DIR/jukebox.py"
Path=$DIR
Icon=$DIR/docs/media/icon.png
Terminal=false
Categories=AudioVideo;Audio;
DESKTOP
echo "Shortcut written to $APPS/jukebox.desktop"

if [ "$FONT_OK" = 1 ]; then
    step "Done. Launch Jukebox from the app menu, or run: .venv/bin/python jukebox.py"
else
    step "Almost done: add the font (see above), then launch Jukebox from the app menu."
fi
