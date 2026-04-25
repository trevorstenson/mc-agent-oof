# mc-agent-oof

Minecraft hurt sounds when your build, lint, or test fails.

Inspired by [`AndrewVos/endless-toil`](https://github.com/AndrewVos/endless-toil) — a plugin that plays escalating groans while an agent reads code — and [`lorenzohess`'s comment](https://news.ycombinator.com/item?id=47888465) asking for a Minecraft-flavored version that fires on actual build failures, lint errors, and segfaults instead.

## What it does

After every shell command (or every Bash tool call your AI agent makes), mc-agent-oof classifies the result and plays one Minecraft sound:

| Tier | When | Sound |
|---|---|---|
| **hurt** | lint fail, test fail, generic non-zero exit | the iconic Minecraft player "oof" |
| **explode** | build / compile failure, missing module, syntax error | TNT explosion |
| **anvil** | segfault, panic, core dump, OOM, stack overflow | anvil drop |
| **levelup** | a previously-failing command in this directory just went green | the level-up "ding" |
| *silence* | success that wasn't a recovery | — |

Sounds are **bit-identical to in-game Minecraft** — the script downloads the `.ogg` files on first run from Mojang's official asset CDN (`resources.download.minecraft.net`), the same one the Minecraft launcher uses. Nothing audio-related is bundled in this repo.

## Three ways to use it

### 1. Plugin (Codex / Claude Code / Cursor)

Mirrors endless-toil's install flow exactly.

#### Claude Code

```bash
git clone https://github.com/<you>/mc-agent-oof
cd mc-agent-oof && claude
```

```text
/plugin marketplace add ./
/plugin install mc-agent-oof@mc-agent-oof
```

After install, every Bash tool call your agent runs is intercepted by a `PostToolUse` hook — sounds fire automatically without the agent having to remember.

You can also invoke the bundled skill explicitly:

```text
/mc-agent-oof
```

#### Codex CLI

```bash
codex plugin marketplace add ./
```

```text
/plugins
```

Choose `mc-agent-oof`, install, restart Codex if needed, then ask Codex to use it:

```text
Use $mc-agent-oof while running my build commands.
```

#### Codex Desktop

Open this directory in Codex Desktop, go to **Plugins**, find `mc-agent-oof`, click **Add to Codex**, and ask Codex to use it from a new thread.

#### Cursor

Add this folder as a local Cursor plugin marketplace, install `mc-agent-oof`, then:

```text
Use mc-agent-oof while running my builds.
```

### 2. Shell wrapper (no agent needed)

```bash
bin/mc-agent-oof npm test
bin/mc-agent-oof cargo build --release
bin/mc-agent-oof sh -c './configure && make'
```

Pass-through: stdin/stdout/stderr behave exactly as if you'd run the command directly. The wrapper just listens to the exit code + stderr tail and reacts.

Symlink it onto your `PATH` if you want it everywhere:

```bash
ln -s "$(pwd)/bin/mc-agent-oof" ~/.local/bin/mc-agent-oof
```

### 3. Direct script

```bash
python3 plugins/mc-agent-oof/skills/mc-agent-oof/scripts/mc_agent_oof.py \
    --exit-code 1 \
    --command "npm test" \
    --stderr-tail "FAIL: 3 errors"
```

## Test the sounds

```bash
python3 plugins/mc-agent-oof/skills/mc-agent-oof/scripts/fetch_sounds.py
python3 plugins/mc-agent-oof/skills/mc-agent-oof/scripts/test_sounds.py --list
python3 plugins/mc-agent-oof/skills/mc-agent-oof/scripts/test_sounds.py hurt explode anvil levelup
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

Want the actual `.ogg`s straight from your Minecraft install? They live at `~/Library/Application Support/minecraft/assets/objects/<hash>` (macOS) or `~/.minecraft/assets/objects/<hash>` (Linux), but the cache mc-agent-oof populates already pulls them from Mojang's CDN — so unless you want a different version's audio, you don't need to bother.

## How it classifies

Highest priority first; first match wins.

| Pattern (in stderr) | Tier |
|---|---|
| `Segmentation fault`, `core dumped`, `panicked at`, `OutOfMemoryError`, `SIGSEGV`, `Aborted` | anvil |
| Exit code 134 / 138 / 139 | anvil |
| `error:`, `FAILED`, `fatal:`, `compilation error`, `cannot find module`, `SyntaxError` | explode |
| Any other non-zero exit | hurt |
| Exit 0, but the previous run for this `cwd:tool` failed | levelup |
| Exit 0 (no prior failure) | silence |

This is heuristic. False positives happen — a test that asserts on the literal string `"Segmentation fault"` will fire `anvil`. That's part of the joke. Don't take the tier as proof of anything.

Triumph (`levelup`) is gated on the command starting with a build-ish name (`make|cargo|npm|pnpm|yarn|bun|go|gradle|mvn|pytest|jest|vitest|tsc|eslint|...`). Running `cd /tmp` after a failed `npm test` won't fire the ding.

## Limitations

- **macOS / Linux only.** Windows users: PRs welcome.
- **Heuristic classification.** The `error:` pattern matches innocuous "error: 0 issues found" output too. Acceptable cost for the joke.
- **The shell wrapper uses `bash` process substitution.** Plain POSIX `sh` won't run it.

## License

MIT for the plugin code. The Minecraft sound files themselves are © Mojang/Microsoft and downloaded from their official CDN at runtime — they are **not** redistributed in this repository.

## Source

Plugin layout follows endless-toil's structure and the OpenAI Codex / Claude Code plugin docs:

- https://developers.openai.com/codex/plugins
- https://code.claude.com/docs/en/plugins
- https://github.com/cursor/plugins
