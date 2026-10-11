---
name: feedback-kernel-skill-voice
description: How the user wants kernel skill content organized and written (practitioner voice, situation-named files) and how READMEs should be laid out (collapsible, little scrolling)
metadata:
  type: feedback
---

Write kernel skill references the way veteran kernel engineers think and work, not as a topic taxonomy. Name each file for the situation it serves (`debugging.md`, `review.md`, `stable.md`), organize debugging by symptom, put commands and the reason behind each rule first, and cite `Documentation/` files inline at the rule they govern.

**Why:** the user rejected a set of references with names like "driver-api-cookbook", "advanced-tooling", "doc-routes", each opening with "Contents" and "Source map" boilerplate and generic numbered loops, saying it "sounds AI generated". They asked to think like veteran kernel engineers, researchers, architects, and hackers.

**How to apply:**
- No "Source map", "Overview", or generic step lists; tables only for symptom/meaning or old/new API mappings.
- Write one exemplar file yourself first and give it to any parallel writers as the style sample; a constraint list alone reproduces the template voice.
- Keep SKILL.md small with a "read X when Y" routing table so references load lazily; the user checks for this.
- READMEs for GitHub use `<details>` per install target, `> [!TIP]`/`> [!NOTE]` alerts, and collapsed dev sections, so the page fits about one screen.

Related: [[project-kernel-skill-generic]]
