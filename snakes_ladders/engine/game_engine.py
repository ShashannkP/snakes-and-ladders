"""Game engine facade (SDD C10): the single entry point to the rules."""

import random

from snakes_ladders.engine.dice import DiceService
from snakes_ladders.engine.models import Event, GameState, TurnResult


class GameEngine:
    def __init__(self, rng: random.Random | None = None) -> None:
        self._dice = DiceService(rng)

    def roll_and_move(self, state: GameState) -> TurnResult:
        """Roll once for the current player and apply the result (SDD 3.2)."""
        index = state.current_index
        player = state.players[index]

        # Step 1: roll (FR-03). No dice argument is accepted (SEC-04).
        roll = self._dice.roll()
        state.last_roll = roll

        # Step 2: move forward by exactly the dice value (FR-04).
        from_pos = player.position
        target = from_pos + roll
        # TODO FR-10: step 3, overshoot past 100.
        # TODO FR-06/07: step 4, board.resolve(target) for snakes and ladders.
        player.position = target

        # TODO FR-09: step 5, win check.
        # TODO FR-08/FR-05: steps 6-7, extra roll or pass the turn.

        return TurnResult(
            player_index=index,
            roll=roll,
            from_pos=from_pos,
            landed_pos=target,
            final_pos=target,
            event=Event.NONE,
            extra_roll=False,
            winner_index=None,
            next_index=index,
        )
