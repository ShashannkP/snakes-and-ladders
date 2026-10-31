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
        if not self._is_awaiting_roll():
            return None
        self.last_result = self.engine.roll_and_move(self.state)
        if self.last_result.winner_index is not None:
            self.screen = "result"
        else:
            self.state.phase = Phase.ANIMATING
        return self.last_result

    def on_animation_done(self):
        """The UI calls this when the token has finished moving (SDD 3.1)."""
        if self.state is not None and self.state.phase is Phase.ANIMATING:
            self.state.phase = Phase.AWAITING_ROLL

    def on_save_requested(self):
        """Saving is only allowed between rolls (FR-17). The write itself is FR-15."""
        return self._is_awaiting_roll()

    def _is_awaiting_roll(self):
        return self.screen == "game" and self.state is not None and self.state.phase is Phase.AWAITING_ROLL


    def new_game_requested(self):
        """Return to setup from results; the next Start creates fresh players."""
        if self.screen == "result":
            self.state = None
            self.last_result = None
            self.screen = "setup"

    def exit_requested(self):
        if self.screen == "result":
            self.running = False
