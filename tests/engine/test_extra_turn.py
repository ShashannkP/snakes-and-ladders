"""Tests for the extra-turn rule (FR-08)."""

import pytest

from snakes_ladders.engine import GameEngine, Phase
from tests.engine.test_factories import make_state
from tests.engine.scripted_rng import ScriptedRng


def make_extra_state(*positions, enabled=True):
    state = make_state(*positions)
    state.extra_turn_enabled = enabled
    return state


def test_six_grants_an_extra_roll():
    # TC-FR08-1: P1 from 0 rolls 6 then 2. After the 6 P1 rolls again; after the 2 the turn passes.
    state = make_extra_state(0, 0)
    engine = GameEngine(rng=ScriptedRng([6, 2]))

    first = engine.roll_and_move(state)
    assert first.extra_roll is True
    assert first.next_index == 0
    assert state.current_index == 0
    assert state.extra_rolls_used == 1

    second = engine.roll_and_move(state)
    assert state.players[0].position == 8
    assert second.extra_roll is False
    assert second.next_index == 1


def test_at_most_two_extra_rolls_then_counter_resets():
    # TC-FR08-2: P1 rolls 6, 6, 6 (6, 12, 18). The third 6 gives no extra roll.
    # P2 then rolls 6 and 1 and gets one extra roll, so the counter was reset.
    state = make_extra_state(0, 0)
    engine = GameEngine(rng=ScriptedRng([6, 6, 6, 6, 1]))

    results = [engine.roll_and_move(state) for _ in range(3)]
    assert [r.extra_roll for r in results] == [True, True, False]
    assert [p.position for p in state.players] == [18, 0]
    assert state.current_index == 1
    assert state.extra_rolls_used == 0

    p2_six = engine.roll_and_move(state)
    assert p2_six.player_index == 1
    assert p2_six.extra_roll is True
    assert engine.roll_and_move(state).player_index == 1


@pytest.mark.parametrize("roll", [1, 2, 3, 4, 5])
def test_non_six_gives_no_extra_roll(roll):
    # TC-FR08-3
    state = make_extra_state(30, 0)
    result = GameEngine(rng=ScriptedRng([roll])).roll_and_move(state)
    assert result.extra_roll is False
    assert result.next_index == 1


def test_option_disabled_six_gives_no_extra_roll():
    # TC-FR08-4
    state = make_extra_state(0, 0, enabled=False)
    result = GameEngine(rng=ScriptedRng([6])).roll_and_move(state)
    assert result.extra_roll is False
    assert result.next_index == 1
    assert state.extra_rolls_used == 0


def test_six_onto_snake_still_gives_extra_roll():
    # TC-FR08-5: token at 11, roll 6 lands on snake head 17 -> 7, extra roll still granted.
    state = make_extra_state(11, 0)
    result = GameEngine(rng=ScriptedRng([6])).roll_and_move(state)
    assert state.players[0].position == 7
    assert result.extra_roll is True
    assert result.next_index == 0


def test_six_that_overshoots_gives_no_extra_roll():
    # TC-FR08-6 (design decision D-1): token at 97, roll 6 overshoots.
    state = make_extra_state(97, 0)
    result = GameEngine(rng=ScriptedRng([6])).roll_and_move(state)
    assert state.players[0].position == 97
    assert result.extra_roll is False
    assert result.next_index == 1


def test_six_that_wins_gives_no_extra_roll():
    # TC-FR08-7: token at 94, roll 6 reaches 100.
    state = make_extra_state(94, 0)
    result = GameEngine(rng=ScriptedRng([6])).roll_and_move(state)
    assert result.winner_index == 0
    assert result.extra_roll is False
    assert state.phase is Phase.GAME_OVER
