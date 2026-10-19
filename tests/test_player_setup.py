import pytest

from snakes_ladders.controller.input_validator import validate_setup
from snakes_ladders.engine.setup import InputValidationError, PlayerConfig, validate_name


@pytest.mark.parametrize("name", ["", "   ", "ABCDEFGHIJKLMNOP", "Bob!", "Al_ice", "a-b", "é", "名前", "A\t", "A\n", "A\0"])
def test_invalid_names_rejected(name):
    with pytest.raises(InputValidationError):
        validate_name(name)


@pytest.mark.parametrize("name,expected", [("A", "A"), ("ABCDEFGHIJKLMNO", "ABCDEFGHIJKLMNO"), (" Sam ", "Sam"), ("Player 1", "Player 1")])
def test_valid_names_normalized(name, expected):
    assert validate_name(name) == expected


@pytest.mark.parametrize("configs", [
    [PlayerConfig("Sam", "blue"), PlayerConfig("sam", "orange")],
    [PlayerConfig("Sam", "blue"), PlayerConfig("Alice", "blue")],
    [PlayerConfig("Sam", "red")],
])
def test_duplicate_or_unsupported_player_details_rejected(configs):
    with pytest.raises(InputValidationError):
        validate_setup(configs)


def test_four_players_preserve_setup_order_and_input():
    configs = [PlayerConfig(f" P{i} ", colour) for i, colour in enumerate(("blue", "orange", "green", "magenta"))]
    result = validate_setup(configs)
    assert [p.name for p in result] == ["P0", "P1", "P2", "P3"]
    assert configs[0].name == " P0 "
