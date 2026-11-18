---
id: MEM-001
title: Member lookup
kind: as-is
status: draft
owner: "@gprothia"
issue: "#1"
source: legacy/membership-api
---

# MEM-001: Member lookup (as-is)

## What it does today
Members look up their own membership on the website; member-services agents look up any
member at the desk. One call returns the member's details, plan, expiry date and phone.

## Observed behaviour

### MEM-001-B1 [api]
- **Given** Alice (member `M-1001`) is signed in
- **When** she calls `GET /getMember?id=M-1001`
- **Then** `200` with `memberId`, `name`, `phone`, `plan` `PLUS`, `status` `ACTIVE`, `expires` `12/31/2026`, `paid` `124.0`
- **Source:** `legacy/membership-api/src/main/java/org/aaa/membership/MemberServlet.java:26-43`, `:97-101`
- **Confidence:** high (harness: `test_member_reads_own_record`)

### MEM-001-B2 [api]
- **Given** agent Ana is signed in
- **When** she looks up any member
- **Then** `200` with that member's details
- **Source:** `legacy/membership-api/src/main/java/org/aaa/membership/User.java:11-12`
- **Confidence:** high (harness: `test_agent_reads_any_record`)

### MEM-001-B3 [api]
- **Given** Bob (member `M-1002`) is signed in
- **When** he looks up Alice (`M-1001`)
- **Then** `403` with body `{"error": "Not allowed"}`, which tells him the record exists
- **Source:** `legacy/membership-api/src/main/java/org/aaa/membership/MemberServlet.java:31-35`
- **Confidence:** high (harness: `test_member_cannot_read_another_record`)

### MEM-001-B4 [api]
- **Given** an agent is signed in
- **When** she looks up an ID that does not exist
- **Then** `200` (not 404) with body `{"error": "Member not found"}`
- **Source:** `legacy/membership-api/src/main/java/org/aaa/membership/MemberServlet.java:36-40`
- **Confidence:** high (harness: `test_unknown_member`)

### MEM-001-B5 [api]
- **Given** no credentials, or a wrong password
- **When** any endpoint is called
- **Then** `401` with `WWW-Authenticate: Basic` and an HTML error page
- **Source:** `legacy/membership-api/src/main/java/org/aaa/membership/MemberServlet.java:85-95`
- **Confidence:** high (harness: `test_sign_in_required`)

## Hidden behaviours
- Dates are returned as US text `MM/dd/yyyy`, not ISO dates.
- Amounts are JSON numbers with one decimal place (`124.0`), not strings with cents.
- The phone number is returned to agents and members alike, unmasked.

## Data and dependencies
Reads `members` (name, phone, plan, status, expires, paid) and `users` for sign-in. No external calls.

## Security & access (as found)
### Authentication
HTTP Basic. Passwords are stored and compared in clear text (`legacy/membership-api/src/main/java/org/aaa/membership/MemberDao.java:18-27`).
### Authorization
| Action | Roles allowed today |
|---|---|
| Look up own record | MEMBER |
| Look up any record | AGENT |
### Accounting
Nothing is audited.

## Logging (as found)
Every lookup logs the member's ID, **name and full phone number** and the user who asked
(`legacy/membership-api/src/main/java/org/aaa/membership/MemberServlet.java:41`). Plain text through log4j.

## API contract (as found)
| Method | Path | Success | Errors |
|---|---|---|---|
| GET | /getMember?id= | 200 | 401 (HTML), 403 `{"error"}`, not found = 200 `{"error"}` |

## Performance baseline
<!-- Example values; replace with the first measured run (reports/examples/discovery-summary.md) -->
```baseline
p95_latency_ms: 180
error_rate_pct: 0.2
```

## Deviations from standards
| ID | Behaviour | Rule | Kind |
|---|---|---|---|
| DEV-001-01 | Another member's record gives 403, revealing it exists | AAA-7 | security |
| DEV-001-02 | Unknown member gives 200 with `{"error"}` | API-2, API-3 | api |
| DEV-001-03 | Name and full phone number logged on every lookup | LOG-4 | privacy |
| DEV-001-04 | HTTP Basic with clear-text passwords | AAA-1, SEC-1 | security |
| DEV-001-05 | No audit of who looked at which member | AAA-9 | audit |
| DEV-001-06 | US date text and float amounts | API (data formats) | api |

## Open questions
- [ ] (Security) DEV-001-01, -03, -04, -05 are security fixes (MOD-5): confirm no exception is needed.
- [ ] (Business) Do any other systems parse `MM/dd/yyyy` dates or the `{"error"}` body? If so they need the new format before cut-over.
- [ ] (Business) Should agents see the full phone number, or the last two digits unless they click "reveal" (audited)?
