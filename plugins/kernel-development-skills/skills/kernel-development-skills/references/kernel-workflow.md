# Kernel Workflow Reference

## Table Of Contents

- Core source map
- Patch design
- Commit messages and tags
- Maintainers and submission
- Regressions and stable
- Vendor and LTS branches
- Review checklist

## Core Source Map

Start from the checked-out kernel documentation when available:

- `Documentation/process/submitting-patches.rst`
- `Documentation/process/submit-checklist.rst`
- `Documentation/process/coding-style.rst`
- `Documentation/process/deprecated.rst`
- `Documentation/process/handling-regressions.rst`
- `Documentation/process/stable-kernel-rules.rst`
- `Documentation/maintainer/`
- `MAINTAINERS`
- `scripts/checkpatch.pl`
- `scripts/get_maintainer.pl`

Current upstream references:

- https://docs.kernel.org/process/submitting-patches.html
- https://docs.kernel.org/process/submit-checklist.html
- https://docs.kernel.org/process/handling-regressions.html
- https://docs.kernel.org/process/stable-kernel-rules.html
- https://docs.kernel.org/maintainer/rebasing-and-merging.html
- https://docs.kernel.org/maintainer/pull-requests.html
- https://docs.kernel.org/dev-tools/checkpatch.html

## Patch Design

- Make one logical change per patch. Split refactors, functional changes, ABI additions, bindings, DTS, config, and tests when reviewers may need to route them differently.
- Preserve bisectability: every commit should build and should not require a later commit to avoid obvious breakage.
- Prefer subsystem-local patterns over generic helpers. Kernel review values consistency with nearby code.
- Avoid churn: no drive-by formatting, renames, include shuffles, or broad cleanups mixed with behavior changes.
- If a public interface changes, include the ABI/user impact in the commit message and update docs/tests.
- For vendor trees, mark local policy clearly and avoid hiding upstream deltas in unrelated commits.

## Commit Messages And Tags

Use the upstream kernel commit shape:

```text
subsystem: area: imperative summary under reviewable length

Explain the problem, the user-visible or developer-visible impact, and why
this fix is correct. Mention hardware, datasheet, logs, or regression evidence
when relevant.

Fixes: <12+ sha> ("original subject")
Link: https://lore.kernel.org/...
Closes: https://bugzilla.kernel.org/...
Reported-by: Name <mail>
Tested-by: Name <mail>
Reviewed-by: Name <mail>
Signed-off-by: Name <mail>
```

Rules of thumb:

- The body should justify the change, not narrate the diff.
- Add `Fixes:` for bug fixes whenever a culprit commit is known.
- Add `Link:` or `Closes:` to reports, discussions, or bug trackers that establish context.
- Keep `Reported-by`, `Tested-by`, `Reviewed-by`, and `Acked-by` accurate; do not invent review tags.
- Include `Signed-off-by:` when preparing kernel-style patches.
- For stable candidates, `Fixes:` is helpful but does not replace stable rules or `Cc: stable@vger.kernel.org`.

## Maintainers And Submission

Before submission or review handoff:

```bash
scripts/checkpatch.pl --strict --codespell <patch-file>
scripts/get_maintainer.pl <changed-files-or-patch>
```

Use `--strict` as a review aid, not a replacement for judgment. Some warnings are false positives; explain intentional exceptions.

Routing guidance:

- Check `MAINTAINERS` and subsystem docs before assuming LKML-only routing.
- Watch subsystem-specific subject prefixes and patch ordering.
- CC lists, maintainers, and reviewers on every revision unless a maintainer asks otherwise.
- Explain changes since v1/v2 in a cover letter or below the `---` separator.
- Do not rebase public/shared history casually. Private patch series can be rebased; published branches containing others' history should usually be reverted/fixed forward.

## Regressions And Stable

Kernel regression policy is user-workflow centered. If a real user workflow broke, treat it as urgent even if the new behavior is technically cleaner.

Regression handling:

- Reproduce or narrowly characterize the failure.
- Identify the culprit with logs, bisect, or commit analysis.
- CC `regressions@lists.linux.dev` for regression reports when appropriate.
- Use regzbot when tracking matters, especially for mailed reports:

```text
#regzbot ^introduced: <commit-or-version-range>
```

Stable candidates should generally:

- Be small, obvious fixes for real bugs.
- Already exist upstream or be headed upstream.
- Include `Fixes:` when possible.
- Include `Cc: stable@vger.kernel.org` when submitting upstream if the patch meets stable rules.
- Avoid feature additions, major refactors, and risky behavior changes.

## Vendor And LTS Branches

When maintaining vendor or LTS kernels:

- First determine whether a fix is upstream, backported, vendor-local, or still missing.
- Prefer upstream commits with preserved metadata over hand-rewritten local fixes.
- Record conflicts and behavioral deltas in commit messages.
- Validate against the vendor integration surface, not just upstream expectations: boot chain, DTS overlays, rootfs packages, firmware blobs, out-of-tree modules, and CI artifacts.
- Do not blindly update config defaults that affect userspace ABI or hardware-accelerated packages.

## Review Checklist

Before finalizing:

- `git diff --check` has no whitespace errors.
- Patch is split by review boundary and remains bisectable.
- Commit message explains problem, impact, and correctness.
- Maintainers and subsystem rules are checked.
- ABI, DT ABI, userspace, firmware, and stable impact are considered.
- Tests and runtime evidence match the change risk.
- Existing user or generated changes are preserved.
