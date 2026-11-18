"""Fixtures for the characterisation harness. TARGET=legacy|modern picks the system."""

import pytest

from .adapters import make_adapter


def pytest_configure(config):
    config.addinivalue_line("markers", "behaviour(id): the legacy behaviour (as-is spec) this test pins")
    config.addinivalue_line("markers", "ac(id): the to-be acceptance criterion this test proves")
    config.addinivalue_line("markers", "deviation(id): an approved deviation; the result differs per target")
    config.addinivalue_line("markers", "legacy_only: capability not built in the new service yet")


def pytest_collection_modifyitems(config, items):
    import os

    if os.environ.get("TARGET", "legacy") == "modern":
        skip = pytest.mark.skip(reason="not migrated yet (to-be spec pending)")
        for item in items:
            if "legacy_only" in item.keywords:
                item.add_marker(skip)


@pytest.fixture(scope="session")
def svc():
    return make_adapter()


@pytest.fixture(autouse=True)
def fresh(svc):
    """Every test starts from the seed data and the frozen clock (2026-03-10 12:00 UTC)."""
    svc.reset()
    yield


@pytest.fixture
def expect(svc):
    """Pick the expected value for this target: expect(legacy=..., modern=...)."""

    def pick(*, legacy, modern):
        return legacy if svc.target == "legacy" else modern

    return pick


def pytest_runtest_makereport(item, call):
    """Copy the IDs into the JUnit report so results trace back to specs."""
    if call.when == "call":
        for name in ("behaviour", "ac", "deviation"):
            for mark in item.iter_markers(name):
                item.user_properties.append((name, mark.args[0]))
