# Legacy membership API (as found)

The service AAA's member-services desk and the website have used since 2011 to look up
members, renew memberships and cancel them with a refund. Java 8 servlets on Tomcat 7, a
JDBC database, configuration in `membership.properties`. Nobody on the current team wrote it.

**This folder is read-only.** It is the evidence for discovery (`/discover-legacy`) and the
system the characterisation harness is proven against (`standards/modernization.md`, MOD-6).
Do not fix anything here: every fix happens in the new service, as an approved deviation.

| Endpoint | What it does |
|---|---|
| `GET /getMember?id=<memberId>` | Member details, plan, expiry date, phone |
| `POST /renewMember` (`id`, `autopay`) | Adds a year to the membership and charges the price |
| `POST /cancelMember` (`id`) | Cancels and refunds the unused part of the year |

Sign-in is HTTP Basic against the `users` table: members see their own record, agents see
everyone's. A small Dockerfile (`Dockerfile`) runs it in a GKE sandbox so the harness can
call it; nothing else about it changes.
