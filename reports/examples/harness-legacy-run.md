<!-- Example output of /extract-harness: TARGET=legacy, namespace mod-mod-membership-harness -->
### Harness on the LEGACY service: PASSED - 15/15

Commit `4f1c2a9` · legacy image `legacy-membership:4f1c2a9e0b77` · clock frozen at 2026-03-10 12:00 UTC

| | Behaviour | Test |
|---|---|---|
| ✅ | `MEM-001-B1` | test_member_reads_own_record |
| ✅ | `MEM-001-B2` | test_agent_reads_any_record |
| ✅ | `MEM-001-B3` | test_member_cannot_read_another_record (legacy: 403) |
| ✅ | `MEM-001-B4` | test_unknown_member (legacy: 200 + error body) |
| ✅ | `MEM-001-B5` | test_sign_in_required |
| ✅ | `MEM-002-B1` | test_active_renewal_continues_term |
| ✅ | `MEM-002-B2` | test_autopay_discount |
| ✅ | `MEM-002-B3` | test_long_lapsed_renewal_starts_today |
| ✅ | `MEM-003-B1` | test_refund_is_pro_rata_rounded_down (100, not 100.22) |
| ✅ | `MEM-003-B2` | test_no_refund_near_expiry |
| ✅ | `MEM-003-B3` | test_second_cancellation (legacy refunds again) |
| ✅ | `MEM-003-B4` | test_member_cannot_cancel_another (legacy: 403) |
| ✅ | `MEM-003-B5` | test_agent_cancels_any_member |
| ✅ | `MEM-003-B5` | test_agent_large_refund (legacy: no supervisor) |
| ✅ | `MEM-003-B6`, `B7` | test_days_counted_in_utc_with_365_day_year (99 at 01:00 UTC) |

Not yet confirmed: `MEM-002-B4` (medium), `MEM-002-B5` (low): no seed data for them yet.
