"""Minecraft jukebox desktop widget: click to play a random C418 track."""

import colorsys
import math
import os
import random
import time
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent

PRESET = {
    "window_size": (400, 400),
    "window_top_margin": 40,          # distance from the top of the screen
    "window_layer": "below",          # "below": under every app, "normal", or "top": always on top
    "transparent": True,
    "fallback_background": (29, 29, 29),
    "fps": 60,
    "cube_scale": 6,                  # screen pixels per texel (horizontal)
    "cube_top_y": 120,
    "hover_outline": (0, 0, 0, 140),
    "click_squash": 0.08,             # height loss at the peak of the bounce
    "click_duration": 0.25,
    "disc_scale": 4,
    "disc_rise": 95,                  # pixels above the slot
    "disc_rise_time": 0.6,
    "disc_bob": 3,
    "autoplay": True,                 # a new random track starts when one ends
    "volume_default": 0.7,
    "volume_step": 0.1,               # per mouse wheel notch
    "note_scale_min": 2,              # note size at the lowest volume (integer: crisp pixels)
    "note_scale_max": 4,              # note size at full volume
    "note_interval_max": 1.0,         # seconds between two notes at the lowest volume
    "note_interval_min": 0.3,         # seconds between two notes at full volume
    "note_life": 1.4,
    "note_spread": 70,                # horizontal spawn range around the slot
    "note_rise": 70,
    "font_size": 16,
    "text_y": 368,
    "text_show_time": 3.0,
    "text_fade_time": 1.0,
    "text_hue_period": 2.5,           # seconds for a full rainbow cycle
    "text_saturation": 0.7,
    "text_value": 1.0,                # 0.6 in game, brighter here to read on any wallpaper
    "drag_threshold": 4,
    "drag_fps": 120,                  # window position updates per second while dragging
    "compact_delay": 10.0,            # seconds without hover or click before the compact mode
    "compact_transition": 0.8,
    "compact_size": (360, 120),       # compact layout; below the note headroom it is the clickable area
    "compact_origin": (20, 80),       # top-left of the compact layout inside the window
    "compact_cube_scale": 2,
    "compact_cube_pos": (8, 48),      # inside the compact window, room above for the notes
    "compact_text_pos": (84, 64),     # left edge, vertical centre
    "compact_note_scale_div": 2,      # compact notes are this many times smaller
    "compact_note_spread": 24,        # horizontal spawn range around the slot
    "compact_note_rise": 40,
    "compact_text_color": (255, 255, 255),
    "compact_text_shadow": (63, 63, 63),
    "xp_bar_rect": (84, 86, 264, 5),  # x, y, width, height in texels of xp_bar_scale
    "xp_bar_scale": 2,
    "xp_bar_border": (0, 0, 0),
    "xp_bar_empty": (48, 48, 48),
    "xp_bar_fill": (128, 255, 32),
    "xp_bar_fill_shade": (76, 168, 18),
    "chest_scale": 1.5,               # small chest next to the jukebox
    "arrow_scale": 3,                 # indicator arrow above the small chest
    "arrow_tip_y": 6,                 # tip position below the top corner of the small chest
    "arrow_bob": 3,                   # pixels up and down
    "arrow_bob_period": 2.0,          # seconds for one up-and-down
    "chest_gap": 4,                   # pixels between the jukebox and the small chest
    "chest_ui_scale": 3,              # screen pixels per GUI texel
    "chest_ui_pos": (404, 78),        # top-left of the chest GUI, right of the jukebox
    "chest_ui_margin": 16,            # extra window width on the right while the chest is open
    "chest_region_delay": 0.3,        # seconds after opening before the clickable area is set again
    "chest_ui_size": (176, 95),       # texels: single chest GUI without the player inventory
    "chest_columns": 9,
    "chest_rows": 3,
    "chest_slots_origin": (7, 17),    # texels, top-left of the first 18x18 slot
    "chest_title": "Chest",
    "chest_title_pos": (8, 10),       # texels, left edge and vertical centre
    "chest_text_color": (64, 64, 64),
    "chest_prev_button": (7, 75, 20, 14),
    "chest_next_button": (149, 75, 20, 14),
    "chest_page_pos": (88, 82),       # texels, centre of the page number
    "slot_hover": (255, 255, 255, 128),
    "tooltip_offset": (12, -12),      # texels from the cursor
    "tooltip_background": (16, 0, 16, 240),
    "tooltip_border_top": (80, 0, 255, 80),
    "tooltip_border_bottom": (40, 0, 127, 80),
    "tooltip_name": "Music Disc",
    "tooltip_name_color": (85, 255, 255),
    "tooltip_title_color": (170, 170, 170),
}


FAMILY_WILD = 65535


def accept_wildcard_auth():
    """Let python-xlib use the "any host" cookie mutter writes for XWayland, as libX11 does.
    Without it the connection fails once the hostname changes (new IPv6 lease) and the window turns opaque."""
    from Xlib import error, xauth
    original = xauth.Xauthority.get_best_auth

    def get_best_auth(self, family, address, dispno, types=(b"MIT-MAGIC-COOKIE-1",)):
        try:
            return original(self, family, address, dispno, types)
        except error.XNoAuthError:
            for efam, _, enum, ename, edata in self.entries:
                if efam == FAMILY_WILD and enum in (b"", str(dispno).encode()) and ename in types:
                    return ename, edata
            raise

    xauth.Xauthority.get_best_auth = get_best_auth


def x_display():
    try:
        from Xlib import display
        accept_wildcard_auth()
        return display.Display()
    except Exception:
        return None


def argb_visual_id(xdisplay):
    """Id of a 32-bit TrueColor X visual (needed for a transparent window), or None."""
    try:
        from Xlib import X
        for depth in xdisplay.screen().allowed_depths:
            if depth.depth == 32:
                for visual in depth.visuals:
                    if visual.visual_class == X.TrueColor:
                        return visual.visual_id
    except Exception:
        return None
    return None


# Wayland does not let a window choose its position or stay on top: go through XWayland.
os.environ.setdefault("SDL_VIDEODRIVER", "x11")
# SDL's default OpenGL-backed window surface drops alpha: use the plain X11 framebuffer instead.
os.environ.setdefault("SDL_FRAMEBUFFER_ACCELERATION", "0")
XDISPLAY = x_display()
VISUAL_ID = argb_visual_id(XDISPLAY) if PRESET["transparent"] and XDISPLAY else None
if VISUAL_ID is not None:
    os.environ["SDL_VIDEO_X11_VISUALID"] = hex(VISUAL_ID)

import pygame  # noqa: E402  (environment must be set first)

import player  # noqa: E402
import textures  # noqa: E402


def ease_out(t):
    return 1 - (1 - t) ** 3


def ease_in_out(t):
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


def open_window(p):
    pygame.display.init()
    width, height = p["window_size"]
    desktop_w, _ = pygame.display.get_desktop_sizes()[0]
    window = pygame.Window("Jukebox", (width, height), ((desktop_w - width) // 2, p["window_top_margin"]),
                           borderless=True, always_on_top=p["window_layer"] == "top")
    return window.get_surface(), window


def resize_window(window, size):
    """The window grows to the right while the chest is open; the jukebox does not move."""
    window.size = size
    return window.get_surface()


def present(window, screen, frame, transparent):
    """Copy the frame to the window. With an ARGB visual, alpha bytes are sent as-is (premultiplied)."""
    if transparent and screen.get_pitch() == frame.get_pitch():
        screen.get_buffer().write(bytes(frame.premul_alpha().get_buffer()))
    else:
        screen.fill(PRESET["fallback_background"])
        screen.blit(frame, (0, 0))
    window.flip()


def pointer_on_screen():
    """Absolute pointer position: event.pos is relative to the window, which moves while dragging."""
    if XDISPLAY is None:
        return pygame.mouse.get_pos()
    pointer = XDISPLAY.screen().root.query_pointer()
    return pointer.root_x, pointer.root_y


def drag_target(start_window, start_pointer, pointer):
    return (start_window[0] + pointer[0] - start_pointer[0], start_window[1] + pointer[1] - start_pointer[1])


def find_x_window():
    """Our X11 top-level window, found by process id among the windows GNOME manages."""
    if XDISPLAY is None:
        return None
    root = XDISPLAY.screen().root
    clients = root.get_full_property(XDISPLAY.intern_atom("_NET_CLIENT_LIST"), 0)
    pid_atom = XDISPLAY.intern_atom("_NET_WM_PID")
    for window_id in clients.value if clients else []:
        candidate = XDISPLAY.create_resource_object("window", window_id)
        pid = candidate.get_full_property(pid_atom, 0)
        if pid and pid.value[0] == os.getpid():
            return candidate
    return None


def wait_for_x_window(timeout=1.0):
    """GNOME lists the window only once it is mapped: pump events until it shows up."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        pygame.event.pump()
        x_window = find_x_window()
        if x_window is not None:
            return x_window
        time.sleep(0.02)
    return None


def mask_rects(mask, offset):
    """Opaque pixels of a mask as one rectangle per horizontal run, shifted by offset."""
    rects = []
    w, h = mask.get_size()
    for y in range(h):
        x = 0
        while x < w:
            if mask.get_at((x, y)):
                start = x
                while x < w and mask.get_at((x, y)):
                    x += 1
                rects.append((offset[0] + start, offset[1] + y, x - start, 1))
            x += 1
    return rects


def set_input_region(x_window, rects):
    """Only these rectangles catch the mouse: clicks on the transparent parts go through to what is below."""
    if x_window is None:
        return
    from Xlib import X
    from Xlib.ext import shape
    x_window.shape_rectangles(shape.SO.Set, shape.SK.Input, X.Unsorted, 0, 0, rects)
    XDISPLAY.flush()


def keep_below(x_window):
    """Ask GNOME to keep the window under all others (_NET_WM_STATE_BELOW), like a desktop widget."""
    from Xlib import X
    from Xlib.protocol import event
    wm_state = XDISPLAY.intern_atom("_NET_WM_STATE")
    below = XDISPLAY.intern_atom("_NET_WM_STATE_BELOW")
    message = event.ClientMessage(window=x_window, client_type=wm_state, data=(32, [1, below, 0, 1, 0]))
    XDISPLAY.screen().root.send_event(message, event_mask=X.SubstructureRedirectMask | X.SubstructureNotifyMask)
    XDISPLAY.flush()


def move_window(window, x_window, pos):
    """Asynchronous X11 move: SDL's own setter waits ~10 ms (up to 100 ms at a screen edge) for GNOME to confirm."""
    if x_window is None:
        window.position = pos
        return
    x_window.configure(x=pos[0], y=pos[1])
    XDISPLAY.flush()


def draw_hover(frame, geometry, offset, p):
    ox, oy = offset
    shift = lambda pt: (pt[0] + ox, pt[1] + oy)
    pygame.draw.polygon(frame, p["hover_outline"], [shift(q) for q in geometry["outline"]], 2)
    for a, b in geometry["edges"]:
        pygame.draw.line(frame, p["hover_outline"], shift(a), shift(b), 2)


def draw_cube(frame, cube, cube_pos, click_t, p):
    """Cube with a short squash-and-bounce after a click (anchored at the bottom)."""
    if click_t < p["click_duration"]:
        k = 1 - p["click_squash"] * math.sin(math.pi * click_t / p["click_duration"])
        w, h = cube.get_size()
        squashed = pygame.transform.scale(cube, (w, round(h * k)))
        frame.blit(squashed, (cube_pos[0], cube_pos[1] + h - squashed.get_height()))
    else:
        frame.blit(cube, cube_pos)


def draw_disc(frame, disc, slot, progress, now, p):
    """Disc rising out of the slot: clipped so nothing shows below the slot line."""
    if progress <= 0:
        return
    w, h = disc.get_size()
    bob = p["disc_bob"] * math.sin(now * 2) if progress >= 1 else 0
    center_y = slot[1] + h / 2 - (p["disc_rise"] + h / 2) * ease_out(progress) + bob
    frame.set_clip(pygame.Rect(0, 0, frame.get_width(), slot[1]))
    frame.blit(disc, (slot[0] - w / 2, center_y - h / 2))
    frame.set_clip(None)


def note_settings(volume, p):
    """Louder means bigger and more frequent notes. Returns (scale, interval), interval None when muted."""
    if volume <= 0:
        return p["note_scale_min"], None
    scale = round(p["note_scale_min"] + (p["note_scale_max"] - p["note_scale_min"]) * volume)
    interval = p["note_interval_max"] - (p["note_interval_max"] - p["note_interval_min"]) * volume
    return scale, interval


def spawn_note(slot, spread, scale, rise):
    color = textures.note_color(random.randint(0, 24))
    return {
        "sprite": textures.note(color, scale),
        "x": slot[0] + random.uniform(-spread, spread),
        "y": slot[1] + random.uniform(-0.3, 0.15) * spread,
        "drift": random.uniform(-0.17, 0.17) * spread,
        "rise": rise,
        "age": 0.0,
    }


def draw_notes(frame, notes, dt, p):
    for n in notes:
        n["age"] += dt
        t = n["age"] / p["note_life"]
        sprite = n["sprite"]
        sprite.set_alpha(int(255 * min(1, (1 - t) * 3)))
        frame.blit(sprite, (n["x"] + n["drift"] * t - sprite.get_width() / 2,
                            n["y"] - n["rise"] * ease_out(t)))
    notes[:] = [n for n in notes if n["age"] < p["note_life"]]


def draw_moving_cube(frame, cubes, big_pos, small_pos, k):
    """Cube on its way between the normal (k=0) and compact (k=1) layouts.
    cubes: one native cube per pixel scale, from the biggest to the smallest; the closest one is resized
    (nearest-neighbour) so the pixel art stays sharp and there is no jump at either end."""
    big, small = cubes[0], cubes[-1]
    w = lerp(big.get_width(), small.get_width(), k)
    h = lerp(big.get_height(), small.get_height(), k)
    source = min(cubes, key=lambda c: abs(c.get_width() - w))
    if source.get_size() != (round(w), round(h)):
        source = pygame.transform.scale(source, (round(w), round(h)))
    frame.blit(source, (round(lerp(big_pos[0], small_pos[0], k)), round(lerp(big_pos[1], small_pos[1], k))))


def draw_xp_bar(frame, origin, progress, p):
    """Experience-bar look: black border, dark empty part, green fill with a darker bottom row."""
    x, y, w, h = p["xp_bar_rect"]
    s = p["xp_bar_scale"]
    left, top = origin[0] + x, origin[1] + y
    frame.fill(p["xp_bar_border"], (left, top, w, h * s))
    inner = pygame.Rect(left + s, top + s, w - 2 * s, (h - 2) * s)
    frame.fill(p["xp_bar_empty"], inner)
    filled = round(inner.width * progress)
    if filled:
        frame.fill(p["xp_bar_fill"], (inner.x, inner.y, filled, inner.height))
        frame.fill(p["xp_bar_fill_shade"], (inner.x, inner.bottom - s, filled, s))


def draw_compact_info(frame, font, title, progress, origin, p):
    """Compact mode: title in white with the in-game drop shadow, progress bar below."""
    unit = max(1, p["font_size"] // 8)
    x, y = origin[0] + p["compact_text_pos"][0], origin[1] + p["compact_text_pos"][1]
    for col, off in ((p["compact_text_shadow"], unit), (p["compact_text_color"], 0)):
        img = font.render(title, False, col)
        frame.blit(img, (x + off, y - img.get_height() / 2 + off))
    if progress is not None:
        draw_xp_bar(frame, origin, progress, p)


def draw_now_playing(frame, font, text, age, p):
    """In-game record message: rainbow colour, drop shadow, fade out."""
    if age > p["text_show_time"] + p["text_fade_time"]:
        return
    alpha = 1 - max(0, age - p["text_show_time"]) / p["text_fade_time"]
    hue = (age / p["text_hue_period"]) % 1
    color = tuple(int(c * 255) for c in colorsys.hsv_to_rgb(hue, p["text_saturation"], p["text_value"]))
    shadow = tuple(c // 4 for c in color)
    unit = max(1, p["font_size"] // 8)
    for col, off in ((shadow, unit), (color, 0)):
        img = font.render(text, False, col)
        img.set_alpha(int(255 * alpha))
        frame.blit(img, ((frame.get_width() - img.get_width()) / 2 + off, p["text_y"] - img.get_height() / 2 + off))


def draw_text(surface, font, text, color, x, center_y, shadow=None, centered=False):
    """Text left-aligned (or centred) on x, vertically centred on center_y, optional in-game drop shadow."""
    unit = max(1, font.point_size // 8)
    img = font.render(text, False, color)
    left = x - img.get_width() / 2 if centered else x
    top = center_y - img.get_height() / 2
    if shadow:
        surface.blit(font.render(text, False, shadow), (left + unit, top + unit))
    surface.blit(img, (left, top))


def chest_background(font, p):
    """Chest GUI drawn once: panel, slots, page buttons and title, scaled to screen pixels."""
    w, h = p["chest_ui_size"]
    sx, sy = p["chest_slots_origin"]
    tex = textures.chest_panel(w, h)
    for r in range(p["chest_rows"]):
        for c in range(p["chest_columns"]):
            textures.draw_slot(tex, sx + 18 * c, sy + 18 * r)
    textures.draw_button(tex, p["chest_prev_button"])
    textures.draw_button(tex, p["chest_next_button"])
    s = p["chest_ui_scale"]
    surface = pygame.transform.scale(tex, (w * s, h * s))
    draw_text(surface, font, p["chest_title"], p["chest_text_color"], p["chest_title_pos"][0] * s,
              p["chest_title_pos"][1] * s)
    for (x, y, bw, bh), label in ((p["chest_prev_button"], "<"), (p["chest_next_button"], ">")):
        draw_text(surface, font, label, (255, 255, 255), (x + bw / 2) * s, (y + bh / 2) * s, (63, 63, 63), True)
    return surface


def ui_rect(texel_rect, p):
    x, y, w, h = texel_rect
    s, (ox, oy) = p["chest_ui_scale"], p["chest_ui_pos"]
    return pygame.Rect(ox + x * s, oy + y * s, w * s, h * s)


def slot_at(pos, p):
    """Index of the chest slot under pos on the current page, or None."""
    s, (ox, oy), (sx, sy) = p["chest_ui_scale"], p["chest_ui_pos"], p["chest_slots_origin"]
    c, r = ((pos[0] - ox) // s - sx) // 18, ((pos[1] - oy) // s - sy) // 18
    if 0 <= c < p["chest_columns"] and 0 <= r < p["chest_rows"]:
        return r * p["chest_columns"] + c
    return None


def draw_chest_ui(frame, background, font, discs, page, pages, hover_slot, p):
    """Panel, the discs of this page, white veil on the hovered slot, page number."""
    s, (sx, sy) = p["chest_ui_scale"], p["chest_slots_origin"]
    frame.blit(background, p["chest_ui_pos"])
    per_page = p["chest_columns"] * p["chest_rows"]
    for i, sprite in enumerate(discs[page * per_page:(page + 1) * per_page]):
        c, r = i % p["chest_columns"], i // p["chest_columns"]
        frame.blit(sprite, ui_rect((sx + 1 + 18 * c, sy + 1 + 18 * r, 16, 16), p))
    if hover_slot is not None:
        c, r = hover_slot % p["chest_columns"], hover_slot // p["chest_columns"]
        veil = pygame.Surface((16 * s, 16 * s), pygame.SRCALPHA)
        veil.fill(p["slot_hover"])
        frame.blit(veil, ui_rect((sx + 1 + 18 * c, sy + 1 + 18 * r, 16, 16), p))
    page_x, page_y = ui_rect((*p["chest_page_pos"], 0, 0), p).topleft
    draw_text(frame, font, f"{page + 1}/{pages}", p["chest_text_color"], page_x, page_y, centered=True)


def draw_tooltip(frame, font, lines, pos, p):
    """In-game item tooltip: near-black purple box, purple gradient border, text with drop shadow."""
    s = p["chest_ui_scale"]
    imgs = [font.render(text, False, color) for text, color in lines]
    w = max(img.get_width() for img in imgs)
    h = 8 * s + 12 * s * (len(lines) - 1)
    x = min(pos[0] + p["tooltip_offset"][0] * s, frame.get_width() - w - 5 * s)
    y = max(4 * s, pos[1] + p["tooltip_offset"][1] * s)
    box = pygame.Surface((w + 10 * s, h + 8 * s), pygame.SRCALPHA)
    bw, bh = box.get_size()
    box.fill(p["tooltip_background"], (s, 0, bw - 2 * s, bh))
    box.fill(p["tooltip_background"], (0, s, bw, bh - 2 * s))
    for row in range(1, bh // s - 1):
        k = (row - 1) / max(1, bh // s - 3)
        color = [round(lerp(a, b, k)) for a, b in zip(p["tooltip_border_top"], p["tooltip_border_bottom"])]
        if row in (1, bh // s - 2):
            box.fill(color, (s, row * s, bw - 2 * s, s))
        else:
            box.fill(color, (s, row * s, s, s))
            box.fill(color, (bw - 2 * s, row * s, s, s))
    frame.blit(box, (x - 4 * s, y - 4 * s))
    for i, (text, color) in enumerate(lines):
        draw_text(frame, font, text, color, x + s, y + 4 * s + 12 * s * i, tuple(c // 4 for c in color))


def draw_arrow(frame, sprite, tip, now, p):
    """Indicator arrow pointing down at the chest, gently moving up and down."""
    bob = p["arrow_bob"] * math.sin(now * math.tau / p["arrow_bob_period"])
    frame.blit(sprite, (tip[0] - sprite.get_width() // 2, round(tip[1] - sprite.get_height() + bob)))


def now_playing(track, p):
    """Disc sprite and message shown when a track starts."""
    return textures.disc(track["label"], p["disc_scale"]), f"Now Playing: C418 - {track['title']}"


def main(p=PRESET):
    pygame.mixer.pre_init(44100)
    pygame.init()
    screen, window = open_window(p)
    transparent = VISUAL_ID is not None
    clock = pygame.time.Clock()

    cube, geometry = textures.iso_cube(textures.jukebox_top(), textures.jukebox_side(), p["cube_scale"])
    cube_mask = pygame.mask.from_surface(cube)
    cube_pos = ((p["window_size"][0] - cube.get_width()) // 2, p["cube_top_y"])
    slot = (cube_pos[0] + geometry["slot_center"][0], cube_pos[1] + geometry["slot_center"][1])
    cubes = [textures.iso_cube(textures.jukebox_top(), textures.jukebox_side(), scale)[0]
             for scale in range(p["cube_scale"], p["compact_cube_scale"] - 1, -1)]
    _, small_geometry = textures.iso_cube(textures.jukebox_top(), textures.jukebox_side(), p["compact_cube_scale"])
    compact_rect = pygame.Rect(p["compact_origin"], p["compact_size"])
    small_cube_pos = (compact_rect.x + p["compact_cube_pos"][0], compact_rect.y + p["compact_cube_pos"][1])
    compact_slot = (small_cube_pos[0] + small_geometry["slot_center"][0],
                    small_cube_pos[1] + small_geometry["slot_center"][1])
    font_path = PROJECT_DIR / "fonts/Minecraftia-Regular.ttf"
    if not font_path.exists():
        raise SystemExit(f"Font missing: download Minecraftia from https://www.dafont.com/minecraftia.font "
                         f"and put Minecraftia-Regular.ttf in {font_path.parent}/")
    font = pygame.font.Font(font_path, p["font_size"])
    jukebox = player.Player(player.load_tracks(PROJECT_DIR / "sounds", PROJECT_DIR / "tracks.yaml"),
                            p["volume_default"])
    # Chest order: in-game discs first, then the rainbow of the other tracks.
    chest_tracks = sorted(jukebox.tracks, key=lambda t: t["disc"] == "generic")
    for track, label in zip(chest_tracks, textures.label_colors([t["disc"] for t in chest_tracks])):
        track["label"] = label
    chest_discs = [textures.disc(t["label"], p["chest_ui_scale"]) for t in chest_tracks]
    per_page = p["chest_columns"] * p["chest_rows"]
    pages, page = math.ceil(len(chest_tracks) / per_page), 0
    ui_font = pygame.font.Font(font_path, 8 * p["chest_ui_scale"])
    chest_ui = chest_background(ui_font, p)
    chest_ui_rect = pygame.Rect(p["chest_ui_pos"], chest_ui.get_size())
    open_size = (chest_ui_rect.right + p["chest_ui_margin"], p["window_size"][1])
    chest, chest_geometry = textures.iso_cube(textures.chest_top(), textures.chest_front(), p["chest_scale"],
                                              right_side=textures.chest_side())
    chest_mask = pygame.mask.from_surface(chest)
    arrow = textures.arrow(p["arrow_scale"])
    chest_pos = (cube_pos[0] + cube.get_width() + p["chest_gap"], cube_pos[1] + cube.get_height() - chest.get_height())
    arrow_tip = (chest_pos[0] + chest.get_width() // 2, chest_pos[1] + p["arrow_tip_y"])
    chest_open, chest_hover, region_timer = False, False, None

    disc_sprite, disc_progress = None, 0.0
    message, message_age = "", math.inf
    notes, compact_notes, note_timer = [], [], 0.0
    click_t = math.inf
    press_pos, dragging, hover = None, False, False
    drag_start, drag_last = None, None
    present(window, screen, pygame.Surface(p["window_size"], pygame.SRCALPHA), transparent)
    x_window = wait_for_x_window()
    if x_window is not None and p["window_layer"] == "below":
        keep_below(x_window)
    # The window keeps its size: the compact mode is drawn inside it and only the clickable area changes.
    normal_region = mask_rects(cube_mask, cube_pos) + mask_rects(chest_mask, chest_pos)
    chest_region = normal_region + [tuple(chest_ui_rect)]
    compact_region = [(compact_rect.x, small_cube_pos[1], compact_rect.width, compact_rect.bottom - small_cube_pos[1])]
    set_input_region(x_window, normal_region)
    now = 0.0
    idle, compact_t, compact_target, compact_shown = 0.0, 0.0, False, False
    pointer_at_compact = None

    def on_cube(pos):
        x, y = pos[0] - cube_pos[0], pos[1] - cube_pos[1]
        return 0 <= x < cube.get_width() and 0 <= y < cube.get_height() and cube_mask.get_at((x, y))

    def on_chest(pos):
        x, y = pos[0] - chest_pos[0], pos[1] - chest_pos[1]
        return 0 <= x < chest.get_width() and 0 <= y < chest.get_height() and chest_mask.get_at((x, y))

    def show_chest(show):
        """Returns (chest_open, screen, region_timer): the window surface changes with the window size.
        GNOME clips the clickable area to the window size known when it is set: resize first, set it after,
        and once more after chest_region_delay, when GNOME has applied the new size."""
        surface = resize_window(window, open_size if show else p["window_size"])
        set_input_region(x_window, chest_region if show else normal_region)
        return show, surface, p["chest_region_delay"] if show else None

    running = True
    while running:
        # Capped so a slow frame does not make the animations jump.
        dt = min(clock.tick(p["drag_fps"] if dragging else p["fps"]) / 1000, 1 / 30)
        now += dt
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if chest_open:
                    chest_open, screen, region_timer = show_chest(False)
                else:
                    running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                running = False
            elif event.type == player.TRACK_END:
                if jukebox.on_track_end():
                    if p["autoplay"]:
                        disc_sprite, message = now_playing(jukebox.play_random(), p)
                        disc_progress, message_age = 0.0, 0.0
                    else:
                        notes.clear()
                        compact_notes.clear()
            elif event.type == pygame.MOUSEMOTION and (compact_shown or compact_target):
                # Cursor back on the jukebox. Changing the clickable area under a still cursor also sends
                # a motion event: ignore it.
                if not compact_shown or pointer_on_screen() != pointer_at_compact:
                    compact_target, idle = False, 0.0
            elif compact_t > 0:
                continue                                # no clicks or wheel until the normal layout is back
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and on_chest(event.pos):
                chest_open, screen, region_timer = show_chest(not chest_open)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and chest_open \
                    and chest_ui_rect.collidepoint(event.pos):
                slot_index = slot_at(event.pos, p)
                if slot_index is not None and page * per_page + slot_index < len(chest_tracks):
                    # Same animation as a click on the jukebox, then the chest closes.
                    disc_sprite, message = now_playing(jukebox.play(chest_tracks[page * per_page + slot_index]), p)
                    disc_progress, message_age, click_t = 0.0, 0.0, 0.0
                    chest_open, screen, region_timer = show_chest(False)
                elif ui_rect(p["chest_prev_button"], p).collidepoint(event.pos):
                    page = (page - 1) % pages
                elif ui_rect(p["chest_next_button"], p).collidepoint(event.pos):
                    page = (page + 1) % pages
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and on_cube(event.pos):
                press_pos, dragging = event.pos, False
                drag_start = (window.position, pointer_on_screen())
                drag_last = window.position
            elif event.type == pygame.MOUSEMOTION:
                hover, chest_hover = on_cube(event.pos), on_chest(event.pos)
                if press_pos and not dragging:
                    dragging = math.hypot(event.pos[0] - press_pos[0], event.pos[1] - press_pos[1]) > p["drag_threshold"]
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if press_pos and not dragging:
                    disc_sprite, message = now_playing(jukebox.play_random(), p)
                    disc_progress, message_age, click_t = 0.0, 0.0, 0.0
                press_pos, dragging, idle = None, False, 0.0
            elif event.type == pygame.MOUSEWHEEL and on_cube(pygame.mouse.get_pos()):
                jukebox.set_volume(jukebox.volume + event.y * p["volume_step"])
                idle = 0.0
            elif event.type == pygame.WINDOWLEAVE:
                hover, chest_hover = False, False

        if region_timer is not None:
            region_timer -= dt
            if region_timer <= 0:
                set_input_region(x_window, chest_region)
                region_timer = None

        if dragging:
            # One move per frame, computed from screen coordinates: no feedback loop with the window position.
            # Past a screen edge GNOME keeps the window inside on its own.
            target = drag_target(*drag_start, pointer_on_screen())
            if target != drag_last:
                move_window(window, x_window, target)
                drag_last = target

        if hover or press_pos or chest_open:
            idle = 0.0
        elif not compact_target:
            idle += dt
            compact_target = idle >= p["compact_delay"]
        if compact_target:
            compact_t = min(1.0, compact_t + dt / p["compact_transition"])
            if compact_t >= 1 and not compact_shown:
                set_input_region(x_window, compact_region)
                compact_shown, hover = True, False
                pointer_at_compact = pointer_on_screen()
                notes.clear()
        else:
            if compact_shown:
                set_input_region(x_window, normal_region)
                compact_shown = False
                compact_notes.clear()
            compact_t = max(0.0, compact_t - dt / p["compact_transition"])
        k = ease_in_out(compact_t)

        playing = jukebox.current is not None
        step = dt / p["disc_rise_time"]
        disc_progress = min(1.0, disc_progress + step) if playing else max(0.0, disc_progress - step)
        click_t += dt
        message_age += dt
        note_scale, note_interval = note_settings(jukebox.volume, p)
        if playing and note_interval and (compact_t == 0 or compact_shown):
            note_timer += dt
            if note_timer >= note_interval:
                note_timer = 0.0
                if compact_shown:
                    compact_notes.append(spawn_note(compact_slot, p["compact_note_spread"],
                                                    max(1, note_scale // p["compact_note_scale_div"]),
                                                    p["compact_note_rise"]))
                else:
                    notes.append(spawn_note(slot, p["note_spread"], note_scale, p["note_rise"]))

        frame = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        if k < 1:
            # Disc, notes, message and small chest fade out together while the cube shrinks.
            extras = pygame.Surface(p["window_size"], pygame.SRCALPHA)
            extras.blit(chest, chest_pos)
            if not chest_open and k == 0:
                draw_arrow(extras, arrow, arrow_tip, now, p)
            if disc_sprite:
                draw_disc(extras, disc_sprite, slot, disc_progress, now, p)
            draw_notes(extras, notes, dt, p)
            if message:
                draw_now_playing(extras, font, message, message_age, p)
            extras.set_alpha(round(255 * (1 - k)))
            if k > 0:
                draw_moving_cube(frame, cubes, cube_pos, small_cube_pos, k)
                frame.blit(extras, (0, 0))
            else:
                draw_cube(frame, cube, cube_pos, click_t, p)
                frame.blit(extras, (0, 0))
                if hover:
                    draw_hover(frame, geometry, cube_pos, p)
                if chest_hover:
                    draw_hover(frame, chest_geometry, chest_pos, p)
        else:
            draw_moving_cube(frame, cubes, cube_pos, small_cube_pos, k)
        if k > 0:
            info = pygame.Surface(p["window_size"], pygame.SRCALPHA)
            draw_notes(info, compact_notes, dt, p)
            if playing:
                draw_compact_info(info, font, f"C418 - {jukebox.current['title']}", jukebox.progress(),
                                  compact_rect.topleft, p)
            info.set_alpha(round(255 * k))
            frame.blit(info, (0, 0))
        if chest_open:
            mouse = pygame.mouse.get_pos()
            hover_slot = slot_at(mouse, p) if chest_ui_rect.collidepoint(mouse) else None
            if hover_slot is not None and page * per_page + hover_slot >= len(chest_tracks):
                hover_slot = None
            draw_chest_ui(frame, chest_ui, ui_font, chest_discs, page, pages, hover_slot, p)
            if hover_slot is not None:
                track = chest_tracks[page * per_page + hover_slot]
                draw_tooltip(frame, ui_font, [(p["tooltip_name"], p["tooltip_name_color"]),
                                              (f"C418 - {track['title']}", p["tooltip_title_color"])], mouse, p)
        present(window, screen, frame, transparent)

    pygame.quit()


if __name__ == "__main__":
    main()
