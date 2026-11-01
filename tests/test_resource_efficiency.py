"""NFR-14: verify gameplay memory and save-file size limits."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import psutil

from snakes_ladders.controller.game_controller import GameController
from snakes_ladders.engine.setup import COLOURS, PlayerConfig
from snakes_ladders.persistence import SaveManager
from snakes_ladders.persistence.save_manager import MAX_SAVE_SIZE
from snakes_ladders.ui.game_screen import GameScreen
from snakes_ladders.ui.viewport import LOGICAL_SIZE

MAX_GAMEPLAY_MEMORY_BYTES = 200_000_000


def largest_player_configs():
    return [
        PlayerConfig(f"Player{i:02d}" + "X" * 7, COLOURS[i])
        for i in range(4)
    ]


def test_largest_save_stays_within_10_kibibytes(tmp_path):
    manager = SaveManager(directory=tmp_path)
    controller = GameController(save_manager=manager)
    controller.start_new_game(largest_player_configs())

    assert controller.on_save_requested()

    assert manager.save_path.stat().st_size <= MAX_SAVE_SIZE


def test_oversized_save_is_rejected_without_replacing_previous_save(tmp_path):
    manager = SaveManager(directory=tmp_path)
    controller = GameController(save_manager=manager)
    controller.start_new_game(
        [PlayerConfig("Sam", "blue"), PlayerConfig("Alice", "orange")]
    )
    assert controller.on_save_requested()
    previous_save = manager.save_path.read_bytes()

    controller.state.players[0].name = "X" * MAX_SAVE_SIZE

    assert controller.on_save_requested() is False
    assert controller.error_message == "Save file exceeds the 10 KB limit."
    assert manager.save_path.read_bytes() == previous_save
    assert not manager.temp_path.exists()
    assert manager.load()["players"][0]["name"] == "Sam"


def test_four_player_gameplay_stays_within_memory_limit(tmp_path):
    pygame.init()
    surface = pygame.display.set_mode(LOGICAL_SIZE)
    manager = SaveManager(directory=tmp_path)
    controller = GameController(save_manager=manager)
    controller.start_new_game(largest_player_configs())
    screen = GameScreen(controller)
    process = psutil.Process()
    peak_memory = process.memory_info().rss

    try:
        for _ in range(300):
            screen.draw(surface)
            pygame.display.flip()
            peak_memory = max(peak_memory, process.memory_info().rss)

            if controller.screen == "result":
                controller.new_game_requested()
                controller.start_new_game(largest_player_configs())
            else:
                controller.on_roll_requested()
                controller.on_animation_done()

        assert peak_memory <= MAX_GAMEPLAY_MEMORY_BYTES, (
            f"Peak process RSS was {peak_memory / 1_000_000:.1f} MB; "
            f"limit is {MAX_GAMEPLAY_MEMORY_BYTES / 1_000_000:.0f} MB."
        )
    finally:
        pygame.quit()
