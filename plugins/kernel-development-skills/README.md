# Kernel Field Guide

An Agent Skill that gives coding agents the working habits of experienced Linux
kernel engineers. It covers driver code and teardown order, devicetree bindings
and DTS, Kconfig, debugging by symptom, KUnit and kselftest, patch review and
submission with correct tags, regression and bot reports, and stable, LTS,
Android, and vendor trees. Guidance that changed between kernel releases is
marked "since vX.Y", so it holds on older trees too.

The agent loads the short `SKILL.md` first and opens one of eleven reference
files only when the task needs it. Three local Python scripts triage changed
paths, flag deprecated driver APIs, and index a tree's `Documentation/`.

## Example prompts

- "My I2C temperature sensor never probes on this board. Find out why."
- "Review this driver patch before I send it: check teardown order, locking,
  and the commit tags."
- "syzbot reported a use-after-free in my driver. Help me reproduce it, fix it,
  and draft the `#syz test` reply for me to send."

## Install

```bash
claude plugin marketplace add UtsavBalar1231/kernel-development-skills
claude plugin install kernel-development-skills@kernel-development-skills
```

Other harnesses (Codex, Copilot, Cursor, Gemini CLI, and more) are covered in
the repository README:
https://github.com/UtsavBalar1231/kernel-development-skills

## Data and network use

The skill collects nothing and makes no network calls. The scripts read only
the kernel tree you point them at; see `PRIVACY.md` in the repository.

## License

MIT. See `LICENSE`.
