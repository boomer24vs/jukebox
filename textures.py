"""Procedural Minecraft-style pixel art: jukebox textures, isometric cube, music discs, note particle."""

import math
import random

import pygame

TEXTURE_PRESET = {
    "seed": 418,
    "border": (40, 26, 19),
    "lattice": (78, 52, 37),
    "wood": (108, 73, 52),
    "wood_light": (124, 86, 62),
    "slot": (14, 9, 7),
    "slot_rim": (58, 39, 28),
    "shade_top": 1.0,
    "shade_left": 0.8,
    "shade_right": 0.6,
}

# Label colour of each disc, close to the in-game items
DISC_COLORS = {
    "13": (230, 200, 50), "cat": (90, 200, 60), "blocks": (220, 90, 40),
    "chirp": (200, 40, 40), "far": (150, 220, 90), "mall": (120, 80, 200),
    "mellohi": (220, 120, 200), "stal": (60, 60, 60), "strad": (235, 235, 235),
    "ward": (40, 110, 60), "11": (25, 25, 25), "wait": (60, 130, 220),
    "generic": (150, 150, 150),
}

NOTE_PATTERN = [
    "....##..",
    "....###.",
    "....#.##",
    "....#..#",
    "....#...",
    ".####...",
    "#####...",
    ".###....",
]


def _vary(color, rng, amount=6):
    d = rng.randint(-amount, amount)
    return tuple(max(0, min(255, c + d)) for c in color)


def jukebox_side(p=TEXTURE_PRESET):
    """16x16 side texture: dark border, diamond lattice over brown wood."""
    rng = random.Random(p["seed"])
    tex = pygame.Surface((16, 16))
    for y in range(16):
        for x in range(16):
            if x in (0, 15) or y in (0, 15):
                color = p["border"]
            elif (x + y) % 4 == 0 or (x - y) % 4 == 0:
                color = p["lattice"]
            else:
                color = p["wood_light"] if rng.random() < 0.15 else p["wood"]
            tex.set_at((x, y), _vary(color, rng))
    return tex


def jukebox_top(p=TEXTURE_PRESET):
    """16x16 top texture: same lattice with a horizontal disc slot in the middle."""
    tex = jukebox_side(p)
    for y in range(5, 11):
        for x in range(2, 14):
            inner = 3 <= x <= 12 and 7 <= y <= 8
            tex.set_at((x, y), p["slot"] if inner else p["slot_rim"])
    return tex


def _shade(color, k):
    return tuple(int(c * k) for c in color[:3])


def iso_cube(top, side, scale, p=TEXTURE_PRESET):
    """Draw a 16x16-textured cube in 2:1 isometric. Returns (surface, geometry dict)."""
    s, h = scale, round(scale * 7 / 6)
    u, v = (s, s / 2), (-s, s / 2)
    width, height = 32 * s, 16 * s + 16 * h
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    t = (width / 2, 0)

    def pt(origin, a, b, ia, ib):
        return (origin[0] + a[0] * ia + b[0] * ib, origin[1] + a[1] * ia + b[1] * ib)

    def face(tex, origin, a, b, shade):
        for j in range(16):
            for i in range(16):
                quad = [pt(origin, a, b, i, j), pt(origin, a, b, i + 1, j),
                        pt(origin, a, b, i + 1, j + 1), pt(origin, a, b, i, j + 1)]
                pygame.draw.polygon(surf, _shade(tex.get_at((i, j)), shade), quad)

    down = (0, h)
    left = pt(t, v, v, 16, 0)
    middle = pt(t, u, v, 16, 16)
    right = pt(t, u, u, 16, 0)
    face(top, t, u, v, p["shade_top"])
    face(side, left, u, down, p["shade_left"])
    face(side, middle, (-v[0], -v[1]), down, p["shade_right"])

    bottom = (middle[0], middle[1] + 16 * h)
    geometry = {
        "outline": [t, right, (right[0], right[1] + 16 * h), bottom, (left[0], left[1] + 16 * h), left],
        "edges": [(left, middle), (middle, right), (middle, bottom)],
        "slot_center": pt(t, u, v, 8, 8),
    }
    return surf, geometry


def disc(name, scale):
    """Music disc item icon, scaled with nearest-neighbour."""
    label = DISC_COLORS.get(name, DISC_COLORS["generic"])
    tex = pygame.Surface((16, 16), pygame.SRCALPHA)
    for y in range(16):
        for x in range(16):
            d = math.hypot(x - 7.5, y - 7.5)
            if d > 7.6:
                continue
            if d > 6.6:
                color = (12, 12, 12)
            elif d < 1.0:
                color = (20, 20, 20)
            elif d < 3.0:
                color = label
            elif 4.2 < d < 5.2:
                color = (48, 48, 48)
            else:
                color = (30, 30, 30)
            if x + y < 9 and 3.0 <= d <= 6.6:
                color = tuple(min(255, c + 25) for c in color)
            tex.set_at((x, y), color + (255,))
    return pygame.transform.scale(tex, (16 * scale, 16 * scale))


def note(color, scale):
    """Minecraft note particle (8x8), tinted."""
    tex = pygame.Surface((8, 8), pygame.SRCALPHA)
    for y, row in enumerate(NOTE_PATTERN):
        for x, ch in enumerate(row):
            if ch == "#":
                tex.set_at((x, y), color + (255,))
    return pygame.transform.scale(tex, (8 * scale, 8 * scale))


def note_color(pitch):
    """In-game note colour formula, pitch 0..24."""
    f = pitch / 24
    r = max(0.0, math.sin((f + 0.0) * math.tau) * 0.65 + 0.35)
    g = max(0.0, math.sin((f + 1 / 3) * math.tau) * 0.65 + 0.35)
    b = max(0.0, math.sin((f + 2 / 3) * math.tau) * 0.65 + 0.35)
    return (int(r * 255), int(g * 255), int(b * 255))
