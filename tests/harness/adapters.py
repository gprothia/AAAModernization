"""One interface, two systems: the legacy servlet API and the new /v1 API (MOD-7).

Tests call `svc.lookup(...)`, `svc.renew(...)`, `svc.cancel(...)` and compare `Outcome`s, so
the same behaviour test runs against both. Only this file knows the URLs, sign-in and formats.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

import httpx

# Outcome kinds, the same for both systems
OK, NOT_FOUND, FORBIDDEN, UNAUTHENTICATED, CONFLICT = "ok", "not_found", "forbidden", "unauthenticated", "conflict"

PASSWORDS = {"alice": "alice", "bob": "bob", "ana": "ana"}  # legacy demo users (seed.sql)


@dataclass
class Outcome:
    kind: str
    data: dict = field(default_factory=dict)
    code: str | None = None  # the error code, where the API has one (only the new service does)
    raw_status: int = 0


def money(value) -> str:
    """Normalise an amount (legacy: JSON number like 124.0; new: "124.00") to "124.00"."""
    return str(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def iso_date(value: str) -> str:
    """Normalise a date (legacy: "12/31/2026"; new: "2026-12-31") to ISO."""
    if "/" in value:
        return datetime.strptime(value, "%m/%d/%Y").date().isoformat()
    return value


def normalise(body: dict) -> dict:
    out = {}
    for key, value in body.items():
        k = {"memberId": "member_id"}.get(key, key)
        if k in ("expires",):
            value = iso_date(value)
        elif k in ("paid", "charged", "refund"):
            value = money(value)
        out[k] = value
    return out


class LegacyAdapter:
    """GET /getMember, POST /renewMember, POST /cancelMember; HTTP Basic; errors in a 200 body."""

    target = "legacy"

    def __init__(self, base_url: str):
        self.http = httpx.Client(base_url=base_url, timeout=10)
        self.reset_url = os.environ.get("HARNESS_RESET_URL")  # sandbox-only sidecar

    def _call(self, method: str, path: str, user: str | None, params: dict) -> Outcome:
        auth = (user, PASSWORDS[user]) if user else None
        r = self.http.request(
            method,
            path,
            params=params if method == "GET" else None,
            data=params if method == "POST" else None,
            auth=auth,
        )
        if r.status_code == 401:
            return Outcome(UNAUTHENTICATED, raw_status=401)
        if r.status_code == 403:
            return Outcome(FORBIDDEN, raw_status=403)
        body = r.json()
        if "error" in body:  # legacy reports "not found" as HTTP 200 + {"error": ...}
            return Outcome(NOT_FOUND if "not found" in body["error"] else FORBIDDEN, raw_status=r.status_code)
        return Outcome(OK, normalise(body), raw_status=r.status_code)

    def lookup(self, user, member_id):
        return self._call("GET", "/getMember", user, {"id": member_id})

    def renew(self, user, member_id, autopay=False):
        return self._call("POST", "/renewMember", user, {"id": member_id, "autopay": str(autopay).lower()})

    def cancel(self, user, member_id):
        return self._call("POST", "/cancelMember", user, {"id": member_id})

    def reset(self, clock: str = "2026-03-10 12:00:00"):
        httpx.post(f"{self.reset_url}/reset", json={"clock": clock}, timeout=30).raise_for_status()


class ModernAdapter:
    """The new service: /v1 paths, bearer tokens, standard error bodies (standards/api.md)."""

    target = "modern"

    def __init__(self, base_url: str):
        self.http = httpx.Client(base_url=base_url, timeout=10)
        self._tokens: dict[str, str] = {}

    def token(self, user: str) -> str:
        if user not in self._tokens:
            r = self.http.post("/v1/auth/demo-login", json={"user": user})
            r.raise_for_status()
            self._tokens[user] = r.json()["token"]
        return self._tokens[user]

    def _call(self, method: str, path: str, user: str | None, body: dict | None = None) -> Outcome:
        headers = {"Authorization": f"Bearer {self.token(user)}"} if user else {}
        r = self.http.request(method, path, json=body, headers=headers)
        kinds = {401: UNAUTHENTICATED, 403: FORBIDDEN, 404: NOT_FOUND, 409: CONFLICT}
        if r.status_code in kinds:
            return Outcome(kinds[r.status_code], code=r.json().get("code"), raw_status=r.status_code)
        r.raise_for_status()
        return Outcome(OK, normalise(r.json()), raw_status=r.status_code)

    def lookup(self, user, member_id):
        return self._call("GET", f"/v1/members/{member_id}", user)

    def renew(self, user, member_id, autopay=False):
        return self._call("POST", f"/v1/members/{member_id}/renewals", user, {"autopay": autopay})

    def cancel(self, user, member_id):
        return self._call("POST", f"/v1/members/{member_id}/cancellation", user)

    def reset(self, clock: str = "2026-03-10 12:00:00"):
        self.http.post("/test/reset", json={"clock": clock}).raise_for_status()


def make_adapter() -> LegacyAdapter | ModernAdapter:
    target = os.environ.get("TARGET", "legacy")
    base_url = os.environ["BASE_URL"]
    return LegacyAdapter(base_url) if target == "legacy" else ModernAdapter(base_url)
