#!/usr/bin/env bash
# Harness sandbox on GKE: the legacy and the new service side by side (standards/modernization.md).
#
#   scripts/sandbox.sh legacy up    build and start the legacy service (+ db, reset sidecar)
#   scripts/sandbox.sh harness      run tests/harness against TARGET=legacy|modern inside the cluster
#   scripts/sandbox.sh baseline     synthetic traffic against the legacy service: p95, error rate (MOD-8)
#   scripts/sandbox.sh all          build both, start both, harness on both, control tests on the new one
#   scripts/sandbox.sh compare      tools/compare_legacy.py inside the cluster (MOD-10)
#   scripts/sandbox.sh publish      post the harness, parity and baseline reports on the PR
#   scripts/sandbox.sh down         delete the namespace
#
# Settings: deploy/sandbox/sandbox.env. Namespace: mod-<branch>. Images tagged with the commit.
set -euo pipefail
cd "$(dirname "$0")/.."
source deploy/sandbox/sandbox.env
BRANCH="$(git rev-parse --abbrev-ref HEAD)"
SLUG="$(echo "$BRANCH" | tr '[:upper:]' '[:lower:]' | tr -c 'a-z0-9\n' '-' | cut -c1-40)"
export NS="mod-${SLUG}" BRANCH="$SLUG" TAG="$(git rev-parse --short=12 HEAD)"
export AR="${REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}"
REPORTS="reports/${NS}"
render() { python3 -c 'import os,sys; sys.stdout.write(os.path.expandvars(sys.stdin.read()))'; }

[[ -z "$(git status --porcelain)" ]] || { echo "Commit first: evidence must match a commit." >&2; exit 2; }

build() {   # $1 = image name, $2 = folder
  gcloud builds submit "$2" --project "$PROJECT_ID" --tag "$AR/$1:$TAG" --quiet
}
up_ns() { render < deploy/sandbox/namespace.yaml | kubectl apply -f -; }

run_tests() {   # $1 = TARGET, $2 = BASE_URL, $3 = path
  kubectl -n "$NS" run "tests-$1" --rm -i --restart=Never --image "$AR/harness:$TAG" \
    --env "TARGET=$1" --env "BASE_URL=$2" --env "HARNESS_RESET_URL=http://legacy-membership:9000" \
    -- pytest "$3" --junitxml=/dev/stdout -q | tee "$REPORTS/$1-$(basename "$3").xml"
}

mkdir -p "$REPORTS"
case "${1:-}" in
  legacy)
    build legacy-membership legacy/membership-api
    build harness-reset tools/harness-reset
    up_ns; render < deploy/sandbox/legacy.yaml | kubectl apply -f -
    kubectl -n "$NS" rollout status deploy/legacy-membership --timeout=10m ;;
  harness)
    target="${TARGET:-legacy}"
    url=$([[ $target == legacy ]] && echo http://legacy-membership:8080 || echo http://membership:8080)
    run_tests "$target" "$url" tests/harness ;;
  baseline)
    kubectl -n "$NS" run loadgen --rm -i --restart=Never --image "$AR/harness:$TAG" \
      -- python tools/loadgen.py --target legacy --url http://legacy-membership:8080 | tee "$REPORTS/baseline.txt" ;;
  all)
    "$0" legacy up
    build membership services/membership
    build harness .
    render < deploy/sandbox/membership.yaml | kubectl apply -f -
    kubectl -n "$NS" rollout status deploy/membership --timeout=10m
    TARGET=legacy "$0" harness
    TARGET=modern "$0" harness
    run_tests modern http://membership:8080 tests/api ;;
  compare)
    kubectl -n "$NS" run compare --rm -i --restart=Never --image "$AR/harness:$TAG" \
      -- python tools/compare_legacy.py --legacy http://legacy-membership:8080 --modern http://membership:8080 \
         --md /dev/stdout | tee "$REPORTS/parity.md" ;;
  publish)
    pr="$(gh pr view --json number -q .number)"
    gh pr comment "$pr" --body-file "$REPORTS/parity.md" ;;
  down)
    kubectl delete namespace "$NS" --ignore-not-found --wait=false ;;
  *) sed -n '2,12p' "$0"; exit 1 ;;
esac
