"""Harness for specs/as-is/MEM-003-cancel-and-refund.md, proving specs/MEM-003-cancel-and-refund.md.

Runs against legacy (must be 100% green first, MOD-6) and against the new service.
"""

import pytest

from .adapters import CONFLICT, FORBIDDEN, NOT_FOUND, OK


@pytest.mark.behaviour("MEM-003-B1")
@pytest.mark.ac("MEM-003-AC1")
def test_refund_is_pro_rata_rounded_down(svc):
    r = svc.cancel("alice", "M-1001")
    assert r.kind == OK
    assert r.data["refund"] == "100.00"  # 124 / 365 x 295 = 100.22, rounded down (kept: DEV-003-05)


@pytest.mark.behaviour("MEM-003-B2")
@pytest.mark.ac("MEM-003-AC2")
def test_no_refund_near_expiry(svc):
    assert svc.cancel("bob", "M-1002").data["refund"] == "0.00"  # 20 days left <= 30


@pytest.mark.behaviour("MEM-003-B3")
@pytest.mark.ac("MEM-003-AC3")
@pytest.mark.deviation("DEV-003-04")
def test_second_cancellation(svc, expect):
    svc.cancel("alice", "M-1001")
    again = svc.cancel("alice", "M-1001")
    assert again.kind == expect(legacy=OK, modern=CONFLICT)
    if svc.target == "legacy":
        assert again.data["refund"] == "100.00"  # the legacy bug: refunded twice
    else:
        assert again.code == "ALREADY_CANCELLED"


@pytest.mark.behaviour("MEM-003-B4")
@pytest.mark.ac("MEM-003-AC4")
@pytest.mark.deviation("DEV-003-01")
def test_member_cannot_cancel_another(svc, expect):
    r = svc.cancel("bob", "M-1001")
    assert r.kind == expect(legacy=FORBIDDEN, modern=NOT_FOUND)


@pytest.mark.behaviour("MEM-003-B5")
@pytest.mark.ac("MEM-003-AC6")
def test_agent_cancels_any_member(svc):
    r = svc.cancel("ana", "M-1001")  # refund 100.00: within an agent's limit, so parity holds
    assert r.kind == OK
    assert r.data["refund"] == "100.00"


@pytest.mark.behaviour("MEM-003-B5")
@pytest.mark.ac("MEM-003-AC5")
@pytest.mark.deviation("DEV-003-07")
def test_agent_large_refund(svc, expect):
    r = svc.cancel("ana", "M-1004")  # refund 132.00
    assert r.kind == expect(legacy=OK, modern=FORBIDDEN)
    if svc.target == "modern":
        assert r.code == "REFUND_NEEDS_SUPERVISOR"


@pytest.mark.behaviour("MEM-003-B6")
@pytest.mark.behaviour("MEM-003-B7")
@pytest.mark.ac("MEM-003-AC10")
def test_days_counted_in_utc_with_365_day_year(svc):
    # 01:00 UTC on 11 March is still 10 March (6 pm) in California, but the day count uses UTC:
    # 294 days left, 124 / 365 x 294 = 99.88, rounded down. Kept for parity (DEV-003-06).
    svc.reset(clock="2026-03-11 01:00:00")
    assert svc.cancel("alice", "M-1001").data["refund"] == "99.00"
