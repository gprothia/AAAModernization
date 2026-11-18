<!-- Example output of the Strangler release workflow, step 10, posted on the release PR -->
### Strangler step 10%: KEPT

Approved by @gprothia in the `production` environment · gateway `membership` in `membership-prod`
· weights new 10 / legacy 90 · 300 s window

| | Budget (MEM-003 SLO) | Legacy baseline | New service |
|---|---|---|---|
| p95 latency | ≤ 250 ms | 310 ms | **96 ms** ✅ |
| Error rate | ≤ 0.5% | 0.6% | **0.0%** ✅ |

Parity on the release commit: 12/12 (0 unexplained). Next step (50%) can be started from Actions → Strangler release.
