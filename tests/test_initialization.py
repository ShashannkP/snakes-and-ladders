import pytest

from snakes_ladders.controller.game_controller import GameController
from snakes_ladders.engine import GameEngine, Phase
from snakes_ladders.engine.setup import COLOURS, InputValidationError, PlayerConfig


def configs(count):
    return [PlayerConfig(f"P{i}", COLOURS[i % 4]) for i in range(count)]


@pytest.mark.parametrize("count", [0, 1, 5])
def test_invalid_count_rejected_by_engine_and_controller(count):
    with pytest.raises(InputValidationError):
        GameEngine().new_game(configs(count))
    controller = GameController()
    with pytest.raises(InputValidationError):
        controller.start_new_game(configs(count))
    assert controller.state is None
    assert controller.screen == "setup"


@pytest.mark.parametrize("count", [2, 3, 4])
def test_new_game_starts_clean_and_in_setup_order(count):
    controller = GameController()
    controller.start_new_game(configs(count))
    state = controller.state
    assert controller.screen == "game"
    assert [p.name for p in state.players] == [f"P{i}" for i in range(count)]
    assert [p.position for p in state.players] == [0] * count
    assert state.current_index == 0
    assert state.last_roll is None
    assert state.extra_rolls_used == 0
    assert state.phase is Phase.AWAITING_ROLL


def test_new_state_does_not_reuse_previous_players():
    engine = GameEngine()
    original = engine.new_game(configs(2))
    original.players[0].position = 90
    fresh = engine.new_game(configs(2))
    assert fresh.players[0].position == 0
    assert original.players[0].position == 90


def test_invalid_setup_does_not_replace_current_game():
    controller = GameController()
    controller.start_new_game(configs(2))
    original = controller.state
    with pytest.raises(InputValidationError):
        controller.start_new_game([PlayerConfig("Sam", "blue"), PlayerConfig("sam", "orange")])
    assert controller.state is original


def test_roll_is_ignored_before_start_or_after_game_over():
    controller = GameController()
    assert controller.on_roll_requested() is None
    controller.start_new_game(configs(2))
    controller.state.phase = Phase.GAME_OVER
    assert controller.on_roll_requested() is None
    assert controller.state.last_roll is None
