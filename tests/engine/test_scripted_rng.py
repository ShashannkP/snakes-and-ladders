"""Scripted RNG for engine tests (as specified in TestPlan.md)
ScriptedRng -> DiceService -> GameEngine

dice = DiceService(rng=ScriptedRng([6,2]))
dice.roll() #6
dice.roll() #2
"""

class ScriptedRng:
    def __init__(self, values: list[int]) -> None:
        self._values = list(values)

    def randint(self, a: int, b: int) -> int:
        if not self._values:
            raise AssertionError("ScriptedRng ran out of values; the test rolled more than expected")
        value = self._values.pop(0)
        if not a <= value <= b:
            raise AssertionError(f"Scripted value {value} is outside randint({a}, {b})")
        return value

    @property
    def remaining(self) -> int:
        return len(self._values)