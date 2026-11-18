# Service levels and releases

## Every capability has an SLO
- SLO-1. Each spec has an **SLO** section with a machine-readable block:

  ```slo
  p95_latency_ms: 300
  error_rate_pct: 1.0
  ```

  `p95_latency_ms`: 95% of requests finish within this time. `error_rate_pct`: share of
  requests that may fail with a `5xx`. Defaults if a capability has no special need: 300 ms, 1%.
- SLO-2. For a modernised service the SLO is **at least as good as the legacy baseline**
  measured during discovery (`standards/modernization.md`, MOD-8).

## Releases replace the change board for standard changes
- SLO-3. A **standard change** is a merged PR whose specs pass `check_spec.py`, whose tests
  and parity report passed in its GKE sandbox, which has no `needs-approval` label, and which
  touches none of `standards/`, `deploy/prod/`, `.github/CODEOWNERS` or the release gate.
- SLO-4. Standard changes go to production as a **canary**: about 10% of traffic for a
  fixed window, judged against the spec's SLO. For a modernised service the canary is the
  strangler step: traffic moves from the legacy service to the new one (MOD-9).
- SLO-5. Within budget: promoted automatically. Over budget: rolled back automatically, and
  the SRE agent opens a root-cause PR. Anything that is not a standard change still needs a
  named approver in the GitHub `production` environment.
