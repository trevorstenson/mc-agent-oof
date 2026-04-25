#!/usr/bin/env bash
# Claude Code PostToolUse hook for the Bash tool.
#
# Forwards the event JSON on stdin to a Python helper that parses it and queues
# audio in a detached background process. Returns immediately.

set -u

if ! command -v python3 >/dev/null 2>&1; then
  exit 0
fi

HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$HOOK_DIR/posttooluse_bash_inner.py"
