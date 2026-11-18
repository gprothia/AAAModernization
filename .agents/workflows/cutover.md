---
description: Follow a strangler step in production and explain it; never approve or move traffic yourself (MOD-9)
---

# /cutover

Usage: `/cutover status` or `/cutover follow <step>` (10, 50 or 100).

1. `status`: read `deploy/prod/route.yaml` on `main` and the latest **Strangler release** runs
   (`gh run list --workflow strangler-release.yml`): current weights, SLO verdicts, legacy baseline.
2. `follow <step>`: the user starts the step in GitHub (Actions → Strangler release → Run
   workflow, with the step). It waits for a reviewer in the `production` environment. Never
   approve it yourself. Watch the run and explain each stage: parity report on the release
   commit, new weights applied, traffic window, new service vs SLO and vs legacy baseline,
   then **kept** or **rolled back** to the previous weights.
3. After a rollback, summarise the evidence: which endpoint, the numbers, the parity report. The SRE agent opens a root-cause PR, which goes through the same checks.
4. Retiring the legacy service (MOD-11) is a separate PR a person opens and approves.
