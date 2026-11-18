<!-- Example output of /discover-legacy #1, posted as a comment on the modernisation request -->
### Discovery: legacy/membership-api

Read in one pass: 7 Java classes (287 lines), `web.xml`, `membership.properties`, `seed.sql`, `pom.xml`.

| Capability | As-is spec | Behaviours | Confidence (high / medium / low) | Deviations |
|---|---|---|---|---|
| Member lookup | `specs/as-is/MEM-001-member-lookup.md` | 5 | 5 / 0 / 0 | 6 |
| Renew membership | `specs/as-is/MEM-002-renew-membership.md` | 5 | 3 / 1 / 1 | 4 |
| Cancel and refund | `specs/as-is/MEM-003-cancel-and-refund.md` | 7 | 6 / 1 / 0 | 7 |

**17 deviations:** security 3 · privacy 3 · audit 3 · api 2 · business 6 (one, agent refund limits, is also a security question)

**Things nobody had written down**
- Refunds are rounded **down** to whole dollars (`RefundCalc.java:23`).
- A second cancellation **refunds again** (`MemberServlet.java:75`, `MemberDao.java:48-51`).
- Days are counted on the server's UTC clock, so a member cancelling in the evening in California loses a day (`RefundCalc.java:14-15`).
- The renewal grace rule only checks `status`, not the expiry date (`RenewalService.java:29`).
- Phone numbers and the `card` parameter are logged in clear (`MemberServlet.java:41, 66, 76`).

**Legacy baseline** (synthetic traffic, GKE sandbox): lookup p95 180 ms · renew p95 260 ms · cancel p95 310 ms.

**12 open questions:** 3 for Security, 7 for Business, 1 for Finance, 1 for Business and Security together. Please answer here, one comment per question.
