#!/usr/bin/env python3
"""Audition mc-agent-oof tiers without classifying anything.

  test_sounds.py --list
  test_sounds.py hurt explode anvil levelup
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mc_agent_oof import TIERS, ensure_sounds, play, sounds_dir


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("tiers", nargs="*", help=f"One or more of: {' '.join(TIERS)}")
    p.add_argument("--list", action="store_true", help="List tiers and exit.")
    p.add_argument("--gap", type=float, default=1.5, help="Seconds between sounds.")
    args = p.parse_args()

    if args.list:
        for t in TIERS:
            print(t)
        return 0

    if not args.tiers:
        args.tiers = list(TIERS)

    invalid = [t for t in args.tiers if t not in TIERS]
    if invalid:
        print(f"unknown tier(s): {invalid}. valid: {TIERS}", file=sys.stderr)
        return 2

    ensure_sounds(verbose=True)
    print(f"sound cache: {sounds_dir()}")

    for i, tier in enumerate(args.tiers):
        if i > 0:
            time.sleep(args.gap)
        print(f"  {tier}")
        play(tier, foreground=True, verbose=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
