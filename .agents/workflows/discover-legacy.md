---
description: Read a legacy service end to end and write its as-is specs (rules in AGENTS.md section 2)
---

# /discover-legacy

Usage: `/discover-legacy #<modernisation request>`. Follow `AGENTS.md` and
`standards/modernization.md`. Never change anything under `legacy/`.

## 1. Gather
// turbo
1. `gh issue view <n> --comments`: which service, why, any known problems or decisions.
// turbo
2. Read `standards/` (all files), `specs/_TEMPLATE-as-is.md`, and the existing specs.
3. Load the **whole** legacy service into context at once: code, configuration, schema,
   build files, any docs (`legacy/<service>/**`). Use long context; don't sample files.

## 2. Map it
4. Write an inventory to `.tmp/discovery.md`: every endpoint or entry point, data read and
   written, external calls, scheduled jobs, configuration values, and the capabilities they
   add up to (one capability = one future spec, e.g. lookup, renew, cancel and refund).
5. For each capability, trace every code path and list each behaviour as Given/When/Then with
   exact values. Include the odd ones: rounding, dates and time zones, defaults, repeated
   requests, errors returned as success, missing checks.
6. For every behaviour, record **Source** (file:lines) and **Confidence** (MOD-3). Mark `high`
   only after `/extract-harness` has confirmed it; until then the most is `medium`.

## 3. Compare with the standards
7. Check each capability against every standard (AAA, API, logging, security, code style,
   SLO). Every gap is a row in "Deviations from standards" with the rule ID and a kind:
   security, privacy, audit, api or business (MOD-4).
8. Write one open question per deviation and per `low` behaviour, addressed to the owner
   who decides: Security for AAA/LOG/SEC rules (MOD-5), Business or Finance for the rest.

## 4. Write and share
9. One file per capability: `specs/as-is/<ID>-<name>.md` from the as-is template,
   `kind: as-is`, `status: draft`, `issue` = the request.
// turbo
10. `python scripts/check_spec.py`: fix anything it reports.
11. Show the user a summary: capabilities, behaviours by confidence, deviations by kind,
    open questions by owner. Wait for their OK.
12. Commit on `mod/<service>-discovery`, `git push -u origin HEAD`, then comment on the issue
    with the summary and links. Show the comment text first.
