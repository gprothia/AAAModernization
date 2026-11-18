---
description: Prove the new service behaves like the legacy one, except for approved deviations (MOD-10)
---

# /compare-legacy

Usage: `/compare-legacy` on a branch whose GKE sandbox has both services running.

// turbo
1. `TARGET=legacy` and `TARGET=modern` harness runs in the sandbox; both must be green.
// turbo
2. `python tools/compare_legacy.py --legacy <legacy url> --modern <new url> --md reports/parity.md`:
   replays `tests/golden/` to both and diffs normalised responses.
3. Read the report. An **unexplained** difference is a bug in the new service or a missing
   decision: fix the code, or stop and ask the user to raise it on the issue. Never add an
   entry to `tests/golden/allowed_differences.yaml` without an approved deviation in a spec.
4. Show the user the summary line ("N requests, N identical, N approved, 0 unexplained"),
   then post the report on the PR (`scripts/sandbox.sh publish`).
