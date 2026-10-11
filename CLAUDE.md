# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

@AGENTS.md

## Claude Code specifics

- Change the version with `/bump-version <x.y.z>`; it updates all eight locations listed in AGENTS.md.
- Run `/validate-plugin` before calling packaging, skill, or script work done.
- Test install commands with a temporary `CLAUDE_CONFIG_DIR`, `CODEX_HOME`, or `HOME` so your own harness configs stay untouched.
