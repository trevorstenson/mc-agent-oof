---
name: mc-agent-oof
description: Audible Minecraft reactions for command failures. Use when the user wants the agent to play the iconic Minecraft "oof", explosion, anvil-drop, or level-up sounds in response to command results — build failures, lint failures, segfaults, panics, or a previously-failing command finally going green. Triggered by phrases like "play minecraft sounds when builds fail", "minecraft hurt sound on segfault", "make my agent suffer like a minecraft player", or explicit use of $mc-agent-oof.
---

# mc-agent-oof

## Overview

Use this skill to play Minecraft sound effects in reaction to shell-command outcomes:

- the classic player **"oof"** when a lint fails or a test errors out,
- a **TNT explosion** when a build / compile / module-resolution error happens,
- an **anvil drop** for segfaults, panics, OOMs, and other crashes,
- a **level-up "ding"** when a previously-failing build is finally green again.

This skill cannot automatically intercept every Bash tool call by itself — when active, treat each shell command run during the turn as requiring a follow-up reaction call.

(Claude Code users who install this as a plugin also get an automatic `PostToolUse` hook that fires without the agent having to remember. The skill instructions still apply elsewhere — Codex and Cursor.)

## Quick Start

Resolve bundled files relative to the directory containing this `SKILL.md`; do not assume the current working directory is the skill directory. Below, `SKILL_DIR` means that directory.

After running a shell command, immediately call:

```bash
python3 "$SKILL_DIR/scripts/mc_agent_oof.py" \
  --exit-code "$EXIT" \
  --command "$COMMAND_LINE" \
  --stderr-tail "$STDERR_LAST_4KB"
```

`--stderr-tail` should be the last few KB of stderr (or combined output if stderr is unavailable). Truncate to ~4096 bytes — classification only looks at error markers, more is wasted.

Audition the sounds directly:

```bash
python3 "$SKILL_DIR/scripts/test_sounds.py" --list
python3 "$SKILL_DIR/scripts/test_sounds.py" hurt explode anvil levelup
```

Pre-fetch sounds explicitly (otherwise `mc_agent_oof.py` does it lazily on first run):

```bash
python3 "$SKILL_DIR/scripts/fetch_sounds.py"
```

## Workflow

1. Run shell commands normally.
2. After each command, capture its exit code, command line, and the tail of its stderr.
3. Invoke `scripts/mc_agent_oof.py` with those three values.
4. Use `--dry-run` when sound would be disruptive (e.g., the user is on a call), when running in CI, or when the user asked for a quiet session.
5. Keep this playful — the heuristic classification is a vibe, not a verdict.

## After-Run Ritual

Every time the agent runs a shell command — `bash`, `make`, `npm`, `cargo`, `pytest`, `tsc`, etc. — react with one call:

```bash
python3 "$SKILL_DIR/scripts/mc_agent_oof.py" --exit-code 1 --command "npm test" --stderr-tail "FAIL src/foo.test.ts"
```

If the same command was failing before and now passes, the script will pick `levelup` automatically — no extra logic needed in the agent.

For bulk sequences (e.g., `make && pytest && tsc`), react to the *outermost* command's exit code; you don't need to break the chain apart.

Skip the ritual for read-only commands (`ls`, `pwd`, `cat`) — there's nothing to react to and silence is correct. The script's triumph filter ignores non-build commands automatically, so calling it on `ls` is harmless if you'd rather be consistent.

## Reaction Tiers

- `hurt`: lint fail, test fail, generic non-zero exit.
- `explode`: build/compile failure, missing module, syntax error.
- `anvil`: segfault, panic, core dump, OOM, stack overflow.
- `levelup`: previously-failing command in this directory now succeeds.
- *silence*: success that wasn't a recovery.

## Requirements

- Python 3.10+
- A local audio player: `afplay` (macOS) or `paplay`, `ffplay`, or `mpv` (Linux). `aplay` is tried last — it doesn't decode `.ogg`, so install one of the others on Linux for sound to actually play.
- Internet access on first run (sound files download once from Mojang's official asset CDN, ~140KB total). Subsequent runs use the cache at `~/.cache/mc-agent-oof/sounds`.

If an audio player is unavailable, the script still classifies and exits 0 — just no sound.

## Sound Source

Sounds are downloaded on first run from Mojang's official asset CDN at `resources.download.minecraft.net` — the same CDN the Minecraft launcher uses. No audio is bundled in this repo. Cache lives at `~/.cache/mc-agent-oof/sounds/`.

Override with `MC_AGENT_OOF_SOUNDS=/path/to/dir` if you want to point at your local Minecraft install's `assets/objects/...` or supply your own `.ogg` files. The directory should contain files matching the expected names (e.g., `hit1.ogg`, `explode1.ogg`, `anvil_land.ogg`, `levelup.ogg`) — or any `.ogg` whose name starts with the tier name (`hurt*.ogg`, `explode*.ogg`, etc.).

## Script Notes

`mc_agent_oof.py` queues audio in a detached background process by default so the agent thread continues immediately. Use `--foreground` only when explicitly testing playback. Use `--verbose` to print the chosen tier; use `--dry-run` for classification without sound.

Triumph state lives at `~/.cache/mc-agent-oof/last-state.json`, keyed by `cwd::tool` — so `npm test` and `cargo build` track independently in the same project.

## Installation Layout

Install this whole directory as `mc-agent-oof`:

- Codex personal skill: `~/.codex/skills/mc-agent-oof/SKILL.md`
- Claude personal skill: `~/.claude/skills/mc-agent-oof/SKILL.md`
- Claude project skill: `.claude/skills/mc-agent-oof/SKILL.md`

Keep `SKILL.md`, `scripts/`, and `agents/` together; the scripts derive their sound-cache and asset paths from environment + user home, so the skill folder can move freely.
