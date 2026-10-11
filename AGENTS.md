# Kernel Field Guide plugin

## Repository purpose

This repository packages the `kernel-development-skills` Agent Skill for
Claude Code, Codex, GitHub Copilot, Cursor, Gemini CLI, OpenCode, and every
other agent that reads Agent Skills, Agent Plugins manifests, or `AGENTS.md`.
`adapters/major-agent-setup.md` lists how each harness discovers and installs
it.

## Editing rules

- Commit directly to `main`. Subjects are imperative, sentence case, with no
  conventional-commit prefix and no trailing period.
- Keep `plugins/kernel-development-skills/skills/kernel-development-skills/SKILL.md`
  under 500 lines, with standing rules near the top, because some harnesses
  keep only the first few thousand tokens of a skill after compaction.
- SKILL.md frontmatter may use only `name`, `description`, `license`,
  `metadata`, and `allowed-tools`, because the Codex validator rejects any
  other key. Keep the description at or under 1024 characters with no `<` or
  `>`.
- Put detailed kernel guidance in one-level `references/` files and
  deterministic helpers in `scripts/`. A reference over 100 lines opens with a
  `Covers:` line naming its `##` sections in order, so a partial read still
  shows the whole scope; no pointers between reference files.
- Keep the skill generic: no vendor-, board-, or product-specific content, and
  no local absolute paths or machine-specific assumptions in shipped files.
- Keep the skill directory lean. Evals live in
  `plugins/kernel-development-skills/evals/`, outside the skill, because some
  harnesses load every file in a skill directory.
- `scripts/index_kernel_docs.py` writes generated indexes to a per-tree cache
  directory; never commit them. Keep the references free of tree-specific
  content.
- Name each reference for the situation it serves (`debugging.md`, not
  `debugging-testing-reference.md`), write it as practitioner notes with
  commands and the reason behind each rule, and cite `Documentation/` files
  inline at the rule they govern instead of in a list.
- Write kernel facts newer than the oldest supported LTS as "since vX.Y" with
  the older-tree alternative, and verify each against current mainline
  `Documentation/` or source before adding it.
- Scripts are stdlib-only and must run on Python 3.9: keep
  `from __future__ import annotations`, and avoid `match` and runtime `X | Y`
  unions. Do not run `ruff format` on them; they are not ruff-formatted.

## Versioning

The version lives in eight places. Change all of them together:

- `plugins/kernel-development-skills/plugin.json` (`.version`)
- `plugins/kernel-development-skills/.claude-plugin/plugin.json` (`.version`)
- `plugins/kernel-development-skills/.codex-plugin/plugin.json` (`.version`)
- `plugins/kernel-development-skills/.cursor-plugin/plugin.json` (`.version`)
- `.claude-plugin/marketplace.json` (`.plugins[0].version`)
- `.cursor-plugin/marketplace.json` (`.metadata.version` and `.plugins[0].version`)
- SKILL.md frontmatter (`metadata.version`)

`.agents/plugins/marketplace.json` has no version field by design.

## Validation

Run these before considering packaging, manifest, skill, or script work
complete:

```bash
claude plugin validate plugins/kernel-development-skills
claude plugin validate .
python3 -m py_compile plugins/kernel-development-skills/skills/kernel-development-skills/scripts/*.py
gh skill publish --dry-run
npx skills add . --list
```

If Codex system skills are installed, also run
`~/.codex/skills/.system/skill-creator/scripts/quick_validate.py` on the skill
directory and `~/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py`
on the plugin directory. Most other harnesses have no validator; when adding
one, test its install command in an isolated config home and label untested
commands in the adapters doc.

After changing the SKILL.md description, rerun the trigger suite described in
`plugins/kernel-development-skills/evals/README.md`; harnesses decide whether
to load the skill from the description alone.
