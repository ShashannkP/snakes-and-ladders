"""Tests for token movement (FR-04)."""

import pytest

from snakes_ladders.engine import Event, GameEngine, Player
from tests.engine.test_factories import make_state
from tests.engine.test_scripted_rng import ScriptedRng





def test_new_player_starts_at_zero():
    assert Player("P1", "blue").position == 0


def test_from_zero_roll_3():
    # TC-FR04-1
    state = make_state(0, 0)
    result = GameEngine(rng=ScriptedRng([3])).roll_and_move(state)
    assert state.players[0].position == 3
    assert (result.from_pos, result.landed_pos, result.final_pos) == (0, 3, 3)
    assert result.roll == 3
    assert result.event is Event.NONE


def test_from_10_roll_5():
    # TC-FR04-2
    state = make_state(10, 0)
    GameEngine(rng=ScriptedRng([5])).roll_and_move(state)
    assert state.players[0].position == 15


def test_sequence_adds_exact_dice_value():
    # TC-FR04-3: rolls 6, 5, 2 from 0 give 6, 11, 13.
    state = make_state(0, 0)
    engine = GameEngine(rng=ScriptedRng([6, 5, 2]))
    positions = []
    for _ in range(3):
        state.current_index = 0  # keep P1's turn so this tests movement only, not turn order (FR-05)
        engine.roll_and_move(state)
        positions.append(state.players[0].position)
    assert positions == [6, 11, 13]


@pytest.mark.parametrize("roll", [1, 2, 3, 4, 5, 6])
def test_every_dice_value_moves_exactly(roll):
    # Squares 31-36 have no snakes or ladders, so this stays valid after FR-06/07.
    state = make_state(30, 0)
    GameEngine(rng=ScriptedRng([roll])).roll_and_move(state)
    assert state.players[0].position == 30 + roll


def test_only_current_player_moves():
    state = make_state(5, 12, 20)
    state.current_index = 1
    GameEngine(rng=ScriptedRng([4])).roll_and_move(state)
    assert [p.position for p in state.players] == [5, 16, 20]


def test_last_roll_is_recorded():
    state = make_state(0, 0)
    GameEngine(rng=ScriptedRng([4])).roll_and_move(state)
    assert state.last_roll == 4
