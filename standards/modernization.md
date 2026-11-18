# Modernising legacy services

These rules apply when an existing service is rebuilt, not when a new feature is added. They
sit on top of every other standard: a modernised service meets AAA, API, logging, security,
code-style and SLO standards like any new service.

## Discover before you build
- MOD-1. **Behaviour parity by default.** The new service does what the legacy service does,
  including odd behaviour that members or other systems may rely on, unless a person decides
  otherwise (MOD-4).
- MOD-2. **As-is specs come first.** Discovery writes one as-is spec per capability under
  `specs/as-is/` (template `specs/_TEMPLATE-as-is.md`), describing what the code does today,
  not what anyone thinks it should do.
- MOD-3. **Every extracted rule cites its source**: the file and line range it was read
  from, and a confidence level: `high` (read in the code and confirmed by the harness on the
  legacy service), `medium` (read in the code, not yet confirmed) or `low` (inferred from
  configuration, names or data). A `low` rule is always an open question.

## Decide every change
- MOD-4. **Every deviation is a decision.** Where the legacy service breaks a standard, or
  behaves oddly, the as-is spec lists it with the rule ID. The to-be spec keeps it (parity)
  or changes it, and each change is recorded as an **approved deviation** with who decided.
- MOD-5. Security, privacy and audit deviations (AAA, LOG, SEC rules) are **always fixed**
  unless the Security owner records an exception. Business-rule deviations (rounding, dates,
  limits) are decided by the business owner.

## Prove it against the old system
- MOD-6. **The harness is proven on the legacy first.** Characterisation tests under
  `tests/harness/` must pass 100% against the legacy service before any new code is written.
  A test that only passes against the new service proves nothing about parity.
- MOD-7. **Same tests, both systems.** Harness tests describe behaviour, not URLs: they call
  the service through an adapter (`tests/harness/adapters.py`), so one test runs against
  both the legacy and the new API. An approved deviation is the only reason a test may
  expect different results per target (`@pytest.mark.deviation`).
- MOD-8. **Measure the baseline.** Discovery records the legacy service's p95 latency and
  error rate under the same synthetic traffic; the new service's SLO is no worse.

## Move traffic gradually
- MOD-9. **Strangler releases.** The new service takes traffic in steps (10%, 50%, 100%)
  through the gateway, judged at each step against its SLO and the legacy baseline. Any step
  over budget rolls traffic back to the legacy service automatically.
- MOD-10. **Differential testing before each step.** Recorded legacy traffic
  (`tests/golden/`) is replayed to both services; responses must match except for the
  approved deviations (`tests/golden/allowed_differences.yaml`). Zero unexplained differences.
- MOD-11. The legacy service is retired only after 100% of traffic has run on the new one
  for an agreed period, with a person's approval.
