"""Tests for snake encounters (FR-06)."""

import pytest

from snakes_ladders.engine import Board, Event, GameEngine
from tests.engine.test_factories import make_state
from tests.engine.test_scripted_rng import ScriptedRng

# Written out again from SRS 4.3 on purpose: the test must not trust the code's own table.
SRS_SNAKES = {17: 7, 54: 34, 62: 19, 64: 60, 87: 36, 93: 73, 95: 75, 98: 79}


def test_land_on_snake_head():
    # TC-FR06-1: token at 14, roll 3, lands on 17 -> slides to 7.
    state = make_state(14, 0)
    result = GameEngine(rng=ScriptedRng([3])).roll_and_move(state)
    assert state.players[0].position == 7
    assert (result.landed_pos, result.final_pos, result.event) == (17, 7, Event.SNAKE)


@pytest.mark.parametrize("head, tail", sorted(SRS_SNAKES.items()))
def test_every_snake(head, tail):
    # TC-FR06-2: from head - 1 with a roll of 1.
    state = make_state(head - 1, 0)
    result = GameEngine(rng=ScriptedRng([1])).roll_and_move(state)
    assert state.players[0].position == tail
    assert result.event is Event.SNAKE


def test_snake_tail_is_not_a_trigger():
    # TC-FR06-3: token at 2, roll 5, lands on 7 (a tail) -> stays.
    state = make_state(2, 0)
    result = GameEngine(rng=ScriptedRng([5])).roll_and_move(state)
    assert state.players[0].position == 7
    assert result.event is Event.NONE


def test_turn_passes_after_snake():
    # FR-06: the slide happens "before the turn ends", then the turn passes as normal.
    state = make_state(14, 0)
    result = GameEngine(rng=ScriptedRng([3])).roll_and_move(state)
    assert result.next_index == 1


def test_board_snakes_match_srs():
    # TC-BRD-1 (snake part).
    board = Board()
    assert dict(board.snakes) == SRS_SNAKES
    assert all(head > tail for head, tail in board.snakes.items())
    assert Board.SIZE not in board.snakes


def test_resolve_plain_square():
    assert Board().resolve(50) == (50, Event.NONE)


def test_board_cannot_be_modified():
    with pytest.raises(TypeError):
        Board().snakes[17] = 1
