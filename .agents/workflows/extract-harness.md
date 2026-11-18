---
description: Write characterisation tests from the as-is specs and prove them on the legacy service (MOD-6, MOD-7)
---

# /extract-harness

Usage: `/extract-harness specs/as-is/<ID>-<name>.md` (or all as-is specs of a service).

## 1. Write the tests
1. For each behaviour, a test in `tests/harness/test_<id-lower>.py`, tagged
   `@pytest.mark.behaviour("<ID>-Bn")`. Call the service only through
   `tests/harness/adapters.py` (`svc.lookup`, `svc.renew`, `svc.cancel`; add adapter methods
   for new capabilities). Assert exact values from the spec.
2. If the adapter needs a new operation, add it for **both** systems (MOD-7).
3. Use the seed data and the frozen clock; add seed rows to `legacy/<service>/db/seed.sql`
   only through a reviewed change to the sandbox seed, never to the legacy code.

## 2. Prove them on the legacy service
// turbo
4. `scripts/sandbox.sh legacy up`: legacy service in `mod-<branch>` on GKE with its reset sidecar.
// turbo
5. `TARGET=legacy scripts/sandbox.sh harness`: run the harness against the legacy service.
6. **Every test must pass on the legacy.** A failing test means the spec misread the code:
   fix the as-is spec and the test together, never the legacy service. Repeat until green.
7. Upgrade each confirmed behaviour to `Confidence: high` with the test's name.
// turbo
8. `python scripts/check_traceability.py`: every `high` behaviour has a test.

## 3. Baseline and evidence
// turbo
9. `scripts/sandbox.sh baseline`: synthetic traffic against the legacy service; write the
   measured p95 and error rate into each spec's `baseline` block (MOD-8).
10. Optionally record and scrub real traffic samples into `tests/golden/` (no personal data).
11. Commit, push, open a PR "Harness for <service>". Post the harness report (every test,
    its behaviour, green on legacy) and the baseline as PR comments. Show them first.
