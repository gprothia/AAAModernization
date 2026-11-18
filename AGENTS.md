# AGENTS.md: the rulebook for coding agents

Antigravity, Gemini CLI and other agents read this file first. The saved commands in
`.agents/workflows/` list the steps; this file and `standards/` are the rules they follow.

**This repo:** modernising AAA's legacy **membership API** (`legacy/membership-api`, Java 8
servlets) into a new **membership service on GKE** (`services/membership`), by first
extracting what the legacy code really does, proving it with tests, and only then building
the replacement against that proof.

## The cycle

```
modernisation request (GitHub issue)
  → discovery: whole legacy service read in long context      /discover-legacy #<issue>
      → as-is specs: every behaviour with source and confidence, every deviation from standards
  → harness: characterisation tests, proven 100% on the legacy  /extract-harness
  → people decide each deviation: keep (parity) or change      (comments on the issue)
  → to-be spec: parity + approved deviations + AAA controls    /to-be-spec
  → new service built until the SAME harness passes            /build-spec
  → parity: recorded legacy traffic replayed to both           /compare-legacy
  → PR checks re-run everything on GKE → a person merges
  → strangler release: 10% → 50% → 100% of traffic, approved per step   /cutover
```

## Never
- Change anything under `legacy/`. It is evidence. Fixes happen in `services/`, as approved deviations.
- Mark a behaviour `Confidence: high` before the harness has passed it on the legacy service.
- Change a harness test's expected **legacy** result to make the new service pass.
- Add an entry to `tests/golden/allowed_differences.yaml`, or a `@pytest.mark.deviation`,
  without an approved deviation in a to-be spec.
- Take a decision the issue doesn't contain: ask, or write it as an open question.
- Change `standards/`, approve a release, or change production traffic weights.
- Commit to `main`, merge, or post an issue, comment or PR before showing the user its text.

---

## 0. Standards come first
Read `standards/README.md` and every file it lists, `modernization.md` above all, before
discovery, specs or code. Quote rule IDs (AAA-7, LOG-4, MOD-6) where they decide something.

## 1. Modernisation request
One GitHub issue per legacy service, from the "Modernisation request" form: why, who uses
it, known problems, constraints. All decisions about the migration are recorded as comments
on that issue.

## 2. Discovery and as-is specs (MOD-1..MOD-4)
- Read the **whole** service at once: code, configuration, schema, build files.
- One as-is spec per capability: `specs/as-is/<ID>-<name>.md` from `specs/_TEMPLATE-as-is.md`.
- Each behaviour is `### <ID>-B<n> [api]`, Given/When/Then with exact values, plus
  **Source** (`file:lines`) and **Confidence** (`high` | `medium` | `low`).
- Every gap against a standard is a row in "Deviations from standards" with the rule ID.
  Every deviation and every `low` behaviour gets an open question for its owner.
- `scripts/check_spec.py` enforces this.

## 3. Characterisation harness (MOD-6, MOD-7)
- Tests in `tests/harness/test_<id-lower>.py`, tagged `@pytest.mark.behaviour("<ID>-Bn")`.
- Call the service only through `tests/harness/adapters.py`, so one test runs on both systems.
- Proven on the legacy service first, in a GKE sandbox (`scripts/sandbox.sh harness` with
  `TARGET=legacy`). A failing test means the spec misread the code: fix the spec and the test.

## 4. To-be specs (MOD-4, MOD-5)
- `specs/<ID>-<name>.md` from `specs/_TEMPLATE.md`, same ID, `replaces:` the as-is spec.
- Each criterion is **Parity** with `<ID>-Bn` or **Deviation** `DEV-...`; every deviation is
  in "Approved deviations" with who decided. Security, privacy and audit deviations are
  always fixed unless Security records an exception.
- The SLO is no worse than the legacy baseline (MOD-8).

## 5. Build and prove
Gates before a PR, in order:
1. `python scripts/check_spec.py` and `python scripts/check_traceability.py` pass.
2. `ruff format . && ruff check .` pass.
3. Harness and `tests/api` green against the new service locally.
4. Commit everything (the sandbox refuses uncommitted changes).
5. `scripts/sandbox.sh all`: legacy and new service side by side in `mod-<branch>` on GKE;
   harness green on **both**; control tests green on the new one.
6. `scripts/sandbox.sh compare`: parity report with **0 unexplained** differences (MOD-10).
7. Push, open the PR from `.github/pull_request_template.md`, `scripts/sandbox.sh publish`.

## 6. Cut-over (MOD-9, MOD-11)
A person starts each strangler step (Actions → Strangler release) and a reviewer of the
`production` environment approves it. Agents follow and explain it with `/cutover`; they
never approve a step or change `deploy/prod/route.yaml` themselves.

## Environments

| Environment | Where | What runs | Test hooks |
|---|---|---|---|
| Local | your machine | new service | on |
| Harness sandbox | GKE `mod-<branch>` / `mod-pr-<N>` | legacy + new side by side, frozen clock | on |
| Production | GKE `membership-prod` | new service + legacy (via `legacy-facade`), split by the gateway | off |
