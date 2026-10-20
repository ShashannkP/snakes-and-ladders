"""Playable board with turn controls and a player legend."""

import pygame

from snakes_ladders.engine import Phase
from snakes_ladders.ui.board_view import BoardView
from snakes_ladders.ui.widgets import BACKGROUND, TOKEN_COLOURS, button, label


class GameScreen:
    def __init__(self, controller):
        self.controller = controller
        self.board_view = BoardView()
        self.roll_button = pygame.Rect(700, 560, 220, 50)

    def handle_event(self, event):
        clicked = event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.roll_button.collidepoint(event.pos)
        pressed = event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE
        if clicked or pressed:
            self.controller.on_roll_requested()

    def draw(self, surface):
        surface.fill(BACKGROUND)
        state = self.controller.state
        label(surface, "Snakes and Ladders", (40, 15), 38)
        self.board_view.draw(surface, state.players)
        label(surface, "Players", (700, 150), 30)
        for i, player in enumerate(state.players):
            y = 200 + i * 75
            pygame.draw.circle(surface, TOKEN_COLOURS[player.colour], (720, y + 15), 20)
            label(surface, str(i + 1), (714, y + 6), colour=(15, 20, 30))
            label(surface, f"{player.name}   |   Square {player.position}", (755, y))
        if state.phase is Phase.GAME_OVER:
            winner = state.players[self.controller.last_result.winner_index]
            label(surface, f"Winner: {winner.name}", (700, 80), 32)
        else:
            current_player = state.players[state.current_index]
            pygame.draw.circle(surface, TOKEN_COLOURS[current_player.colour], (720, 95), 20)
            label(surface, str(state.current_index + 1), (714, 86), colour=(15, 20, 30))
            label(surface, f"Turn: {current_player.name}", (755, 80), 32)
        label(surface, "Snakes: red curves", (700, 465), 25)
        label(surface, "Ladders: brown rails", (700, 495), 25)
        button(surface, self.roll_button, "Roll Dice (Space)", state.phase is Phase.AWAITING_ROLL)
        if state.last_roll is not None:
            label(surface, f"Last roll: {state.last_roll}", (950, 575))
