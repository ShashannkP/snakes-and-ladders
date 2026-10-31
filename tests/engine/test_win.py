"""Tests for the win condition (FR-09)."""

from snakes_ladders.engine import GameEngine, Phase
from tests.engine.test_factories import make_state
from tests.engine.test_scripted_rng import ScriptedRng


def test_reaching_100_wins():
    # TC-FR09-1 (engine part): token at 94, roll 6.
    state = make_state(94, 0)
    result = GameEngine(rng=ScriptedRng([6])).roll_and_move(state)
    assert state.players[0].position == 100
    assert result.winner_index == 0
    assert state.phase is Phase.GAME_OVER


def test_from_99_roll_1_wins():
    # TC-FR09-2
    state = make_state(99, 0)
    result = GameEngine(rng=ScriptedRng([1])).roll_and_move(state)
    assert result.winner_index == 0


def test_ladder_to_99_is_not_a_win():
    # TC-FR09-3: 79 + 1 lands on ladder 80 -> 99. No winner, turn passes.
    # A later roll of 1 from 99 wins.
    state = make_state(79, 0)
    engine = GameEngine(rng=ScriptedRng([1, 2, 1]))

    first = engine.roll_and_move(state)
    assert state.players[0].position == 99
    assert first.winner_index is None
    assert state.phase is Phase.AWAITING_ROLL
    assert first.next_index == 1

    engine.roll_and_move(state)  # P2: 0 -> 2
    last = engine.roll_and_move(state)  # P1: 99 -> 100
    assert last.winner_index == 0
    assert state.phase is Phase.GAME_OVER


def test_turn_does_not_pass_after_a_win():
    state = make_state(94, 0)
    result = GameEngine(rng=ScriptedRng([6])).roll_and_move(state)
    assert result.next_index == 0
    assert state.current_index == 0


def test_any_player_can_win():
    state = make_state(0, 97)
    state.current_index = 1
    result = GameEngine(rng=ScriptedRng([3])).roll_and_move(state)
    assert result.winner_index == 1


def test_normal_move_has_no_winner():
    state = make_state(10, 0)
    result = GameEngine(rng=ScriptedRng([3])).roll_and_move(state)
    assert result.winner_index is None
    assert state.phase is Phase.AWAITING_ROLL
