"""Winner announcement and final standings (FR-16)."""

import pygame

from snakes_ladders.ui.widgets import BACKGROUND, TOKEN_COLOURS, button, label


class ResultScreen:
    def __init__(self, controller):
        self.controller = controller
        self.new_game_button = pygame.Rect(60, 580, 180, 50)
        self.exit_button = pygame.Rect(270, 580, 150, 50)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.new_game_button.collidepoint(event.pos):
                self.controller.new_game_requested()
            elif self.exit_button.collidepoint(event.pos):
                self.controller.exit_requested()

    def draw(self, surface):
        surface.fill(BACKGROUND)
        standings = self.controller.engine.standings(self.controller.state)
        winner_index = self.controller.last_result.winner_index
        winner = self.controller.state.players[winner_index]
        label(surface, f"Winner: {winner.name}!", (60, 55), 48)
        label(surface, "Final standings", (60, 125), 32)
        label(surface, "Rank", (60, 190))
        label(surface, "Player", (180, 190))
        label(surface, "Position", (650, 190))
        for row, standing in enumerate(standings):
            y = 250 + row * 65
            label(surface, str(standing.rank), (75, y))
            pygame.draw.circle(surface, TOKEN_COLOURS[standing.colour], (155, y + 10), 18)
            label(surface, str(standing.player_index + 1), (150, y + 2), 22, (15, 20, 30))
            label(surface, standing.name, (190, y))
            label(surface, str(standing.position), (670, y))
        button(surface, self.new_game_button, "New Game")
        button(surface, self.exit_button, "Exit")
