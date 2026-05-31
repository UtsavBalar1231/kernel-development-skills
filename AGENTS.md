# Kernel Development Practice Plugin

## Repository Purpose

This repository packages the `kernel-development-practice` Agent Skill for
Codex, Claude Code, OpenCode, GitHub Copilot, Gemini CLI, Cursor, Windsurf, and
other coding agents that understand Agent Skills or `AGENTS.md`.

## Editing Rules

- Keep `plugins/kernel-development-practice/skills/kernel-development-practice/SKILL.md` concise.
- Put detailed kernel guidance in one-level `references/` files and deterministic helpers in `scripts/`.
- Do not commit generated `assets/kernel-doc-index.jsonl`; regenerate it per checkout.
- Do not add local absolute paths, board-private paths, or machine-specific assumptions to runtime skill files.
- Keep RK3576/Lapis material optional and clearly scoped to repos that match that vendor tree.

## Validation

Run these checks before considering plugin packaging complete:

```bash
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  plugins/kernel-development-practice/skills/kernel-development-practice
python3 ~/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py \
  plugins/kernel-development-practice
claude plugin validate plugins/kernel-development-practice
claude plugin validate .
python3 -m py_compile plugins/kernel-development-practice/skills/kernel-development-practice/scripts/*.py
```

Use native marketplace validation when adding support for another host.
