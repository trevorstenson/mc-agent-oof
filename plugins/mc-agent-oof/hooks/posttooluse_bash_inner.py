#!/usr/bin/env python3
"""Read a Claude Code PostToolUse event from stdin, call mc_agent_oof.py."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    if event.get("tool_name") != "Bash":
        return 0

    resp = event.get("tool_response") or {}
    inp = event.get("tool_input") or {}

    exit_code: int | None = None
    for key in ("exit_code", "exitCode", "code", "returncode"):
        val = resp.get(key)
        if isinstance(val, int):
            exit_code = val
            break
    if exit_code is None:
        if resp.get("is_error") or resp.get("interrupted"):
            exit_code = 1
        else:
            exit_code = 0

    stderr = resp.get("stderr") or resp.get("stdout") or ""
    if not isinstance(stderr, str):
        stderr = ""
    stderr = stderr[-4096:]

    command = inp.get("command", "") or ""
    cwd = event.get("cwd") or ""

    script = Path(__file__).resolve().parents[1] / "scripts" / "mc_agent_oof.py"
    if not script.exists():
        return 0

    subprocess.Popen(
        [sys.executable, str(script),
         "--exit-code", str(exit_code),
         "--command", command,
         "--stderr-tail", stderr,
         "--cwd", cwd],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True,
        start_new_session=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
