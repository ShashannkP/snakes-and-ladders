"""Tests for overshoot handling (FR-10)."""

import pytest

from snakes_ladders.engine import Event, GameEngine, Phase
from tests.engine.factories import make_state
from tests.engine.scripted_rng import ScriptedRng


def test_overshoot_stays_and_turn_passes():
    # TC-FR10-1: token at 97, roll 4 (would be 101).
    state = make_state(97, 0)
    result = GameEngine(rng=ScriptedRng([4])).roll_and_move(state)
    assert state.players[0].position == 97
    assert result.event is Event.OVERSHOOT
    assert (result.from_pos, result.landed_pos, result.final_pos) == (97, 97, 97)
    assert result.next_index == 1


def test_overshoot_still_shows_the_roll():
    # TC-FR10-2 (engine part): the dice shows 2, the token does not move, next player is current.
    state = make_state(99, 0)
    result = GameEngine(rng=ScriptedRng([2])).roll_and_move(state)
    assert result.roll == 2
    assert state.last_roll == 2
    assert state.players[0].position == 99
    assert state.current_index == 1


def test_exactly_100_is_a_win_not_an_overshoot():
    # TC-FR10-3: token at 96, roll 4.
    state = make_state(96, 0)
    result = GameEngine(rng=ScriptedRng([4])).roll_and_move(state)
    assert result.event is Event.NONE
    assert result.winner_index == 0


@pytest.mark.parametrize("position, roll", [(99, 2), (99, 6), (97, 4), (96, 5)])
def test_any_roll_past_100_is_an_overshoot(position, roll):
    state = make_state(position, 0)
    result = GameEngine(rng=ScriptedRng([roll])).roll_and_move(state)
    assert state.players[0].position == position
    assert result.event is Event.OVERSHOOT


def test_overshoot_is_not_a_win():
    state = make_state(99, 0)
    result = GameEngine(rng=ScriptedRng([3])).roll_and_move(state)
    assert result.winner_index is None
    assert state.phase is Phase.AWAITING_ROLL
