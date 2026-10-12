# Changelog

All notable changes to this project are listed here. Versions follow
[semantic versioning](https://semver.org/).

## Unreleased

### Added

- `check_kernel_api_patterns.py` reads a `.diff`, a `git format-patch`
  `.patch`, or a b4 `.mbx` and scans only the lines it adds, reporting
  post-patch line numbers, so a patch under review no longer has to be applied
  first. Mail headers, the commit message, and the signature are skipped.

## 0.4.3 (2026-10-12)

### Security

- Two references still told the agent to act on text from a mail. On a stable
  "FAILED: patch" notice they said to follow its commands, which end with
  `git commit -s` and `git send-email`. On a kernel test robot report they
  said to run its reproduce commands, which switch branches and download a
  toolchain. Both now read that text as data and work in a separate worktree
  so the current branch stays as it was. The backport's sign-off and send are
  left to the human submitter, and the robot's `reproduce` file runs only
  after an explicit yes.
- regzbot commands, `kci-dev checkout` test submissions, and stable backport
  sends now carry the explicit-yes rule where the references give them.

### Changed

- The plugin README's syzbot example asks for a drafted `#syz test` reply
  instead of a sent one.

## 0.4.2 (2026-10-12)

### Security

- The skill now treats oops and console logs, bot reports, mailing-list mail,
  commit messages, and code comments as data, not instructions. It no longer
  runs a command, sends a reply, or changes the tree because such text says
  to.
- Replies to a list or a bot, including `#syz` commands, and real `b4 send` or
  `git send-email` runs now wait for an explicit yes from the user. The dry
  runs (`b4 send -o`, `b4 send --reflect`) still run without asking.

## 0.4.1 (2026-10-12)

### Security

- `triage_kernel_change.py` and `check_kernel_api_patterns.py` now reject an
  `--against` value that starts with `-`. Before this, a value such as
  `--against=--output=PATH` reached `git diff` as an option and made it write a
  file at PATH.

### Added

- Plugin README with example prompts, a LICENSE copy inside the plugin, an
  icon, and directory listing fields for the Anthropic and OpenAI catalogs.
- `PRIVACY.md`, `SECURITY.md`, `CONTRIBUTING.md`, this changelog, a CI
  workflow, and Dependabot for GitHub Actions.

### Changed

- Display name is now Kernel Field Guide. The install name stays
  `kernel-development-skills`.
- Every reference opens with a `Covers:` line listing its sections.
- The ruff rule set is pinned so newer ruff defaults cannot break the Python
  3.9 floor.

## 0.4.0 (2026-10-12)

- Rewrote the skill around working situations: eleven references (tree,
  archaeology, build, drivers, devicetree, debugging, testing, review, patches,
  regressions, stable) written as practitioner notes and checked against
  mainline v7.3-rc6.
- Removed all vendor-specific content.
- Packaged for more harnesses: an Agent Plugins manifest, Cursor plugin files,
  and install docs for about 25 harnesses.
- Added a 20-case trigger eval suite and six behavior evals.

## 0.3.0 (2026-06-10)

- Audited the skill format and kernel content against the Agent Skills
  standard and mainline documentation, and fixed every finding.

## 0.2.0 (2026-05-31)

- Added driver API and review guidance and an advisory API pattern checker.

## 0.1.0 (2026-05-31)

- Initial plugin, renamed to `kernel-development-skills` before publishing.
