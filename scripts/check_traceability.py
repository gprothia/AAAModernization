#!/usr/bin/env python3
"""Every behaviour and criterion has a test; every deviation a test claims is approved.

- Each as-is behaviour marked `high` confidence has a harness test tagged
  @pytest.mark.behaviour (MOD-3, MOD-6). `medium` and `low` ones without a test are listed as
  still to confirm: a capability is not migrated until its behaviours are confirmed.
- Each to-be criterion (MEM-xxx-ACn) of an approved or implemented spec has a test tagged
  @pytest.mark.ac, in tests/harness or tests/api.
- Each @pytest.mark.deviation("DEV-...") and each entry in tests/golden/allowed_differences.yaml
  names a deviation in some to-be spec's "Approved deviations" table (MOD-4, MOD-7, MOD-10).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

CRIT = re.compile(r"^### ([A-Z]{3}-\d{3}-(?:AC|B)\d+) \[", re.M)
STATUS = re.compile(r"^status:\s*(\w+)", re.M)


def marks(name: str) -> set[str]:
    pat = re.compile(rf'@pytest\.mark\.{name}\("([^"]+)"\)')
    return {m for f in Path("tests").rglob("test_*.py") for m in pat.findall(f.read_text())}


def main() -> int:
    errors = []
    behaviours, high, acs, approved = set(), set(), set(), set()
    for spec in Path("specs").rglob("*.md"):
        if spec.name.startswith("_"):
            continue
        text = spec.read_text()
        ids = set(CRIT.findall(text))
        if "as-is" in spec.parts:
            behaviours |= ids
            for chunk in re.split(r"(?=^### )", text, flags=re.M):
                m = CRIT.match(chunk)
                if m and "**Confidence:** high" in chunk:
                    high.add(m.group(1))
        elif (STATUS.search(text) or [None, ""])[1] in ("approved", "implemented"):
            acs |= ids
        if "## Approved deviations" in text:
            approved |= set(re.findall(r"^\| (DEV-\d{3}-\d{2}) \|", text.split("## Approved deviations")[1], re.M))

    tested_b, tested_ac, claimed = marks("behaviour"), marks("ac"), marks("deviation")
    golden = set(re.findall(r"deviation: (DEV-\d{3}-\d{2})", Path("tests/golden/allowed_differences.yaml").read_text()))
    errors += [
        f"as-is behaviour {b} is marked high confidence but has no harness test (MOD-3)"
        for b in sorted(high - tested_b)
    ]
    to_confirm = sorted(behaviours - tested_b - high)
    errors += [f"criterion {c} has no test" for c in sorted(acs - tested_ac)]
    errors += [f"test tagged {t} which no spec defines" for t in sorted((tested_b | tested_ac) - behaviours - acs)]
    errors += [f"deviation {d} is not approved in any to-be spec" for d in sorted((claimed | golden) - approved)]

    print(f"{len(behaviours)} legacy behaviours, {len(acs)} criteria, {len(approved)} approved deviations")
    for b in to_confirm:
        print(f"⚠️  {b} not confirmed by the harness yet (medium/low confidence)")
    for e in errors:
        print("❌ " + e)
    if not errors:
        print("✅ every behaviour and criterion has a test; every deviation is approved")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
