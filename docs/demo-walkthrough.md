# Demo walkthrough (about 20 minutes, nothing to run)

The story: *AAA's membership API is 15 years old. Nobody knows all its rules. Antigravity
reads all of it, writes down what it really does, proves that with tests on the old system,
lets your people decide what to keep, and builds the new GKE service against that proof.*

Open the repository on GitHub and follow the steps. Each one names the file to open and the
point to make.

## 1. The problem: legacy code nobody fully understands (2 min)

Open `legacy/membership-api/src/main/java/org/aaa/membership/RefundCalc.java`.

> "This is real-looking legacy: a refund calculation from 2017. Look at line 23: refunds are
> always rounded **down**. Was that a business rule or an accident? Nobody knows. If we rewrite
> this from a requirements document, we either break it or copy it blindly."

## 2. The rules: AAA's standards, including how to modernise (2 min)

Open `standards/modernization.md`.

> "Your standards are files. Next to AAA's security, logging and API rules, this one says how
> a modernisation must work: parity by default (MOD-1), every rule cited to its source line
> (MOD-3), every change a recorded decision (MOD-4), and the tests must pass on the **old**
> system first (MOD-6)."

Then `AGENTS.md`, the "Never" list: never change `legacy/`, never mark a rule as confirmed
before the harness proves it, never add an allowed difference without an approved deviation.

## 3. Discovery: the agent writes down what the code really does (4 min)

Open `.agents/workflows/discover-legacy.md`, step 3: *load the whole service into context at
once*. That is where Gemini's long context matters: it reads every class, the configuration
and the schema together, so it can follow a rule across files.

Open `reports/examples/discovery-summary.md`: 3 capabilities, 17 behaviours, 17 deviations,
and the "things nobody had written down".

Open `specs/as-is/MEM-003-cancel-and-refund.md`:

- `MEM-003-B1`: the refund rule, with **Source** `RefundCalc.java:13-24` and **Confidence: high**.
- `MEM-003-B3`: a second cancellation refunds again.
- "Deviations from standards": each one with its AAA rule ID (AAA-7, LOG-4, AAA-9).
- "Open questions": each one addressed to Security, Business or Finance.

> "This is the as-is spec: evidence, not wishes. Every line can be checked against the code."

## 4. Harness: proven on the old system first (3 min)

Open `tests/harness/test_mem_003.py`, `test_second_cancellation`:

> "One test, two systems. On the legacy service it expects the double refund, because that is
> what the code does today. On the new service it expects `409`, because Finance decided so,
> and the test says which decision: `DEV-003-04`."

Open `tests/harness/adapters.py` briefly: the same test calls `/cancelMember` with Basic auth on
the old system and `/v1/members/{id}/cancellation` with a token on the new one.

Open `reports/examples/harness-legacy-run.md`: 15/15 on the legacy service, and two behaviours
honestly marked "not yet confirmed".

## 5. Decisions: people decide what changes (2 min)

Open `specs/MEM-003-cancel-and-refund.md`, "Approved deviations":

> "Security fixes are mandatory under MOD-5: 404 instead of 403, masked phone numbers, an
> audit trail. Finance chose to stop double refunds. The business chose to **keep** whole-dollar
> rounding and UTC days for now: that's parity by decision, written down, with a follow-up."

Point at a criterion: `MEM-003-AC1` says **Parity** with `MEM-003-B1`; `MEM-003-AC3` says
**Deviation** `DEV-003-04`.

## 6. The new service on GKE (3 min)

Open `services/membership/app.py`, `refund_for()`:

> "The new code even keeps the legacy floating-point arithmetic, so refunds match to the dollar.
> The comments name the spec criterion or deviation behind each line."

Open `deploy/sandbox/legacy.yaml`: in the test sandbox the old and the new service run side by
side, the old one with a frozen clock so results repeat.

Open `reports/examples/parity-report.md`: 12 recorded requests, 8 identical, 4 approved
deviations, **0 unexplained**.

> "Any unexplained difference fails the PR. The only allowed differences are the decisions
> your people made."

## 7. Cut-over without a big bang (2 min)

Open `deploy/prod/route.yaml`: the gateway sends 10% of `/v1/members` traffic to the new
service and 90% to the legacy one, through a thin facade.

Open `.github/workflows/strangler-release.yml`: each step (10, 50, 100%) is started by a person,
approved in the `production` environment, measured against the SLO and the legacy baseline,
and rolled back automatically if it's over budget.

Open `reports/examples/strangler-step-10.md`: new service p95 96 ms vs legacy 310 ms.

## 8. Close (1 min)

> "Extract, prove, decide, build, compare, cut over. The agent does the reading, the writing
> and the testing; your standards decide what's allowed; your people decide what changes."

## If they ask

| Question | Show |
|---|---|
| "How do you know the spec is right?" | `MEM-003-B1` Source line, then the harness on legacy (MOD-6) |
| "What if the agent misreads the code?" | The harness fails on the legacy service, and the spec is corrected (extract-harness step 6) |
| "Can the agent just change a test to pass?" | `AGENTS.md` "Never", plus `check_traceability.py` rejecting unapproved deviations |
| "What about behaviour you can't see in code?" | `tests/golden/`: recorded real traffic, replayed to both |
| "Who can change these rules?" | `.github/CODEOWNERS` |
| "What about the other capabilities?" | MEM-002 renew: as-is done, decisions pending; harness runs on legacy only (`legacy_only`) |
