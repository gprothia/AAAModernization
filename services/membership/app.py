"""Membership service: the modern replacement for legacy/membership-api, on GKE.

Built from the to-be specs (specs/MEM-001, specs/MEM-003) and proven by the same
characterisation harness as the legacy service (tests/harness). Comments name the spec
criterion or deviation that decides each behaviour.
"""

from __future__ import annotations

import base64
import contextvars
import hashlib
import hmac
import json
import math
import os
import re
import sys
import time
import uuid
from collections import deque
from datetime import UTC, date, datetime

from fastapi import Depends, FastAPI, Header, Request
from fastapi.responses import JSONResponse

TEST_HOOKS = os.environ.get("ENABLE_TEST_HOOKS", "false") == "true"  # sandboxes only (SEC-2)
SECRET = os.environ.get("DEMO_AUTH_SECRET", "demo-only-not-a-secret").encode()
SUPERVISOR_REFUND_LIMIT = 100  # DEV-003-07: above this, an agent needs a supervisor
REFUND_CUTOFF_DAYS = 30  # parity with membership.properties refund.cutoff.days

app = FastAPI(title="Membership", version="1.0.0")

# --------------------------------------------------------------------------- logging (LOG-1..5)
request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")
PHONE = re.compile(r"\+?\d[\d\s-]{8,}\d")
RECENT_LOGS: deque[dict] = deque(maxlen=500)


def mask(text: str) -> str:
    """LOG-4: phone numbers keep their last two digits only."""
    return PHONE.sub(lambda m: "*" * (len(m.group()) - 2) + m.group()[-2:], text)


def emit(event: str, **fields) -> None:
    line = {
        "ts": datetime.now(UTC).isoformat(),
        "severity": "INFO",
        "event": event,
        "request_id": request_id_var.get(),
        **fields,
    }
    line = json.loads(mask(json.dumps(line)))
    RECENT_LOGS.append(line)
    print(json.dumps(line), file=sys.stdout, flush=True)


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str):
        self.status, self.code, self.message = status, code, message


@app.exception_handler(ApiError)
async def api_error(_: Request, e: ApiError):
    # API-2: one error shape everywhere (legacy: 200 with {"error"}, DEV-001-02)
    return JSONResponse({"code": e.code, "message": e.message, "request_id": request_id_var.get()}, e.status)


@app.middleware("http")
async def request_context(request: Request, call_next):
    rid = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:16]
    request_id_var.set(rid)
    start = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = rid  # API-4
    if request.url.path != "/healthz":
        emit(
            "http.request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=round((time.perf_counter() - start) * 1000, 1),
            user=getattr(request.state, "user", None),
        )
    return response


# --------------------------------------------------------------------------- data (same seed as legacy)
USERS = {
    "alice": ("member", "M-1001"),
    "bob": ("member", "M-1002"),
    "ana": ("agent", None),
    "sam": ("supervisor", None),
}
MEMBERS: dict[str, dict] = {}
AUDIT: list[dict] = []
CLOCK: dict[str, datetime | None] = {"now": None}


def seed() -> None:
    MEMBERS.clear()
    AUDIT.clear()
    for mid, name, phone, plan, status, expires, paid in [
        ("M-1001", "Alice Ng", "+1 555 010 4455", "PLUS", "ACTIVE", "2026-12-31", "124.00"),
        ("M-1002", "Bob Ortiz", "+1 555 010 7788", "CLASSIC", "ACTIVE", "2026-03-31", "69.00"),
        ("M-1003", "Cara Diaz", "+1 555 010 2211", "PREMIER", "LAPSED", "2025-09-15", "164.00"),
        ("M-1004", "Dan Lee", "+1 555 010 9933", "PREMIER", "ACTIVE", "2026-12-31", "164.00"),
    ]:
        MEMBERS[mid] = {
            "member_id": mid,
            "name": name,
            "phone": phone,
            "plan": plan,
            "status": status,
            "expires": expires,
            "paid": paid,
        }


def now() -> datetime:
    """UTC, as the legacy service (DEV-003-06 kept for parity). Test hooks may freeze it."""
    return CLOCK["now"] or datetime.now(UTC).replace(tzinfo=None)


seed()


# --------------------------------------------------------------------------- authentication (AAA-1, DEV-001-04)
def sign(payload: dict) -> str:
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
    return body + "." + hmac.new(SECRET, body.encode(), hashlib.sha256).hexdigest()


def current_user(request: Request, authorization: str | None = Header(default=None)) -> dict:
    if authorization and authorization.lower().startswith("bearer "):
        body, _, sig = authorization[7:].partition(".")
        if hmac.compare_digest(sig, hmac.new(SECRET, body.encode(), hashlib.sha256).hexdigest()):
            user = json.loads(base64.urlsafe_b64decode(body))
            if user["exp"] > time.time():  # AAA-2
                request.state.user = user["sub"]
                return user
    raise ApiError(401, "UNAUTHENTICATED", "Sign in required")


@app.post("/v1/auth/demo-login")
def demo_login(body: dict):
    """AAA-3, demo only: in production the company SSO issues the token."""
    role, member_id = USERS[body["user"]]
    return {"token": sign({"sub": body["user"], "role": role, "member_id": member_id, "exp": time.time() + 8 * 3600})}


def visible_member(member_id: str, user: dict) -> dict:
    """AAA-7: someone else's record and a missing one look the same (DEV-001-01, DEV-003-01)."""
    m = MEMBERS.get(member_id)
    if not m or (user["role"] == "member" and user["member_id"] != member_id):
        raise ApiError(404, "MEMBER_NOT_FOUND", "Member not found")
    return m


def audit(event: str, user: dict, target: str, **details) -> None:
    """AAA-9, AAA-10 (DEV-003-03: the legacy service audits nothing)."""
    entry = {
        "event": event,
        "actor": user["sub"],
        "target": target,
        "at": now().isoformat(),
        "request_id": request_id_var.get(),
        **details,
    }
    AUDIT.append(entry)
    emit("audit", **entry)


# --------------------------------------------------------------------------- MEM-001 lookup
@app.get("/v1/members/{member_id}")
def get_member(member_id: str, user: dict = Depends(current_user)):
    return visible_member(member_id, user)  # MEM-001-AC1..AC3; nothing personal is logged


# --------------------------------------------------------------------------- MEM-003 cancel and refund
def refund_for(m: dict, today: datetime) -> int:
    """Parity with legacy RefundCalc.java:13-24, including its floating-point arithmetic.

    Days left are whole days to midnight at the start of the expiry date (truncated), counted
    on the UTC clock; under 31 days: no refund; otherwise paid / 365 x days, rounded down to
    whole dollars (DEV-003-05 and DEV-003-06 kept by decision on #1).
    """
    expiry = datetime.combine(date.fromisoformat(m["expires"]), datetime.min.time())
    days_left = int((expiry - today).total_seconds() // 86400)
    if days_left <= REFUND_CUTOFF_DAYS:
        return 0
    return math.floor(float(m["paid"]) / 365 * days_left)


@app.post("/v1/members/{member_id}/cancellation", status_code=201)
def cancel(member_id: str, user: dict = Depends(current_user)):
    m = visible_member(member_id, user)  # 404 before any other check: no hints (MEM-003-AC4)
    if m["status"] == "CANCELLED":
        raise ApiError(409, "ALREADY_CANCELLED", "Membership is already cancelled")  # DEV-003-04
    refund = refund_for(m, now())
    if refund > SUPERVISOR_REFUND_LIMIT and user["role"] != "supervisor":
        raise ApiError(403, "REFUND_NEEDS_SUPERVISOR", "Refunds above 100.00 need a supervisor")  # DEV-003-07
    previous, m["status"] = m["status"], "CANCELLED"
    refund_id = "RF-" + uuid.uuid4().hex[:8].upper()
    audit("membership.cancelled", user, member_id, previous_status=previous)
    audit("refund.issued", user, member_id, amount=f"{refund:.2f}", refund_id=refund_id)
    return {"member_id": member_id, "status": "CANCELLED", "refund": f"{refund:.2f}", "refund_id": refund_id}


@app.get("/v1/audit")
def read_audit(target: str | None = None, user: dict = Depends(current_user)):
    if user["role"] != "supervisor":
        raise ApiError(403, "FORBIDDEN", "Your role may not do this")  # AAA-5
    return [e for e in AUDIT if target in (None, e["target"])]


@app.get("/healthz")
def healthz():
    return {"ok": True}


# --------------------------------------------------------------------------- test hooks (sandboxes only, SEC-2)
if TEST_HOOKS:

    @app.post("/test/reset", include_in_schema=False)
    def test_reset(body: dict):
        seed()
        CLOCK["now"] = datetime.fromisoformat(body["clock"]) if body.get("clock") else None
        return {"ok": True}

    @app.get("/test/logs", include_in_schema=False)
    def test_logs():
        return list(RECENT_LOGS)
