#!/usr/bin/env python3
"""Pre-download Minecraft sound effects from Mojang's official asset CDN.

Idempotent — re-running skips files already cached. Sounds go to ~/.cache/mc-agent-oof/sounds
unless $MC_AGENT_OOF_SOUNDS is set.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mc_agent_oof import SOUND_HASHES, ensure_sounds, sounds_dir


def main() -> int:
    out = sounds_dir()
    print(f"sound cache: {out}")
    ok = ensure_sounds(verbose=True)
    if not ok:
        print("\nsome sounds failed to download. Run again when online, or set "
              "$MC_AGENT_OOF_SOUNDS to a directory containing the .ogg files.", file=sys.stderr)
        return 1
    counts = {tier: len(files) for tier, files in SOUND_HASHES.items()}
    total = sum(counts.values())
    print(f"\nready: {total} files ({', '.join(f'{t}:{n}' for t, n in counts.items())})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
