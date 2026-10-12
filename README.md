# Kernel Field Guide

[![ci](https://github.com/UtsavBalar1231/kernel-development-skills/actions/workflows/ci.yml/badge.svg)](https://github.com/UtsavBalar1231/kernel-development-skills/actions/workflows/ci.yml)
[![release](https://img.shields.io/github/v/release/UtsavBalar1231/kernel-development-skills)](https://github.com/UtsavBalar1231/kernel-development-skills/releases)
[![license](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

An [Agent Skill](https://agentskills.io), installed as
`kernel-development-skills`, that teaches coding agents to work on the Linux®
kernel the way experienced kernel engineers do: drivers, devicetree, Kconfig,
debugging, testing, patch submission, regressions, and stable, LTS, and vendor
trees. One portable directory, packaged for Claude Code, Codex, GitHub Copilot,
Cursor, Gemini CLI, and 20+ other harnesses.

> [!TIP]
> Any harness, one line:
> `npx skills add UtsavBalar1231/kernel-development-skills -s kernel-development-skills -a <agent>`

<details>
<summary><b>Walkthrough video (2 min 40 s)</b></summary>

The install and three real Codex CLI sessions with the skill: a driver patch
review, a board fan that never spins, and a syzbot report that carries an
injected instruction. Recorded in a fresh Codex home with only this plugin
installed; sped up where the video says so.

https://github.com/user-attachments/assets/e6b773a1-d5bf-4a1c-8238-92714d599be2

</details>

## Install

<details>
<summary><b>Claude Code</b></summary>

```bash
claude plugin marketplace add UtsavBalar1231/kernel-development-skills
claude plugin install kernel-development-skills@kernel-development-skills
```

Inside a session use `/plugin marketplace add` and `/plugin install`. For local
development: `claude --plugin-dir ./plugins/kernel-development-skills`.

</details>

<details>
<summary><b>Codex</b></summary>

```bash
codex plugin marketplace add UtsavBalar1231/kernel-development-skills
codex plugin add kernel-development-skills@kernel-development-skills
```

From a local clone, pass the clone path (for example `"$PWD"`) to
`codex plugin marketplace add`.

</details>

<details>
<summary><b>GitHub Copilot (CLI and VS Code)</b></summary>

```bash
copilot plugin marketplace add UtsavBalar1231/kernel-development-skills
copilot plugin install kernel-development-skills@kernel-development-skills
```

VS Code agent mode: run "Chat: Install Plugin From Source" and enter the
repository, or add it to the `chat.plugins.marketplaces` setting.

</details>

<details>
<summary><b>Cursor</b></summary>

Open Customize, choose "From GitHub Repository", and enter the repository URL.
Cursor reads `.cursor-plugin/marketplace.json`, and also discovers skills in
`.agents/skills/` and `.cursor/skills/` without a plugin.

</details>

<details>
<summary><b>Gemini CLI</b></summary>

```bash
gemini skills install https://github.com/UtsavBalar1231/kernel-development-skills \
  --path plugins/kernel-development-skills/skills/kernel-development-skills
```

From a local clone, pass the skill directory directly.

</details>

<details>
<summary><b><code>npx skills</code> or <code>gh skill</code> (any harness)</b></summary>

```bash
npx skills add UtsavBalar1231/kernel-development-skills -s kernel-development-skills -a <agent>
gh skill install UtsavBalar1231/kernel-development-skills kernel-development-skills --agent <agent>
```

Both write the skill where the chosen agent looks. `--help` lists agent names.

</details>

<details>
<summary><b>Everything else</b></summary>

[`adapters/major-agent-setup.md`](adapters/major-agent-setup.md) covers
discovery paths, install commands, and `AGENTS.md` support for Windsurf/Devin,
OpenCode, Amp, Goose, Kiro, Cline, Roo Code, Kilo Code, Continue, Zed, Junie,
Factory Droid, Qwen Code, Antigravity, Augment, Warp, OpenHands, Crush, Mistral
Vibe, Kimi CLI, and Aider.

</details>

> [!NOTE]
> Claude Code, Codex, Gemini CLI, `gh skill`, and `npx skills` installs were
> tested against this repository. The Copilot and Cursor steps come from their
> documentation.

## What the agent gets

```text
plugins/kernel-development-skills/skills/kernel-development-skills/
├── SKILL.md       principles, gotchas, verification matrix, routing table
├── references/    11 situation guides, each opened only when the task needs it
└── scripts/       change triage, deprecated-API checker, Documentation/ indexer
```

<details>
<summary><b>The 11 references</b></summary>

| Reference | Opened when |
| --- | --- |
| `tree.md` | working outside plain mainline: linux-next, subsystem, stable, Android GKI, vendor BSP |
| `archaeology.md` | finding why code is the way it is, who owns it, how others solved it |
| `build.md` | configuring, building, cross-compiling, fast VM boots, per-commit builds |
| `drivers.md` | writing driver code |
| `devicetree.md` | bindings, DTS, overlays, schema checks |
| `debugging.md` | any failure, organized by symptom |
| `testing.md` | KUnit, kselftest, fault injection, fuzzing, evidence |
| `review.md` | reviewing a patch, with a catalog of bug classes reviewers catch |
| `patches.md` | commit messages, tags, AI attribution, sending a series |
| `regressions.md` | regression reports, syzbot, kernel test robot, KernelCI |
| `stable.md` | stable rules, backports, vendor intake, security and CVEs |

</details>

## Development

<details>
<summary><b>Validate</b></summary>

```bash
claude plugin validate plugins/kernel-development-skills
claude plugin validate .
python3 -m py_compile plugins/kernel-development-skills/skills/kernel-development-skills/scripts/*.py
gh skill publish --dry-run
npx skills add . --list
```

With Codex system skills installed, also run
`~/.codex/skills/.system/skill-creator/scripts/quick_validate.py` on the skill
directory and `~/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py`
on the plugin directory. In Claude Code, `/validate-plugin` runs all of this.

</details>

<details>
<summary><b>Evals</b></summary>

Trigger and behavior evals live in
[`plugins/kernel-development-skills/evals/`](plugins/kernel-development-skills/evals/),
outside the skill directory, because some harnesses load every file in a skill
directory. Run the 20-query trigger suite with:

```bash
claude plugin eval plugins/kernel-development-skills --tag trigger \
  --ablation none --runs 3 --threshold 0.5 --model sonnet --no-publish
```

</details>

<details>
<summary><b>Index a kernel tree's documentation</b></summary>

```bash
python3 plugins/kernel-development-skills/skills/kernel-development-skills/scripts/index_kernel_docs.py \
  /path/to/linux [--out DIR]
```

Writes a route map and a JSONL index to a per-tree directory under
`~/.cache/kernel-development-skills/` unless `--out` names another one.
Nothing is written inside the skill.

</details>

<details>
<summary><b>Versioning and conventions</b></summary>

The version lives in eight places, listed in [`AGENTS.md`](AGENTS.md); in
Claude Code, `/bump-version <x.y.z>` updates all of them. Research provenance
is kept in `research/sources.tsv` and is never loaded at runtime.

</details>

## License and trademarks

MIT. The skill collects no data and makes no network calls; see
[`PRIVACY.md`](PRIVACY.md) and [`SECURITY.md`](SECURITY.md).

Linux® is the registered trademark of Linus Torvalds in the U.S. and other
countries. This project is not affiliated with or endorsed by the Linux
Foundation or the kernel maintainers.
