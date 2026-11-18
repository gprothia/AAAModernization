"""AAA control tests for specs/MEM-003-cancel-and-refund.md that only the new service has."""

import pytest

CANCEL = "/v1/members/{}/cancellation"


@pytest.mark.ac("MEM-003-AC5")
def test_supervisor_issues_large_refund(as_user):
    r = as_user("sam").post(CANCEL.format("M-1004"))
    assert r.status_code == 201
    assert r.json()["refund"] == "132.00"


@pytest.mark.ac("MEM-003-AC5")
def test_agent_large_refund_changes_nothing(as_user):
    assert as_user("ana").post(CANCEL.format("M-1004")).status_code == 403
    assert as_user("sam").get("/v1/members/M-1004").json()["status"] == "ACTIVE"


@pytest.mark.ac("MEM-003-AC7")
@pytest.mark.parametrize("header", [None, "Bearer not-a-token"])
def test_sign_in_required(api, header):
    r = api.post(CANCEL.format("M-1001"), headers={"Authorization": header} if header else {})
    assert r.status_code == 401
    assert r.json()["code"] == "UNAUTHENTICATED"


@pytest.mark.ac("MEM-003-AC8")
def test_cancellation_is_audited(as_user):
    r = as_user("alice").post(CANCEL.format("M-1001"))
    rid = r.headers["X-Request-ID"]
    events = as_user("sam").get("/v1/audit", params={"target": "M-1001"}).json()
    by_name = {e["event"]: e for e in events}
    assert by_name["membership.cancelled"]["actor"] == "alice"
    assert by_name["refund.issued"]["amount"] == "100.00"
    assert {e["request_id"] for e in events} == {rid}


@pytest.mark.ac("MEM-003-AC8")
def test_members_cannot_read_audit(as_user):
    r = as_user("alice").get("/v1/audit", params={"target": "M-1001"})
    assert r.status_code == 403
    assert r.json()["code"] == "FORBIDDEN"


@pytest.mark.ac("MEM-003-AC9")
def test_phone_never_logged(as_user, api):
    r = as_user("alice").post(CANCEL.format("M-1001"))
    rid = r.headers["X-Request-ID"]
    lines = [line for line in api.get("/test/logs").json() if line.get("request_id") == rid]
    assert lines, "the request's log lines carry its request_id"
    assert not any("555 010 4455" in str(line) for line in lines)
