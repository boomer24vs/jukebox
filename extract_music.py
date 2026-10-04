"""Copy C418 tracks from the local Minecraft install into sounds/ and write tracks.yaml."""

import json
import shutil
import sys
from pathlib import Path

# Where launchers keep the game assets (indexes/ + objects/). A path given on the command line wins.
ASSETS_DIRS = [
    Path.home() / ".minecraft/assets",
    Path.home() / ".var/app/com.mojang.Minecraft/.minecraft/assets",
    Path.home() / ".local/share/PrismLauncher/assets",
    Path.home() / ".var/app/org.prismlauncher.PrismLauncher/data/PrismLauncher/assets",
]
PROJECT_DIR = Path(__file__).parent
SOUNDS_DIR = PROJECT_DIR / "sounds"
TRACKS_FILE = PROJECT_DIR / "tracks.yaml"

# Jukebox discs by C418: asset name -> display title (disc = asset name)
DISCS = {
    "13": "13", "cat": "cat", "blocks": "blocks", "chirp": "chirp",
    "far": "far", "mall": "mall", "mellohi": "mellohi", "stal": "stal",
    "strad": "strad", "ward": "ward", "11": "11", "wait": "wait",
}

# Background music by C418: asset path (under sounds/music/) -> display title
BACKGROUND = {
    "game/minecraft": "Minecraft", "game/clark": "Clark", "game/sweden": "Sweden",
    "game/subwoofer_lullaby": "Subwoofer Lullaby", "game/living_mice": "Living Mice",
    "game/haggstrom": "Haggstrom", "game/danny": "Danny", "game/key": "Key",
    "game/oxygene": "Oxygène", "game/dry_hands": "Dry Hands", "game/wet_hands": "Wet Hands",
    "game/mice_on_venus": "Mice on Venus",
    "game/creative/biome_fest": "Biome Fest", "game/creative/blind_spots": "Blind Spots",
    "game/creative/haunt_muskie": "Haunt Muskie", "game/creative/aria_math": "Aria Math",
    "game/creative/dreiton": "Dreiton", "game/creative/taswell": "Taswell",
    "menu/mutation": "Mutation", "menu/moog_city_2": "Moog City 2",
    "menu/beginning_2": "Beginning 2", "menu/floating_trees": "Floating Trees",
    "game/end/the_end": "The End", "game/end/boss": "Boss", "game/end/alpha": "Alpha",
    "game/nether/concrete_halls": "Concrete Halls", "game/nether/dead_voxel": "Dead Voxel",
    "game/nether/warmth": "Warmth", "game/nether/ballad_of_the_cats": "Ballad of the Cats",
    "game/water/axolotl": "Axolotl", "game/water/dragon_fish": "Dragon Fish",
    "game/water/shuniji": "Shuniji",
}


def find_assets_dir():
    candidates = [Path(sys.argv[1]).expanduser()] if len(sys.argv) > 1 else ASSETS_DIRS
    for path in candidates:
        if any((path / "indexes").glob("*.json")):
            return path
    raise SystemExit("No Minecraft assets found: launch Minecraft Java once from the launcher, "
                     "or pass the assets folder: python extract_music.py /path/to/assets")


def latest_index(assets_dir):
    indexes = sorted((assets_dir / "indexes").glob("*.json"), key=lambda p: p.stat().st_mtime)
    return json.loads(indexes[-1].read_text())["objects"]


def copy_asset(assets_dir, objects, asset_key, dest_name):
    asset_hash = objects[asset_key]["hash"]
    src = assets_dir / "objects" / asset_hash[:2] / asset_hash
    dest = SOUNDS_DIR / f"{dest_name}.ogg"
    shutil.copyfile(src, dest)
    return dest.name


def main():
    assets_dir = find_assets_dir()
    print(f"Minecraft assets: {assets_dir}")
    objects = latest_index(assets_dir)
    SOUNDS_DIR.mkdir(exist_ok=True)
    entries = []
    for name, title in DISCS.items():
        file = copy_asset(assets_dir, objects, f"minecraft/sounds/records/{name}.ogg", name)
        entries.append((title, file, name))
    for path, title in BACKGROUND.items():
        file = copy_asset(assets_dir, objects, f"minecraft/sounds/music/{path}.ogg", path.rsplit("/", 1)[-1])
        entries.append((title, file, "generic"))

    lines = ["# C418 tracks extracted from Minecraft. disc: texture name, 'generic' if none.", "tracks:"]
    for title, file, disc in entries:
        lines += [f'  - title: "{title}"', f"    file: {file}", f'    disc: "{disc}"']
    TRACKS_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(entries)} tracks copied to {SOUNDS_DIR}, list written to {TRACKS_FILE.name}")


if __name__ == "__main__":
    main()
