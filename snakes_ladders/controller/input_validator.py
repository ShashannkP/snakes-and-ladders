"""Application input validation, shared with the domain creation boundary."""

from snakes_ladders.engine.setup import (
    InputValidationError, PlayerConfig, validate_name, validate_players,
)


def validate_setup(configs: list[PlayerConfig]) -> list[PlayerConfig]:
    return validate_players(configs)
