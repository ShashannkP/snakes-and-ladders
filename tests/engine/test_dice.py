"""Tests for DiceService"""

import secrets

import pytest

from snakes_ladders.engine import DiceService
from tests.engine.test_scripted_rng import ScriptedRng


@pytest.mark.parametrize("value", [1, 2, 3, 4, 5, 6])
def test_roll_returns_value_from_rng(value):
    # Engine-level part of TC-FR03-1 / TC-FR03-2: the rolled value is what the RNG produced.
    dice = DiceService(rng=ScriptedRng([value]))
    assert dice.roll() == value


def test_rolls_are_consumed_in_order():
    rng = ScriptedRng([6, 2, 5])
    dice = DiceService(rng=rng)
    assert [dice.roll(), dice.roll(), dice.roll()] == [6, 2, 5]
    assert rng.remaining == 0


def test_production_dice_range_and_coverage():
    # TC-FR03-3: 6,000 rolls from the production DiceService.
    dice = DiceService()
    rolls = [dice.roll() for _ in range(6000)]
    assert all(1 <= r <= 6 for r in rolls)
    assert set(rolls) == {1, 2, 3, 4, 5, 6}


def test_default_rng_is_system_random():
    # SDD C13: production dice use secrets.SystemRandom.
    assert isinstance(DiceService()._rng, secrets.SystemRandom)


def test_no_public_way_to_set_dice_value():
    # SEC-04: roll() is the only public behaviour; no setter or value attribute is exposed.
    public = {name for name in dir(DiceService()) if not name.startswith("_")}
    assert public == {"SIDES", "roll"}
