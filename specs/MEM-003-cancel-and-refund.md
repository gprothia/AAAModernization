---
id: MEM-003
title: Cancel and refund
status: approved
owner: "@gprothia"
issue: "#1"
replaces: specs/as-is/MEM-003-cancel-and-refund.md
---

# MEM-003: Cancel and refund

## Why
Members and agents cancel memberships and refund the unused part of the year. The new
membership service on GKE keeps the refund rules members and Finance rely on, and fixes the
security, audit and double-refund problems found in the legacy service.

## Scope
- In: cancelling a membership; calculating and recording the refund; who may do it; audit.
- Out: paying the refund to the card (Finance's payment run reads the recorded refunds, as today).

## Acceptance criteria

### MEM-003-AC1 [api]
**Parity** with `MEM-003-B1`.
- **Given** Alice paid `124.00` for a membership expiring `2026-12-31`, and today is 2026-03-10
- **When** she sends `POST /v1/members/M-1001/cancellation`
- **Then** `201` with `status` `CANCELLED` and `refund` `"100.00"`: 124 / 365 x 295 days, rounded down to whole dollars

### MEM-003-AC2 [api]
**Parity** with `MEM-003-B2`.
- **Given** Bob's membership expires in 20 days
- **When** he cancels
- **Then** `201` with `refund` `"0.00"`

### MEM-003-AC3 [api]
**Deviation** `DEV-003-04` (was `MEM-003-B3`: refunded twice).
- **Given** Alice's membership is already cancelled
- **When** the cancellation is sent again
- **Then** `409` with code `ALREADY_CANCELLED`, and no second refund is recorded

### MEM-003-AC4 [api]
**Deviation** `DEV-003-01` (was `MEM-003-B4`: 403).
- **Given** Bob is signed in
- **When** he cancels Alice's membership (`M-1001`)
- **Then** `404` with code `MEMBER_NOT_FOUND`, the same as for an ID that does not exist (AAA-7)

### MEM-003-AC5 [api]
**Deviation** `DEV-003-07` (was `MEM-003-B5`: any agent, any amount).
- **Given** agent Ana is signed in and Dan's refund would be `132.00`
- **When** she cancels Dan's membership (`M-1004`)
- **Then** `403` with code `REFUND_NEEDS_SUPERVISOR`, and nothing changes
- **And** when supervisor Sam sends the same request, `201` with `refund` `"132.00"`

### MEM-003-AC6 [api]
**Parity** with `MEM-003-B5` for refunds up to `100.00`.
- **Given** agent Ana is signed in
- **When** she cancels Alice's membership (refund `100.00`)
- **Then** `201` with `refund` `"100.00"`

### MEM-003-AC7 [api]
- **Given** no token, or an expired one
- **When** `POST /v1/members/M-1001/cancellation` is sent
- **Then** `401` with code `UNAUTHENTICATED` (AAA-1)

### MEM-003-AC8 [api]
**Deviation** `DEV-003-03` (no audit today).
- **Given** a successful cancellation
- **When** a supervisor reads `GET /v1/audit?target=M-1001`
- **Then** it shows `membership.cancelled` and `refund.issued`, each with `actor`, `target`, `request_id`, and `amount` on the refund

### MEM-003-AC9 [api]
**Deviation** `DEV-003-02` (phone logged in clear).
- **Given** a successful cancellation
- **When** the service's log lines for that request are read
- **Then** no line contains the member's full phone number; the `http.request` and audit lines carry the `request_id`

### MEM-003-AC10 [api]
**Parity** with `MEM-003-B6` and `MEM-003-B7`.
- **Given** the clock is 2026-03-11 01:00 UTC (still 10 March, 6 pm, in California)
- **When** Alice cancels
- **Then** `refund` `"99.00"`: 294 days counted from the UTC clock, 365-day year, rounded down, exactly as in the legacy service

## Approved deviations
| ID | Legacy behaviour | New behaviour | Rule | Decided by |
|---|---|---|---|---|
| DEV-003-01 | Another member's record: 403 | 404 `MEMBER_NOT_FOUND` | AAA-7 | Security (MOD-5), #1 |
| DEV-003-02 | Full phone number in logs | Phone masked to last two digits | LOG-4 | Security (MOD-5), #1 |
| DEV-003-03 | No audit | `membership.cancelled`, `refund.issued` audit events | AAA-9 | Security (MOD-5), #1 |
| DEV-003-04 | Second cancellation refunds again | `409 ALREADY_CANCELLED` | API-5 | Finance, #1 |
| DEV-003-07 | Any agent refunds any amount | Above `100.00` needs a supervisor | AAA-5 | Business and Security, #1 |
| DEV-001-04 | HTTP Basic, clear-text passwords | Bearer token from SSO | AAA-1 | Security (MOD-5), #1 |

Kept for parity, by decision on #1: whole-dollar rounding down (`DEV-003-05`) and UTC day
counting (`DEV-003-06`). Both are listed as follow-ups for after cut-over.

## Security & access (AAA)

### Authentication
`Authorization: Bearer <token>` (AAA-1). Missing, invalid or expired: `401 UNAUTHENTICATED`.

### Authorization
| Action | Roles allowed |
|---|---|
| Cancel own membership | member (owner only; others get 404, AAA-7) |
| Cancel any membership, refund up to 100.00 | agent |
| Cancel any membership, any refund | supervisor |
| Read audit events | supervisor |

### Accounting
| Audit event | When | Details recorded |
|---|---|---|
| `membership.cancelled` | A membership is cancelled | actor, target, request_id, previous status |
| `refund.issued` | A refund is recorded (including 0.00) | actor, target, request_id, amount, refund_id |

## Logging
One `http.request` line per request (LOG-2) and one `audit` line per audit event (LOG-5),
all with the `request_id`. The member's phone number is never logged; names are not logged.

## API contract
| Method | Path | Success | Errors |
|---|---|---|---|
| POST | /v1/members/{id}/cancellation | 201 | 401 UNAUTHENTICATED, 403 REFUND_NEEDS_SUPERVISOR, 404 MEMBER_NOT_FOUND, 409 ALREADY_CANCELLED |
| GET | /v1/audit?target= | 200 | 401, 403 FORBIDDEN |

Amounts are strings with two decimals; dates are ISO `YYYY-MM-DD` (API standard).

## SLO
No worse than the legacy baseline (p95 310 ms, 0.6% errors, MOD-8).
```slo
p95_latency_ms: 250
error_rate_pct: 0.5
```

## Open questions
- [x] (Finance) Reject a second cancellation? → Yes, 409 (#1)
- [x] (Business) Refund to the cent? → No, keep whole dollars for now; follow-up after cut-over (#1)
- [x] (Business) Use the member's time zone? → Keep UTC for parity; follow-up (#1)
- [x] (Business, Security) Supervisor for large refunds? → Above 100.00 (#1)
