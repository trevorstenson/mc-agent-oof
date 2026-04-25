# mc-agent-oof

Minecraft hurt sounds when your build, lint, or test fails — automatically, no agent cooperation needed.

Inspired by [`AndrewVos/endless-toil`](https://github.com/AndrewVos/endless-toil) and [`lorenzohess`'s comment](https://news.ycombinator.com/item?id=47888465) asking for a Minecraft-flavored version that fires on actual failures (build errors, segfaults, lint fails) instead of static-code heuristics.

## What it does

Every Bash tool call your Claude Code agent runs gets classified by exit code + stderr; one of four Minecraft sounds plays:

| Tier | When | Sound |
|---|---|---|
| **hurt** | lint fail, test fail, generic non-zero exit | the iconic Minecraft player "oof" |
| **explode** | build / compile failure, missing module, syntax error | TNT explosion |
| **anvil** | segfault, panic, core dump, OOM, stack overflow | anvil drop |
| **levelup** | a previously-failing command in this directory just went green | the level-up "ding" |
| *silence* | success that wasn't a recovery | — |

Sounds are **bit-identical to in-game Minecraft** — the script downloads the `.ogg` files on first run from Mojang's official asset CDN (`resources.download.minecraft.net`), the same one the Minecraft launcher uses. Nothing audio-related is bundled in this repo.

## Why Claude Code only

This plugin uses Claude Code's `PostToolUse` hook to react automatically — it fires on every Bash tool call without the agent having to know the plugin exists.

Other agent CLIs (Codex, Cursor) only support skill-based activation, where the LLM has to remember to call a script after each command. That's not reliable enough — the agent can forget mid-session and the sounds stop. So those paths have been dropped intentionally. If those CLIs add real hook systems, support can come back.

## Install in Claude Code

```bash
git clone https://github.com/trevorstenson/mc-agent-oof
cd mc-agent-oof
claude
```

Inside Claude Code:

```text
/plugin marketplace add ./
/plugin install mc-agent-oof@mc-agent-oof
```

`/exit` and re-launch `claude` so the hook registers. Verify:

```text
/hooks
```

You should see `PostToolUse → Bash → mc-agent-oof/posttooluse-bash.sh`. From this point on, every failing command Claude runs makes a sound. The agent doesn't see the hook fire and won't comment on it.

## Use without an agent (shell wrapper)

```bash
bin/mc-agent-oof npm test
bin/mc-agent-oof cargo build --release
bin/mc-agent-oof sh -c './configure && make'
```

Pass-through: stdin/stdout/stderr behave exactly as if you'd run the command directly. The wrapper just listens to the exit code + stderr tail and reacts.

Symlink onto your `PATH`:

```bash
ln -s "$(pwd)/bin/mc-agent-oof" ~/.local/bin/mc-agent-oof
```

## Test the sounds

```bash
python3 plugins/mc-agent-oof/scripts/fetch_sounds.py
python3 plugins/mc-agent-oof/scripts/test_sounds.py --list
python3 plugins/mc-agent-oof/scripts/test_sounds.py hurt explode anvil levelup
```

## Requirements

- **Python 3.10+**
- **A local audio player.** macOS has `afplay` built in. On Linux, install `paplay` (PulseAudio), `ffplay` (ffmpeg), or `mpv`. `aplay` doesn't decode `.ogg` so it won't work alone — install one of the others.
- **Internet on first run** — the four sound files (≈140 KB total) download once from Mojang's official asset CDN, then cache to `~/.cache/mc-agent-oof/sounds/`.

If the audio player or network is unavailable, mc-agent-oof still classifies and exits 0 — you just won't hear the sound.

## Customizing sounds

Set `MC_AGENT_OOF_SOUNDS=/path/to/dir` to override the cache. Drop your own `.ogg` files in there with names matching the tier prefix:

```
hurt1.ogg     hurt2.ogg     hurt3.ogg     # any of these for `hurt`
explode1.ogg  explode2.ogg                # for `explode`
anvil_land.ogg                            # for `anvil`
levelup.ogg                               # for `levelup`
```

## How it classifies

Highest priority first; first match wins.

| Pattern (in stderr) | Tier |
|---|---|
| `Segmentation fault`, `core dumped`, `panicked at`, `OutOfMemoryError`, `SIGSEGV`, `Aborted` | anvil |
| Exit code 134 / 138 / 139 | anvil |
| `error:`, `error TS\d+`, `error[E\d+]`, `: error`, `FAILED`, `fatal:`, `compilation error`, `cannot find module`, `SyntaxError` | explode |
| Any other non-zero exit | hurt |
| Exit 0, but the previous run for this `cwd:tool` failed | levelup |
| Exit 0 (no prior failure) | silence |

This is heuristic. False positives happen — a test that asserts on the literal string `"Segmentation fault"` will fire `anvil`. That's part of the joke. Don't take the tier as proof of anything.

Triumph (`levelup`) is gated on the command starting with a build-ish first word (`make|cargo|npm|pnpm|yarn|bun|go|gradle|mvn|pytest|jest|vitest|tsc|eslint|python3|...`). State is keyed by `cwd + first-word-of-command`, so `npm test` and `npm install` share a key (any npm success after an npm failure fires the ding), but `npm` and `cargo` are independent.

## Limitations

- **Claude Code only.** Codex and Cursor agents are not supported because they don't expose programmatic post-tool-use hooks.
- **macOS / Linux only.** Windows users: PRs welcome.
- **Heuristic classification.** Acceptable cost for the joke.
- **The shell wrapper uses `bash` process substitution.** Plain POSIX `sh` won't run it.

## License

MIT for the plugin code. The Minecraft sound files themselves are © Mojang/Microsoft and downloaded from their official CDN at runtime — they are **not** redistributed in this repository.

## Source

Plugin layout follows the Claude Code plugin docs:

- https://code.claude.com/docs/en/plugins
