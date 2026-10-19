"""Turn manager (SDD C12): decides whose turn it is."""

from snakes_ladders.engine.models import GameState


class TurnManager:
    def advance(self, state: GameState) -> None:
        """Pass the turn to the next player in setup order (FR-05, SDD 3.2 step 7)."""
        state.current_index = (state.current_index + 1) % len(state.players)
        state.extra_rolls_used = 0
