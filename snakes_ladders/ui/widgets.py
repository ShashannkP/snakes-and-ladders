"""Small shared drawing helpers."""

import pygame

BACKGROUND = (21, 28, 43)
TEXT = (237, 241, 249)
TOKEN_COLOURS = {
    "blue": (80, 160, 240), "orange": (240, 155, 65),
    "green": (70, 195, 140), "magenta": (215, 100, 200),
}


def label(surface, text, position, size=26, colour=TEXT):
    font = pygame.font.Font(None, size)
    surface.blit(font.render(text, True, colour), position)


def button(surface, rect, text, enabled=True):
    pygame.draw.rect(surface, (45, 110, 165) if enabled else (60, 65, 75), rect, border_radius=8)
    label(surface, text, (rect.x + 12, rect.y + 12))
