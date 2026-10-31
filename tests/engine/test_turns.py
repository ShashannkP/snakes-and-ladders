"""Tests for turn management (FR-05)."""

from snakes_ladders.engine import GameEngine
from tests.engine.test_factories import make_state
from tests.engine.test_scripted_rng import ScriptedRng


def roll_n(engine, state, n):
    """Roll n times and return the index of the player who rolled each time."""
    return [engine.roll_and_move(state).player_index for _ in range(n)]


def test_turn_passes_in_setup_order():
    # TC-FR05-1: 3 players, rolls 2, 3, 5, then 2 more -> P1, P2, P3, P1, P2.
    state = make_state(0, 0, 0)
    engine = GameEngine(rng=ScriptedRng([2, 3, 5, 3, 2]))
    assert roll_n(engine, state, 5) == [0, 1, 2, 0, 1]
    assert [p.position for p in state.players] == [5, 5, 5]


def test_four_players_two_full_rounds():
    # TC-FR05-2 (engine part): rolls 2,2,2,2,3,3,3,3 -> P1..P4 twice.
    state = make_state(0, 0, 0, 0)
    engine = GameEngine(rng=ScriptedRng([2, 2, 2, 2, 3, 3, 3, 3]))
    assert roll_n(engine, state, 8) == [0, 1, 2, 3, 0, 1, 2, 3]
    assert [p.position for p in state.players] == [5, 5, 5, 5]


def test_last_player_wraps_to_first():
    state = make_state(10, 10, 10, 10)
    state.current_index = 3
    GameEngine(rng=ScriptedRng([1])).roll_and_move(state)
    assert state.current_index == 0


def test_result_reports_next_player():
    state = make_state(0, 0)
    result = GameEngine(rng=ScriptedRng([3])).roll_and_move(state)
    assert result.player_index == 0
    assert result.next_index == 1 == state.current_index


def test_extra_roll_counter_resets_when_turn_passes():
    # SDD 3.2 step 7: the counter resets for the next player (needed by FR-08).
    state = make_state(0, 0)
    state.extra_rolls_used = 1
    GameEngine(rng=ScriptedRng([3])).roll_and_move(state)
    assert state.extra_rolls_used == 0
