#!/usr/bin/env python3
"""Mechanical rules for specs (to-be in specs/, as-is in specs/as-is/). Exit 1 on any error.

To-be specs: front matter, the enterprise sections, an slo block, parity/deviation marks on a
modernised capability, and every deviation it marks listed in "Approved deviations".
As-is specs (standards/modernization.md): every behaviour cites Source and Confidence (MOD-3),
a baseline block (MOD-8), a "Deviations from standards" table (MOD-4), and an open question
for every low-confidence behaviour.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

FRONT = re.compile(r"^---\n(.*?)\n---\n", re.S)
FIELD = re.compile(r"^(\w+):\s*(.*?)(?:\s+#\s.*)?\s*$", re.M)
BLOCK = re.compile(r"^### (~~)?([A-Z]{3}-\d{3})-(AC|B)(\d+) \[(api|ui|api,ui)\]", re.M)
TO_BE_SECTIONS = [
    "## Why",
    "## Scope",
    "## Acceptance criteria",
    "## Security & access (AAA)",
    "### Authentication",
    "### Authorization",
    "### Accounting",
    "## Logging",
    "## API contract",
    "## SLO",
    "## Open questions",
]
AS_IS_SECTIONS = [
    "## What it does today",
    "## Observed behaviour",
    "## Hidden behaviours",
    "## Data and dependencies",
    "## Security & access (as found)",
    "## Logging (as found)",
    "## API contract (as found)",
    "## Performance baseline",
    "## Deviations from standards",
    "## Open questions",
]


def blocks(text: str) -> list[tuple[str, str]]:
    """(criterion id, its text) for each ### block."""
    out = []
    matches = list(BLOCK.finditer(text))
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else text.find("\n## ", m.end())
        out.append((f"{m.group(2)}-{m.group(3)}{m.group(4)}", text[m.start() : end]))
    return out


def check(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    errs = []
    fm = FRONT.match(text)
    if not fm:
        return [f"{path}: no front matter"]
    meta = dict(FIELD.findall(fm.group(1)))
    as_is = meta.get("kind") == "as-is"
    for key in ("id", "title", "status", "owner", "issue"):
        if not meta.get(key):
            errs.append(f"{path}: front matter needs `{key}`")
    if not path.name.startswith(meta.get("id", "?")):
        errs.append(f"{path}: file name must start with its id {meta.get('id')}")
    for section in AS_IS_SECTIONS if as_is else TO_BE_SECTIONS:
        if section not in text:
            errs.append(f"{path}: missing section '{section}'")

    if as_is:
        for cid, body in blocks(text):
            if "**Source:**" not in body or not re.search(r"`[^`]+:\d+(-\d+)?`", body):
                errs.append(f"{path}: {cid} needs a Source with file:lines (MOD-3)")
            conf = re.search(r"\*\*Confidence:\*\* (high|medium|low)", body)
            if not conf:
                errs.append(f"{path}: {cid} needs Confidence high|medium|low (MOD-3)")
            elif conf.group(1) == "low" and cid.split("-")[-1] not in text.split("## Open questions")[-1]:
                errs.append(f"{path}: {cid} is low confidence, so it needs an open question (MOD-3)")
        if "```baseline" not in text:
            errs.append(f"{path}: Performance baseline needs a ```baseline block (MOD-8)")
        if not re.search(r"\| DEV-\d{3}-\d{2} \|", text):
            errs.append(f"{path}: Deviations from standards needs a table of DEV-... rows, or 'None' (MOD-4)")
    else:
        if "```slo" not in text:
            errs.append(f"{path}: SLO needs a ```slo block (SLO-1)")
        if meta.get("status") in ("approved", "implemented") and "- [ ]" in text:
            errs.append(f"{path}: an {meta['status']} spec has unanswered open questions")
        if meta.get("replaces"):
            table = (
                text.split("## Approved deviations")[-1].split("\n## ")[0] if "## Approved deviations" in text else ""
            )
            if not table:
                errs.append(f"{path}: a modernised capability needs '## Approved deviations' (MOD-4)")
            for cid, body in blocks(text):
                marked = re.findall(r"\*\*Deviation\*\* `(DEV-\d{3}-\d{2})`", body)
                for dev in marked:
                    if f"| {dev} |" not in table:
                        errs.append(f"{path}: {cid} cites {dev}, which is not in Approved deviations")
            if not Path(meta["replaces"]).exists():
                errs.append(f"{path}: replaces {meta['replaces']}, which does not exist")
    return errs


def main() -> int:
    files = [p for p in sorted(Path("specs").rglob("*.md")) if not p.name.startswith("_")]
    errors = [e for p in files for e in check(p)]
    for p in files:
        print(("❌ " if any(e.startswith(str(p)) for e in errors) else "✅ ") + str(p))
    for e in errors:
        print("   " + e)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
