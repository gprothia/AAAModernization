---
description: Turn an as-is spec plus the people's decisions into an approved to-be spec (MOD-4, MOD-5)
---

# /to-be-spec

Usage: `/to-be-spec specs/as-is/<ID>-<name>.md`.

1. Read the as-is spec and the modernisation issue with all its comments. Decisions come
   from the issue only. Any open question without an answer: stop and list it for the user.
2. Copy `specs/_TEMPLATE.md` to `specs/<ID>-<name>.md` (same ID), `replaces:` the as-is spec.
3. For every behaviour, write a to-be criterion marked **Parity** with `<ID>-Bn`, or
   **Deviation** `DEV-...` where a decision changes it. Security, privacy and audit
   deviations are always fixed unless the issue records a Security exception (MOD-5).
4. Add the control criteria the standards require (401, 403/404, audit, log masking).
5. Fill the "Approved deviations" table: legacy behaviour, new behaviour, rule, who decided
   and where (issue comment). List the behaviours kept for parity by decision.
6. Write the enterprise sections in the new contract (AAA, Logging, API contract) and an SLO
   no worse than the baseline (MOD-8).
// turbo
7. `python scripts/check_spec.py` and `python scripts/check_traceability.py`.
8. Show the user the deviations table and the parity list. When they approve, set
   `status: approved`, commit, push, and comment on the issue. Show the comment first.
