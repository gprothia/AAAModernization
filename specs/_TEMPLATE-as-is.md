---
id: MEM-000            # area prefix + number; the to-be spec keeps the same ID
title: Short capability name
kind: as-is            # as-is: what the legacy service does today (standards/modernization.md)
status: draft          # as-is specs stay draft; they are evidence, not an agreement
owner: "@github-handle"
issue: "#123"          # the modernisation request
source: legacy/<service>
---

# MEM-000: Short capability name (as-is)

## What it does today
Two or three sentences in plain words: who uses it and what it achieves.

## Observed behaviour
<!--
One block per behaviour: ### <ID>-B<n> [api] (B = observed behaviour). Never renumber.
Given / When / Then exactly as the legacy service behaves, including odd behaviour.
Every block ends with Source (file:lines) and Confidence (MOD-3):
  high   = read in the code AND confirmed by the harness on the legacy service
  medium = read in the code, not yet confirmed
  low    = inferred from config, names or data; always also an open question
-->

### MEM-000-B1 [api]
- **Given** ...
- **When** ...
- **Then** ...
- **Source:** `legacy/<service>/src/...:10-24`
- **Confidence:** high

## Hidden behaviours
Undocumented rules found in the code: rounding, dates and time zones, defaults, side effects.

## Data and dependencies
Tables and fields read or written, external calls, scheduled jobs.

## Security & access (as found)
### Authentication
### Authorization
| Action | Roles allowed today |
|---|---|
### Accounting
What is audited today, if anything.

## Logging (as found)
What is logged; any personal data in clear.

## API contract (as found)
| Method | Path | Success | Errors |
|---|---|---|---|

## Performance baseline
<!-- MOD-8: measured on the legacy service in a GKE sandbox with tools/loadgen -->
```baseline
p95_latency_ms: 0
error_rate_pct: 0
```

## Deviations from standards
<!-- MOD-4: every place the legacy breaks a standard or behaves oddly -->
| ID | Behaviour | Rule | Kind |
|---|---|---|---|
| DEV-000-01 | ... | AAA-7 | security |

## Open questions
<!-- One per deviation and per low-confidence rule: keep (parity) or change? -->
- [ ] (Security) ...
- [ ] (Business) ...
