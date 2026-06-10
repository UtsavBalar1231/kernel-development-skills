# Kernel Development Skills Plugin

## Repository Purpose

This repository packages the `kernel-development-skills` Agent Skill for
Codex, Claude Code, OpenCode, GitHub Copilot, Gemini CLI, Cursor, Windsurf, and
other coding agents that understand Agent Skills or `AGENTS.md`.

## Editing Rules

- Keep `plugins/kernel-development-skills/skills/kernel-development-skills/SKILL.md` concise.
- Put detailed kernel guidance in one-level `references/` files and deterministic helpers in `scripts/`.
- Do not commit generated `assets/` artifacts (`kernel-doc-index.jsonl`, `kernel-doc-routes.md`); regenerate them per checkout. Keep `references/doc-routes.md` curated and free of tree-specific content.
- Do not add local absolute paths, board-private paths, or machine-specific assumptions to runtime skill files.
- Keep RK3576/Lapis material optional and clearly scoped to repos that match that vendor tree.

## Validation

Run these checks before considering plugin packaging complete:

```bash
claude plugin validate plugins/kernel-development-skills
claude plugin validate .
python3 -m py_compile plugins/kernel-development-skills/skills/kernel-development-skills/scripts/*.py
```

If Codex system skills are installed, also run
`~/.codex/skills/.system/skill-creator/scripts/quick_validate.py` and
`~/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py` against the
skill and plugin directories. Keep the version field in sync across
`.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`, the marketplace
entry, and the SKILL.md `metadata`.

Use native marketplace validation when adding support for another host.
