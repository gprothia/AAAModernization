---
id: MEM-003
title: Cancel and refund
kind: as-is
status: draft
owner: "@gprothia"
issue: "#1"
source: legacy/membership-api
---

# MEM-003: Cancel and refund (as-is)

## What it does today
Members and member-services agents cancel a membership and calculate a pro-rata refund for the unused part of the year. It sets the member's status to `CANCELLED` and inserts a negative `REFUND` row into `payments` for Finance's reconciliation.

## Observed behaviour

### MEM-003-B1 [api]
- **Given** Alice (`M-1001`, `paid` `124.00`, `expires` `2026-12-31`) and `today` is `2026-03-10` (295 days left, `> 30` cutoff)
- **When** she sends `POST /cancelMember?id=M-1001`
- **Then** `status` is updated to `CANCELLED`, `payments` gets a `REFUND` row with `-100`, and HTTP `200` returns `{"memberId": "M-1001", "refund": 100}` (`floor((124 / 365) * 295) = floor(100.219...) = 100`)
- **Source:** `legacy/membership-api/src/main/java/org/aaa/membership/RefundCalc.java:13-24`
- **Confidence:** medium

### MEM-003-B2 [api]
- **Given** a member whose `expires` is `<= 30` days (`refund.cutoff.days=30`) from `today` (e.g., Bob `M-1002`, `expires` `2026-03-31`, `today` `2026-03-10`, 20 days left)
- **When** `POST /cancelMember?id=M-1002` is sent
- **Then** `status` becomes `CANCELLED`, `payments` gets a `REFUND` row with `0`, and HTTP `200` returns `{"memberId": "M-1002", "refund": 0}`
- **Source:** `legacy/membership-api/src/main/java/org/aaa/membership/RefundCalc.java:17-20`
- **Confidence:** medium

### MEM-003-B3 [api]
- **Given** a member whose `status` is already `CANCELLED`
- **When** `POST /cancelMember?id=M-1001` is sent a second time
- **Then** there is no check for an earlier cancellation: `members` is updated again, a second `REFUND` row is inserted into `payments`, and HTTP `200` returns the refund again
- **Source:** `legacy/membership-api/src/main/java/org/aaa/membership/MemberServlet.java:72-79`
- **Confidence:** medium

### MEM-003-B4 [api]
- **Given** Bob (`bob`, role `MEMBER`, `M-1002`) is signed in
- **When** he sends `POST /cancelMember?id=M-1001`
- **Then** HTTP `403` with JSON `{"error": "Not allowed"}`
- **Source:** `legacy/membership-api/src/main/java/org/aaa/membership/MemberServlet.java:51-55`
- **Confidence:** medium

### MEM-003-B5 [api]
- **Given** agent Ana (`ana`, role `AGENT`) is signed in
- **When** she sends `POST /cancelMember?id=M-1004` (Dan, `paid` `164.00`, refund `132`)
- **Then** HTTP `200` with `{"memberId": "M-1004", "refund": 132}` — any agent can cancel any member and issue any refund amount without supervisor approval
- **Source:** `legacy/membership-api/src/main/java/org/aaa/membership/MemberServlet.java:73-78`
- **Confidence:** medium

### MEM-003-B6 [api]
- **Given** the server clock is `2026-03-11 01:00 UTC` (still `2026-03-10` 6 pm in California)
- **When** Alice (`M-1001`, `expires` `2026-12-31`) cancels
- **Then** `daysLeft` is computed from `new java.util.Date()` in UTC (`294` days), returning `refund: 99`
- **Source:** `legacy/membership-api/src/main/java/org/aaa/membership/MemberServlet.java:74`
- **Confidence:** medium

### MEM-003-B7 [api]
- **Given** any cancellation with `daysLeft > 30`
- **When** the daily rate is computed
- **Then** `m.paid.doubleValue() / 365` is used even in a leap year, and `Math.floor(perDay * daysLeft)` rounds down to whole dollars
- **Source:** `legacy/membership-api/src/main/java/org/aaa/membership/RefundCalc.java:22-23`
- **Confidence:** medium

## Hidden behaviours
- **Whole-dollar truncation**: `Math.floor` always rounds down to whole dollars (explaining member complaints of refunds being "a dollar short").
- **Duplicate refunds**: `MemberServlet.doPost` does not check `m.status` before calling `dao.saveCancellation` (explaining Finance's duplicate refund reports).
- **Zero-dollar refund row**: Even when `daysLeft <= 30` (`refund == 0`), `saveCancellation` still inserts a `REFUND` row with amount `0` into `payments`.
- **Non-atomic persistence**: `MemberDao.saveCancellation` runs `UPDATE members` and `INSERT INTO payments` on separate JDBC connections (`MemberDao.java:48-63`).

## Data and dependencies
- Reads `users` (`MemberDao.login`) and `members` (`MemberDao.find`).
- Writes `members` (`status='CANCELLED'`) and `payments` (`member_id`, `-refund`, `'REFUND'`, `NOW()`) via `MemberDao.saveCancellation` (`MemberDao.java:48-51`).
- Reads `membership.properties`: `refund.cutoff.days` (`30`).
- No external service calls; no scheduled jobs.

## Security & access (as found)
### Authentication
HTTP Basic against `users` table with clear-text passwords (`MemberServlet.java:85-95`, `MemberDao.java:18-28`).
### Authorization
| Action | Roles allowed today |
|---|---|
| Cancel own membership | `MEMBER` (other IDs return `403`, `MemberServlet.java:51-55`) |
| Cancel any membership, any refund | `AGENT` (no supervisor role or amount limit) |
### Accounting
Inserts a `REFUND` row into `payments`, but records no `actor` (which agent/member cancelled) and emits no audit events.

## Logging (as found)
Log4j plain text (`MemberServlet.java:76`):
`cancelMember id=<id> refund=<refund> phone=<m.phone>`
Logs member's full `phone` in clear text. No `request_id`, no JSON structured logging, no `http.request` line.

## API contract (as found)
| Method | Path | Success | Errors |
|---|---|---|---|
| POST | `/cancelMember?id={memberId}` | `200` (also `200 {"error":"Member not found"}`) | `401` (Basic challenge), `403 {"error":"Not allowed"}` |

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
| DEV-003-01 | Another member's cancellation returns `403` instead of `404` | AAA-7 | security |
| DEV-003-02 | Member's full `phone` logged in clear | LOG-4 | privacy |
| DEV-003-03 | No audit events (`membership.cancelled`, `refund.issued`) or `actor` recorded | AAA-9, AAA-10 | audit |
| DEV-003-04 | Second cancellation on `CANCELLED` member succeeds and records another refund | API-5 | business |
| DEV-003-05 | Refund rounded down to whole dollars (`Math.floor`) instead of cents | MOD-4 | business |
| DEV-003-06 | Days counted from UTC clock and 365-day year (even in leap years) | MOD-4 | business |
| DEV-003-07 | Any agent can issue any refund amount without supervisor approval | AAA-5, AAA-6 | security |

## Open questions
- [ ] (Security) Confirm `404` for other members (`DEV-003-01`), removing `phone` from logs (`DEV-003-02`), adding `membership.cancelled` / `refund.issued` audit events (`DEV-003-03`), and requiring a `supervisor` for refunds above a threshold (`DEV-003-07`).
- [ ] (Finance) Should a second cancellation be rejected with `409 ALREADY_CANCELLED` (`DEV-003-04`)?
- [ ] (Business) Should refunds continue to round down to whole dollars (`DEV-003-05`) or change to cents?
- [ ] (Business) Should day counting continue to use UTC and 365-day year (`DEV-003-06`) or use the member's time zone?
- [ ] (Business, Security) What refund threshold should require `supervisor` approval (`DEV-003-07`)?
