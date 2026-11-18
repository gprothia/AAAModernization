#!/usr/bin/env python3
"""Synthetic traffic for the baseline (MOD-8) and strangler steps: p95 and error rate.

  loadgen.py --target legacy|modern --url <base url> [--seconds 120] [--workers 8]

Uses the harness adapters, so the same mix of lookups runs against either system.
Prints one line: BASELINE {"p95_latency_ms": ..., "error_rate_pct": ..., "requests": ...}
"""

import argparse
import json
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tests.harness.adapters import LegacyAdapter, ModernAdapter  # noqa: E402

MIX = [("alice", "M-1001"), ("ana", "M-1002"), ("ana", "M-1003"), ("bob", "M-1002")]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", choices=["legacy", "modern"], required=True)
    ap.add_argument("--url", required=True)
    ap.add_argument("--seconds", type=int, default=120)
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    make = LegacyAdapter if a.target == "legacy" else ModernAdapter
    samples, errors, lock = [], [0], threading.Lock()
    end = time.monotonic() + a.seconds

    def work() -> None:
        svc, i = make(a.url), 0
        while time.monotonic() < end:
            user, member = MIX[i % len(MIX)]
            start = time.perf_counter()
            try:
                svc.lookup(user, member)
                ok = True
            except Exception:  # noqa: BLE001 - any failure counts as an error
                ok = False
            with lock:
                samples.append((time.perf_counter() - start) * 1000)
                errors[0] += 0 if ok else 1
            i += 1

    threads = [threading.Thread(target=work) for _ in range(a.workers)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    samples.sort()
    p95 = samples[int(0.95 * (len(samples) - 1))] if samples else 0
    print(
        "BASELINE "
        + json.dumps(
            {
                "p95_latency_ms": round(p95, 1),
                "error_rate_pct": round(100 * errors[0] / max(1, len(samples)), 2),
                "requests": len(samples),
            }
        )
    )


if __name__ == "__main__":
    main()
