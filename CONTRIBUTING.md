# Contributing

Corrections and additions from people who work on the kernel are the most
useful contributions: an API that changed in a release the references miss, a
review trap they do not list, or a harness install path that moved.

## Before you open a pull request

- Read [`AGENTS.md`](AGENTS.md). It holds the repository rules: generic
  content only, references named for the situation they serve, `Covers:` lines,
  Python 3.9 stdlib-only scripts, and the eight places the version lives.
- Back every kernel fact with a source: a `Documentation/` path, a commit, or a
  header in current mainline. Write facts newer than v6.1 as "since vX.Y".
- Run the checks:

  ```bash
  claude plugin validate --strict plugins/kernel-development-skills
  claude plugin validate --strict .
  python3 -m py_compile plugins/kernel-development-skills/skills/kernel-development-skills/scripts/*.py
  ruff check .
  npx skills add . --list
  ```

  CI runs these and more on every pull request. If you change the SKILL.md
  description, also run the trigger suite in
  `plugins/kernel-development-skills/evals/README.md`.

## Commits

Imperative, sentence-case subjects with no conventional-commit prefix. Explain
why in the body.

## AI-assisted contributions

Welcome, with the same disclosure the skill teaches for kernel patches: say in
the pull request which tools helped and how you checked the result. You are
responsible for every line you submit.
