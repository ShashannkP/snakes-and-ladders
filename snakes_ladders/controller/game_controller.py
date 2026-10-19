"""Use cases connecting screens to the Pygame-free engine."""

from snakes_ladders.controller.input_validator import validate_setup
from snakes_ladders.engine import GameEngine, Phase


class GameController:
    def __init__(self, engine=None):
        self.engine = engine if engine is not None else GameEngine()
        self.state = None
        self.screen = "setup"
        self.running = True
        self.last_result = None

    def start_new_game(self, configs, extra_turn=False):
        configs = validate_setup(configs)
        state = self.engine.new_game(configs, extra_turn)
        self.state = state
        self.last_result = None
        self.screen = "game"

    def on_roll_requested(self):
        if self.screen != "game" or self.state is None or self.state.phase is not Phase.AWAITING_ROLL:
            return None
        self.last_result = self.engine.roll_and_move(self.state)
        return self.last_result
