# mc-agent-oof

Plays Minecraft sounds when Claude's commands fail.

## what it does

Every Bash tool call goes through a PostToolUse hook. Exit code + stderr decide which sound plays:

| tier | when | sound |
|---|---|---|
| **hurt** | lint fail, test fail, generic non-zero exit | the iconic player "oof" |
| **explode** | build / compile error, missing module, syntax error | TNT |
| **anvil** | segfault, panic, core dump, OOM | anvil drop |
| **levelup** | a previously-failing command finally goes green | the "ding" |
| nothing | success without a prior failure | — |

Real Minecraft sounds. Pulled on first run from Mojang's CDN (`resources.download.minecraft.net`) and cached at `~/.cache/mc-agent-oof/sounds/`. Nothing audio is checked in.

## install (claude code)

```bash
git clone https://github.com/trevorstenson/mc-agent-oof
cd mc-agent-oof
claude
```

In Claude:

```
/plugin marketplace add ./
/plugin install mc-agent-oof@mc-agent-oof
```

Restart Claude. Run `/hooks` and confirm you see `PostToolUse → Bash → mc-agent-oof/posttooluse-bash.sh`. Done.

## use without claude

```bash
bin/mc-agent-oof npm test
bin/mc-agent-oof cargo build --release
bin/mc-agent-oof sh -c './configure && make'
```

Same classifier, runs locally on whatever command you pass. stdin/stdout/stderr pass straight through. Symlink it onto your `PATH` if you want it everywhere:

```bash
ln -s "$(pwd)/bin/mc-agent-oof" ~/.local/bin/mc-agent-oof
```

## test the sounds

```bash
python3 plugins/mc-agent-oof/scripts/fetch_sounds.py
python3 plugins/mc-agent-oof/scripts/test_sounds.py hurt explode anvil levelup
```

## requirements

- Python 3.10+
- An audio player. macOS has `afplay`. Linux: install `paplay`, `ffplay`, or `mpv`. (`aplay` doesn't decode `.ogg`.)
- Internet on first run (~140 KB of sounds, downloaded once).

If anything's missing, classification still runs. You just won't hear it.

## custom sounds

`MC_AGENT_OOF_SOUNDS=/path/to/dir` overrides the cache. File names matching the tier prefix work:

```
hurt1.ogg, hurt2.ogg, hurt3.ogg     → hurt
explode1.ogg, explode2.ogg, ...      → explode
anvil_land.ogg                       → anvil
levelup.ogg                          → levelup
```

## how it classifies

First match wins, top to bottom:

| stderr or exit | tier |
|---|---|
| `Segmentation fault`, `panicked at`, `OutOfMemoryError`, `SIGSEGV`, `Aborted` | anvil |
| exit 134 / 138 / 139 | anvil |
| `error:`, `error TS\d+`, `error[E\d+]`, `FAILED`, `fatal:`, `cannot find module` | explode |
| any other non-zero exit | hurt |
| exit 0 with prior failure (same cwd + tool) | levelup |
| exit 0, no prior failure | silence |

Heuristic. If a test asserts on the literal string "Segmentation fault" you'll get an anvil. Whatever, it's a sound effect, not a verdict.

`levelup` is gated on the command's first word being build-ish: `make`, `cargo`, `npm`, `pnpm`, `yarn`, `bun`, `go`, `gradle`, `mvn`, `pytest`, `jest`, `vitest`, `tsc`, `eslint`, `python3`, etc. State is keyed by `cwd + first word`, so `npm test` and `npm install` share state.

## limitations

- Claude Code only. Codex and Cursor don't expose a PostToolUse-equivalent hook.
- macOS / Linux. Windows: PRs welcome.
- Wrapper uses bash process substitution, not POSIX `sh`.

## license

MIT for the code. The sound files belong to Mojang/Microsoft and download from their CDN at runtime — not redistributed here.
