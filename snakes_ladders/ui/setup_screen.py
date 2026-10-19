"""Collect player details; all validation goes through the application layer."""

import pygame

from snakes_ladders.controller.input_validator import validate_setup
from snakes_ladders.engine.setup import COLOURS, InputValidationError, PlayerConfig
from snakes_ladders.ui.widgets import BACKGROUND, TOKEN_COLOURS, button, label


class SetupScreen:
    def __init__(self):
        self.count = 2
        self.names = ["", "", "", ""]
        self.colours = list(COLOURS)
        self.active = 0
        self.count_buttons = [(n, pygame.Rect(260 + (n - 2) * 80, 110, 65, 45)) for n in range(2, 5)]

    def name_rect(self, index):
        return pygame.Rect(140, 205 + index * 80, 420, 48)

    def colour_rect(self, index):
        return pygame.Rect(590, 205 + index * 80, 190, 48)

    def configs(self):
        return validate_setup([
            PlayerConfig(self.names[i], self.colours[i]) for i in range(self.count)
        ])

    def validation_error(self):
        try:
            self.configs()
        except InputValidationError as error:
            return str(error)
        return ""

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for count, rect in self.count_buttons:
                if rect.collidepoint(event.pos):
                    self.count, self.active = count, min(self.active, count - 1)
            for i in range(self.count):
                if self.name_rect(i).collidepoint(event.pos):
                    self.active = i
                if self.colour_rect(i).collidepoint(event.pos):
                    self.colours[i] = COLOURS[(COLOURS.index(self.colours[i]) + 1) % len(COLOURS)]
        elif event.type == pygame.TEXTINPUT:
            # Bound the buffer even for a very large pasted text event.
            self.names[self.active] = (self.names[self.active] + event.text)[:64]
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.names[self.active] = self.names[self.active][:-1]
            elif event.key in (pygame.K_TAB, pygame.K_RETURN):
                self.active = (self.active + 1) % self.count

    def draw(self, surface):
        surface.fill(BACKGROUND)
        label(surface, "Set up your players", (60, 45), 42)
        label(surface, "Players:", (60, 125))
        for count, rect in self.count_buttons:
            button(surface, rect, str(count), self.count == count)
        label(surface, "Click a name to type. Click a colour to change it. Tab: next player.", (60, 170), 24)
        for i in range(self.count):
            rect = self.name_rect(i)
            pygame.draw.rect(surface, (43, 53, 72), rect, border_radius=6)
            pygame.draw.rect(surface, (100, 180, 255) if i == self.active else (90, 100, 120), rect, 2, border_radius=6)
            label(surface, str(i + 1), (100, rect.y + 13))
            label(surface, self.names[i] or "Enter name", (rect.x + 12, rect.y + 13))
            colour_rect = self.colour_rect(i)
            pygame.draw.rect(surface, TOKEN_COLOURS[self.colours[i]], colour_rect, border_radius=6)
            label(surface, f"{i + 1}: {self.colours[i]}", (colour_rect.x + 12, colour_rect.y + 13), colour=(15, 20, 30))
        error = self.validation_error()
        label(surface, error or "Player details are valid.", (60, 560), 25, (255, 180, 145) if error else (110, 230, 165))
