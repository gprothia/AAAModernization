---
id: MEM-001
title: Member lookup
status: approved
owner: "@gprothia"
issue: "#1"
replaces: specs/as-is/MEM-001-member-lookup.md
---

# MEM-001: Member lookup

## Why
Members and agents look up a membership. The new service returns the same facts as the
legacy service, in AAA's API format, without revealing other members' records or logging
personal data.

## Scope
- In: reading one member's record.
- Out: searching members by name (not offered today either).

## Acceptance criteria

### MEM-001-AC1 [api]
**Parity** with `MEM-001-B1` and `MEM-001-B2`.
- **Given** Alice (member `M-1001`) or agent Ana is signed in
- **When** they send `GET /v1/members/M-1001`
- **Then** `200` with `member_id`, `name`, `phone`, `plan` `PLUS`, `status` `ACTIVE`, `expires` `"2026-12-31"`, `paid` `"124.00"`

### MEM-001-AC2 [api]
**Deviation** `DEV-001-01` (was `MEM-001-B3`: 403).
- **Given** Bob is signed in
- **When** he sends `GET /v1/members/M-1001`
- **Then** `404` with code `MEMBER_NOT_FOUND`, identical to an unknown ID (AAA-7)

### MEM-001-AC3 [api]
**Deviation** `DEV-001-02` (was `MEM-001-B4`: 200 with `{"error"}`).
- **Given** an agent is signed in
- **When** she sends `GET /v1/members/M-9999`
- **Then** `404` with body `{"code": "MEMBER_NOT_FOUND", "message": ..., "request_id": ...}` (API-2)

### MEM-001-AC4 [api]
**Deviation** `DEV-001-04` (was `MEM-001-B5`: HTTP Basic).
- **Given** no token, or an invalid one
- **When** `GET /v1/members/M-1001` is sent
- **Then** `401` with code `UNAUTHENTICATED`

## Approved deviations
| ID | Legacy behaviour | New behaviour | Rule | Decided by |
|---|---|---|---|---|
| DEV-001-01 | Another member's record: 403 | 404 `MEMBER_NOT_FOUND` | AAA-7 | Security (MOD-5), #1 |
| DEV-001-02 | Not found: 200 with `{"error"}` | 404 with the standard error body | API-2, API-3 | Architecture, #1 |
| DEV-001-03 | Name and full phone logged | Neither logged | LOG-4 | Security (MOD-5), #1 |
| DEV-001-04 | HTTP Basic, clear-text passwords | Bearer token from SSO | AAA-1 | Security (MOD-5), #1 |
| DEV-001-06 | US date text, float amounts | ISO dates, amounts as two-decimal strings | API standard | Architecture, #1 |

Not audited, by decision on #1: reading a record is not a change (AAA-9 covers changes); the
"reveal full phone" idea is a follow-up feature (DEV-001-05 closed as out of scope).

## Security & access (AAA)
### Authentication
`Authorization: Bearer <token>` (AAA-1).
### Authorization
| Action | Roles allowed |
|---|---|
| Read own record | member (others get 404, AAA-7) |
| Read any record | agent, supervisor |
### Accounting
None: reading changes nothing (AAA-9 covers changes).

## Logging
One `http.request` line per request with `request_id`, `user` and `role`. No names or phone numbers.

## API contract
| Method | Path | Success | Errors |
|---|---|---|---|
| GET | /v1/members/{id} | 200 | 401 UNAUTHENTICATED, 404 MEMBER_NOT_FOUND |

## SLO
No worse than the legacy baseline (p95 180 ms, 0.2%).
```slo
p95_latency_ms: 150
error_rate_pct: 0.2
```

## Open questions
- [x] (Business) Other systems parsing `MM/dd/yyyy`? → The website only; it moves to the new API at cut-over (#1)
- [x] (Business) Mask the phone for agents? → Not now; follow-up feature (#1)
