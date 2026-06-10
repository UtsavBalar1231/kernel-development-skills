# Major Agent Setup Notes

The portable artifact is the Agent Skill at:

```text
plugins/kernel-development-skills/skills/kernel-development-skills/
```

Use native plugin marketplaces where available, and fall back to Agent Skills or
`AGENTS.md` for agents that do not have a compatible plugin marketplace.

## Codex

Use the repo-local Codex marketplace:

```bash
codex plugin marketplace add "$PWD"
codex plugin add kernel-development-skills@kernel-development-skills
```

For direct personal-skill use:

```bash
mkdir -p ~/.agents/skills
ln -s "$PWD/plugins/kernel-development-skills/skills/kernel-development-skills" \
  ~/.agents/skills/kernel-development-skills
```

## Claude Code

Use the repo-local Claude Code marketplace:

```text
/plugin marketplace add /path/to/kernel-development-skills
/plugin install kernel-development-skills@kernel-development-skills
```

For direct skill use:

```bash
mkdir -p ~/.claude/skills
ln -s "$PWD/plugins/kernel-development-skills/skills/kernel-development-skills" \
  ~/.claude/skills/kernel-development-skills
```

## OpenCode

OpenCode can discover `.agents/skills`, `.claude/skills`, and `.opencode/skills`.

```bash
mkdir -p ~/.config/opencode/skills
ln -s "$PWD/plugins/kernel-development-skills/skills/kernel-development-skills" \
  ~/.config/opencode/skills/kernel-development-skills
```

## GitHub Copilot

Copilot supports Agent Skills from project or personal skill folders. For a
repository-local install:

```bash
mkdir -p .github/skills
ln -s "$PWD/plugins/kernel-development-skills/skills/kernel-development-skills" \
  .github/skills/kernel-development-skills
```

For broad project instructions, keep a concise `AGENTS.md` in the target repo
that tells Copilot when to use the skill.

## Gemini CLI

Gemini CLI supports Agent Skills natively: user skills in `~/.gemini/skills/`,
workspace skills in `.gemini/skills/`, and extension-bundled skills.

```bash
mkdir -p ~/.gemini/skills
ln -s "$PWD/plugins/kernel-development-skills/skills/kernel-development-skills" \
  ~/.gemini/skills/kernel-development-skills
```

For older Gemini CLI versions without skill support, fall back to hierarchical
`GEMINI.md` context files: configure Gemini to read `AGENTS.md`, or create a
`GEMINI.md` that imports the shared instructions:

```markdown
# Gemini Context

Use the kernel-development-skills Agent Skill for kernel work.

@./AGENTS.md
```

## Cursor And Windsurf

Use `AGENTS.md` as the shared always-on compatibility layer. Keep it short and
point agents at the skill directory for on-demand kernel workflows. If using
Cursor rules or Windsurf rules, make the rule reference the Agent Skill path
instead of duplicating the full skill content.
