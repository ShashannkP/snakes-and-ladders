"""Dice Service (FR-03): 
   Generates a uniformly distributed discrete random integer X ~ U(1,6) when Roll Dice is clicked or Space is pressed."""

import random
import secrets

class DiceService:
    """Rolls a fair six-sided die"""
    
    SIDES = 6
    
    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng if rng is not None else secrets.SystemRandom()
        
    def roll(self) -> int:
        """Return a uniformly random integer from 1 to 6."""
        return self._rng.randint(1, self.SIDES)