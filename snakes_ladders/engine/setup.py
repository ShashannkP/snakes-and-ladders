"""Player configuration and shared setup invariants."""

import re
from dataclasses import dataclass

COLOURS = ("blue", "orange", "green", "magenta")
NAME_ERROR = "Names must be 1 to 15 letters, digits or spaces."
UNIQUE_ERROR = "Each player needs a unique name and colour."


class InputValidationError(ValueError):
    """Setup input cannot be used to create players."""


@dataclass(frozen=True)
class PlayerConfig:
    name: str
    colour: str


def validate_name(name: str) -> str:
    if not isinstance(name, str):
        raise InputValidationError(NAME_ERROR)
    name = name.strip(" ")
    if not re.fullmatch(r"[A-Za-z0-9 ]{1,15}", name):
        raise InputValidationError(NAME_ERROR)
    return name


def validate_players(configs: list[PlayerConfig]) -> list[PlayerConfig]:
    """Return normalized copies without changing the input."""
    normalized = []
    names, colours = set(), set()
    for config in configs:
        name = validate_name(config.name)
        if config.colour not in COLOURS:
            raise InputValidationError("Choose a supported token colour.")
        if name.casefold() in names or config.colour in colours:
            raise InputValidationError(UNIQUE_ERROR)
        names.add(name.casefold())
        colours.add(config.colour)
        normalized.append(PlayerConfig(name, config.colour))
    return normalized
