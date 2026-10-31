"""Tests for ladder encounters (FR-07) and the full board layout (TC-BRD-1)."""

import pytest

from snakes_ladders.engine import Board, Event, GameEngine
from tests.engine.test_factories import make_state
from tests.engine.test_scripted_rng import ScriptedRng

# Written out again from SRS 4.3 on purpose: the test must not trust the code's own table.
SRS_LADDERS = {1: 38, 4: 14, 9: 31, 21: 42, 28: 84, 51: 67, 72: 91, 80: 99}


def test_land_on_ladder_base():
    # TC-FR07-1: token at 0, roll 4, lands on 4 -> climbs to 14.
    state = make_state(0, 0)
    result = GameEngine(rng=ScriptedRng([4])).roll_and_move(state)
    assert state.players[0].position == 14
    assert (result.landed_pos, result.final_pos, result.event) == (4, 14, Event.LADDER)


@pytest.mark.parametrize("base, top", sorted(SRS_LADDERS.items()))
def test_every_ladder(base, top):
    # TC-FR07-2: from base - 1 with a roll of 1 (from 0 for the ladder at 1).
    state = make_state(base - 1, 0)
    result = GameEngine(rng=ScriptedRng([1])).roll_and_move(state)
    assert state.players[0].position == top
    assert result.event is Event.LADDER


def test_ladder_top_is_not_a_trigger():
    # TC-FR07-3: token at 38, roll 4, lands on 42 (top of 21 -> 42) -> stays.
    state = make_state(38, 0)
    result = GameEngine(rng=ScriptedRng([4])).roll_and_move(state)
    assert state.players[0].position == 42
    assert result.event is Event.NONE


def test_turn_passes_after_ladder():
    state = make_state(0, 0)
    result = GameEngine(rng=ScriptedRng([4])).roll_and_move(state)
    assert result.next_index == 1


def test_board_ladders_match_srs():
    # TC-BRD-1 (ladder part).
    board = Board()
    assert dict(board.ladders) == SRS_LADDERS
    assert all(base < top for base, top in board.ladders.items())


def test_ladders_cannot_be_modified():
    with pytest.raises(TypeError):
        Board().ladders[1] = 100


def test_board_has_no_conflicts_or_chains():
    # TC-BRD-1 / SRS 4.3: no square is both a head and a base, and no tail or
    # top lands on another head or base (so resolve() never needs a second jump).
    board = Board()
    triggers = set(board.snakes) | set(board.ladders)
    destinations = set(board.snakes.values()) | set(board.ladders.values())
    assert not set(board.snakes) & set(board.ladders)
    assert not triggers & destinations
