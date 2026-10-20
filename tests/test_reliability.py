"""End-to-end reliability checks for NFR-03 (TC-N03-1)."""

import random

import pytest

from snakes_ladders.controller.game_controller import GameController
from snakes_ladders.engine import Board, Event, GameEngine, Phase
from snakes_ladders.engine.setup import COLOURS, PlayerConfig


GAME_COUNT = 100
ROLL_CAP = 5_000


def configs(count: int) -> list[PlayerConfig]:
    return [PlayerConfig(f"P{index + 1}", COLOURS[index]) for index in range(count)]


def assert_turn_invariants(state, result, previous_index, previous_extra_rolls, seed):
    """Assert the SDD 3.2 rules independently after a completed controller move."""
    context = f"seed={seed}, roll={result.roll}, player={previous_index}"
    assert result.player_index == previous_index, context
    assert result.next_index == state.current_index, context
    assert 0 <= state.current_index < len(state.players), context
    assert all(0 <= player.position <= Board.SIZE for player in state.players), context
    assert all(
        player.position not in Board().snakes and player.position not in Board().ladders
        for player in state.players
    ), context

    expected_landed = result.from_pos if result.from_pos + result.roll > Board.SIZE else result.from_pos + result.roll
    expected_final, expected_event = Board().resolve(expected_landed)
    if result.from_pos + result.roll > Board.SIZE:
        expected_event = Event.OVERSHOOT
    assert (result.landed_pos, result.final_pos, result.event) == (
        expected_landed,
        expected_final,
        expected_event,
    ), context

    winner_positions = [index for index, player in enumerate(state.players) if player.position == Board.SIZE]
    assert len(winner_positions) <= 1, context
    if result.winner_index is not None:
        assert result.winner_index == previous_index == winner_positions[0], context
        assert state.phase is Phase.GAME_OVER, context
        assert state.current_index == previous_index, context
        return

    expected_extra_roll = (
        state.extra_turn_enabled
        and result.roll == 6
        and result.event is not Event.OVERSHOOT
        and previous_extra_rolls < 2
    )
    assert result.extra_roll is expected_extra_roll, context
    if expected_extra_roll:
        assert state.current_index == previous_index, context
        assert state.extra_rolls_used == previous_extra_rolls + 1, context
    else:
        assert state.current_index == (previous_index + 1) % len(state.players), context
        assert state.extra_rolls_used == 0, context


@pytest.mark.parametrize("seed", range(GAME_COUNT))
def test_one_hundred_full_games_preserve_rule_invariants(seed):
    """TC-N03-1: each seeded game must finish without violating a rule."""
    engine = GameEngine(rng=random.Random(seed))
    controller = GameController(engine)
    controller.start_new_game(configs(2 + seed % 3), extra_turn=bool(seed % 2))

    for roll_count in range(1, ROLL_CAP + 1):
        state = controller.state
        previous_index = state.current_index
        previous_extra_rolls = state.extra_rolls_used
        result = controller.on_roll_requested()

        assert result is not None, f"seed={seed}, roll={roll_count}: roll request was rejected"
        assert_turn_invariants(state, result, previous_index, previous_extra_rolls, seed)
        if state.phase is Phase.GAME_OVER:
            assert controller.screen == "result", f"seed={seed}, roll={roll_count}"
            break
    else:
        pytest.fail(f"seed={seed}: game did not finish within {ROLL_CAP} rolls")
