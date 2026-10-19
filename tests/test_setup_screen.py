import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pytest

pygame = pytest.importorskip("pygame")

from snakes_ladders.ui.setup_screen import SetupScreen


@pytest.fixture
def surface():
    pygame.init()
    yield pygame.display.set_mode((1280, 720))
    pygame.quit()


def test_edit_names_and_change_colours(surface):
    screen = SetupScreen()
    screen.handle_event(pygame.event.Event(pygame.TEXTINPUT, text=" Sam "))
    screen.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_TAB))
    screen.handle_event(pygame.event.Event(pygame.TEXTINPUT, text="Alice"))
    assert [p.name for p in screen.configs()] == ["Sam", "Alice"]
    screen.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=screen.colour_rect(0).center))
    assert "unique" in screen.validation_error()
    screen.draw(surface)


def test_large_input_is_bounded_and_invalid(surface):
    screen = SetupScreen()
    screen.handle_event(pygame.event.Event(pygame.TEXTINPUT, text="A" * 10000))
    assert len(screen.names[0]) == 64
    assert screen.validation_error()
    screen.draw(surface)
