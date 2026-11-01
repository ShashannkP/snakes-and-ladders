"""Keep hardware acceptance benchmarks separate from portable CI checks."""

import pytest


def pytest_addoption(parser):
    parser.addoption("--run-fps-benchmark", action="store_true", default=False,
                     help="Enforce the NFR-12 FPS limit on the benchmark machine")


def pytest_configure(config):
    config.addinivalue_line("markers", "fps_benchmark: NFR-12 hardware acceptance test")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-fps-benchmark"):
        return
    marker = pytest.mark.skip(reason="Hardware acceptance: enable with --run-fps-benchmark")
    for item in items:
        if "fps_benchmark" in item.keywords:
            item.add_marker(marker)
