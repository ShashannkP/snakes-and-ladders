"""NFR-08: saved games preserve gameplay state through repeated round trips."""

from snakes_ladders.controller.game_controller import GameController
from snakes_ladders.engine.setup import COLOURS, PlayerConfig
from snakes_ladders.persistence import SaveManager


def _state_snapshot(state):
    return (
        tuple((player.name, player.colour, player.position) for player in state.players),
        state.current_index,
        state.extra_turn_enabled,
        state.extra_rolls_used,
        state.last_roll,
        state.phase,
    )


def _configure_cycle_state(controller, cycle):
    player_count = 2 + cycle % 3
    configs = [
        PlayerConfig(f"Player{cycle:02d}{index}", COLOURS[index])
        for index in range(player_count)
    ]
    controller.start_new_game(configs, extra_turn=cycle % 2 == 0)

    positions = [0, 99, (cycle * 7) % 100, (cycle * 11) % 100]
    for index, player in enumerate(controller.state.players):
        player.position = positions[(cycle + index) % len(positions)]

    controller.state.current_index = cycle % player_count
    if controller.state.extra_turn_enabled:
        controller.state.extra_rolls_used = cycle % 3
    if controller.state.extra_rolls_used:
        controller.state.last_roll = 6
    elif cycle % 2 == 0:
        controller.state.last_roll = None
    else:
        controller.state.last_roll = cycle % 5 + 1


def test_twenty_save_resume_cycles_preserve_every_state_field(tmp_path):
    manager = SaveManager(directory=tmp_path)

    for cycle in range(20):
        original = GameController(save_manager=manager)
        _configure_cycle_state(original, cycle)
        expected = _state_snapshot(original.state)

        assert original.on_save_requested(), f"Save failed in cycle {cycle}"

        resumed = GameController(save_manager=SaveManager(directory=tmp_path))
        assert resumed.on_resume_requested(), f"Resume failed in cycle {cycle}"
        assert _state_snapshot(resumed.state) == expected, (
            f"State changed after resume in cycle {cycle}"
        )

        if cycle % 4 == 2:
            assert resumed.on_save_requested(), (
                f"Immediate re-save failed in cycle {cycle}"
            )
            resumed_again = GameController(
                save_manager=SaveManager(directory=tmp_path)
            )
            assert resumed_again.on_resume_requested(), (
                f"Second resume failed in cycle {cycle}"
            )
            assert _state_snapshot(resumed_again.state) == expected, (
                f"State changed after immediate re-save in cycle {cycle}"
            )
