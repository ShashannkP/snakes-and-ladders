"""Small shared drawing helpers."""

from functools import lru_cache

import pygame

BACKGROUND = (21, 28, 43)
TEXT = (237, 241, 249)
# Pygame uses pixels: 14 pt at the reference 96 DPI rounds up to 19 px.
MIN_FONT_SIZE = 19
# Okabe-Ito palette; player numbers provide a second, non-colour identifier.
TOKEN_COLOURS = {
    "blue": (86, 180, 233), "orange": (230, 159, 0),
    "green": (0, 158, 115), "magenta": (204, 121, 167),
}


@lru_cache(maxsize=512)
def _render_label(text, size, colour):
    """Bound memory use while avoiding font loading and rasterizing every frame."""
    font = pygame.font.Font(None, max(MIN_FONT_SIZE, size))
    return font.render(text, True, colour)


def label(surface, text, position, size=26, colour=TEXT):
    surface.blit(_render_label(text, size, tuple(colour)), position)


def button(surface, rect, text, enabled=True):
    pygame.draw.rect(surface, (45, 110, 165) if enabled else (60, 65, 75), rect, border_radius=8)
    label(surface, text, (rect.x + 12, rect.y + 12))
