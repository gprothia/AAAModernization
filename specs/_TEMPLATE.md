---
id: XXX-000            # area prefix + number; a modernised capability keeps its as-is ID
title: Short capability name
status: draft          # draft | approved | implemented
owner: "@github-handle"
issue: "#123"          # the feature or modernisation request
replaces: specs/as-is/XXX-000-name.md   # only for a modernised capability; delete otherwise
---

# XXX-000: Short capability name

## Why
One or two sentences: the problem and the outcome.

## Scope
- In: ...
- Out: ...

## Acceptance criteria
<!--
One block per criterion: ### <ID>-AC<n> [api] | [ui] | [api,ui]. Never renumber.
Given / When / Then, with exact status codes, error codes, field names and values.
Include the control criteria the enterprise sections below imply (401, 403/404, audit).
For a modernised capability, mark each criterion **Parity** (same as the as-is criterion
it names) or **Deviation DEV-...** (changed by an approved decision).
-->

### XXX-000-AC1 [api]
- **Given** ...
- **When** ...
- **Then** ...

## Approved deviations
<!-- Modernised capabilities only (standards/modernization.md MOD-4, MOD-5) -->
| ID | Legacy behaviour | New behaviour | Rule | Decided by |
|---|---|---|---|---|

## Security & access (AAA)
<!-- standards/aaa.md -->
### Authentication
### Authorization
| Action | Roles allowed |
|---|---|
### Accounting
| Audit event | When | Details recorded |
|---|---|---|

## Logging
<!-- standards/logging.md -->

## API contract
<!-- standards/api.md -->
| Method | Path | Success | Errors |
|---|---|---|---|

## SLO
<!-- standards/slo.md; for a modernised capability, no worse than the legacy baseline (MOD-8) -->
```slo
p95_latency_ms: 300
error_rate_pct: 1.0
```

## Open questions
- [ ] ...
