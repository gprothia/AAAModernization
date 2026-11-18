"""Harness for specs/as-is/MEM-002-renew-membership.md. Runs against legacy and modern."""

import pytest

from .adapters import OK

# Wave 2: MEM-002's to-be spec is still waiting for decisions, so the new service doesn't
# renew yet. These tests run against the legacy service only, for now.
pytestmark = pytest.mark.legacy_only


@pytest.mark.behaviour("MEM-002-B1")
def test_active_renewal_continues_term(svc):
    r = svc.renew("bob", "M-1002")
    assert r.kind == OK
    assert r.data["expires"] == "2027-03-31"
    assert r.data["charged"] == "69.00"


@pytest.mark.behaviour("MEM-002-B2")
def test_autopay_discount(svc):
    r = svc.renew("alice", "M-1001", autopay=True)
    assert r.data["charged"] == "117.80"  # 124 - 5%, half-up to the cent


@pytest.mark.behaviour("MEM-002-B3")
def test_long_lapsed_renewal_starts_today(svc):
    r = svc.renew("ana", "M-1003")
    assert r.data["expires"] == "2027-03-10"  # lapsed > 30 days: new year starts today
    assert r.data["charged"] == "164.00"
