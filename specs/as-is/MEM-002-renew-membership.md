---
id: MEM-002
title: Renew membership
kind: as-is
status: draft
owner: "@gprothia"
issue: "#1"
source: legacy/membership-api
---

# MEM-002: Renew membership (as-is)

## What it does today
Members and member-services agents renew a membership for one additional year, optionally with a 5% autopay discount. It updates the member's expiry date, status (`ACTIVE`), and `paid` amount, and inserts a `RENEWAL` row into `payments`.

## Observed behaviour

### MEM-002-B1 [api]
- **Given** an `ACTIVE` member (e.g., `M-1001`, `PLUS`, `expires` `2026-12-31`, `price.PLUS=124`)
- **When** `POST /renewMember?id=M-1001` is sent without `autopay=true`
- **Then** `expires` advances by 1 calendar year to `12/31/2027`, `charged` is `124`, `members` is updated (`status='ACTIVE'`, `expires`, `paid=124`), a `RENEWAL` row is inserted into `payments`, and HTTP `200` returns `{"memberId": "M-1001", "expires": "12/31/2027", "charged": 124}`
- **Source:** `legacy/membership-api/src/main/java/org/aaa/membership/RenewalService.java:19-44`
- **Confidence:** medium

### MEM-002-B2 [api]
- **Given** an `ACTIVE` member (e.g., `M-1001`, `PLUS`, `price.PLUS=124`)
- **When** `POST /renewMember?id=M-1001&autopay=true` is sent
- **Then** a 5% discount (`autopay.discount=0.05`) is applied and rounded `HALF_UP` to 2 decimal places (`124 - 6.20 = 117.80`), `charged` is `117.8` (or `117.80`), and `expires` advances by 1 year
- **Source:** `legacy/membership-api/src/main/java/org/aaa/membership/RenewalService.java:35-38`
- **Confidence:** medium

### MEM-002-B3 [api]
- **Given** a `LAPSED` member whose `expires` date is more than `30` days (`renewal.grace.days=30`) before `today` (e.g., `M-1003`, `PREMIER`, `expires` `2025-09-15`, `today` `2026-03-10`)
- **When** `POST /renewMember?id=M-1003` is sent by an agent
- **Then** the new year starts from `today` instead of the old expiry (`today + 1 year`), `status` becomes `ACTIVE`, and `charged` is `164`
- **Source:** `legacy/membership-api/src/main/java/org/aaa/membership/RenewalService.java:24-32`
- **Confidence:** medium

### MEM-002-B4 [api]
- **Given** a `LAPSED` member whose `expires` date is within `30` days of `today` (`!today.after(graceEnd)`)
- **When** `POST /renewMember` is sent
- **Then** the new year continues from the old `expires` date (`expires + 1 year`), not `today`, and `status` becomes `ACTIVE`
- **Source:** `legacy/membership-api/src/main/java/org/aaa/membership/RenewalService.java:24-32`
- **Confidence:** medium

### MEM-002-B5 [api]
- **Given** a `CANCELLED` member or a request with a `card` parameter
- **When** `POST /renewMember?id=<id>&card=<card>` is sent
- **Then** `CANCELLED` is not rejected (only `"LAPSED".equals(m.status)` is checked, so a cancelled member is reactivated from `expires + 1 year`), and `card` is logged in clear without calling any payment processor
- **Source:** `legacy/membership-api/src/main/java/org/aaa/membership/MemberServlet.java:62-70`
- **Confidence:** low

## Hidden behaviours
- **29 Feb leap-day rule**: `Calendar.add(Calendar.YEAR, 1)` turns `29 Feb` into `28 Feb` the following year (`RenewalService.java:32`).
- **Time zone**: `Calendar.getInstance()` uses the server's default time zone (UTC in the container) (`RenewalService.java:20`).
- **Non-atomic persistence**: `MemberDao.saveRenewal` opens two separate JDBC connections for `UPDATE members` and `INSERT INTO payments` (`MemberDao.java:43-46,53-63`), so a failure on the second statement leaves `members` updated without a `payments` row.
- **No `CANCELLED` guard**: `RenewalService` only checks `"LAPSED".equals(m.status)`; renewing a `CANCELLED` member silently sets `status='ACTIVE'` and extends from `expires`.

## Data and dependencies
- Reads `users` (`MemberDao.login`) and `members` (`MemberDao.find`).
- Writes `members` (`status='ACTIVE'`, `expires`, `paid`) and `payments` (`member_id`, `amount`, `'RENEWAL'`, `NOW()`) via `MemberDao.saveRenewal` (`MemberDao.java:43-46`).
- Reads `membership.properties`: `price.CLASSIC` (`69`), `price.PLUS` (`124`), `price.PREMIER` (`164`), `autopay.discount` (`0.05`), `renewal.grace.days` (`30`).
- No external payment gateway calls; no scheduled jobs.

## Security & access (as found)
### Authentication
HTTP Basic against `users` table with clear-text passwords (`MemberServlet.java:85-95`, `MemberDao.java:18-28`).
### Authorization
| Action | Roles allowed today |
|---|---|
| Renew own membership | `MEMBER` (other IDs return `403`, `MemberServlet.java:51-55`) |
| Renew any membership | `AGENT` |
### Accounting
Inserts a `RENEWAL` row into `payments`, but records no `actor` (which user/agent renewed) and emits no audit events.

## Logging (as found)
Log4j plain text (`MemberServlet.java:66`):
`renewMember id=<id> charged=<r.charged> card=<req.getParameter("card")>`
Logs the `card` query/form parameter in clear text. No `request_id`, no JSON structured logging, no `http.request` line.

## API contract (as found)
| Method | Path | Success | Errors |
|---|---|---|---|
| POST | `/renewMember?id={memberId}&autopay={true\|false}&card={card}` | `200` (also `200 {"error":"Member not found"}`) | `401` (Basic challenge), `403 {"error":"Not allowed"}` |

## Performance baseline
<!-- MOD-8: measured on the legacy service in a GKE sandbox with tools/loadgen -->
```baseline
p95_latency_ms: 0
error_rate_pct: 0
```
*(Not yet measured in sandbox during discovery.)*

## Deviations from standards
| ID | Behaviour | Rule | Kind |
|---|---|---|---|
| DEV-002-01 | Another member's renewal returns `403` instead of `404` | AAA-7 | security |
| DEV-002-02 | Unknown member returns HTTP `200` with `{"error": "Member not found"}` instead of `404` | API-2, API-3 | api |
| DEV-002-03 | `card` parameter logged in clear; no structured `http.request` or `request_id` logs | LOG-1, LOG-2, LOG-4 | security |
| DEV-002-04 | No audit event (`membership.renewed`) recorded with `actor` | AAA-9, AAA-10 | audit |
| DEV-002-05 | `CANCELLED` member can be renewed without `409`; `members` and `payments` updated outside a transaction | API-5 | business |
| DEV-002-06 | HTTP Basic auth, unversioned verb path `/renewMember`, `MM/dd/yyyy` dates | AAA-1, API-1 | security |

## Open questions
- [ ] (Security) Confirm replacing HTTP Basic with Bearer token (`DEV-002-06`), `404` for other members (`DEV-002-01`), removing `card` from logs (`DEV-002-03`), and adding `membership.renewed` audit events (`DEV-002-04`).
- [ ] (Business) For `MEM-002-B5`, should renewing a `CANCELLED` member be rejected with `409` (`DEV-002-05`), or allowed? And is the `card` parameter still needed by the website?
- [ ] (Business) Should the 30-day grace period (`MEM-002-B4`) and UTC clock be kept for parity?
- [ ] (Business) Confirm moving to `/v1/members/{id}/renewal`, `404` for unknown member (`DEV-002-02`), ISO dates, and atomic DB transaction (`DEV-002-05`).
