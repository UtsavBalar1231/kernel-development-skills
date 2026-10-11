---
name: project-publishing-channels
description: Where Kernel Field Guide is submitted or listed, which listings pin a release, and which channels only the maintainer can submit to (as of 2026-10-12)
metadata:
  type: project
---

Kernel Field Guide (install name `kernel-development-skills`) was first released as immutable v0.4.1 on 2026-10-12 and submitted to:

- github/awesome-copilot issue #4883: external plugin, intake and all quality gates passed, awaiting a maintainer `/approve`. Pinned to tag v0.4.1 plus its SHA; approved listings are re-reviewed every six months.
- davepoon/buildwithclaude PR #425: git-subdir entry pinned to v0.4.1 and its SHA.
- nhivp/Awesome-Embedded PR #80: one README line.

Only the maintainer can submit (web portals or human-only forms): Anthropic Directory (claude.ai/directory/manage, plugin path `plugins/kernel-development-skills`), OpenAI plugins portal (identity verification), agentskill.sh, mcpmarket.com, hesreallyhim/awesome-claude-code. Deliberately skipped: Gemini gallery and Antigravity (manifest conflicts), Cursor (partner-only), VoltAgent and travisvn (adoption or AI-PR rules).

**Why:** pinned listings do not follow new releases on their own, and several catalogs reject duplicate or premature resubmissions.

**How to apply:** after every release, open update PRs for the pinned entries (buildwithclaude, awesome-copilot re-review) with the new tag and SHA; check these statuses before submitting anywhere again. Related: [[feedback-kernel-skill-voice]]
