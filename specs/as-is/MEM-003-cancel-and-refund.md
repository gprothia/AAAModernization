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
A member or an agent cancels a membership; the unused part of the year is refunded pro
rata. Added in 2017. Finance reconciles refunds from the `payments` table each month.

## Observed behaviour

### MEM-003-B1 [api]
- **Given** Alice paid `124` for a membership expiring `12/31/2026`, and today is 2026-03-10
- **When** she calls `POST /cancelMember` with `id=M-1001`
- **Then** `200` with `refund` `100`: 124 / 365 x 295 days left = 100.22, **rounded down to whole dollars**
- **Source:** `legacy/membership-api/src/main/java/org/aaa/membership/RefundCalc.java:13-24`
- **Confidence:** high (harness: `test_refund_is_pro_rata_rounded_down`)

### MEM-003-B2 [api]
- **Given** Bob's membership expires in 20 days
- **When** he cancels
- **Then** `refund` `0`: no refund within 30 days of expiry (`refund.cutoff.days`)
- **Source:** `legacy/membership-api/src/main/java/org/aaa/membership/RefundCalc.java:17-20`
- **Confidence:** high (harness: `test_no_refund_near_expiry`)

### MEM-003-B3 [api]
- **Given** Alice's membership was already cancelled and refunded
- **When** the cancellation is sent again
- **Then** `200` and a **second** refund of `100` is recorded
- **Source:** `legacy/membership-api/src/main/java/org/aaa/membership/MemberServlet.java:72-78`, `legacy/membership-api/src/main/java/org/aaa/membership/MemberDao.java:48-51`
- **Confidence:** high (harness: `test_second_cancellation`)

### MEM-003-B4 [api]
- **Given** Bob is signed in
- **When** he cancels Alice's membership
- **Then** `403` `{"error": "Not allowed"}`
- **Source:** `legacy/membership-api/src/main/java/org/aaa/membership/MemberServlet.java:51-55`
- **Confidence:** high (harness: `test_member_cannot_cancel_another`)

### MEM-003-B5 [api]
- **Given** agent Ana is signed in
- **When** she cancels any member's membership
- **Then** the refund is paid whatever the amount; no second person approves it
- **Source:** `legacy/membership-api/src/main/java/org/aaa/membership/MemberServlet.java:73`
- **Confidence:** high (harness: `test_agent_cancels_any_member`)

### MEM-003-B6 [api]
- **Given** a cancellation late in the evening, US time
- **When** the refund is calculated
- **Then** days left are counted from the server's clock (UTC) and truncated, so the member may get one day less
- **Source:** `legacy/membership-api/src/main/java/org/aaa/membership/RefundCalc.java:14-15`
- **Confidence:** high (harness: `test_days_counted_in_utc_with_365_day_year`, clock 2026-03-11 01:00 UTC gives 99, not 100)

### MEM-003-B7 [api]
- **Given** a cancellation in a leap year
- **When** the refund is calculated
- **Then** the daily rate still divides by 365
- **Source:** `legacy/membership-api/src/main/java/org/aaa/membership/RefundCalc.java:22`
- **Confidence:** medium (read in the code; the seed data has no leap-year case yet)

## Hidden behaviours
- Refunds are whole dollars, always rounded down; the cents are kept by AAA.
- Status `CANCELLED` is set, but nothing stops a second cancellation from refunding again.
- The refund is stored as a negative `REFUND` payment; there is no refund ID.

## Data and dependencies
Reads `members`; updates `members.status`; inserts into `payments` (`REFUND`). Finance's monthly reconciliation reads `payments`.

## Security & access (as found)
### Authentication
HTTP Basic (see MEM-001).
### Authorization
| Action | Roles allowed today |
|---|---|
| Cancel own membership | MEMBER |
| Cancel any membership, any refund amount | AGENT |
### Accounting
Nothing is audited; only the `payments` row shows a refund happened, not who issued it.

## Logging (as found)
Logs the member ID, refund and **full phone number** (`legacy/membership-api/src/main/java/org/aaa/membership/MemberServlet.java:76`).

## API contract (as found)
| Method | Path | Success | Errors |
|---|---|---|---|
| POST | /cancelMember (`id`) | 200 | 401, 403, not found = 200 `{"error"}`; repeat = 200 (refunds again) |

## Performance baseline
```baseline
p95_latency_ms: 310
error_rate_pct: 0.6
```

## Deviations from standards
| ID | Behaviour | Rule | Kind |
|---|---|---|---|
| DEV-003-01 | Another member's cancellation gives 403, revealing the record exists | AAA-7 | security |
| DEV-003-02 | Full phone number logged | LOG-4 | privacy |
| DEV-003-03 | No audit of who cancelled or refunded | AAA-9 | audit |
| DEV-003-04 | A repeated cancellation refunds again | API-5 (invalid state change gets 409) | business, finance |
| DEV-003-05 | Refund rounded down to whole dollars | none | business |
| DEV-003-06 | Days counted in server UTC | none | business |
| DEV-003-07 | Any agent may refund any amount | AAA-5 (roles per action) | business, security |

## Open questions
- [ ] (Security) DEV-003-01, -02, -03 are security fixes (MOD-5): confirm.
- [ ] (Finance) DEV-003-04: reject a second cancellation with 409?
- [ ] (Business) DEV-003-05: keep rounding down to whole dollars, or refund to the cent?
- [ ] (Business) DEV-003-06: keep UTC, or use the member's home time zone?
- [ ] (Business, Security) DEV-003-07: should refunds above a limit need a supervisor?
