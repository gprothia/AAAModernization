# Deployment to Google Cloud (GKE Autopilot)

Nothing here has been applied; these are the manifests the workflows use.

| Folder | Environment | Namespace | Applied by |
|---|---|---|---|
| `sandbox/` | Harness sandbox: legacy and new service side by side, frozen clock, test hooks on | `mod-<branch>` or `mod-pr-<N>` | `/extract-harness`, `/compare-legacy`, PR checks |
| `prod/` | Production: legacy and new service behind one gateway, traffic split by weight | `membership-prod` | `strangler-release.yml` only |

The production split is the strangler step (standards/modernization.md, MOD-9): the gateway
sends a share of `/v1/members` traffic to the new service and the rest to the legacy
service through `legacy-facade`, a thin translation layer that gives the legacy service the
same `/v1` contract. The release changes the two `weight` values in `prod/route.yaml`:
10 → 50 → 100.
