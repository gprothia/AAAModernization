#!/usr/bin/env python3
"""Differential test (MOD-10): replay recorded legacy traffic to both services and compare.

  compare_legacy.py --legacy http://legacy-membership:8080 --modern http://membership:8080 \
                    [--golden tests/golden/membership-golden.jsonl] [--md reports/parity.md]

Each request is sent to both services (from the same seed and frozen clock) and the
responses are normalised by tests/harness/adapters.py, so format changes (dates, amounts,
field names) are not differences. A remaining difference must match an entry in
tests/golden/allowed_differences.yaml (an approved deviation); anything else fails.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tests.harness.adapters import LegacyAdapter, ModernAdapter  # noqa: E402


def run(adapter, req: dict):
    op = getattr(adapter, req["op"])
    args = (req["as"], req["member"]) + ((req.get("autopay", False),) if req["op"] == "renew" else ())
    if req.get("repeat"):
        op(*args)  # the recorded request was the second of two
    return op(*args)


def allowed(req: dict, legacy, modern, rules: list[dict]) -> str | None:
    for rule in rules:
        when = rule["when"]
        if when.get("op") != req["op"]:
            continue
        if any(req.get(k) != v for k, v in when.items() if k not in ("op", "legacy_kind")):
            continue
        if "legacy_kind" in when and when["legacy_kind"] != legacy.kind:
            continue
        if rule["modern_kind"] == modern.kind:
            return rule["deviation"]
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--legacy", required=True)
    ap.add_argument("--modern", required=True)
    ap.add_argument("--golden", default="tests/golden/membership-golden.jsonl")
    ap.add_argument("--allowed", default="tests/golden/allowed_differences.yaml")
    ap.add_argument("--md", default="reports/parity.md")
    a = ap.parse_args()

    legacy, modern = LegacyAdapter(a.legacy), ModernAdapter(a.modern)
    rules = yaml.safe_load(Path(a.allowed).read_text())
    rows, unexplained = [], 0
    for line in Path(a.golden).read_text().splitlines():
        req = json.loads(line)
        legacy.reset()
        modern.reset()
        lo, mo = run(legacy, req), run(modern, req)
        if (lo.kind, lo.data) == (mo.kind, mo.data):
            verdict = "identical"
        elif dev := allowed(req, lo, mo, rules):
            verdict = f"approved deviation `{dev}`"
        else:
            verdict = "**UNEXPLAINED**"
            unexplained += 1
        rows.append(f"| {req['id']} | {req['op']} {req['member']} as {req['as']} | {lo.kind} | {mo.kind} | {verdict} |")

    same = sum("identical" in r for r in rows)
    approved = sum("approved" in r for r in rows)
    status = "PASSED" if unexplained == 0 else "FAILED"
    md = [
        f"### Parity report: {status} - {len(rows)} requests, {same} identical, {approved} approved deviations, "
        f"{unexplained} unexplained",
        "",
        "| Request | What | Legacy | New | Verdict |",
        "|---|---|---|---|---|",
        *rows,
    ]
    Path(a.md).parent.mkdir(parents=True, exist_ok=True)
    Path(a.md).write_text("\n".join(md) + "\n")
    print("\n".join(md))
    return 0 if unexplained == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
