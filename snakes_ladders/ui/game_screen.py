"""Minimal playable view for the setup-to-engine flow."""

import pygame

from snakes_ladders.engine import Phase
from snakes_ladders.ui.widgets import BACKGROUND, TOKEN_COLOURS, button, label


class GameScreen:
    def __init__(self, controller):
        self.controller = controller
        self.roll_button = pygame.Rect(60, 560, 200, 50)

    def handle_event(self, event):
        clicked = event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.roll_button.collidepoint(event.pos)
        pressed = event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE
        if clicked or pressed:
            self.controller.on_roll_requested()

    def draw(self, surface):
        surface.fill(BACKGROUND)
        state = self.controller.state
        label(surface, "Snakes and Ladders", (60, 45), 42)
        for i, player in enumerate(state.players):
            y = 160 + i * 80
            pygame.draw.circle(surface, TOKEN_COLOURS[player.colour], (90, y + 15), 24)
            label(surface, str(i + 1), (84, y + 6), colour=(15, 20, 30))
            label(surface, f"{player.name}   |   Square {player.position}", (140, y))
        if state.phase is Phase.GAME_OVER:
            winner = state.players[self.controller.last_result.winner_index]
            label(surface, f"Winner: {winner.name}", (60, 490), 32)
        else:
            label(surface, f"Turn: {state.players[state.current_index].name}", (60, 490), 32)
        button(surface, self.roll_button, "Roll Dice (Space)", state.phase is Phase.AWAITING_ROLL)
        if state.last_roll is not None:
            label(surface, f"Last roll: {state.last_roll}", (300, 575))
