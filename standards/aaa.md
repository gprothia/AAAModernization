# AAA: Authentication, Authorization, Accounting

## Authentication: who are you?
- AAA-1. Every `/v1` endpoint requires `Authorization: Bearer <token>`, except sign-in.
  Missing or invalid token: `401` with code `UNAUTHENTICATED`.
- AAA-2. Tokens expire (8 hours here). An expired token is treated as missing.
- AAA-3. Demo only: `POST /v1/auth/demo-login` issues a token for a seeded user. In
  production the company identity provider (SSO) issues it; nothing else changes.
- AAA-4. On GKE, services are private to the cluster: only the gateway and named callers may
  reach them (Kubernetes NetworkPolicy). Nothing is exposed with a public load balancer.

## Authorization: what may you do?
- AAA-5. Deny by default. Each endpoint lists the roles allowed; any other role gets `403`
  with code `FORBIDDEN`.
- AAA-6. Roles: `member` (a customer), `agent` (member-services staff) and `supervisor`
  (staff who may approve money movements such as refunds).
- AAA-7. Never reveal that someone else's record exists: a member asking for another
  member's record gets `404`, not `403`.
- AAA-8. Every spec has an **Authorization** table: action → roles.

## Accounting: what did you do?
- AAA-9. Every sign-in and every change writes an audit event: `event`, `actor`, `target`,
  `at`, `request_id`, and what changed.
- AAA-10. Audit events are also written to the log (`event: "audit"`), so they reach the
  central log store. Supervisors can read them at `GET /v1/audit`.
- AAA-11. Event names are `<thing>.<past-tense verb>`: `membership.renewed`, `refund.issued`.
