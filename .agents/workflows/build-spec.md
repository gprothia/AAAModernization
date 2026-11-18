---
description: Build the new service against an approved to-be spec and the harness; prove it on GKE (AGENTS.md section 5)
---

# /build-spec

Usage: `/build-spec specs/<ID>-<name>.md` (approved). Same loop as for any feature.

1. Check `status: approved` and that you're on `mod/<service>-<id-lower>` from up-to-date `main`.
2. Plan: the endpoints, data, audit events and the tests per criterion. Show it; wait for approval.
3. Tag the harness tests that prove each criterion with `@pytest.mark.ac`; add
   `@pytest.mark.deviation` and the per-target expectation for each approved deviation.
4. Write the control tests the harness can't express in `tests/api/` (audit, logs, roles).
// turbo
5. Run the harness against the new service locally (`TARGET=modern`): the new tests fail.
6. Write the code in `services/<service>/` until **all** tests pass, harness and controls.
   Never change a harness test's expected legacy result or an as-is spec to make it pass.
// turbo
7. `ruff format . && ruff check .`, `python scripts/check_spec.py`, `python scripts/check_traceability.py`.
// turbo
8. `scripts/sandbox.sh all`: legacy and new service side by side in `mod-<branch>` on GKE;
   the harness runs against both.
9. Then `/compare-legacy`. Only with both green: push, open the PR, publish the evidence.
