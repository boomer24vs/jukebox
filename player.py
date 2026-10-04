"""Audio handling (see audio/audio.md): random track, no immediate repeat, end-of-track event."""

import random
from pathlib import Path

import pygame
import yaml

AUDIO_EXTENSIONS = {".mp3", ".ogg", ".wav"}
TRACK_END = pygame.USEREVENT + 1


def load_tracks(sounds_dir, tracks_file):
    """Scan sounds_dir; titles and discs come from tracks.yaml when listed there."""
    meta = {}
    if tracks_file.exists():
        for entry in yaml.safe_load(tracks_file.read_text(encoding="utf-8"))["tracks"]:
            meta[entry["file"]] = entry
    tracks = []
    for path in sorted(Path(sounds_dir).iterdir()):
        if path.suffix.lower() in AUDIO_EXTENSIONS:
            entry = meta.get(path.name, {})
            tracks.append({
                "path": path,
                "title": entry.get("title", path.stem),
                "disc": entry.get("disc", "generic"),
            })
    return tracks


class Player:
    def __init__(self, tracks, volume=1.0):
        if not tracks:
            raise SystemExit("No audio file in sounds/: run extract_music.py first.")
        self.tracks = tracks
        self.current = None
        self.previous = None
        self.volume = 0.0
        self.set_volume(volume)
        pygame.mixer.music.set_endevent(TRACK_END)

    def set_volume(self, volume):
        """Volume 0..1, kept from one track to the next."""
        self.volume = round(min(1.0, max(0.0, volume)), 2)
        pygame.mixer.music.set_volume(self.volume)

    def play_random(self):
        """Stop the current track and start a random one, never the one just played."""
        last = self.current or self.previous
        choices = [t for t in self.tracks if t is not last] or self.tracks
        pygame.mixer.music.stop()
        self.previous = last
        self.current = random.choice(choices)
        pygame.mixer.music.load(self.current["path"])
        pygame.mixer.music.set_volume(self.volume)
        pygame.mixer.music.play()
        return self.current

    def on_track_end(self):
        """Natural end of the track: back to idle. Returns False for the event sent by a manual stop."""
        if pygame.mixer.music.get_busy():
            return False
        self.previous, self.current = self.current, None
        return True
