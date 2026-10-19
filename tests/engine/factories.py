"""Shared helpers for building game states in tests."""

from snakes_ladders.engine import GameState, Player

COLOURS = ["blue", "orange", "green", "magenta"]


def make_state(*positions: int) -> GameState:
    """One player per position, named P1..P4, in setup order."""
    players = [Player(f"P{i + 1}", COLOURS[i], pos) for i, pos in enumerate(positions)]
    return GameState(players=players)
