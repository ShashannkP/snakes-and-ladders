"""NFR-04 / SEC-06: the application reaches setup without network access."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import ast
import socket
from pathlib import Path

import pygame

from snakes_ladders import main as app
from snakes_ladders.ui.setup_screen import SetupScreen

SOURCE_DIR = Path(__file__).resolve().parent.parent / "snakes_ladders"
NETWORK_MODULES = {
    "_socket",
    "aiohttp",
    "ftplib",
    "http",
    "httpx",
    "requests",
    "socket",
    "smtplib",
    "telnetlib",
    "urllib",
    "websocket",
    "xmlrpc",
}
ASYNC_NETWORK_CALLS = {
    "open_connection",
    "start_server",
    "start_unix_connection",
    "start_unix_server",
}


def test_application_does_not_import_network_modules():
    violations = []
    for path in sorted(SOURCE_DIR.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                modules = [node.module or ""]
                if node.module == "asyncio" and any(
                    alias.name == "streams" for alias in node.names
                ):
                    violations.append(f"{path.name}:{node.lineno}: asyncio streams")
            else:
                modules = []

            for module in modules:
                if module.split(".", 1)[0] in NETWORK_MODULES:
                    violations.append(f"{path.name}:{node.lineno}: {module}")

            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "asyncio"
                and node.func.attr in ASYNC_NETWORK_CALLS
            ):
                violations.append(
                    f"{path.name}:{node.lineno}: asyncio.{node.func.attr}"
                )

    assert not violations, "Application source must remain offline:\n" + "\n".join(
        violations
    )


def test_application_launches_to_setup_when_network_is_blocked(monkeypatch):
    def reject_network(*args, **kwargs):
        raise AssertionError("Application attempted network access")

    monkeypatch.setattr(socket, "socket", reject_network)
    monkeypatch.setattr(socket, "create_connection", reject_network)
    monkeypatch.setattr(socket, "getaddrinfo", reject_network)

    setup_drawn = False
    draw_setup = SetupScreen.draw

    def record_setup_draw(screen, surface):
        nonlocal setup_drawn
        setup_drawn = True
        draw_setup(screen, surface)

    monkeypatch.setattr(SetupScreen, "draw", record_setup_draw)
    monkeypatch.setattr(
        pygame.event,
        "get",
        lambda: [pygame.event.Event(pygame.QUIT)],
    )

    app.main()

    assert setup_drawn, "Application did not reach the setup screen"
