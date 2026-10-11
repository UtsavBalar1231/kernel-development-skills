---
name: kernel-development-skills
description: Workflows of experienced Linux kernel engineers for writing, debugging, reviewing, and upstreaming kernel code in mainline, linux-next, stable/LTS, Android, and vendor BSP trees. Use for any kernel or driver task, including probe/remove and devm teardown bugs, devicetree bindings and DTS (dt_binding_check, dtbs_check), Kconfig and defconfig, oopses, KASAN or lockdep splats, hangs, a device that will not probe, KUnit or kselftest failures including ones that appear only on linux-next, bisecting a regression, replying to syzbot, kernel test robot, or KernelCI reports (#syz test, Reported-by and Closes tags), checkpatch, get_maintainer, b4 or git send-email, commit tags (Fixes, Cc stable, Assisted-by), stable backports, and kernel security fixes. Use it even when the user never says "kernel", for example "my I2C sensor does not probe" or "dtbs_check fails on my board". Not for userspace-only programs, Android apps, or microcontroller firmware.
license: MIT
metadata:
  version: "0.4.0"
---

# Kernel field guide

How experienced kernel engineers change, debug, and upstream Linux kernel code,
in mainline and in the stable, LTS, and vendor trees people actually ship.
Explicit user instructions and the target repository's own rules (AGENTS.md,
README, MAINTAINERS, subsystem `maintainer-*.rst` profiles) take precedence
over this skill.

## How experienced kernel engineers work

- Investigate before writing. Read the code, then its history (`git log -p`,
  `git blame`, and the lore thread behind the last change). Most problems have
  been argued about on a list before, and the answer is often in a commit
  message.
- Design for the tree you are in. Use the subsystem's framework instead of a
  private interface. Devicetree describes hardware, not driver policy. Anything
  userspace can see is ABI and stays forever.
- Iterate fast. Reproduce in QEMU or virtme-ng when the bug is not
  hardware-specific, rebuild only the object you touched, and bisect instead
  of guessing.
- Ship like a maintainer. Every patch builds on its own, explains why in the
  commit message, and carries only tags that are true. Reviewer time is the
  scarcest resource in the process.

## Start here

1. Identify the tree: `make kernelversion`, `git describe`, and the branch it
   tracks. References mark newer APIs with "since vX.Y"; confirm a symbol with
   `git grep` in the target tree before using it, because stable branches
   backport some new names and vendor trees carry their own.
2. Read the repository's own guidance and any documented build wrapper, and run
   `git status --short`. Leave pre-existing uncommitted changes alone.
3. Find the owners and the house style before editing:
   `scripts/get_maintainer.pl -f <file>`, and `git log --oneline -10 -- <file>`
   for the subject prefix the maintainer actually applies.
4. Run `python3 scripts/triage_kernel_change.py [paths...]` for the checks that
   apply to the touched paths.

## References load on demand

Open a reference only when its row below matches the task in front of you.
Most tasks need one or two; do not read the whole `references/` directory up
front, and do not reread a reference already loaded in this session.
Independent reads (MAINTAINERS entry, binding, driver, DTS, Kconfig) can be
done together in one step.

| Read | When |
| --- | --- |
| `references/tree.md` | Working anywhere other than plain mainline (linux-next, a subsystem tree, stable/LTS, Android GKI, a vendor BSP), choosing a base, or using a build wrapper |
| `references/archaeology.md` | You need to know why code is the way it is, who owns it, or how other drivers solved the same problem |
| `references/build.md` | Configuring, building, cross-compiling, booting a test kernel quickly, or checking that every commit in a series builds |
| `references/drivers.md` | Writing or substantially changing driver code |
| `references/devicetree.md` | Writing a binding, editing DTS, DTSI, or overlays, or fixing `dt_binding_check` and `dtbs_check` |
| `references/debugging.md` | Any failure: oops, warning splat, no probe, hang, corruption, race, early-boot death, suspend/resume, latency, or "it worked before" |
| `references/testing.md` | Writing or running KUnit or kselftest, fault injection, fuzzing, or deciding what evidence proves a change |
| `references/review.md` | Reviewing a patch, your own before sending or someone else's |
| `references/patches.md` | Commit messages and tags, AI attribution, preparing and sending a series, or answering review |
| `references/regressions.md` | Acting on a regression report or a bot (syzbot, kernel test robot, KernelCI), or on flaky CI |
| `references/stable.md` | Fixes headed for stable or LTS, backports, vendor tree intake, security bugs and CVEs |

Find documentation in the tree itself with `git grep -ln '<term>' Documentation/`;
`scripts/index_kernel_docs.py` builds a map of a tree's docs when you need one.

## Gotchas

- Never add `Signed-off-by:`. Only a human can certify the Developer's
  Certificate of Origin, so the human submitter adds it after review.
- Add `Assisted-by:` in the format of the receiving tree's
  `Documentation/process/coding-assistants.rst`. For upstream work that is
  current mainline: `Assisted-by: LLM [TOOL...]` as of v7.3, while v7.0 to v7.2
  used `AGENT_NAME:MODEL_VERSION [TOOL...]`. Trees before v7.0 have no copy, so
  use mainline's.
- Add `Reviewed-by:`, `Tested-by:`, or `Acked-by:` only when that person gave
  it explicitly; inventing one misrepresents review. `Reported-by:` is followed
  by `Closes:` (or `Link:` for a partial fix) pointing at a public URL.
- `Fixes:` takes at least 12 hex digits and the original subject:
  `git log -1 --abbrev=12 --format='Fixes: %h ("%s")' <sha>`.
- `make <vendor>/<board>.dtb` alone runs no schema validation. Use
  `make CHECK_DTBS=y <vendor>/<board>.dtb`, and
  `make dt_binding_check DT_SCHEMA_FILES=<binding>` for the binding.
- APIs move between releases: `timer_delete()` exists since v6.2 and
  `del_timer()` was removed in v6.15, platform `.remove` returns void since
  v6.11, and `strncpy()` was removed in v7.2. Check the target tree with
  `git grep` instead of inferring from the version number.
- Board wiring belongs in the board `.dts`/`.dtsi`, not the SoC `.dtsi`,
  because every board using that SoC inherits SoC-file edits.
- When a tree documents a build wrapper (BSP `build.sh`, Android Kleaf, Yocto,
  Buildroot), build and configure through it; it sets the toolchain, config
  fragments, and output directory that plain `make` misses.
- Devicetree bindings, sysfs, ioctl, netlink, and uapi headers are ABI.
  Existing users break even when every in-tree caller is updated.
- A new warning, probe error, or test failure stays in scope until you show it
  is unrelated.
- Report pre-existing bugs you notice as follow-ups instead of folding them
  into the change; mixed patches are harder to review and backport.

## Working rules

- Proceed without asking to read code, build, run checkers and tests, draft
  commits and patches, and make local reversible edits.
- Ask before pushing, sending mail, posting to lists, rewriting published
  history, changing a defconfig shared with other boards, or changing ABI.
- Split a series so each patch builds: dt-bindings first, then driver, then
  DTS, then defconfig.
- Done means fresh evidence: build output, checker output, test results, or
  runtime logs. State explicitly what you could not test and why.

## Verification matrix

| Change | Minimum checks |
| --- | --- |
| C driver logic | `scripts/checkpatch.pl --strict -g HEAD`; `make W=1 <dir>/<file>.o`; `make C=1` (sparse); relevant KUnit or kselftest; probe and log evidence at runtime |
| A series | every commit builds: `git rebase -x 'make -j"$(nproc)" W=1 <dir>/' <base>` |
| Kconfig or defconfig | `make olddefconfig` (through the wrapper if one exists); `scripts/diffconfig` on the resolved `.config`; `make savedefconfig` for defconfig edits |
| dt-bindings YAML | `make dt_binding_check DT_SCHEMA_FILES=<file>` |
| DTS or overlay | `make CHECK_DTBS=y <vendor>/<board>.dtb`; boot, probe, and sysfs evidence on hardware when available |
| Documentation or kernel-doc | `make htmldocs`, or `scripts/kernel-doc -none -Wall <file>` |
| uapi or ABI | `scripts/check-uapi.sh`; an entry under `Documentation/ABI/` |
| Stable or regression fix | culprit proven by bisect or revert; `Fixes:`; `Closes:` or `Link:`; decide on `Cc: stable@vger.kernel.org` |
| Backport | `git cherry-pick -x`; prerequisites identified; deltas from upstream explained in the commit message |

## Example trailer block

```text
gpio: foo: fix IRQ domain leak on probe failure

The IRQ domain allocated in foo_probe() is not released when
devm_gpiochip_add_data() fails, so a deferred probe leaks it.

Fixes: 1234567890ab ("gpio: foo: add IRQ support")
Reported-by: Jane Doe <jane@example.org>
Closes: https://lore.kernel.org/r/<message-id>
Cc: stable@vger.kernel.org
Assisted-by: <format from Documentation/process/coding-assistants.rst>
```

The human submitter adds `Signed-off-by:` after reviewing the patch.

## Bundled scripts

Run these; there is no need to read their source. Each supports `--help`.
Paths are relative to this skill's directory, and they need python3 3.9 or
newer (stdlib only).

- `scripts/triage_kernel_change.py [--against REV] [paths...]`: prints the
  references and checks that apply to the changed paths (from `git diff` when
  no paths are given). Exits 0; 2 only on bad arguments.
- `scripts/check_kernel_api_patterns.py [--against REV] [--strict] [--json] [paths...]`:
  advisory scan for deprecated or risky driver APIs; each finding says which
  kernel version it applies from. Exits 1 on findings with `--strict`, 2 on a
  missing path or bad arguments.
- `scripts/index_kernel_docs.py <kernel_root> [--out DIR]`: indexes the tree's
  `Documentation/` into a routes file and a JSONL index under a per-tree cache
  directory, then prints both paths. Query the JSONL with `rg` or `jq`; do not
  load it whole.
