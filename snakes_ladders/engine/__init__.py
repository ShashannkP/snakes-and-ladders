"""Domain layer: game rules (SDD 2.2).

Modules in this package must NOT import pygame (C4, NFR-06).
"""

from snakes_ladders.engine.dice import DiceService

__all__ = ["DiceService"]
