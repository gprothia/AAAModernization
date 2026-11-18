# AAA Modernization: legacy service → spec → GKE microservice

A worked example of modernising a legacy AAA service with **Antigravity** and **Gemini's long
context**, the spec-driven way:

1. **Extract** the behavioural specification from the legacy code: what it really does,
   quirks included, every rule cited to its source line.
2. **Prove** it with a characterisation harness that passes against the legacy service.
3. **Decide** every difference from AAA's standards: keep it, or change it.
4. **Build** the new GKE microservice until the **same harness** passes.
5. **Compare** both systems on recorded traffic, then move traffic over step by step.

The example service is the **membership API** (look up, renew, cancel and refund), a Java 8
servlet app from 2011 with the kind of behaviour real legacy systems have: refunds rounded
down, a double-refund bug, phone numbers in the logs, and dates counted in UTC.

> This repository is a static demo. Nothing has been deployed or run; the files under
> `reports/examples/` show what the workflows produce.

## The journey, and where each part lives

| Step | What happens | Where it is |
|---|---|---|
| Rules | AAA's standards, plus the modernisation rules MOD-1..MOD-11 | [`standards/`](standards/), [`standards/modernization.md`](standards/modernization.md) |
| Agent rulebook | What agents must and must never do | [`AGENTS.md`](AGENTS.md) |
| Legacy code | The service as found, read-only | [`legacy/membership-api/`](legacy/membership-api/) |
| Request | One modernisation issue per service | [`.github/ISSUE_TEMPLATE/modernization-request.yml`](.github/ISSUE_TEMPLATE/modernization-request.yml) |
| 1. Discover | Whole service read in long context → as-is specs | [`/discover-legacy`](.agents/workflows/discover-legacy.md) → [`specs/as-is/`](specs/as-is/) |
| 2. Harness | Behaviour tests that run on both systems, proven on legacy first | [`/extract-harness`](.agents/workflows/extract-harness.md) → [`tests/harness/`](tests/harness/) |
| 3. Decide | Parity or change, per deviation, by its owner | issue comments → [`/to-be-spec`](.agents/workflows/to-be-spec.md) → [`specs/MEM-003-cancel-and-refund.md`](specs/MEM-003-cancel-and-refund.md) |
| 4. Build | New service until harness and AAA controls pass | [`/build-spec`](.agents/workflows/build-spec.md) → [`services/membership/`](services/membership/), [`tests/api/`](tests/api/) |
| 5. Compare | Recorded legacy traffic replayed to both | [`/compare-legacy`](.agents/workflows/compare-legacy.md) → [`tools/compare_legacy.py`](tools/compare_legacy.py), [`tests/golden/`](tests/golden/) |
| Checks | Every PR, independently, on GKE | [`.github/workflows/modernization-checks.yml`](.github/workflows/modernization-checks.yml) |
| 6. Cut over | Gateway moves traffic 10 → 50 → 100%, approved per step | [`/cutover`](.agents/workflows/cutover.md), [`strangler-release.yml`](.github/workflows/strangler-release.yml), [`deploy/prod/route.yaml`](deploy/prod/route.yaml) |

## One rule, end to end

The legacy service refunds twice if a cancellation is sent twice:

- **Legacy code:** [`MemberServlet.java:75`](legacy/membership-api/src/main/java/org/aaa/membership/MemberServlet.java) saves a refund with no check for an earlier one.
- **As-is spec:** behaviour `MEM-003-B3`, deviation `DEV-003-04`, open question for Finance.
- **Harness:** `test_second_cancellation` passes on the legacy service (it does refund twice).
- **Decision:** Finance answers on the issue: reject it.
- **To-be spec:** `MEM-003-AC3`, **Deviation** `DEV-003-04`: `409 ALREADY_CANCELLED`.
- **New service:** [`services/membership/app.py`](services/membership/app.py), `cancel()`.
- **Same test, new service:** `test_second_cancellation` expects `conflict` on the new target.
- **Parity report:** request `g-009` is an *approved deviation*, not a failure.

## Checks you can run without any cloud

```
python scripts/check_spec.py          # as-is and to-be specs follow the rules
python scripts/check_traceability.py  # every behaviour/criterion tested, every deviation approved
```

## Demo

[`docs/demo-walkthrough.md`](docs/demo-walkthrough.md): what to open, in which order, and what to say.
