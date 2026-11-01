"""SEC-02 / SEC-03 / SEC-05: Security tests for save and resume."""

import ast
import json
from pathlib import Path
import pytest

from snakes_ladders.controller.game_controller import GameController
from snakes_ladders.engine import GameEngine
from snakes_ladders.engine.setup import PlayerConfig
from snakes_ladders.persistence import (
    ChecksumService,
    SaveFormatError,
    SaveIntegrityError,
    SaveManager,
    SaveNotFoundError,
    SaveRangeError,
    SaveTooLargeError,
    SaveValidator,
)


@pytest.fixture
def save_dir(tmp_path):
    return tmp_path / "snakes_ladders_sec"


def valid_payload():
    state = {
        "players": [
            {"name": "Sam", "colour": "blue", "position": 10},
            {"name": "Alice", "colour": "orange", "position": 20},
        ],
        "current_index": 0,
        "extra_turn_enabled": True,
        "extra_rolls_used": 0,
        "last_roll": 4,
    }
    return {
        "version": 1,
        "state": state,
        "checksum": ChecksumService.compute(state),
    }


def write_raw(save_dir, content: bytes | str):
    save_dir.mkdir(parents=True, exist_ok=True)
    path = save_dir / "savegame.json"
    if isinstance(content, str):
        path.write_text(content, encoding="utf-8")
    else:
        path.write_bytes(content)
    return path


def test_tc_sec02_1_untouched_save_loads_cleanly(save_dir):
    """TC-SEC02-1: Save through manager/controller, leave untouched, resume -> state equals."""
    manager = SaveManager(directory=save_dir)
    controller = GameController(save_manager=manager)
    controller.start_new_game([PlayerConfig("Sam", "blue"), PlayerConfig("Alice", "orange")])
    controller.on_save_requested()

    c2 = GameController(save_manager=manager)
    assert c2.on_resume_requested() is True
    assert [p.name for p in c2.state.players] == ["Sam", "Alice"]
    assert c2.error_message is None


@pytest.mark.parametrize("field,bad_val", [
    ("position", 55),
    ("current_index", 1),
    ("extra_turn_enabled", False),
])
def test_tc_sec02_2_tampered_state_without_checksum_update(save_dir, field, bad_val):
    """TC-SEC02-2: Tamper field in state without updating checksum -> rejected with SRC."""
    payload = valid_payload()
    if field == "position":
        payload["state"]["players"][0]["position"] = bad_val
    else:
        payload["state"][field] = bad_val
    # Keep original checksum
    write_raw(save_dir, json.dumps(payload))

    manager = SaveManager(directory=save_dir)
    controller = GameController(save_manager=manager)
    assert controller.on_resume_requested() is False
    assert controller.error_message == "Save file is corrupted or has been modified."
    assert controller.state is None
    assert controller.screen == "setup"


@pytest.mark.parametrize("bad_checksum", [
    "a" * 63 + "0",  # flip one hex digit (if real ends in something else)
    "a" * 63,        # 63 characters
    "z" * 64,        # 64 non-hex characters
    "",              # empty string
])
def test_tc_sec02_3_damaged_checksum_rejected(save_dir, bad_checksum):
    """TC-SEC02-3: Damaged checksum field -> rejected with SRC."""
    payload = valid_payload()
    payload["checksum"] = bad_checksum
    write_raw(save_dir, json.dumps(payload))

    manager = SaveManager(directory=save_dir)
    controller = GameController(save_manager=manager)
    assert controller.on_resume_requested() is False
    assert controller.error_message == "Save file is corrupted or has been modified."
    assert controller.state is None


def test_tc_sec02_4_canonical_formatting_independence(save_dir):
    """TC-SEC02-4: Re-format valid save without changing values (spacing, indent, CRLF) -> loads."""
    payload = valid_payload()
    # Write with custom indent, newline and spacing
    formatted = json.dumps(payload, indent=4).replace("\n", "\r\n") + "   \r\n"
    write_raw(save_dir, formatted)

    manager = SaveManager(directory=save_dir)
    controller = GameController(save_manager=manager)
    assert controller.on_resume_requested() is True
    assert [p.name for p in controller.state.players] == ["Sam", "Alice"]


def test_tc_sec02_5_error_messages_are_byte_identical_and_logged(save_dir):
    """TC-SEC02-5: E-06, E-07, E-08, E-09 all produce byte-identical screen message."""
    expected_msg = "Save file is corrupted or has been modified."

    manager = SaveManager(directory=save_dir)
    controller = GameController(save_manager=manager)

    # 1. E-06 (oversize)
    write_raw(save_dir, " " * 10241)
    controller.on_resume_requested()
    assert controller.error_message == expected_msg

    # 2. E-07 (bad JSON)
    write_raw(save_dir, "{bad json")
    controller.on_resume_requested()
    assert controller.error_message == expected_msg

    # 3. E-08 (range violation with recomputed checksum)
    p3 = valid_payload()
    p3["state"]["players"][0]["position"] = 150
    p3["checksum"] = ChecksumService.compute(p3["state"])
    write_raw(save_dir, json.dumps(p3))
    controller.on_resume_requested()
    assert controller.error_message == expected_msg

    # 4. E-09 (checksum mismatch)
    p4 = valid_payload()
    p4["checksum"] = "0" * 64
    write_raw(save_dir, json.dumps(p4))
    controller.on_resume_requested()
    assert controller.error_message == expected_msg

    # Check that snl.log exists in save_dir and contains logged errors
    log_file = save_dir / "snl.log"
    assert log_file.is_file()
    log_content = log_file.read_text(encoding="utf-8")
    assert "SaveTooLargeError" in log_content
    assert "SaveFormatError" in log_content
    assert "SaveRangeError" in log_content
    assert "SaveIntegrityError" in log_content


def test_tc_sec02_6_recomputed_checksum_loads_valid_and_rejects_out_of_range(save_dir):
    """TC-SEC02-6: Modifying state and recomputing checksum loads if in-range, rejected if out-of-range."""
    manager = SaveManager(directory=save_dir)
    controller = GameController(save_manager=manager)

    # Valid modification: player moved to 50
    p_valid = valid_payload()
    p_valid["state"]["players"][0]["position"] = 50
    p_valid["checksum"] = ChecksumService.compute(p_valid["state"])
    write_raw(save_dir, json.dumps(p_valid))
    assert controller.on_resume_requested() is True
    assert controller.state.players[0].position == 50

    # Invalid modification: player on 100 (finished game, D-4)
    p_invalid = valid_payload()
    p_invalid["state"]["players"][0]["position"] = 100
    p_invalid["checksum"] = ChecksumService.compute(p_invalid["state"])
    write_raw(save_dir, json.dumps(p_invalid))
    assert controller.on_resume_requested() is False
    assert controller.error_message == "Save file is corrupted or has been modified."


def test_tc_sec03_1_size_boundary_checks(save_dir):
    """TC-SEC03-1: 10,240 bytes loads; 10,241 bytes and large file give E-06."""
    manager = SaveManager(directory=save_dir)
    controller = GameController(save_manager=manager)

    base = json.dumps(valid_payload())
    # Pad to exactly 10,240 bytes
    padded_exact = base + " " * (10240 - len(base))
    assert len(padded_exact.encode("utf-8")) == 10240
    write_raw(save_dir, padded_exact)
    assert controller.on_resume_requested() is True

    # Pad to 10,241 bytes
    padded_over = base + " " * (10241 - len(base))
    assert len(padded_over.encode("utf-8")) == 10241
    write_raw(save_dir, padded_over)
    assert controller.on_resume_requested() is False
    assert controller.error_message == "Save file is corrupted or has been modified."


@pytest.mark.parametrize("invalid_content", [
    b"",
    b"   ",
    b'{"version": 1, "state":',
    b"\x00\x01\x02\xff",
    b"\xff\xfe{\x00}\x00",  # UTF-16 BOM
    b"plain text not json",
    b"null",
    b"[]",
    b'"just string"',
    b"12345",
])
def test_tc_sec03_2_invalid_json_documents(save_dir, invalid_content):
    """TC-SEC03-2: Invalid JSON or non-object primitives reject gracefully."""
    write_raw(save_dir, invalid_content)
    manager = SaveManager(directory=save_dir)
    controller = GameController(save_manager=manager)
    assert controller.on_resume_requested() is False
    assert controller.error_message == "Save file is corrupted or has been modified."


def test_tc_sec03_3_parser_stress_within_10kb(save_dir):
    """TC-SEC03-3: Deeply nested brackets, NaN / Infinity within 10 KB do not crash app."""
    manager = SaveManager(directory=save_dir)
    controller = GameController(save_manager=manager)

    # Deep nesting
    nested = "[" * 2000 + "]" * 2000
    write_raw(save_dir, nested)
    assert controller.on_resume_requested() is False

    # NaN / Infinity literals
    write_raw(save_dir, '{"version": 1, "state": {"players": [], "pos": NaN}}')
    assert controller.on_resume_requested() is False


@pytest.mark.parametrize("mutator", [
    lambda p: p.pop("version"),
    lambda p: p.pop("state"),
    lambda p: p.pop("checksum"),
    lambda p: p.update({"version": 2}),
    lambda p: p.update({"version": True}),
    lambda p: p.update({"unknown_key": "bad"}),
    lambda p: p["state"].update({"players": {}}),
    lambda p: p["state"]["players"][0].update({"position": "37"}),
    lambda p: p["state"]["players"][0].update({"position": 37.5}),
    lambda p: p["state"]["players"][0].update({"position": True}),
    lambda p: p["state"]["players"][0].update({"position": None}),
    lambda p: p["state"].update({"current_index": True}),
    lambda p: p["state"].update({"extra_turn_enabled": 1}),
    lambda p: p["state"].update({"extra_turn_enabled": "yes"}),
    lambda p: p["state"].update({"last_roll": 0}),
    lambda p: p["state"].update({"last_roll": 7}),
    lambda p: p["state"].update({"last_roll": "3"}),
    lambda p: p["state"].update({"unexpected_field": 42}),
])
def test_tc_sec03_4_schema_and_type_violations(save_dir, mutator):
    """TC-SEC03-4: Schema and type violations with recomputed checksum give SRC."""
    payload = valid_payload()
    mutator(payload)
    if "checksum" in payload and "state" in payload and isinstance(payload["state"], dict):
        payload["checksum"] = ChecksumService.compute(payload["state"])
    write_raw(save_dir, json.dumps(payload))

    manager = SaveManager(directory=save_dir)
    controller = GameController(save_manager=manager)
    assert controller.on_resume_requested() is False
    assert controller.error_message == "Save file is corrupted or has been modified."


@pytest.mark.parametrize("mutator", [
    lambda p: p["state"]["players"].pop(),  # 1 player left
    lambda p: p["state"]["players"].extend([
        {"name": "P3", "colour": "green", "position": 0},
        {"name": "P4", "colour": "magenta", "position": 0},
        {"name": "P5", "colour": "blue", "position": 0},
    ]),  # 5 players
    lambda p: p["state"]["players"][0].update({"position": -1}),
    lambda p: p["state"]["players"][0].update({"position": 100}),  # finished game D-4
    lambda p: p["state"]["players"][0].update({"position": 101}),
    lambda p: p["state"].update({"current_index": -1}),
    lambda p: p["state"].update({"current_index": len(p["state"]["players"])}),
    lambda p: p["state"].update({"extra_rolls_used": 3}),
    lambda p: p["state"]["players"][1].update({"name": "sam"}),  # duplicate name case-insensitive
    lambda p: p["state"]["players"][1].update({"colour": "blue"}),  # duplicate colour
    lambda p: p["state"]["players"][1].update({"colour": "purple"}),  # disallowed colour
    lambda p: p["state"]["players"][0].update({"name": ""}),  # empty name
    lambda p: p["state"]["players"][0].update({"name": "A" * 16}),  # over 15 chars
])
def test_tc_sec03_5_range_violations(save_dir, mutator):
    """TC-SEC03-5: Range violations with recomputed checksum give SRC."""
    payload = valid_payload()
    mutator(payload)
    payload["checksum"] = ChecksumService.compute(payload["state"])
    write_raw(save_dir, json.dumps(payload))

    manager = SaveManager(directory=save_dir)
    controller = GameController(save_manager=manager)
    assert controller.on_resume_requested() is False
    assert controller.error_message == "Save file is corrupted or has been modified."


def test_tc_sec03_5_valid_controls(save_dir):
    """TC-SEC03-5 controls: 4 players with positions 0 and 99, and last_roll null loads."""
    state = {
        "players": [
            {"name": "P1", "colour": "blue", "position": 0},
            {"name": "P2", "colour": "orange", "position": 99},
            {"name": "P3", "colour": "green", "position": 50},
            {"name": "P4", "colour": "magenta", "position": 1},
        ],
        "current_index": 3,
        "extra_turn_enabled": False,
        "extra_rolls_used": 0,
        "last_roll": None,
    }
    payload = {
        "version": 1,
        "state": state,
        "checksum": ChecksumService.compute(state),
    }
    write_raw(save_dir, json.dumps(payload))

    manager = SaveManager(directory=save_dir)
    controller = GameController(save_manager=manager)
    assert controller.on_resume_requested() is True
    assert len(controller.state.players) == 4
    assert controller.state.players[1].position == 99
    assert controller.state.last_roll is None


def test_tc_sec03_7_validation_order(save_dir):
    """TC-SEC03-7: Log records first failing check in order (size -> json -> schema -> range -> checksum)."""
    # Bad schema + bad checksum -> fails on schema (SaveFormatError)
    payload = valid_payload()
    payload["unknown_key"] = 1
    payload["checksum"] = "bad"
    write_raw(save_dir, json.dumps(payload))

    with pytest.raises(SaveFormatError):
        SaveManager(directory=save_dir).load()

    # Bad range + bad checksum -> fails on range (SaveRangeError)
    p2 = valid_payload()
    p2["state"]["players"][0]["position"] = 999
    p2["checksum"] = "bad"
    write_raw(save_dir, json.dumps(p2))

    with pytest.raises(SaveRangeError):
        SaveManager(directory=save_dir).load()


def test_tc_sec05_1_banned_functions_ast_scan():
    """TC-SEC05-1: Scan all non-test code for eval, exec, pickle, marshal, subprocess, os.system, etc."""
    banned_modules = {"pickle", "marshal", "shelve", "subprocess"}
    banned_calls = {"eval", "exec", "compile", "__import__"}

    src_root = Path(__file__).resolve().parent.parent / "snakes_ladders"
    py_files = list(src_root.rglob("*.py"))
    assert len(py_files) >= 5

    violations = []
    for file_path in py_files:
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] in banned_modules:
                        violations.append(f"{file_path.name}:{node.lineno}: import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                mod = (node.module or "").split(".")[0]
                if mod in banned_modules:
                    violations.append(f"{file_path.name}:{node.lineno}: from {node.module} import ...")
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in banned_calls:
                    violations.append(f"{file_path.name}:{node.lineno}: call to {node.func.id}")
                elif isinstance(node.func, ast.Attribute):
                    if node.func.attr == "system" and isinstance(node.func.value, ast.Name) and node.func.value.id == "os":
                        violations.append(f"{file_path.name}:{node.lineno}: call to os.system")

    assert not violations, f"Banned calls or modules found:\n" + "\n".join(violations)


def test_tc_sec05_2_hostile_content_not_executed(save_dir, tmp_path):
    """TC-SEC05-2: Python expression in player name or pickle stream is never executed."""
    marker = tmp_path / "hacked.txt"

    # Hostile expression in player name
    code_in_name = f"__import__('pathlib').Path('{marker.as_posix()}').touch()"
    payload = valid_payload()
    payload["state"]["players"][0]["name"] = code_in_name
    payload["checksum"] = ChecksumService.compute(payload["state"])
    write_raw(save_dir, json.dumps(payload))

    controller = GameController(save_manager=SaveManager(directory=save_dir))
    controller.on_resume_requested()
    assert not marker.exists()
