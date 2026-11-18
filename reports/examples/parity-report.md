<!-- Example output of /compare-legacy (tools/compare_legacy.py), posted on the build PR -->
### Parity report: PASSED - 12 requests, 8 identical, 4 approved deviations, 0 unexplained

Legacy `legacy-membership:4f1c2a9e0b77` vs new `membership:9b03d71c55e2`, both from the seed data and the frozen clock.

| Request | What | Legacy | New | Verdict |
|---|---|---|---|---|
| g-001 | lookup M-1001 as alice | ok | ok | identical |
| g-002 | lookup M-1003 as ana | ok | ok | identical |
| g-003 | lookup M-1001 as bob | forbidden | not_found | approved deviation `DEV-001-01` |
| g-004 | lookup M-9999 as ana | not_found | not_found | identical |
| g-005 | renew M-1002 as bob | ok | ok | identical |
| g-006 | renew M-1001 as alice | ok | ok | identical |
| g-007 | renew M-1003 as ana | ok | ok | identical |
| g-008 | cancel M-1001 as alice | ok | ok | identical |
| g-009 | cancel M-1001 as alice (repeat) | ok | conflict | approved deviation `DEV-003-04` |
| g-010 | cancel M-1002 as bob | ok | ok | identical |
| g-011 | cancel M-1001 as bob | forbidden | not_found | approved deviation `DEV-003-01` |
| g-012 | cancel M-1004 as ana | ok | forbidden | approved deviation `DEV-003-07` |

Format differences (US dates vs ISO, `124.0` vs `"124.00"`, `memberId` vs `member_id`) are removed by normalisation and are not differences.
