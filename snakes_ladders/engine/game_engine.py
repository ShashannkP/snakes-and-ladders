"""Game engine facade (SDD C10): the single entry point to the rules."""

import random

from snakes_ladders.engine.dice import DiceService
from snakes_ladders.engine.models import Event, GameState, TurnResult
from snakes_ladders.engine.turn_manager import TurnManager
from snakes_ladders.engine.board import Board


class GameEngine:
    def __init__(self, rng: random.Random | None = None) -> None:
        self._dice = DiceService(rng)
        self._turns = TurnManager()
        self._board = Board()


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
        # Step 4: snake or ladder at the landing square (FR-06, FR-07).
        final, event = self._board.resolve(target)
        player.position = final

        # TODO FR-09: step 5, win check (the turn does not pass if someone won).
        # TODO FR-08: step 6, extra roll after a 6 (the turn does not pass).

        # Step 7: pass the turn to the next player in setup order (FR-05).
        self._turns.advance(state)


        return TurnResult(
            player_index=index,
            roll=roll,
            from_pos=from_pos,
            landed_pos=target,
            final_pos=final,
            event=event,
            extra_roll=False,
            winner_index=None,
            next_index=state.current_index,
        )
