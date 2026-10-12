---
name: project-publishing-channels
description: Where Kernel Field Guide is submitted or listed, which listings pin a release, and which channels only the maintainer can submit to (as of 2026-10-13)
metadata:
  type: project
---

Kernel Field Guide (install name `kernel-development-skills`) was first released as immutable v0.4.1 on 2026-10-12; the latest release is v0.4.4 (e46ac37, 2026-10-13: patch-reading API checker, no guessed hardware facts). It is submitted to:

- github/awesome-copilot issue #4883: external plugin, intake and all quality gates passed, awaiting a maintainer `/approve`. Still pinned to tag v0.4.1 plus its SHA: the maintainer chose not to move it to v0.4.2 while it has no review activity. Approved listings are re-reviewed every six months.
- davepoon/buildwithclaude: PR #425 (v0.4.1) was closed unmerged 2026-10-11 with a security review asking the skill to treat oops logs, bot reports, list mail, and commit messages as data and to wait for an explicit yes before sending mail or a bot test command. v0.4.2 (101ce74) added those rules, and v0.4.3 (62eedd7) an hour later removed two reference lines that still said to follow a stable FAILED mail and to run a robot `reproduce` file. PR #435, the git-subdir entry pinned to v0.4.3 and its SHA, was merged by davepoon on 2026-10-12 after he confirmed each point of his review, so the plugin is listed there at v0.4.3, one release behind v0.4.4. Before answering a review like this, grep the references for wording that defers to mail or report text, not only the rule the reviewer named. davepoon closes PRs with security feedback instead of requesting changes; the expected response is to fix upstream, cut a new tag, and open a fresh PR pinned to it (as #424 then #426 did).
- nhivp/Awesome-Embedded PR #80: one README line, open and mergeable with no review yet (2026-10-13).

The OpenAI portal's required video walkthrough is https://github.com/user-attachments/assets/3a3c8e9d-9cb7-455e-8a04-04c9a747c858 (2 min 24 s, Remotion replay of real Codex 0.162.1 TUI sessions recorded through a pseudo-terminal in an isolated HOME and CODEX_HOME; also in the README and the v0.4.3 release notes). A GitHub user-attachment returns 404 to anonymous visitors until a saved issue, comment, or release body references it; a README reference pushed through git does not make it public.

Only the maintainer can submit (web portals or human-only forms): Anthropic Directory (claude.ai/directory/manage, plugin path `plugins/kernel-development-skills`), OpenAI plugins portal (waits on the maintainer's identity verification; the review notes, test cases, and v0.4.4 ZIP with its rebuild command are kept locally in the gitignored `demo/openai-submission/`, next to the Remotion project in `demo/walkthrough/`), agentskill.sh (a stray listing exists; the maintainer must claim the repo), mcpmarket.com, hesreallyhim/awesome-claude-code. Deliberately skipped: Gemini gallery and Antigravity (manifest conflicts), Cursor (partner-only), VoltAgent and travisvn (adoption or AI-PR rules).

**Why:** pinned listings do not follow new releases on their own, and several catalogs reject duplicate or premature resubmissions.

**How to apply:** after every release, open update PRs for the pinned entries (buildwithclaude, awesome-copilot re-review) with the new tag and SHA; check these statuses before submitting anywhere again. Related: [[feedback-kernel-skill-voice]]
