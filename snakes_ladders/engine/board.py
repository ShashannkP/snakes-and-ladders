"""Board (SDD C11): the fixed 10x10 layout from SRS Appendix 4.3."""

from types import MappingProxyType

from snakes_ladders.engine.models import Event

# Snake head -> tail (SRS Appendix 4.3).
SNAKES = {17: 7, 54: 34, 62: 19, 64: 60, 87: 36, 93: 73, 95: 75, 98: 79}


class Board:
    SIZE = 100

    def __init__(self) -> None:
        self.snakes = MappingProxyType(dict(SNAKES))

    def resolve(self, square: int) -> tuple[int, Event]:
        """Return the square a token ends on after landing on `square`, and why."""
        if square in self.snakes:
            return self.snakes[square], Event.SNAKE
        # TODO FR-07: ladders.
        return square, Event.NONE
