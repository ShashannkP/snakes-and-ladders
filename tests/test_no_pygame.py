"""NFR-06 / C4: every module under snakes_ladders/engine/ must NOT import pygame.

This test is the automated check described in SDD 3.9.
It runs as part of the normal pytest suite, so the GitHub Actions workflow
(which already runs pytest + coverage on every PR) enforces the rule
without needing a separate grep step.
"""

import ast
import pathlib

_ENGINE_ROOT = pathlib.Path(__file__).parent.parent / "snakes_ladders" / "engine"


def _pygame_imports(path: pathlib.Path) -> list[str]:
    """Return a description for every pygame import found in *path*."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "pygame" or alias.name.startswith("pygame."):
                    violations.append(
                        f"{path.name}:{node.lineno}: import {alias.name}"
                    )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module == "pygame" or module.startswith("pygame."):
                violations.append(
                    f"{path.name}:{node.lineno}: from {module} import ..."
                )
    return violations


def test_engine_does_not_import_pygame():
    """All .py files under engine/ are pygame-free (NFR-06, C4, SDD 3.9)."""
    py_files = sorted(_ENGINE_ROOT.rglob("*.py"))
    assert py_files, f"No Python files found under {_ENGINE_ROOT} — check the path."

    violations: list[str] = []
    for py_file in py_files:
        violations.extend(_pygame_imports(py_file))

    assert not violations, (
        "engine/ must not import pygame (C4, NFR-06).\n"
        "Violations found:\n" + "\n".join(f"  {v}" for v in violations)
    )
