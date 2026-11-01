"""FR-15 / NFR-08 / NFR-11: Save and resume tests (SDD 3.5, 3.6.3)."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import json
from unittest.mock import patch
import pygame
import pytest

from snakes_ladders.controller.game_controller import GameController
from snakes_ladders.engine import GameEngine, Phase
from snakes_ladders.engine.models import Player
from snakes_ladders.engine.setup import PlayerConfig
from snakes_ladders.persistence import SaveManager, SaveWriteError
from snakes_ladders.ui.game_screen import GameScreen
from snakes_ladders.ui.setup_screen import SetupScreen
from tests.engine.test_scripted_rng import ScriptedRng


@pytest.fixture
def save_dir(tmp_path):
    return tmp_path / "snakes_ladders_saves"


def test_tc_fr15_1_save_and_resume_exact_state(save_dir):
    """TC-FR15-1: 3 players at 12, 37, 0, P3 to move, extra-turn on, last roll 4. Save, relaunch, resume."""
    manager = SaveManager(directory=save_dir)
    engine = GameEngine()
    controller = GameController(engine=engine, save_manager=manager)
    controller.start_new_game([
        PlayerConfig("Asha", "blue"),
        PlayerConfig("Ravi", "orange"),
        PlayerConfig("Maya", "green"),
    ], extra_turn=True)

    controller.state.players[0].position = 12
    controller.state.players[1].position = 37
    controller.state.players[2].position = 0
    controller.state.current_index = 2
    controller.state.last_roll = 4

    assert controller.on_save_requested() is True
    assert manager.exists() is True

    # Relaunch in new controller instance
    new_controller = GameController(engine=GameEngine(), save_manager=SaveManager(directory=save_dir))
    assert new_controller.can_resume() is True
    assert new_controller.on_resume_requested() is True
    assert new_controller.screen == "game"

    loaded = new_controller.state
    assert len(loaded.players) == 3
    assert [(p.name, p.colour, p.position) for p in loaded.players] == [
        ("Asha", "blue", 12),
        ("Ravi", "orange", 37),
        ("Maya", "green", 0),
    ]
    assert loaded.current_index == 2
    assert loaded.extra_turn_enabled is True
    assert loaded.extra_rolls_used == 0
    assert loaded.last_roll == 4
    assert loaded.phase is Phase.AWAITING_ROLL


def test_tc_fr15_2_save_and_resume_with_pending_extra_roll(save_dir):
    """TC-FR15-2: Save while extra roll is pending (after 6, extra_rolls_used 1), resume and roll 6, 6."""
    manager = SaveManager(directory=save_dir)
    # Player 1 rolls 6 (uses extra roll 1), saves, resumes, rolls 6 (uses extra roll 2), rolls 6 (turn passes)
    engine = GameEngine(rng=ScriptedRng([6, 6, 6]))
    controller = GameController(engine=engine, save_manager=manager)
    controller.start_new_game([PlayerConfig("Sam", "blue"), PlayerConfig("Alice", "orange")], extra_turn=True)

    res1 = controller.on_roll_requested()
    assert res1.extra_roll is True
    assert controller.state.current_index == 0
    assert controller.state.extra_rolls_used == 1
    controller.on_animation_done()

    # Save while extra roll is pending
    assert controller.on_save_requested() is True

    # Resume with scripted rng for next rolls
    new_engine = GameEngine(rng=ScriptedRng([6, 6]))
    new_controller = GameController(engine=new_engine, save_manager=SaveManager(directory=save_dir))
    assert new_controller.on_resume_requested() is True
    assert new_controller.state.current_index == 0
    assert new_controller.state.extra_rolls_used == 1

    # First roll after resume: rolls 6 -> gets second extra roll (max 2 used)
    res2 = new_controller.on_roll_requested()
    assert res2.extra_roll is True
    assert new_controller.state.current_index == 0
    assert new_controller.state.extra_rolls_used == 2
    new_controller.on_animation_done()

    # Second roll after resume: rolls 6 -> limit reached, no extra roll, turn passes
    res3 = new_controller.on_roll_requested()
    assert res3.extra_roll is False
    assert new_controller.state.current_index == 1


def test_tc_fr15_3_save_twice_loads_latest_and_no_tmp_file(save_dir):
    """TC-FR15-3: Save twice with different states, then Resume. Only latest loaded; no .tmp remains."""
    manager = SaveManager(directory=save_dir)
    controller = GameController(engine=GameEngine(), save_manager=manager)
    controller.start_new_game([PlayerConfig("Sam", "blue"), PlayerConfig("Alice", "orange")])

    controller.state.players[0].position = 10
    controller.on_save_requested()

    controller.state.players[0].position = 25
    controller.on_save_requested()

    assert not manager.temp_path.exists()

    new_controller = GameController(engine=GameEngine(), save_manager=SaveManager(directory=save_dir))
    assert new_controller.on_resume_requested() is True
    assert new_controller.state.players[0].position == 25


def test_tc_fr15_4_save_extra_turn_off_remains_off(save_dir):
    """TC-FR15-4: Save a game with extra-turn off; resume; roll a 6 -> no extra roll."""
    manager = SaveManager(directory=save_dir)
    controller = GameController(engine=GameEngine(), save_manager=manager)
    controller.start_new_game([PlayerConfig("Sam", "blue"), PlayerConfig("Alice", "orange")], extra_turn=False)
    controller.on_save_requested()

    new_engine = GameEngine(rng=ScriptedRng([6]))
    new_controller = GameController(engine=new_engine, save_manager=SaveManager(directory=save_dir))
    new_controller.on_resume_requested()
    assert new_controller.state.extra_turn_enabled is False

    res = new_controller.on_roll_requested()
    assert res.extra_roll is False
    assert new_controller.state.current_index == 1


def test_tc_fr15_5_save_at_start_and_near_win(save_dir):
    """TC-FR15-5: Save at start (positions 0) and with player on 99; resume each."""
    manager = SaveManager(directory=save_dir)
    controller = GameController(engine=GameEngine(), save_manager=manager)
    controller.start_new_game([PlayerConfig("Sam", "blue"), PlayerConfig("Alice", "orange")])
    assert controller.on_save_requested() is True

    c2 = GameController(save_manager=SaveManager(directory=save_dir))
    c2.on_resume_requested()
    assert [p.position for p in c2.state.players] == [0, 0]

    c2.state.players[0].position = 99
    assert c2.on_save_requested() is True

    c3 = GameController(save_manager=SaveManager(directory=save_dir))
    c3.on_resume_requested()
    assert c3.state.players[0].position == 99


def test_ui_save_and_resume_buttons(save_dir):
    """UI checks for Save button on GameScreen and Resume button on SetupScreen."""
    pygame.init()
    surface = pygame.display.set_mode((1280, 720))

    manager = SaveManager(directory=save_dir)
    controller = GameController(save_manager=manager)
    setup = SetupScreen(
        on_start=controller.start_new_game,
        on_resume=controller.on_resume_requested,
        can_resume=controller.can_resume,
        controller=controller,
    )

    # Before save, can_resume is False
    assert controller.can_resume() is False
    setup.draw(surface)

    # Start a game
    controller.start_new_game([PlayerConfig("Sam", "blue"), PlayerConfig("Alice", "orange")])
    game = GameScreen(controller)
    game.draw(surface)

    # Click Save button
    click_save = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=game.save_button.center)
    game.handle_event(click_save)
    assert manager.exists() is True
    assert controller.status_message == "Game saved."
    game.draw(surface)

    # Back to setup screen
    setup2 = SetupScreen(
        on_start=controller.start_new_game,
        on_resume=controller.on_resume_requested,
        can_resume=controller.can_resume,
        controller=controller,
    )
    assert controller.can_resume() is True
    setup2.draw(surface)

    # Click Resume button
    controller.screen = "setup"
    controller.state = None
    click_resume = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=setup2.resume_button.center)
    setup2.handle_event(click_resume)
    assert controller.screen == "game"
    assert controller.state is not None
    assert [p.name for p in controller.state.players] == ["Sam", "Alice"]
    pygame.quit()


def test_save_write_error_handling(save_dir):
    """SaveWriteError is handled gracefully without crashing and displays error message."""
    manager = SaveManager(directory=save_dir)
    controller = GameController(save_manager=manager)
    controller.start_new_game([PlayerConfig("Sam", "blue"), PlayerConfig("Alice", "orange")])

    with patch("os.replace", side_effect=OSError("Disk full")):
        assert controller.on_save_requested() is False
        assert controller.error_message == "Could not save the game."
        assert not manager.temp_path.exists()
