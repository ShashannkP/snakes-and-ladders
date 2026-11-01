"""Persistence and domain exceptions (SDD 3.4)."""

from snakes_ladders.engine.setup import InputValidationError


class SnlError(Exception):
    """Base exception for Snakes and Ladders."""


class InvalidActionError(SnlError):
    """Action not allowed in current phase (silent, logged)."""


class SaveError(SnlError):
    """Base exception for save and resume errors."""


class SaveNotFoundError(SaveError):
    """Save file not found (E-05)."""


class SaveTooLargeError(SaveError):
    """Save file over 10 KB (E-06)."""


class SaveFormatError(SaveError):
    """Invalid JSON or schema (E-07)."""


class SaveRangeError(SaveError):
    """Field out of range (E-08)."""


class SaveIntegrityError(SaveError):
    """Checksum mismatch (E-09)."""


class SaveWriteError(SaveError):
    """OS error while writing save file (E-10)."""


class EngineInvariantError(SnlError):
    """Engine invariant broken (E-11)."""
