"""NFR-13: minimum text size, numbered tokens and CVD simulation checks."""

import math
import os
from itertools import combinations

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from snakes_ladders.controller.game_controller import GameController
from snakes_ladders.engine.models import Player
from snakes_ladders.engine.setup import PlayerConfig
from snakes_ladders.ui.board_view import BoardView
from snakes_ladders.ui.game_screen import GameScreen
from snakes_ladders.ui.result_screen import ResultScreen
from snakes_ladders.ui.setup_screen import SetupScreen
from snakes_ladders.ui.widgets import BACKGROUND, MIN_FONT_SIZE, TOKEN_COLOURS, label


# Machado et al. (2009), severity 1.0, applied to linear sRGB.
# https://www.inf.ufrgs.br/~oliveira/pubs_files/CVD_Simulation/CVD_Simulation.html
SIMULATIONS = {
    "protanopia": ((.152286, 1.052583, -.204868), (.114503, .786281, .099216), (-.003882, -.048116, 1.051998)),
    "deuteranopia": ((.367322, .860646, -.227968), (.280085, .672501, .047413), (-.011820, .042940, .968881)),
    "tritanopia": ((1.255528, -.076749, -.178779), (-.078411, .930809, .147602), (.004733, .691367, .303900)),
}


def simulate(colour, matrix):
    rgb = [v / 255 for v in colour]
    linear = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in rgb]
    return tuple(max(0, min(1, sum(a * b for a, b in zip(row, linear)))) for row in matrix)


def lab(rgb):
    r, g, b = rgb
    xyz = ((.4124564*r + .3575761*g + .1804375*b)/.95047,
           .2126729*r + .7151522*g + .0721750*b,
           (.0193339*r + .1191920*g + .9503041*b)/1.08883)
    x, y, z = [v ** (1/3) if v > (6/29)**3 else v/(3*(6/29)**2)+4/29 for v in xyz]
    return (116*y-16, 500*(x-y), 200*(y-z))


@pytest.mark.parametrize("kind", SIMULATIONS)
def test_palette_stays_separated_under_colour_vision_simulation(kind):
    colours = {name: lab(simulate(rgb, SIMULATIONS[kind])) for name, rgb in TOKEN_COLOURS.items()}
    for first, second in combinations(colours, 2):
        # A conservative regression guard, supplemented by numbered labels.
        difference = math.dist(colours[first], colours[second])
        assert difference >= 10, (kind, first, second, difference)


@pytest.mark.parametrize("matrix", [((1, 0, 0), (0, 1, 0), (0, 0, 1)), *SIMULATIONS.values()])
def test_token_number_contrast_in_normal_and_simulated_vision(matrix):
    def luminance(colour):
        return sum(a*b for a, b in zip(simulate(colour, matrix), (.2126, .7152, .0722)))

    ink = luminance((15, 20, 30))
    for colour in TOKEN_COLOURS.values():
        assert (luminance(colour) + .05) / (ink + .05) >= 4.5


@pytest.fixture
def surface():
    pygame.init()
    yield pygame.display.set_mode((1280, 720))
    pygame.quit()


def test_all_screens_use_at_least_fourteen_point_text(surface, monkeypatch):
    sizes = []
    original = pygame.font.Font

    def font(path, size):
        sizes.append(size)
        return original(path, size)

    monkeypatch.setattr(pygame.font, "Font", font)
    label(surface, "Small request", (0, 0), size=8)
    controller = GameController()
    controller.start_new_game([PlayerConfig("Sam", "blue"), PlayerConfig("Alice", "orange")])
    SetupScreen().draw(surface)
    GameScreen(controller).draw(surface)
    controller.state.players[0].position = 100
    from snakes_ladders.engine.models import TurnResult, Event
    controller.last_result = TurnResult(0, 1, 99, 100, 100, Event.NONE, False, 0, 0)
    ResultScreen(controller).draw(surface)
    assert sizes and min(sizes) >= MIN_FONT_SIZE == math.ceil(14 * 96 / 72)


@pytest.mark.parametrize("position", [0, 1, 17, 100])
def test_numbered_tokens_fit_without_overlap(surface, position):
    view = BoardView()
    numbers = []
    font = view.token_font

    class RecordingFont:
        def render(self, text, *args):
            numbers.append(text)
            return font.render(text, *args)

    view.token_font = RecordingFont()
    players = [Player(str(i + 1), colour, position) for i, colour in enumerate(TOKEN_COLOURS)]
    surface.fill(BACKGROUND)
    view.draw(surface, players)
    bounds = []
    for index in range(4):
        center = view.token_center(position, index)
        token = pygame.Rect(0, 0, 2 * view.TOKEN_RADIUS, 2 * view.TOKEN_RADIUS)
        token.center = center
        glyph = font.render(str(index + 1), True, (15, 20, 30))
        assert token.contains(glyph.get_rect(center=center))
        assert surface.get_rect().contains(token)
        if position:
            assert view.square_rect(position).contains(token)
        assert all(not token.colliderect(other) for other in bounds)
        bounds.append(token)
    assert numbers == ["1", "2", "3", "4"]
