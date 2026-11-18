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
A member (online) or an agent (at the desk) renews a membership for one more year and the
plan's price is charged. Members on autopay get 5% off.

## Observed behaviour

### MEM-002-B1 [api]
- **Given** Bob's `CLASSIC` membership is `ACTIVE` and expires `03/31/2026`
- **When** he calls `POST /renewMember` with `id=M-1002`
- **Then** `200` with `expires` `03/31/2027` and `charged` `69`
- **Source:** `legacy/membership-api/src/main/java/org/aaa/membership/RenewalService.java:19-44`, `legacy/membership-api/src/main/resources/membership.properties:2-4`
- **Confidence:** high (harness: `test_active_renewal_continues_term`)

### MEM-002-B2 [api]
- **Given** Alice's `PLUS` membership (124)
- **When** she renews with `autopay=true`
- **Then** `charged` is `117.80`: 5% off, rounded half-up to the cent
- **Source:** `legacy/membership-api/src/main/java/org/aaa/membership/RenewalService.java:34-38`
- **Confidence:** high (harness: `test_autopay_discount`)

### MEM-002-B3 [api]
- **Given** Cara's `PREMIER` membership is `LAPSED` since `09/15/2025`, more than 30 days ago
- **When** an agent renews it on 2026-03-10
- **Then** the new year starts **today**: `expires` `03/10/2027`, `charged` `164`
- **Source:** `legacy/membership-api/src/main/java/org/aaa/membership/RenewalService.java:24-31`
- **Confidence:** high (harness: `test_long_lapsed_renewal_starts_today`)

### MEM-002-B4 [api]
- **Given** a membership whose `status` is still `ACTIVE` but which expired more than 30 days ago (the nightly lapse job has not run)
- **When** it is renewed
- **Then** the new year continues from the **old** expiry date: the grace rule only looks at `status`
- **Source:** `legacy/membership-api/src/main/java/org/aaa/membership/RenewalService.java:29`
- **Confidence:** medium (read in the code; no seeded member in this state yet)

### MEM-002-B5 [api]
- **Given** a membership expiring on 29 February
- **When** it is renewed
- **Then** the new expiry is 28 February of the next year
- **Source:** `legacy/membership-api/src/main/java/org/aaa/membership/RenewalService.java:32` (`Calendar.add(YEAR, 1)`)
- **Confidence:** low (inferred from Java's Calendar behaviour)

## Hidden behaviours
- "Today" is the server's date (UTC in the data centre), not the member's.
- Prices live in `membership.properties` and are edited by hand each January.
- No payment provider is called here: the charge is only recorded in `payments`.

## Data and dependencies
Reads and writes `members` (status, expires, paid); inserts into `payments` (`RENEWAL`).

## Security & access (as found)
### Authentication
HTTP Basic (see MEM-001).
### Authorization
| Action | Roles allowed today |
|---|---|
| Renew own membership | MEMBER |
| Renew any membership | AGENT |
### Accounting
Nothing is audited.

## Logging (as found)
Logs the amount and the **`card` request parameter in clear** (`legacy/membership-api/src/main/java/org/aaa/membership/MemberServlet.java:66`).

## API contract (as found)
| Method | Path | Success | Errors |
|---|---|---|---|
| POST | /renewMember (`id`, `autopay`) | 200 | 401, 403, not found = 200 `{"error"}` |

## Performance baseline
```baseline
p95_latency_ms: 260
error_rate_pct: 0.4
```

## Deviations from standards
| ID | Behaviour | Rule | Kind |
|---|---|---|---|
| DEV-002-01 | Card parameter logged in clear | LOG-4, SEC-1 | privacy |
| DEV-002-02 | No audit of renewals or charges | AAA-9 | audit |
| DEV-002-03 | Grace rule ignores the expiry date when `status` is stale (B4) | none | business |
| DEV-002-04 | Server UTC date used as "today" | none | business |

## Open questions
- [ ] (Security) DEV-002-01, -02 are security fixes (MOD-5): confirm.
- [ ] (Business) DEV-002-03: keep the stale-status behaviour, or apply the grace rule by date?
- [ ] (Business) DEV-002-04: keep UTC, or use the member's home time zone?
- [ ] (Business) B5 (low confidence): is 28 February the intended renewal date for 29 February memberships?
