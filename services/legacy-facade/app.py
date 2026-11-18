"""A thin /v1 front for the legacy membership API, used only during the migration (MOD-9).

It translates paths and formats so the gateway can split /v1 traffic between the legacy and
the new service. It does not change legacy behaviour: that is the new service's job.
Retired with the legacy service (MOD-11).
"""

import json
import os
from datetime import datetime

import httpx
from fastapi import FastAPI, Header, Response

LEGACY = os.environ.get("LEGACY_URL", "http://legacy-membership:8080")
app = FastAPI(title="Legacy facade")


def legacy_auth(authorization: str | None) -> dict:
    # During the migration the gateway forwards a service credential for the legacy service.
    return {"Authorization": os.environ.get("LEGACY_SERVICE_AUTH", "")} if authorization else {}


def translate(r: httpx.Response) -> Response:
    if r.status_code in (401, 403):
        return Response(status_code=r.status_code)
    body = r.json()
    if "error" in body:
        return Response(
            status_code=404,
            media_type="application/json",
            content='{"code": "MEMBER_NOT_FOUND", "message": "Member not found"}',
        )
    if "expires" in body:
        body["expires"] = datetime.strptime(body["expires"], "%m/%d/%Y").date().isoformat()
    out = {("member_id" if k == "memberId" else k): v for k, v in body.items()}
    return Response(status_code=200, media_type="application/json", content=json.dumps(out))


@app.get("/v1/members/{member_id}")
def lookup(member_id: str, authorization: str | None = Header(default=None)):
    return translate(httpx.get(f"{LEGACY}/getMember", params={"id": member_id}, headers=legacy_auth(authorization)))


@app.post("/v1/members/{member_id}/cancellation")
def cancel(member_id: str, authorization: str | None = Header(default=None)):
    return translate(httpx.post(f"{LEGACY}/cancelMember", data={"id": member_id}, headers=legacy_auth(authorization)))
