# Major Agent Setup Notes

The portable artifact is the Agent Skill at:

```text
plugins/kernel-development-practice/skills/kernel-development-practice/
```

Use native plugin marketplaces where available, and fall back to Agent Skills or
`AGENTS.md` for agents that do not have a compatible plugin marketplace.

## Codex

Use the repo-local Codex marketplace:

```bash
codex plugin marketplace add "$PWD"
codex plugin add kernel-development-practice@kernel-development-practice
```

For direct personal-skill use:

```bash
mkdir -p ~/.agents/skills
ln -s "$PWD/plugins/kernel-development-practice/skills/kernel-development-practice" \
  ~/.agents/skills/kernel-development-practice
```

## Claude Code

Use the repo-local Claude Code marketplace:

```text
/plugin marketplace add /path/to/kernel-development-practice-plugin
/plugin install kernel-development-practice@kernel-development-practice
```

For direct skill use:

```bash
mkdir -p ~/.claude/skills
ln -s "$PWD/plugins/kernel-development-practice/skills/kernel-development-practice" \
  ~/.claude/skills/kernel-development-practice
```

## OpenCode

OpenCode can discover `.agents/skills`, `.claude/skills`, and `.opencode/skills`.

```bash
mkdir -p ~/.config/opencode/skills
ln -s "$PWD/plugins/kernel-development-practice/skills/kernel-development-practice" \
  ~/.config/opencode/skills/kernel-development-practice
```

## GitHub Copilot

Copilot supports Agent Skills from project or personal skill folders. For a
repository-local install:

```bash
mkdir -p .github/skills
ln -s "$PWD/plugins/kernel-development-practice/skills/kernel-development-practice" \
  .github/skills/kernel-development-practice
```

For broad project instructions, keep a concise `AGENTS.md` in the target repo
that tells Copilot when to use the skill.

## Gemini CLI

Gemini CLI primarily consumes hierarchical `GEMINI.md` context files. Configure
Gemini to read `AGENTS.md`, or create a `GEMINI.md` that imports the shared
instructions:

```markdown
# Gemini Context

Use the kernel-development-practice Agent Skill for kernel work.

@./AGENTS.md
```

## Cursor And Windsurf

Use `AGENTS.md` as the shared always-on compatibility layer. Keep it short and
point agents at the skill directory for on-demand kernel workflows. If using
Cursor rules or Windsurf rules, make the rule reference the Agent Skill path
instead of duplicating the full skill content.
