"""Minecraft jukebox desktop widget: click to play a random C418 track."""

import colorsys
import math
import os
import random
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent

PRESET = {
    "window_size": (400, 400),
    "window_top_margin": 40,          # distance from the top of the screen
    "always_on_top": True,
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
    "note_scale": 3,
    "note_interval": 0.6,             # seconds between two notes while playing
    "note_life": 1.4,
    "note_rise": 70,
    "font_size": 16,
    "text_y": 368,
    "text_show_time": 3.0,
    "text_fade_time": 1.0,
    "text_hue_period": 2.5,           # seconds for a full rainbow cycle
    "text_saturation": 0.7,
    "text_value": 1.0,                # 0.6 in game, brighter here to read on any wallpaper
    "drag_threshold": 4,
}


def argb_visual_id():
    """Id of a 32-bit TrueColor X visual (needed for a transparent window), or None."""
    try:
        from Xlib import X, display
        for depth in display.Display().screen().allowed_depths:
            if depth.depth == 32:
                for visual in depth.visuals:
                    if visual.visual_class == X.TrueColor:
                        return visual.visual_id
    except Exception:
        return None
    return None


# Wayland does not let a window choose its position or stay on top: go through XWayland.
os.environ.setdefault("SDL_VIDEODRIVER", "x11")
VISUAL_ID = argb_visual_id() if PRESET["transparent"] else None
if VISUAL_ID is not None:
    os.environ["SDL_VIDEO_X11_VISUALID"] = hex(VISUAL_ID)

import pygame  # noqa: E402  (environment must be set first)

import player  # noqa: E402
import textures  # noqa: E402


def ease_out(t):
    return 1 - (1 - t) ** 3


def open_window(p):
    pygame.display.init()
    width, height = p["window_size"]
    desktop_w, _ = pygame.display.get_desktop_sizes()[0]
    window = pygame.Window("Jukebox", (width, height), ((desktop_w - width) // 2, p["window_top_margin"]),
                           borderless=True, always_on_top=p["always_on_top"])
    return window.get_surface(), window


def present(window, screen, frame, transparent):
    """Copy the frame to the window. With an ARGB visual, alpha bytes are sent as-is (premultiplied)."""
    if transparent and screen.get_pitch() == frame.get_pitch():
        screen.get_buffer().write(bytes(frame.premul_alpha().get_buffer()))
    else:
        screen.fill(PRESET["fallback_background"])
        screen.blit(frame, (0, 0))
    window.flip()


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


def spawn_note(geometry, cube_pos, p):
    sx, sy = geometry["slot_center"]
    color = textures.note_color(random.randint(0, 24))
    return {
        "sprite": textures.note(color, p["note_scale"]),
        "x": cube_pos[0] + sx + random.uniform(-70, 70),
        "y": cube_pos[1] + sy + random.uniform(-20, 10),
        "drift": random.uniform(-12, 12),
        "age": 0.0,
    }


def draw_notes(frame, notes, dt, p):
    for n in notes:
        n["age"] += dt
        t = n["age"] / p["note_life"]
        sprite = n["sprite"]
        sprite.set_alpha(int(255 * min(1, (1 - t) * 3)))
        frame.blit(sprite, (n["x"] + n["drift"] * t - sprite.get_width() / 2,
                            n["y"] - p["note_rise"] * ease_out(t)))
    notes[:] = [n for n in notes if n["age"] < p["note_life"]]


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
    font = pygame.font.Font(PROJECT_DIR / "fonts/Minecraftia-Regular.ttf", p["font_size"])
    jukebox = player.Player(player.load_tracks(PROJECT_DIR / "sounds", PROJECT_DIR / "tracks.yaml"))

    disc_sprite, disc_progress = None, 0.0
    message, message_age = "", math.inf
    notes, note_timer = [], 0.0
    click_t = math.inf
    press_pos, dragging, hover = None, False, False
    now = 0.0

    def on_cube(pos):
        x, y = pos[0] - cube_pos[0], pos[1] - cube_pos[1]
        return 0 <= x < cube.get_width() and 0 <= y < cube.get_height() and cube_mask.get_at((x, y))

    running = True
    while running:
        dt = clock.tick(p["fps"]) / 1000
        now += dt
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and on_cube(event.pos):
                press_pos, dragging = event.pos, False
            elif event.type == pygame.MOUSEMOTION:
                hover = on_cube(event.pos)
                if press_pos:
                    dx, dy = event.pos[0] - press_pos[0], event.pos[1] - press_pos[1]
                    if dragging or math.hypot(dx, dy) > p["drag_threshold"]:
                        dragging = True
                        wx, wy = window.position
                        window.position = (wx + dx, wy + dy)
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if press_pos and not dragging:
                    track = jukebox.play_random()
                    disc_sprite, disc_progress = textures.disc(track["disc"], p["disc_scale"]), 0.0
                    message, message_age = f"Now Playing: C418 - {track['title']}", 0.0
                    click_t = 0.0
                press_pos, dragging = None, False
            elif event.type == pygame.WINDOWLEAVE:
                hover = False
            elif event.type == player.TRACK_END and jukebox.on_track_end():
                notes.clear()

        playing = jukebox.current is not None
        step = dt / p["disc_rise_time"]
        disc_progress = min(1.0, disc_progress + step) if playing else max(0.0, disc_progress - step)
        click_t += dt
        message_age += dt
        if playing:
            note_timer += dt
            if note_timer >= p["note_interval"]:
                note_timer = 0.0
                notes.append(spawn_note(geometry, cube_pos, p))

        frame = pygame.Surface(p["window_size"], pygame.SRCALPHA)
        draw_cube(frame, cube, cube_pos, click_t, p)
        if disc_sprite:
            draw_disc(frame, disc_sprite, slot, disc_progress, now, p)
        if hover:
            draw_hover(frame, geometry, cube_pos, p)
        draw_notes(frame, notes, dt, p)
        if message:
            draw_now_playing(frame, font, message, message_age, p)
        present(window, screen, frame, transparent)

    pygame.quit()


if __name__ == "__main__":
    main()
