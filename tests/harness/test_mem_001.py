"""Harness for specs/as-is/MEM-001-member-lookup.md. Runs against legacy and modern."""

import pytest

from .adapters import FORBIDDEN, NOT_FOUND, OK, UNAUTHENTICATED


@pytest.mark.behaviour("MEM-001-B1")
@pytest.mark.ac("MEM-001-AC1")
def test_member_reads_own_record(svc):
    r = svc.lookup("alice", "M-1001")
    assert r.kind == OK
    assert r.data["member_id"] == "M-1001"
    assert r.data["plan"] == "PLUS"
    assert r.data["status"] == "ACTIVE"
    assert r.data["expires"] == "2026-12-31"
    assert r.data["paid"] == "124.00"


@pytest.mark.behaviour("MEM-001-B2")
@pytest.mark.ac("MEM-001-AC1")
def test_agent_reads_any_record(svc):
    r = svc.lookup("ana", "M-1002")
    assert r.kind == OK
    assert r.data["member_id"] == "M-1002"


@pytest.mark.behaviour("MEM-001-B3")
@pytest.mark.ac("MEM-001-AC2")
@pytest.mark.deviation("DEV-001-01")
def test_member_cannot_read_another_record(svc, expect):
    r = svc.lookup("bob", "M-1001")
    assert r.kind == expect(legacy=FORBIDDEN, modern=NOT_FOUND)  # AAA-7: don't reveal it exists


@pytest.mark.behaviour("MEM-001-B4")
@pytest.mark.ac("MEM-001-AC3")
def test_unknown_member(svc):
    assert svc.lookup("ana", "M-9999").kind == NOT_FOUND  # legacy 200 + {"error"}, new 404: same outcome


@pytest.mark.behaviour("MEM-001-B5")
@pytest.mark.ac("MEM-001-AC4")
def test_sign_in_required(svc):
    assert svc.lookup(None, "M-1001").kind == UNAUTHENTICATED
