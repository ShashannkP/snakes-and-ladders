"""Validation of save data according to SEC-03 and SDD 3.5."""

import re

from snakes_ladders.engine.setup import COLOURS
from snakes_ladders.persistence.checksum import ChecksumService
from snakes_ladders.persistence.exceptions import SaveFormatError, SaveIntegrityError, SaveRangeError

NAME_PATTERN = re.compile(r"^[A-Za-z0-9 ]{1,15}$")
HEX_PATTERN = re.compile(r"^[0-9a-f]{64}$")

ALLOWED_TOP_KEYS = frozenset({"version", "state", "checksum"})
ALLOWED_STATE_KEYS = frozenset({
    "players",
    "current_index",
    "extra_turn_enabled",
    "extra_rolls_used",
    "last_roll",
})
ALLOWED_PLAYER_KEYS = frozenset({"name", "colour", "position"})


class SaveValidator:
    @classmethod
    def validate(cls, data: dict) -> dict:
        """Validate save data schema, types, ranges and checksum (SDD 2.7, 3.5, SEC-03, SEC-02).
        
        Returns the validated state dictionary.
        """
        cls._validate_schema_and_types(data)
        cls._validate_ranges(data["state"])
        cls._validate_checksum(data["state"], data["checksum"])
        return data["state"]

    @classmethod
    def _validate_schema_and_types(cls, data: dict) -> None:
        if not isinstance(data, dict):
            raise SaveFormatError("Root document must be a JSON object.")

        if set(data.keys()) != ALLOWED_TOP_KEYS:
            raise SaveFormatError(f"Root object must have exactly keys {ALLOWED_TOP_KEYS}.")

        version = data["version"]
        if type(version) is not int or version != 1:
            raise SaveFormatError("Version must be integer 1.")

        checksum = data["checksum"]
        if not isinstance(checksum, str):
            raise SaveFormatError("Checksum must be a string.")

        state = data["state"]
        if not isinstance(state, dict):
            raise SaveFormatError("State must be a JSON object.")

        if set(state.keys()) != ALLOWED_STATE_KEYS:
            raise SaveFormatError(f"State must have exactly keys {ALLOWED_STATE_KEYS}.")

        players = state["players"]
        if not isinstance(players, list):
            raise SaveFormatError("Players must be a list.")

        for p in players:
            if not isinstance(p, dict):
                raise SaveFormatError("Player entry must be an object.")
            if set(p.keys()) != ALLOWED_PLAYER_KEYS:
                raise SaveFormatError(f"Player entry must have exactly keys {ALLOWED_PLAYER_KEYS}.")
            if not isinstance(p["name"], str):
                raise SaveFormatError("Player name must be a string.")
            if not isinstance(p["colour"], str):
                raise SaveFormatError("Player colour must be a string.")
            if type(p["position"]) is not int:
                raise SaveFormatError("Player position must be an integer.")

        current_index = state["current_index"]
        if type(current_index) is not int:
            raise SaveFormatError("current_index must be an integer.")

        extra_turn = state["extra_turn_enabled"]
        if type(extra_turn) is not bool:
            raise SaveFormatError("extra_turn_enabled must be a boolean.")

        extra_rolls_used = state["extra_rolls_used"]
        if type(extra_rolls_used) is not int:
            raise SaveFormatError("extra_rolls_used must be an integer.")

        last_roll = state["last_roll"]
        if last_roll is not None and type(last_roll) is not int:
            raise SaveFormatError("last_roll must be an integer or null.")

    @classmethod
    def _validate_ranges(cls, state: dict) -> None:
        players = state["players"]
        if not (2 <= len(players) <= 4):
            raise SaveRangeError("Player count must be between 2 and 4.")

        seen_names = set()
        seen_colours = set()
        for p in players:
            name = p["name"]
            stripped = name.strip()
            if not stripped or not NAME_PATTERN.match(name):
                raise SaveRangeError("Player name must be 1 to 15 alphanumeric characters or spaces.")
            lower_name = stripped.lower()
            if lower_name in seen_names:
                raise SaveRangeError(f"Duplicate player name: {name}.")
            seen_names.add(lower_name)

            colour = p["colour"]
            if colour not in COLOURS:
                raise SaveRangeError(f"Disallowed player colour: {colour}.")
            if colour in seen_colours:
                raise SaveRangeError(f"Duplicate player colour: {colour}.")
            seen_colours.add(colour)

            pos = p["position"]
            if not (0 <= pos <= 99):
                raise SaveRangeError(f"Player position {pos} must be between 0 and 99.")

        curr_idx = state["current_index"]
        if not (0 <= curr_idx < len(players)):
            raise SaveRangeError(f"current_index {curr_idx} out of range [0, {len(players) - 1}].")

        extra_rolls = state["extra_rolls_used"]
        if not (0 <= extra_rolls <= 2):
            raise SaveRangeError(f"extra_rolls_used {extra_rolls} out of range [0, 2].")

        last_roll = state["last_roll"]
        if last_roll is not None and not (1 <= last_roll <= 6):
            raise SaveRangeError(f"last_roll {last_roll} must be between 1 and 6.")

    @classmethod
    def _validate_checksum(cls, state: dict, checksum: str) -> None:
        if not HEX_PATTERN.match(checksum):
            raise SaveIntegrityError("Checksum must be 64 lowercase hexadecimal characters.")
        expected = ChecksumService.compute(state)
        if checksum != expected:
            raise SaveIntegrityError("Save file is corrupted or has been modified.")
