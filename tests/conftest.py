"""Network/model tests are explicit opt-in; ordinary pytest stays local."""

import os

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--run-live",
        action="store_true",
        default=False,
        help="Run paid Gemini/LiveKit integration tests (sends prompts and evidence).",
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "live: external Gemini/LiveKit integration")
    if config.getoption("--run-live"):
        os.environ["KRN_LIVE_TESTS"] = "1"


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-live") or os.getenv("KRN_LIVE_TESTS") == "1":
        return
    for item in items:
        if "live" in item.keywords:
            item.add_marker(
                pytest.mark.skip(
                    reason="Explicit --run-live required; external service test"
                )
            )
