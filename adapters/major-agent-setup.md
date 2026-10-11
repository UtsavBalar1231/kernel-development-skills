# Agent harness setup

The portable artifact is one Agent Skill directory:

```text
plugins/kernel-development-skills/skills/kernel-development-skills/
```

Harnesses with a plugin system install it through the manifests in this
repository. Every other harness that reads Agent Skills uses the directory
directly, by copy or symlink.

Each entry says how its commands were checked:

- **Tested** means the command was run against this repository with an
  isolated config home, so no real harness config was touched.
- **Documented, not tested** means the command comes from the harness's
  docs and was not run here.

Paths and commands move between releases, so check the harness's own docs if
something does not match.

## Packaging files in this repository

| File | Read by |
| --- | --- |
| `.claude-plugin/marketplace.json` | Claude Code, Codex, Copilot CLI, Factory Droid, `npx skills` |
| `.agents/plugins/marketplace.json` | Codex (adds display name and install policy) |
| `.cursor-plugin/marketplace.json` | Cursor |
| `plugins/kernel-development-skills/plugin.json` (Agent Plugins 1.0) | Codex, Copilot CLI, VS Code, Cursor, Qwen Code, Kiro Powers, OpenHands |
| `plugins/kernel-development-skills/.claude-plugin/plugin.json` | Claude Code, Copilot CLI, VS Code, OpenHands, `npx skills` |
| `plugins/kernel-development-skills/.codex-plugin/plugin.json` | Codex, which overlays its `interface` block on the root manifest |
| `plugins/kernel-development-skills/.cursor-plugin/plugin.json` | Cursor |

The root `plugin.json` follows the closed Agent Plugins schema. Keep
harness-specific fields such as `displayName`, `skills`, and `interface` in
the harness-specific manifests.

## Claude Code

- Project skills: `.claude/skills/`, in the working directory and its
  parents up to the repository root.
- User skills: `~/.claude/skills/`.
- `AGENTS.md`: read only when no `CLAUDE.md` exists in or above the working
  directory. If a `CLAUDE.md` exists, import `AGENTS.md` from it with an
  `@AGENTS.md` line.

Plugin install (tested):

```bash
claude plugin marketplace add UtsavBalar1231/kernel-development-skills
claude plugin install kernel-development-skills@kernel-development-skills
```

A local clone path also works in place of `owner/repo` (tested). Inside a
session, use `/plugin marketplace add` and `/plugin install`.

Plain skill:

```bash
mkdir -p ~/.claude/skills
ln -s "$PWD/plugins/kernel-development-skills/skills/kernel-development-skills" \
  ~/.claude/skills/kernel-development-skills
```

## Codex

- Project skills: `.agents/skills/` in every directory from the working
  directory up to the repository root.
- User skills: `~/.agents/skills/`.
- System skills: `/etc/codex/skills/`.
- `AGENTS.md`: yes. Codex reads `AGENTS.override.md`, then `AGENTS.md`.

Plugin install (tested, from both `owner/repo` and a local clone path):

```bash
codex plugin marketplace add UtsavBalar1231/kernel-development-skills
codex plugin add kernel-development-skills@kernel-development-skills
```

When the plugin has a root `plugin.json`, Codex loads it as the manifest and
applies the `interface` block from `.codex-plugin/plugin.json` on top. Skills
load from `skills/`. The CLI has no validate subcommand. Use the Codex
helper scripts listed in the README instead.

The skill's `agents/openai.yaml` holds Codex UI metadata. Set
`policy.allow_implicit_invocation: false` in it to allow only explicit
`$kernel-development-skills` invocation.

## GitHub Copilot

### Copilot CLI

- Project skills: `.github/skills/`, `.claude/skills/`, `.agents/skills/`.
- User skills: `~/.copilot/skills/`, `~/.agents/skills/`.
- `AGENTS.md`: yes, the nearest one. Copilot also accepts `CLAUDE.md` and
  `GEMINI.md`.

Plugin install (documented, not tested):

```bash
copilot plugin marketplace add UtsavBalar1231/kernel-development-skills
copilot plugin install kernel-development-skills@kernel-development-skills
```

### VS Code agent mode

- Project skills: `.github/skills/`, `.claude/skills/`, `.agents/skills/`.
- User skills: `~/.copilot/skills/`, `~/.claude/skills/`, `~/.agents/skills/`.

Plugin install (documented, not tested): run "Chat: Install Plugin From
Source" from the command palette, or add the repository to the
`chat.plugins.marketplaces` setting as `owner/repo`, a git URL, or a
`file:///` path.

### Copilot coding agent and `gh skill`

The cloud coding agent reads `.github/skills/`, `.claude/skills/`, and
`.agents/skills/` in the repository it works on. Install the skill into a
repository with `gh skill`, which needs GitHub CLI 2.90.0 or later. The
remote install was tested with `--dir`; the `--agent` and `--scope` form below
was not:

```bash
gh skill install UtsavBalar1231/kernel-development-skills kernel-development-skills \
  --agent github-copilot --scope project
```

`gh skill install --from-local /path/to/kernel-development-skills
kernel-development-skills` installs from a clone (tested). `gh skill publish
--dry-run` validates the skill before a release (tested).

## Cursor

- Project skills: `.agents/skills/`, `.cursor/skills/`, including nested
  directories.
- User skills: `~/.agents/skills/`, `~/.cursor/skills/`.
- Cursor also reads `.claude/skills/` and `.codex/skills/` and their user
  equivalents.
- `AGENTS.md`: yes, at the root and in nested directories.

Plugin install (documented, not tested): open Customize, choose "From GitHub
Repository", and enter the repository URL. Cursor reads
`.cursor-plugin/marketplace.json`. For a local test, place the plugin
directory under `~/.cursor/plugins/local/`. The Cursor plugin template's
`scripts/validate-template.mjs` passes against this repository.

## Gemini CLI

- Workspace skills: `.gemini/skills/` or `.agents/skills/`. When both hold
  the same skill, `.agents/skills/` wins.
- User skills: `~/.gemini/skills/` or `~/.agents/skills/`.
- `AGENTS.md`: not read by default. Gemini reads `GEMINI.md`. To read both,
  set `"context": {"fileName": ["AGENTS.md", "GEMINI.md"]}` in
  `settings.json`.
- Workspace skills need folder trust. Skills nested more than one level deep
  under a skills root are not discovered.

Skill install (tested, from the repository and from a local path):

```bash
gemini skills install https://github.com/UtsavBalar1231/kernel-development-skills \
  --path plugins/kernel-development-skills/skills/kernel-development-skills
gemini skills install ./plugins/kernel-development-skills/skills/kernel-development-skills
```

This repository has no `gemini-extension.json`. `gemini extensions install`
has no sub-path option, so it needs an extension manifest at the repository
root, and this plugin lives in a subdirectory.

The geminicli.com docs say Antigravity CLI replaced Gemini CLI on
2026-06-18, for unpaid-tier and Google One users.

## Google Antigravity

- Project skills: `.agents/skills/`. The legacy path is `.agent/skills/`.
- Global skills for Antigravity 2.0 and the IDE: `~/.gemini/config/skills/`.
- Global skills for the Antigravity CLI: `~/.gemini/antigravity-cli/skills/`.
- `AGENTS.md`: unverified.

Plugin install (documented, not tested):

```bash
agy plugin install ./plugins/kernel-development-skills
```

It is unverified whether `agy plugin install` accepts a repository
subdirectory or the Agent Plugins root manifest. If it does not, copy the
skill directory into one of the skill paths above.

## Factory Droid

- Project skills: `.factory/skills/`, `.agents/skills/`.
- User skills: `~/.factory/skills/`, `~/.agents/skills/`.
- `AGENTS.md`: yes.

Plugin install (documented, not tested). Droid falls back to
`.claude-plugin/marketplace.json` when no `.factory-plugin/` exists:

```bash
droid plugin marketplace add UtsavBalar1231/kernel-development-skills
droid plugin install kernel-development-skills@kernel-development-skills --scope user
```

## Augment and Auggie

- Project skills: `.augment/skills/`, `.claude/skills/`, `.agents/skills/`.
- User skills: the same paths under `~`.
- `AGENTS.md`: unverified.

Plugin install (documented, not tested):

```bash
auggie plugin marketplace add UtsavBalar1231/kernel-development-skills
auggie plugin install kernel-development-skills@kernel-development-skills
```

Augment documents `.claude-plugin` compatibility but not the marketplace
path. If the marketplace add fails, use a skill path above.

## Qwen Code

- Project skills: `.qwen/skills/`.
- User skills: `~/.qwen/skills/`.
- `AGENTS.md`: unverified. Qwen's default context file is `QWEN.md`.

Qwen extensions load Agent Plugins manifests and convert Claude plugins.
Install (documented, not tested):

```bash
qwen extensions install UtsavBalar1231/kernel-development-skills
```

It is unverified whether Qwen resolves the plugin in a repository
subdirectory. If it does not, symlink the skill into `~/.qwen/skills/`.

## Kiro

- Project skills: `.kiro/skills/`, used by the IDE, CLI, and web.
- User skills: `~/.kiro/skills/`, used by the IDE only.
- Kiro CLI custom agents need `skill://.kiro/skills/*/SKILL.md` in their
  `resources`.
- `AGENTS.md`: yes.

Install in the IDE (documented, not tested): open Agent Steering & Skills,
choose "+", then "Import a skill", and give the GitHub URL of the skill
folder, not the repository root.

## OpenHands

- Project skills: `.agents/skills/`. The legacy paths are
  `.openhands/skills/` and `.openhands/microagents/`.
- User skills: `~/.agents/skills/`.
- `AGENTS.md`: yes.

Plugin load (documented, not tested): `openhands --plugin
github:<owner>/<repo>` takes an optional subpath and `#ref`. Point it at
`plugins/kernel-development-skills`, or list the source under
`[plugins] sources` in `~/.openhands/config.toml`.

## Amp

- Project skills: `.agents/skills/` in the working directory and its
  parents, and `.claude/skills/`.
- User skills: `~/.config/agents/skills/`, `~/.agents/skills/`,
  `~/.config/amp/skills/`, `~/.claude/skills/`.
- `AGENTS.md`: yes. Amp falls back to `AGENT.md` and `CLAUDE.md`.

Install (documented, not tested):

```bash
amp skill add UtsavBalar1231/kernel-development-skills --global
```

## Harnesses that only need a copy or symlink

These harnesses read `SKILL.md` directories but have no plugin format this
repository targets. Symlink the skill directory into one of their skill
paths. None of these was tested here.

```bash
SKILL="$PWD/plugins/kernel-development-skills/skills/kernel-development-skills"
mkdir -p ~/.agents/skills
ln -s "$SKILL" ~/.agents/skills/kernel-development-skills
```

`~/.agents/skills/` is read by:

- Codex, Cursor, and Copilot
- Gemini CLI and OpenCode
- Windsurf/Devin Desktop and Amp
- Goose, Kilo Code, and Roo Code
- Junie and Zed
- Warp and OpenHands
- Augment and Droid
- Kimi CLI, Crush, and Mistral Vibe

These harnesses do not read `~/.agents/skills/`:

- Claude Code reads `~/.claude/skills/`.
- Kiro reads `~/.kiro/skills/`.
- Antigravity, Continue, and Qwen Code use their own paths, listed in this
  document.

| Harness | Project paths | User paths | Reads `AGENTS.md` |
| --- | --- | --- | --- |
| Windsurf / Devin Desktop | `.devin/skills/` (preferred), `.windsurf/skills/` (legacy), `.agents/skills/`, `.claude/skills/` when Claude config reading is on | `~/.config/devin/skills/`, `~/.codeium/windsurf/skills/`, `~/.agents/skills/` | Yes |
| Devin for Terminal | `.devin/skills/` | `~/.config/devin/skills/` | Unverified |
| OpenCode | `.opencode/skills/`, `.claude/skills/`, `.agents/skills/` | `~/.config/opencode/skills/`, `~/.claude/skills/`, `~/.agents/skills/` | Yes, falls back to `CLAUDE.md` |
| Goose | `.agents/skills/`, `.goose/skills/`, `.claude/skills/` | `~/.agents/skills/`, `~/.claude/skills/` | Unverified |
| Cline | `.cline/skills/`, `.clinerules/skills/`, `.claude/skills/` | `~/.cline/skills/` | Yes |
| Roo Code | `.roo/skills/`, `.agents/skills/` | `~/.roo/skills/`, `~/.agents/skills/` | Unverified |
| Kilo Code | `.kilo/skills/`, `.agents/skills/` | `~/.kilo/skills/`, `~/.agents/skills/` | Yes |
| Continue | `.continue/skills/`, `.claude/skills/` | `~/.continue/skills/` | Yes, also `AGENT.md` and `CLAUDE.md` |
| Zed | `.agents/skills/` in trusted worktrees, flat layout only | `~/.agents/skills/` | Unverified |
| JetBrains Junie | `.junie/skills/`, `.agents/skills/` in trusted projects | `~/.junie/skills/`, `~/.agents/skills/` | Yes, also `.junie/AGENTS.md` |
| Warp | `.agents/skills/`, plus `skills/` under `.claude`, `.codex`, `.cursor`, `.gemini`, `.github`, and other agent dirs | Same paths under `~` | Unverified |
| Crush | `.agents/skills/`, `.crush/skills/`, `.claude/skills/` | `~/.config/agents/skills/`, `~/.config/crush/skills/`, `~/.agents/skills/`, `~/.claude/skills/` | Yes |
| Mistral Vibe | `.agents/skills/`, `.vibe/skills/` in trusted folders | `~/.vibe/skills/`, `~/.agents/skills/` | Yes |
| Kimi CLI | `.kimi/skills/`, `.claude/skills/`, `.codex/skills/`, `.agents/skills/` | `~/.config/agents/skills/`, `~/.agents/skills/`, `~/.kimi/skills/` | Unverified |

## Cross-harness installers

`npx skills` (vercel-labs/skills) knows the skill paths of about 60 agents.
It finds this skill through `.claude-plugin/marketplace.json`. Listing was
tested, and so was a project-scope install with `-a claude-code`:

```bash
npx skills add UtsavBalar1231/kernel-development-skills -s kernel-development-skills -a <agent>
npx skills add . --list
```

`gh skill install` covers a similar list of agents (see `gh skill install
--help`).

`openskills` installs the skill and then writes an `<available_skills>` block
into `AGENTS.md` with `npx openskills sync`. That helps harnesses that read
`AGENTS.md` but have no skill loader. Documented, not tested.

## Aider

Aider has no Agent Skills support and does not read `AGENTS.md`
automatically. Load the skill as read-only context instead, either on the
command line:

```bash
aider --read /path/to/kernel-development-skills/plugins/kernel-development-skills/skills/kernel-development-skills/SKILL.md
```

or in `.aider.conf.yml`:

```yaml
read:
  - AGENTS.md
  - /path/to/kernel-development-skills/plugins/kernel-development-skills/skills/kernel-development-skills/SKILL.md
```

Then open individual `references/` files with `/read` when the task needs
them. Documented, not tested.

JetBrains AI Assistant support was not verified. For JetBrains IDEs, use
Junie, or Copilot agent mode, which documents skill support in JetBrains
IDEs.
