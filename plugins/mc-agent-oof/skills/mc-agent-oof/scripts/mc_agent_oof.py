#!/usr/bin/env python3
"""Play Minecraft hurt sounds when a command fails. Triumph fanfare when it recovers."""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path


MOJANG_CDN = "https://resources.download.minecraft.net"

# Hashes pulled once from Minecraft 1.20.1's asset index. Files served by Mojang's
# official CDN — we never redistribute the audio. Override with $MC_AGENT_OOF_SOUNDS.
SOUND_HASHES: dict[str, list[tuple[str, str]]] = {
    "hurt": [
        ("hit1.ogg", "8760ebb9d4b1fe9457ef272324ecd6b4329a593e"),
        ("hit2.ogg", "144867e8792415e2873293f06ecce85cd32bb4e8"),
        ("hit3.ogg", "c73dcedde5031fcf242b08b3405f63098cd70641"),
    ],
    "explode": [
        ("explode1.ogg", "cd46e41023887558b134547e28327de6e7df189a"),
        ("explode2.ogg", "a116e396d95a0ee245000dd4cdcc333d38ea9e3b"),
        ("explode3.ogg", "a94a69e56568f5789cab05382cfd81f601189fd1"),
        ("explode4.ogg", "f259be40364341edcaf88e339bc24ab01e49845a"),
    ],
    "anvil": [
        ("anvil_land.ogg", "934b16e82b94d5790175615303594f0ec28da4a0"),
    ],
    "levelup": [
        ("levelup.ogg", "b9c60e807ba770e8c4a2b1bae81d51813dc64b6c"),
    ],
}

TIERS = ("hurt", "explode", "anvil", "levelup")

# Stderr classification, highest priority first. Match → tier.
ANVIL_PATTERNS = re.compile(
    r"Segmentation fault|core dumped|panicked at|fatal runtime error|"
    r"OutOfMemoryError|stack overflow|SIGSEGV|SIGABRT|Bus error|"
    r"thread .* panicked|Aborted \(core dumped\)",
    re.IGNORECASE,
)
EXPLODE_PATTERNS = re.compile(
    r"^error[: ]|"
    r"\berror:|"
    r"\berror\s+TS\d+|"        # TypeScript: error TS2304: ...
    r"\berror\[E\d+\]|"        # Rust: error[E0308]: ...
    r": error\b|"              # cc/gcc/clang: foo.c:5: error: ...
    r"\bFAILED\b|"
    r"\bfatal:|"
    r"\bcompilation error\b|"
    r"\bbuild failed\b|"
    r"\bsyntaxerror\b|"
    r"\bcannot find module\b|"
    r"\bmodule not found\b",
    re.IGNORECASE | re.MULTILINE,
)

# Triumph only fires for build/test commands — `cd` succeeding doesn't deserve a fanfare.
BUILD_LIKE_COMMAND = re.compile(
    r"\b(make|cargo|npm|pnpm|yarn|bun|go|gradle|mvn|"
    r"pytest|jest|vitest|mocha|tsc|eslint|prettier|"
    r"ruff|mypy|pyright|flake8|cmake|ninja|bazel|"
    r"docker|kubectl|terraform|ansible|"
    r"python|python3|node|deno|rustc|clang|gcc|g\+\+|"
    r"swift|dotnet|stack|cabal|elm|"
    r"hatch|poetry|pip|uv|pdm|"
    r"git\s+(rebase|merge|cherry-pick))\b",
    re.IGNORECASE,
)

CACHE_DIR = Path(os.environ.get("MC_AGENT_OOF_CACHE", Path.home() / ".cache" / "mc-agent-oof"))
STATE_FILE = CACHE_DIR / "last-state.json"


def sounds_dir() -> Path:
    override = os.environ.get("MC_AGENT_OOF_SOUNDS")
    if override:
        return Path(override).expanduser()
    return CACHE_DIR / "sounds"


def ensure_sounds(verbose: bool = False) -> bool:
    """Download missing sound files. Returns True if all sounds available."""
    out = sounds_dir()
    out.mkdir(parents=True, exist_ok=True)
    all_present = True
    for tier, files in SOUND_HASHES.items():
        for name, sha in files:
            target = out / name
            if target.exists() and target.stat().st_size > 0:
                continue
            url = f"{MOJANG_CDN}/{sha[:2]}/{sha}"
            if verbose:
                print(f"fetching {tier}/{name} from Mojang CDN...", file=sys.stderr)
            try:
                with urllib.request.urlopen(url, timeout=10) as resp:
                    data = resp.read()
                target.write_bytes(data)
            except (urllib.error.URLError, OSError) as exc:
                if verbose:
                    print(f"  failed: {exc}", file=sys.stderr)
                all_present = False
    return all_present


def pick_sound(tier: str) -> Path | None:
    files = SOUND_HASHES.get(tier)
    if not files:
        return None
    name, _ = random.choice(files)
    candidate = sounds_dir() / name
    if candidate.exists():
        return candidate
    # Some user-supplied MC_AGENT_OOF_SOUNDS layouts may use other filenames; fall back
    # to any matching tier prefix in the directory.
    for child in sounds_dir().glob(f"{tier}*.ogg"):
        return child
    return None


def audio_player() -> list[str] | None:
    candidates = [
        ["afplay"],
        ["paplay"],
        ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"],
        ["mpv", "--really-quiet", "--no-video"],
        ["aplay", "-q"],  # last — doesn't decode .ogg, but worth trying for user PCM overrides
    ]
    for cmd in candidates:
        if shutil.which(cmd[0]):
            return cmd
    return None


def play(tier: str, foreground: bool, verbose: bool) -> bool:
    sound = pick_sound(tier)
    if sound is None:
        if verbose:
            print(f"no sound file for tier {tier!r}", file=sys.stderr)
        return False
    player = audio_player()
    if player is None:
        if verbose:
            print(f"[mc-agent-oof] {tier} (no audio player found)", file=sys.stderr)
        return False
    cmd = [*player, str(sound)]
    if foreground:
        subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    # Detached background so the agent thread doesn't wait on audio.
    kwargs: dict = dict(
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True,
    )
    if shutil.which("nohup"):
        cmd = ["nohup", *cmd]
    else:
        kwargs["start_new_session"] = True
    try:
        subprocess.Popen(cmd, **kwargs)
    except OSError as exc:
        if verbose:
            print(f"playback failed: {exc}", file=sys.stderr)
        return False
    return True


def load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def save_state(state: dict) -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(state))
    except OSError:
        pass


def state_key(cwd: str, command: str) -> str:
    # Group by cwd + first arg (the tool). `npm test` and `npm run lint` track
    # independently from `cargo build`.
    head = command.strip().split()[:1]
    return f"{cwd}::{head[0] if head else ''}"


def classify(
    exit_code: int,
    stderr_tail: str,
    command: str,
) -> str | None:
    """Return tier name, or None for silence."""
    stderr_tail = stderr_tail or ""

    if exit_code in (139, 134, 138):  # SIGSEGV, SIGABRT, SIGBUS
        return "anvil"
    if ANVIL_PATTERNS.search(stderr_tail):
        return "anvil"
    if exit_code != 0:
        if EXPLODE_PATTERNS.search(stderr_tail):
            return "explode"
        return "hurt"
    return None  # success — caller checks triumph state separately


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--exit-code", type=int, required=False, help="Exit code of the command being reacted to.")
    p.add_argument("--stderr-tail", default="", help="Last few KB of stderr, used for classification.")
    p.add_argument("--command", default="", help="The command that was run (for triumph filtering).")
    p.add_argument("--cwd", default=os.getcwd(), help="Working directory of the command.")
    p.add_argument("--tier", choices=TIERS, help="Force a specific tier instead of classifying.")
    p.add_argument("--dry-run", action="store_true", help="Print tier without playing audio.")
    p.add_argument("--foreground", action="store_true", help="Block until audio finishes.")
    p.add_argument("--verbose", action="store_true", help="Print classification + playback diagnostics.")
    p.add_argument("--no-fetch", action="store_true", help="Skip sound auto-download.")
    p.add_argument("--no-triumph", action="store_true", help="Disable level-up sound on recovery.")
    args = p.parse_args(argv)

    if not args.no_fetch and not os.environ.get("MC_AGENT_OOF_SOUNDS"):
        ensure_sounds(verbose=args.verbose)

    if args.tier:
        tier = args.tier
    else:
        if args.exit_code is None:
            print("--exit-code or --tier is required", file=sys.stderr)
            return 2
        tier = classify(args.exit_code, args.stderr_tail, args.command)

    # Triumph handling: only when caller passed exit-code (i.e. real reaction, not
    # an explicit --tier override).
    if not args.tier and args.exit_code is not None and not args.no_triumph:
        state = load_state()
        key = state_key(args.cwd, args.command)
        prev = state.get(key)
        is_build_like = bool(BUILD_LIKE_COMMAND.search(args.command)) if args.command else True
        if is_build_like:
            if args.exit_code == 0:
                if prev and prev.get("failed"):
                    tier = "levelup"
                state[key] = {"failed": False, "ts": time.time()}
            else:
                state[key] = {"failed": True, "ts": time.time()}
            save_state(state)

    if tier is None:
        if args.verbose:
            print("[mc-agent-oof] silence", file=sys.stderr)
        return 0

    if args.verbose or args.dry_run:
        print(f"[mc-agent-oof] {tier}", file=sys.stderr)
    if args.dry_run:
        return 0

    play(tier, foreground=args.foreground, verbose=args.verbose)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
