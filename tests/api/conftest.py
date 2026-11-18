"""Fixtures for the new service's own tests (AAA controls). New service only."""

import os

import httpx
import pytest

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8080")


def pytest_configure(config):
    config.addinivalue_line("markers", "ac(id): the to-be acceptance criterion this test proves")


@pytest.fixture
def api():
    with httpx.Client(base_url=BASE_URL, timeout=10) as c:
        c.post("/test/reset", json={"clock": "2026-03-10 12:00:00"}).raise_for_status()
        yield c


@pytest.fixture
def as_user(api):
    def make(user: str) -> httpx.Client:
        token = api.post("/v1/auth/demo-login", json={"user": user}).json()["token"]
        return httpx.Client(base_url=BASE_URL, timeout=10, headers={"Authorization": f"Bearer {token}"})

    return make
