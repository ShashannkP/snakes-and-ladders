"""NFR-01: measure input through the actual application's display flip."""

import os
from time import perf_counter

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from snakes_ladders import main as app
from snakes_ladders.controller.game_controller import GameController
from snakes_ladders.engine import GameEngine
from snakes_ladders.engine.setup import PlayerConfig
from snakes_ladders.ui.board_view import BoardView
from snakes_ladders.ui.widgets import BACKGROUND, TEXT, TOKEN_COLOURS, _render_label
from tests.engine.test_scripted_rng import ScriptedRng


def test_fifty_rolls_are_presented_within_one_second(monkeypatch):
    controller = GameController(GameEngine(rng=ScriptedRng([1] * 50)))
    controller.start_new_game([PlayerConfig("Sam", "blue"), PlayerConfig("Alice", "orange")])
    monkeypatch.setattr(app, "GameController", lambda: controller)
    pygame.init()
    board = BoardView()
    _render_label.cache_clear()  # Include the first uncached gameplay frame.
    durations = []
    started = None
    flip = pygame.display.flip

    def events():
        nonlocal started
        if len(durations) == 50:
            started = None
            return [pygame.event.Event(pygame.QUIT)]
        started = perf_counter()
        return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)]

    def present():
        flip()
        elapsed = perf_counter() - started if started is not None else None
        if elapsed is None:
            return
        assert controller.screen == "game"
        result = controller.last_result
        assert result.roll == controller.state.last_roll == 1
        player = controller.state.players[result.player_index]
        assert player.position == result.final_pos
        surface = pygame.display.get_surface()
        x, y = board.token_center(player.position, result.player_index)
        assert surface.get_at((x - 5, y))[:3] == TOKEN_COLOURS[player.colour]
        # The displayed dice result must also have reached the frame being flipped.
        text = _render_label("Last roll: 1", 26, TEXT)
        expected = pygame.Surface(text.get_size())
        expected.fill(BACKGROUND)
        expected.blit(text, (0, 0))
        actual = surface.subsurface((950, 575, *expected.get_size()))
        assert pygame.image.tobytes(actual, "RGB") == pygame.image.tobytes(expected, "RGB")
        durations.append(elapsed)

    monkeypatch.setattr(pygame.event, "get", events)
    monkeypatch.setattr(pygame.display, "flip", present)
    app.main()
    assert len(durations) == 50
    print(f"50 roll-to-display samples: max={max(durations):.6f}s mean={sum(durations)/50:.6f}s")
    assert all(duration <= 1 for duration in durations), durations
