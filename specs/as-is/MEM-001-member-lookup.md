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
Members on the website and member-services agents look up a member's current record by member ID. It returns the member's name, phone number, plan, status, expiry date, and amount paid.

## Observed behaviour

### MEM-001-B1 [api]
- **Given** Alice (`alice` / `alice`, role `MEMBER`, `member_id` `M-1001`) is signed in via HTTP Basic
- **When** she sends `GET /getMember?id=M-1001`
- **Then** HTTP `200` with JSON `{"memberId": "M-1001", "name": "Alice Ng", "phone": "+1 555 010 4455", "plan": "PLUS", "status": "ACTIVE", "expires": "12/31/2026", "paid": 124}`
- **Source:** `legacy/membership-api/src/main/java/org/aaa/membership/MemberServlet.java:26-43`, `MemberServlet.java:97-101`
- **Confidence:** medium

### MEM-001-B2 [api]
- **Given** agent Ana (`ana` / `ana`, role `AGENT`, `member_id` `NULL`) is signed in via HTTP Basic
- **When** she sends `GET /getMember?id=M-1001` (or any existing member ID)
- **Then** HTTP `200` with that member's JSON record
- **Source:** `legacy/membership-api/src/main/java/org/aaa/membership/User.java:11-13`
- **Confidence:** medium

### MEM-001-B3 [api]
- **Given** Bob (`bob` / `bob`, role `MEMBER`, `member_id` `M-1002`) is signed in via HTTP Basic
- **When** he sends `GET /getMember?id=M-1001`
- **Then** HTTP `403` with JSON `{"error": "Not allowed"}` (revealing that the record belongs to someone else rather than not existing)
- **Source:** `legacy/membership-api/src/main/java/org/aaa/membership/MemberServlet.java:31-35`
- **Confidence:** medium

### MEM-001-B4 [api]
- **Given** agent Ana is signed in via HTTP Basic
- **When** she sends `GET /getMember?id=M-9999` (unknown ID)
- **Then** HTTP `200` with JSON `{"error": "Member not found"}`
- **Source:** `legacy/membership-api/src/main/java/org/aaa/membership/MemberServlet.java:36-40`
- **Confidence:** medium

### MEM-001-B5 [api]
- **Given** no `Authorization` header, a non-Basic header, or invalid username/password
- **When** `GET /getMember?id=M-1001` is sent
- **Then** HTTP `401` with header `WWW-Authenticate: Basic realm="members"`
- **Source:** `legacy/membership-api/src/main/java/org/aaa/membership/MemberServlet.java:85-95`
- **Confidence:** medium

## Hidden behaviours
- `expires` is formatted with `SimpleDateFormat("MM/dd/yyyy")` (`MemberServlet.java:19,100`), which is US date order and uses a non-thread-safe shared `SimpleDateFormat` instance on a servlet.
- `paid` is serialized by `org.json.JSONObject` from `BigDecimal` as a JSON number rather than a two-decimal string (`MemberServlet.java:100`).
- Missing `id` query parameter (`id == null`) for an `AGENT` calls `dao.find(null)`, returning HTTP `200` with `{"error": "Member not found"}`; for a `MEMBER`, `canSee(null)` returns `false`, returning `403`.

## Data and dependencies
- Reads `users` (`username`, `password`, `role`, `member_id`) via `MemberDao.login` (`MemberDao.java:18-28`).
- Reads `members` (`member_id`, `name`, `phone`, `plan`, `status`, `expires`, `paid`) via `MemberDao.find` (`MemberDao.java:30-41`).
- No external service calls; no scheduled jobs.

## Security & access (as found)
### Authentication
HTTP Basic against `users` table with clear-text password storage and comparison (`MemberDao.java:20-24`, `MemberServlet.java:85-95`).
### Authorization
| Action | Roles allowed today |
|---|---|
| Read own record | `MEMBER` (other IDs return `403`, `User.java:11-13`) |
| Read any record | `AGENT` |
### Accounting
None. No audit table or audit log events exist.

## Logging (as found)
Log4j plain text (`MemberServlet.java:41`):
`getMember id=<id> name=<m.name> phone=<m.phone> by <user.name>`
Logs member `name` and full `phone` in clear text. No `request_id`, no JSON structured logging, no `http.request` line.

## API contract (as found)
| Method | Path | Success | Errors |
|---|---|---|---|
| GET | `/getMember?id={memberId}` | `200` (also `200 {"error":"Member not found"}`) | `401` (Basic challenge), `403 {"error":"Not allowed"}` |

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
| DEV-001-01 | Another member's record returns `403` instead of `404` | AAA-7 | security |
| DEV-001-02 | Unknown member returns HTTP `200` with `{"error": "Member not found"}` instead of `404` with standard error body | API-2, API-3 | api |
| DEV-001-03 | Member `name` and full `phone` logged in clear | LOG-4 | privacy |
| DEV-001-04 | HTTP Basic auth with clear-text passwords in DB instead of Bearer token | AAA-1, SEC-1 | security |
| DEV-001-05 | US `MM/dd/yyyy` dates (via shared `SimpleDateFormat`) and numeric `paid` instead of ISO dates and two-decimal strings | API-1 | api |
| DEV-001-06 | Unversioned verb path `/getMember`, no `X-Request-ID`, unstructured plain-text logs | API-1, API-4, LOG-1, LOG-2 | api |

## Open questions
- [ ] (Security) Confirm replacing HTTP Basic + clear-text passwords with Bearer token (`DEV-001-04`), returning `404` for other members' records (`DEV-001-01`), and removing `name` and `phone` from logs (`DEV-001-03`).
- [ ] (Business) Do any callers besides the website parse `MM/dd/yyyy` dates or numeric `paid`, or can we move to ISO `YYYY-MM-DD` and two-decimal strings (`DEV-001-05`) and `/v1/members/{id}` (`DEV-001-02`, `DEV-001-06`)?
- [ ] (Business) Should agents see masked phone numbers or full phone numbers on lookup?
