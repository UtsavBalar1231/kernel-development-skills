# Kernel Development Skills — Format & Content Audit (June 2026)

Audit of the `kernel-development-skills` package against (a) the current Agent
Skills open standard and host-specific formats (Claude Code, Codex, Gemini CLI,
Copilot), (b) 2025–2026 skill-authoring best-practice guidance, and (c) the
latest mainline kernel documentation in Linus's tree.

## Methodology

Four parallel review passes, each independently verifying claims against
primary sources:

1. **Format & packaging** — live fetches of `code.claude.com/docs` (skills,
   plugins-reference, plugin-marketplaces), `platform.claude.com` skill
   authoring best practices, the `openai/skills` repository, Gemini CLI docs,
   and GitHub Copilot docs; `claude plugin validate` executed locally.
2. **Kernel process content** (`kernel-workflow.md`, `debugging-testing.md`,
   `ci-regression.md`) — verified against `Documentation/process/`,
   `Documentation/dev-tools/`, and `Documentation/admin-guide/` in mainline
   master, plus b4, KernelCI, and TuxSuite current documentation.
3. **Driver/DT content** (`driver-api-cookbook.md`,
   `driver-review-checklists.md`, `device-tree-drivers.md`) — verified against
   mainline `Documentation/`, kbuild makefiles, and current headers
   (`platform_device.h`, `pm.h`, `pm_runtime.h`, `regmap.h`, `cleanup.h`).
4. **Scripts & remaining refs** — all four Python helpers executed against
   fixtures; `advanced-tooling.md`, `lapis-rk3576.md`, `doc-routes.md`, and
   `research/sources.tsv` reviewed for currency and internal consistency.

Access note: `docs.kernel.org` and `anthropic.com`/`agentskills.io` returned
HTTP 403 to the sandbox; kernel claims were verified against the
content-identical RST sources in `github.com/torvalds/linux` master, and spec
claims against the fetchable `code.claude.com`/`platform.claude.com` pages plus
corroborating search results (noted inline where confidence is medium).

## Executive summary

The package is in unusually good shape for a multi-host skill. Every manifest
is schema-correct for its host (`claude plugin validate` passes for both the
plugin and the marketplace; `.codex-plugin/plugin.json`,
`.agents/plugins/marketplace.json`, and `agents/openai.yaml` all match
documented Codex conventions). `SKILL.md` is a textbook progressive-disclosure
layout: valid frontmatter, 87 lines (guidance: under 500), references exactly
one level deep, degrees-of-freedom handled correctly (hard rules vs advisory
tooling). On the content side, all checked command syntax in the process and
debugging references is accurate against current mainline docs, and the
deprecated-API table verifies row-by-row against `deprecated.rst`.

That said, the audit found **6 high-severity issues** (2 factually wrong
commands in the DT reference, 3 script bugs, 1 committed artifact violating the
repo's own rules), **~18 medium issues**, and a set of modern-practice gaps
(cleanup.h guards, void `remove()`, b4 workflow, native Gemini skills support).

| Severity | Count | Areas |
| --- | --- | --- |
| High | 6 | device-tree-drivers.md (2), scripts (3), doc-routes.md (1) |
| Medium | ~18 | tags/process (5), packaging/format (5), scripts/generator (7), lapis (1) |
| Low | ~20 | wording, omissions, portability nits |

## High-severity findings

### H1. `DTB_CHECKER_FLAGS=-m` is not a real kbuild variable
`references/device-tree-drivers.md:88` recommends
`make dtbs_check DT_SCHEMA_FILES=<…> DTB_CHECKER_FLAGS=-m`. The actual variable
is `DT_CHECKER_FLAGS` (`scripts/Makefile.dtbs`:
`DT_CHECKER_FLAGS ?= $(if $(DT_SCHEMA_FILES),-l $(DT_SCHEMA_FILES),-m)`), so
the flag is silently ignored — and if corrected naively, `-m` is already the
default when `DT_SCHEMA_FILES` is unset, and setting it explicitly *overrides
the `-l` filtering*, breaking schema selection. Current `writing-schema.rst`
shows plainly `make dtbs_check DT_SCHEMA_FILES=trivial-devices.yaml`.
**Fix:** `make dtbs_check DT_SCHEMA_FILES=<schema-or-pattern>` (optionally note
colon-separated lists and partial-path patterns like `/gpio/`).

### H2. `make <board>.dtbs` is not a valid target
`references/device-tree-drivers.md:89`. The top-level Makefile provides
`%.dtb`, `%.dtbo`, and `dtbs`; there is no `%.dtbs` pattern, and arm64 paths
include the vendor subdir.
**Fix:** `make <vendor>/<board>.dtb` (arm64) / `make <board>.dtb` (arm), or
`make dtbs`.

### H3. `lstrip("./")` mangles dot-leading paths in two scripts
`scripts/triage_kernel_change.py:76,204` and
`scripts/check_lapis_guardrails.py:81`. `lstrip("./")` strips *any* run of `.`
and `/`, not the `./` prefix. Verified: `.config` becomes `config` and misses
the Kconfig triage branch; any path under `.agents/`, `.github/` etc. is
mangled, fails the existence check, and is silently never scanned by the
guardrail checker.
**Fix:** `path.removeprefix("./")` (Python ≥3.9) or
`re.sub(r"^(\./)+", "", path)`.

### H4. Direct-`make` detector flags plain English prose
`scripts/check_lapis_guardrails.py:19` — `DIRECT_MAKE_RE` matches the word
"make" after any whitespace. Verified against the repo's own files: it warns on
`SKILL.md:10` ("Use this skill to **make** kernel changes"), `SKILL.md:34`, and
`debugging-testing.md:123`. 3 of 9 hits in a self-scan are prose false
positives.
**Fix:** require command position plus a kernel-target/flag context, e.g.
`make\s+(-|[A-Za-z._/]+=|\w*config|dtbs|Image|modules|C=|W=)`, or only scan
fenced code blocks in `.md` files.

### H5. `index_kernel_docs.py` writes machine-local absolute paths into a committed artifact
`scripts/index_kernel_docs.py:273` emits
``Kernel root: `{args.kernel_root.resolve()}` `` (verified:
`Kernel root: /tmp/kroot`). The committed `references/doc-routes.md:3` instead
says "generated from the local kernel checkout used by the maintainer" — i.e.
it was hand-scrubbed after generation, and every regeneration reintroduces an
`AGENTS.md` violation ("Do not add local absolute paths… to runtime skill
files"). The header therefore also does not round-trip (doc-routes.md:7 vs the
script's actual output).
**Fix:** add a `--redact-root` behavior (default on) emitting a fixed
placeholder, and make the generated header match the committed wording.

### H6. Committed `doc-routes.md` leaks board-private vendor paths
`references/doc-routes.md:562-587` lists bindings that exist only in the
private vendor tree (`pamir-ai,hwinfo.yaml`,
`pamir-ai,lapis-charge-manager.yaml`, `fpc,fpc2534.yaml`, `awinic,aw35615.yaml`,
`silergy,sy6862c.yaml`, `rockchip,i3c-master.yaml`, `lt7911d.txt` — all 404 on
mainline). This violates `AGENTS.md:14` (no board-private paths in runtime
skill files) and the spirit of `AGENTS.md:13` (generated artifacts are
regenerated per checkout, not committed).
**Fix:** either stop committing `doc-routes.md` (treat it like the JSONL), or
strip the `lapis`/`pamir`/`denali` keyword sections and per-directory counts
from the committed copy, keeping only the evergreen Curated Routes +
regeneration instructions.

## Medium-severity findings

### Kernel process content

- **M1. Tag ordering** — `kernel-workflow.md:58-64,71-72` orders `Closes:`
  before `Reported-by:`. Upstream `submitting-patches.rst` (and checkpatch's
  `BAD_REPORTED_BY_LINK`) require `Closes:` to immediately follow
  `Reported-by:`. Also state the `Link:` vs `Closes:` distinction explicitly.
- **M2. regzbot caret form** — `kernel-workflow.md:104-108` and
  `ci-regression.md:34-39` show only `#regzbot ^introduced:`. The caret form is
  for *replying to someone else's report*; a fresh report uses
  `#regzbot introduced: <range>`. Document both (plus `fix:`/`monitor:`).
- **M3. Stable tag annotations missing** — `kernel-workflow.md:74,115` gives
  only bare `Cc: stable@vger.kernel.org`. `stable-kernel-rules.rst` documents
  `# 6.1.x` version scoping, prerequisite syntax, `# after -rc3`, and
  `Cc: <stable+noautosel@kernel.org> # reason` (AUTOSEL opt-out). Add at least
  the version annotation and noautosel.
- **M4. Regression fixes omit `Closes:`** — `ci-regression.md:44-52` lists
  `Fixes:` + `Cc: stable` but not the `Closes:`/`Link:` tag pointing at the
  regression report, which is what lets regzbot auto-resolve the entry.
- **M5. Stable "headed upstream" nuance** — `kernel-workflow.md:112`,
  `ci-regression.md:50`: tagging at submission is fine, but a patch is only
  applied to stable once it (or an equivalent) is in mainline. The concrete
  criteria (≤100 lines with context, obviously correct and tested, real
  reported issue) are worth adding.

### Driver/DT content

- **M6. Binding dual-licensing unstated** — `device-tree-drivers.md:68` omits
  that new binding schemas must carry
  `SPDX-License-Identifier: (GPL-2.0-only OR BSD-2-Clause)`
  (`devicetree/bindings/submitting-patches.rst`). A reviewer following the doc
  would accept bindings the DT maintainers will reject.
- **M7. `remove()` returns `void`** — `driver-api-cookbook.md` never states
  that platform (6.11+, `remove_new` since deleted), i2c (6.1+), and spi
  (5.18+) `remove()` callbacks return `void` in mainline while older LTS trees
  differ — exactly the version-skew case its "Version And Vendor Trees" section
  exists for. Add a row/bullet and a matching check in
  `driver-review-checklists.md`.

### Format & packaging

- **M8. Phantom `assets/` reference** — `SKILL.md:25` tells the agent to
  "query `assets/kernel-doc-index.jsonl`" but no `assets/` directory exists in
  the package; the regenerate caveat only appears 55 lines later. Reword the
  first mention ("generate and query… — see Local Documentation") or ship
  `assets/.gitkeep`.
- **M9. `/path/to/…` placeholder paths** — `SKILL.md:69-71,83-86`. Spec
  convention is paths relative to the skill directory
  (`python3 scripts/triage_kernel_change.py`), or `${CLAUDE_SKILL_DIR}` on
  Claude Code. Placeholders force the agent to reconstruct the install root,
  which differs per host.
- **M10. Gemini adapter outdated** — `adapters/major-agent-setup.md:70-82`
  describes Gemini CLI as GEMINI.md-only. Gemini CLI now supports Agent Skills
  natively (`.gemini/skills/`, `~/.gemini/skills/`, extension-bundled). Make
  the skills symlink the primary path; keep GEMINI.md as legacy fallback.
- **M11. Stale generated metadata committed** — `doc-routes.md:3,5,9-54`
  ("Total file entries indexed: 9048", per-directory counts of a private
  checkout) is the time-sensitive-information anti-pattern from Anthropic's
  best-practices doc. Overlaps H6; same fix. Additionally the indexed tree is a
  pre-6.4 layout (`Documentation/arm64/…`, `Documentation/powerpc/kasan.txt` —
  both moved under `Documentation/arch/`), with no version stamp disclosing
  that. Have the generator stamp `make kernelversion` into the header.
- **M12. Description is all "when", no "what"; doubled name** — `SKILL.md:3`
  opens with "Use when…". Best practice: state what the skill provides first,
  then triggers. The skill-dir name + plugin name also produce the command
  `/kernel-development-skills:kernel-development-skills`; renaming the skill
  dir to `kernel-development` would deduplicate.

### Scripts & generator

- **M13. Triage emits wrong `scripts/` paths** —
  `triage_kernel_change.py:92,113,128` emit
  `python3 scripts/check_lapis_guardrails.py` alongside
  `scripts/checkpatch.pl`; in a kernel tree `scripts/` is the kernel's dir, so
  the generated commands fail verbatim. Compute via `Path(__file__).parent` or
  emit a `<skill>/scripts/…` placeholder.
- **M14. Forbidden-DTSI classification overwritten** —
  `triage_kernel_change.py:88-106`: the `.dts/.dtsi` branch overwrites
  `kind = "forbidden Lapis SoC DTSI edit"`; the headline type then understates
  severity (guardrail bullet survives). Make the forbidden classification
  terminal.
- **M15. Guardrail self-exclusion matches neither layout** —
  `check_lapis_guardrails.py:51` excludes
  `"/.agents/skills/kernel-development-skills/"`; git paths have no leading
  slash and the repo's real layout
  (`plugins/…/skills/kernel-development-skills/`) is not excluded (verified
  self-flagging). Match on `"skills/kernel-development-skills/" in path`.
- **M16. "Advisory" checker exits 1** — `check_kernel_api_patterns.py:190`
  returns 1 on any finding although the docstring/header say advisory; in CI
  that converts advisories into hard failures. Return 0 by default with a
  `--strict` flag (and error with exit 2 on explicitly-passed nonexistent
  paths, which currently pass silently green).
- **M17. Indexer keyword quality** — `index_kernel_docs.py:205-207,254-256`:
  raw substring matching ("st**abi**lity" → `abi`; `denali` route resolves to
  the unrelated Denali NAND controller) and a 40-path alphabetical collection
  cap that starves later directories (committed `### trace` section contains
  zero `Documentation/trace/*` files). Use word-boundary regexes and score
  during collection.
- **M18. Private testing-matrix path** — `lapis-rk3576.md:113` references
  `linux-docs/testing/data/peripherals/*.tests.json`, a private repo consumers
  of the public skill cannot have. Hedge as "if a local testing-matrix repo
  exists" or drop.

## Low-severity / wording

- `check_kernel_api_patterns.py:71`: strlcpy is *removed* (v6.8), not merely
  deprecated — strengthen the message.
- `kernel-workflow.md`: no mention of the b4 contributor workflow
  (`b4 prep --auto-to-cc`, `b4 send`, `b4 trailers -u`), now the de facto
  recommended flow; fits next to the `get_maintainer.pl` guidance.
- `ci-regression.md:21`: TuxMake/TuxRun transferred to the KernelCI project
  (2026); TuxSuite remains Linaro's commercial service. KernelCI now runs the
  Maestro pipeline/KCIDB-ng. Optional one-line refresh; mention tuxrun for
  boot/test alongside tuxmake.
- `ci-regression.md`: upstream gives concrete urgency numbers (~2 weeks
  ordinary, 2–3 days severe) worth quoting.
- `device-tree-drivers.md`: add binding routing/naming conventions
  (`vendor,device.yaml` filename, `dt-bindings:` subject prefix, CC
  `devicetree@vger.kernel.org`) and DT autoload plumbing
  (`struct of_device_id`/`.of_match_table`, `MODULE_DEVICE_TABLE(of, …)`,
  `module_platform_driver()`, `device_get_match_data()`).
- `debugging-testing.md`: optionally add top-level
  `make TARGETS=… kselftest`/`run_kselftest.sh` variants and KMSAN's
  clang/x86_64-only constraint.
- `advanced-tooling.md:24`: `command -v a b c` returns non-zero if *any* tool
  is missing — note "check the output lines, not the exit code". Consider
  adding virtme-ng/QEMU for fast boot tests.
- `lapis-rk3576.md`: state which rules `check_lapis_guardrails.py` enforces
  (DTSI/defconfig/make only) vs manual ones; avoid hard-coding the Pamir
  fragment name in the script's warning text.
- `SKILL.md` frontmatter: add optional `license`, `metadata` (version), and
  `compatibility` (python3) so the plain-skill symlink install path carries
  provenance.
- `.claude-plugin/marketplace.json:2`: the `$schema` URL
  (`https://anthropic.com/claude-code/marketplace.schema.json`) appears
  invented (unverifiable from sandbox; docs use schemastore-style URLs).
  Harmless at runtime; drop or repoint.
- `README.md:70-73`/`AGENTS.md:22-25`: validation depends on machine-specific
  `~/.codex/skills/.system/` internals; mark "if Codex is installed" or vendor
  a minimal validator for CI.
- Add ToCs to `driver-api-cookbook.md` (162 lines) and `doc-routes.md`
  (601 lines) to match sibling files.
- Manifest metadata (version/description/author) is hand-duplicated across
  three JSON files; consider a sync check. No evaluation scenarios exist
  (Anthropic guidance: ≥3 evals per skill).
- `research/sources.tsv:127`: the smatch kernel-doc URL is dead (no
  `dev-tools/smatch.rst` in mainline); mark dead or repoint. Prefer accessed-on
  dates over `date=current`.
- Scripts: `git_changed_paths()` ignores committed-but-unpushed work (add
  `--against <rev>`); `build_wrapper()` only checks `./`/`../` (walk to git
  root); document warning-vs-error exit-code conventions.

## Modern-practice content gaps (verified present in mainline)

Topics current reviewers expect that the cookbook/checklists do not cover:

1. `<linux/cleanup.h>` scoped cleanup — `__free()`, `guard()`,
   `scoped_guard()`, `DEFINE_FREE`/`DEFINE_GUARD`; widely requested in review
   for locks, OF-node puts, and error-path frees. Biggest gap in the Resource
   Lifetime section (hedge with "if available in this tree" for vendor/LTS).
2. `void` remove() for platform/i2c/spi (M7).
3. `faux_device` (6.14+) — preferred replacement for fake platform devices for
   purely virtual devices.
4. Modern dev_pm_ops macros — `DEFINE_RUNTIME_DEV_PM_OPS`,
   `DEFINE_SIMPLE_DEV_PM_OPS`, `RUNTIME_PM_OPS`/`SYSTEM_SLEEP_PM_OPS`,
   `pm_ptr()`/`pm_sleep_ptr()` (the Runtime PM section says "use subsystem
   helpers/macros" but names none).
5. `devm_pm_runtime_enable()` — avoids unbalanced `pm_runtime_disable()` in
   error paths.
6. `REGCACHE_MAPLE` — recommended regcache for new regmap drivers (RBTREE is
   legacy).
7. `dev_warn_probe()`/`dev_info_probe()` graded probe-log helpers; kernel-doc
   explicitly blesses `dev_err_probe()` even when the error can never be
   `-EPROBE_DEFER`.
8. b4 contributor workflow (see Low list).

## Verified correct (no action)

- All SKILL.md frontmatter constraints (name charset/length, description
  <1024 chars, no XML, trigger-rich); body length and one-level reference depth.
- `claude plugin validate` passes for plugin and marketplace;
  `agents/openai.yaml` matches the official `openai/skills` convention;
  `.codex-plugin/plugin.json` interface block fields and prompt limits all
  valid; Copilot/OpenCode adapter claims accurate; `claude --plugin-dir`
  exists.
- `Fixes:` format, `checkpatch.pl --strict --codespell`, changelog-below-`---`,
  `regressions@lists.linux.dev`, don't-invent-review-tags.
- Dynamic debug (`/proc/dynamic_debug/control` syntax, `DYNAMIC_DEBUG_CORE`
  nuance, loglevel caveat), ftrace via `/sys/kernel/tracing`, KUnit
  `kunit.py run` syntax and KTAP claim, kselftest invocation, sanitizer CONFIG
  names, fault-injection class list, `make C=1` sparse.
- The entire deprecated-API table in `driver-api-cookbook.md` vs current
  `deprecated.rst`; GPIO descriptor guidance; `dev_err_probe()` semantics;
  `pm_runtime_resume_and_get()` preference; all Documentation/ source-map
  paths; `dt_binding_check` syntax; YAML/DTS indentation rules; patch ordering
  (bindings → driver → DTS).
- All rule messages in `check_kernel_api_patterns.py` vs current upstream
  guidance; all tool names in `advanced-tooling.md` (b4, lei, patatt, tuxmake,
  KernelCI, LAVA, labgrid, sparse, smatch, coccinelle, syzkaller, drgn, pahole,
  bpftool, libabigail…); Curated Routes section of `doc-routes.md` fully
  mainline-valid; `sources.tsv` provenance hygiene good.

## Suggested fix order

1. H1/H2 — wrong DT commands (factual errors an agent will execute).
2. H3/H4/M13–M16 — script correctness (these run unattended as guardrails).
3. H5/H6/M11 — generator redaction + de-stale/strip committed doc-routes.md.
4. M1–M7 — process/tag and driver/DT content corrections.
5. M8–M10/M12 — packaging polish (skill-relative paths, assets wording,
   Gemini native skills, description "what + when").
6. Modern-practice additions (cleanup.h, PM macros, b4, REGCACHE_MAPLE) and
   the Low list.
