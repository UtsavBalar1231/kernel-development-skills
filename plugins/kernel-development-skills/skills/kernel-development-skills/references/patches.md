# Getting a patch merged

What a maintainer checks before applying: series shape, subject prefix, commit
message, tags, AI attribution, pre-send checks, sending with b4 or git, timing,
revisions, and answering review. The receiving tree's
`Documentation/process/submitting-patches.rst` wins where it disagrees with
this file.

## Series shape

- One logical change per patch. A refactor, a fix, and a feature are three
  patches, in that order, because a fix buried behind a refactor cannot be
  backported on its own. Mark a pure refactor with "No functional change
  intended." so reviewers know what to verify.
- Every commit builds and boots, so `git bisect` keeps working for the next
  person. Prove it instead of assuming:

  ```bash
  git rebase -x 'make -j"$(nproc)" W=1 drivers/iio/adc/' origin/master
  ```

- Split by who applies it. dt-bindings, driver, DTS, and defconfig usually land
  through different trees (DT and subsystem maintainers, the subsystem tree, the
  SoC tree). Order them binding, driver, DTS, defconfig, so no patch references
  a compatible that is not documented yet.
- Keep whitespace, renames, and include shuffles out of behavior changes. A
  reviewer reading a 400-line diff for a 3-line fix stops trusting the rest.

## Subject line

Take the prefix from history, not from the path:

```bash
git log --oneline -10 -- drivers/iio/adc/foo.c
```

If that shows `iio: adc: foo:`, use exactly that. `drivers: iio: adc:` or
`IIO/ADC:` gets fixed up by hand at best and bounced at worst. Then an
imperative summary that says what changes, not what file:
`iio: adc: foo: fix channel scale for 12-bit mode`.

## Commit message

Say what is wrong, why this is the right fix, and what the user sees. Do not
narrate the diff; the diff is right below. Write in imperative mood ("make foo
do bar"), never "This patch".

```text
iio: adc: foo: fix channel scale for 12-bit mode

The scale table assumes 16-bit samples, so in 12-bit mode every
reading from in_voltage0_raw comes out 16 times too large. Pick the
scale from the configured resolution instead of the table maximum.

Fixes: 54a4f0239f2e ("iio: adc: foo: add 12-bit mode")
Reported-by: Jane Doe <jane@example.org>
Closes: https://lore.kernel.org/r/<message-id>
Assisted-by: LLM
```

- Wrap the body at 75 columns. Never wrap a tag: tools parse each tag as one
  line.
- Refer to other commits as `commit e21d2170f366 ("video: remove unnecessary
  platform_set_drvdata()")`, with at least 12 hex digits. Short IDs collide in
  a tree this size.
- Background discussion goes in `Link:` tags, preferably lore URLs.
- Version history and notes for reviewers go below the `---` line, where
  `git am` drops them.

## Tags

Generate `Fixes:` instead of typing it:

```bash
git config core.abbrev 12
git config pretty.fixes 'Fixes: %h ("%s")'
git log -1 --pretty=fixes <sha>
```

- `Reported-by:` is for bugs, not feature requests, and is followed directly
  by `Closes:` pointing at the report, or `Link:` when the patch fixes only
  part of it. checkpatch warns when neither follows. Both must be public URLs;
  internal tracker links never go upstream.
- Only `Cc:`, `Reported-by:`, and `Suggested-by:` may name someone without
  asking, and only with a name and address that person already used publicly
  on lore or in git history. Addresses seen on bugzilla.kernel.org are
  private.
- `Reviewed-by:`, `Tested-by:`, and `Acked-by:` go in only when the person sent
  them. Carry them to the next version, but drop them when the patch changes
  substantially and say so below `---`.
- For a bot report (kernel test robot, syzbot), paste the exact `Reported-by:`
  and `Closes:` lines the bot gave, so its tracking closes automatically.
- A fix for released kernels adds `Cc: stable@vger.kernel.org`; the stable
  rules decide whether it qualifies.

## AI-assisted patches

`Documentation/process/coding-assistants.rst` (since v7.0) and
`generated-content.rst` govern these.

- An agent never adds `Signed-off-by:`. Only a human can certify the
  Developer's Certificate of Origin; the human submitter reviews the work, adds
  their own sign-off, and answers for it.
- Add `Assisted-by:` in the format of the receiving tree's
  `coding-assistants.rst`. For upstream work that is current mainline:
  `Assisted-by: LLM [TOOL...]` as of v7.3, where v7.0 to v7.2 used
  `AGENT_NAME:MODEL_VERSION [TOOL...]`. Trees before v7.0 have no copy, so use
  mainline's. List specialized analysis tools (coccinelle, sparse, smatch,
  clang-tidy); leave out git, gcc, make, and editors. An empty `Assisted-by:`
  draws a checkpatch warning.
- Say in the cover letter or below `---` which tools were used, their input
  (for example the Coccinelle script), the prompts or a summary of them, which
  parts were generated, and how the result was tested. Maintainers may review
  generated work with extra scrutiny or decline it.
- When an agent finds and fixes a bug, the documented procedure applies: read
  the process docs in full, note the commit ID, build a reproducer for anything
  non-trivial (stop if the bug turns out not to be real), write and verify the
  fix with no new warnings and a clean checkpatch, commit it with `Fixes:`,
  find recipients with `get_maintainer.pl`, state plainly what could not be
  built, tested, or reproduced, and classify the bug against
  `threat-model.rst`.
- An agent never sends mail or posts anything. It hands the patch to the human.

## Checks before sending

```bash
scripts/checkpatch.pl --strict -g origin/master..   # every commit in the series
scripts/checkpatch.pl --strict --codespell 0001-*.patch
scripts/get_maintainer.pl 0001-*.patch
make W=1 drivers/iio/adc/foo.o                      # no new warnings; W=1 also runs kernel-doc
make C=1 drivers/iio/adc/foo.o                      # sparse
make coccicheck MODE=report M=drivers/iio/adc/
```

- checkpatch is advice. Fix what is real and explain deliberate exceptions;
  reviewers will see the same warnings. `--codespell` needs the codespell
  dictionary installed.
- Smatch, when installed, runs per file with its `smatch_scripts/kchecker`;
  confirm each report in the code before acting on it.
- Documentation changes: `make htmldocs`, or `scripts/kernel-doc -none -Wall`
  on the touched file.
- UAPI header changes: `scripts/check-uapi.sh -p <older-ref>`, an entry under
  `Documentation/ABI/`, and `linux-api@vger.kernel.org` on Cc.
- Kconfig changes: `make kconfig-sym-check` (since v7.2) for references to
  symbols that no longer exist.
- netdev expects `allmodconfig` plus `W=1` to stay clean; other subsystems
  list their bar in their `maintainer-*.rst` profile.

## Sending

With b4, which tracks versions, recipients, and the base commit for you:

```bash
b4 prep -n foo-scale-fix       # new series branch
b4 prep --edit-cover           # cover letter
b4 prep --auto-to-cc           # To/Cc from get_maintainer.pl
b4 prep --check                # checkpatch (and codespell) on every patch
b4 prep --check-deps           # prerequisite series declared in the cover
b4 send -o /tmp/out            # dry run: write the messages to a directory
b4 send --reflect              # dry run: send only to yourself
b4 send
b4 trailers -u                 # pull Reviewed-by and friends from the list
```

`b4 send` uses the git `[sendemail]` SMTP settings when present. Without SMTP,
set `b4.send-endpoint-web` to `https://lkml.kernel.org/_b4_submit` and
register once with `b4 send --web-auth-new`, then `--web-auth-verify`.

Without b4:

```bash
git format-patch -v3 --cover-letter --base=auto -o out/ origin/master..
git send-email --to=<maintainer> --cc=<list> out/*.patch
```

`--base=auto` needs an upstream tracking branch and fails without one; the
`base-commit:` line it writes lets bots and maintainers apply the series where
you tested it. Send plain text only: vger drops HTML mail.

## Timing and revisions

- During the two-week merge window, maintainers take fixes only; new features
  wait. Many subsystem trees stop taking features earlier (kvm-x86 closes
  around rc5, net-next closes for the merge window), so check the subsystem
  profile before planning a deadline.
- Expect comments within two to three weeks. Wait at least one week before
  pinging, longer around a merge window. `[PATCH v3 RESEND]` is only for an
  unchanged resubmission; any change is a new version.
- netdev wants at least 24 hours between postings of the same series.
- Put the changes since the last version in the cover letter or below `---`,
  newest first, and credit who asked for each:

  ```text
  ---
  v3: - use devm_clk_get_enabled() (Jane)
      - drop the IRQ rework, it moves to a separate series
  v2: https://lore.kernel.org/r/<message-id>
  ```

- Cc everyone `get_maintainer.pl` lists on every version, unless a maintainer
  asks otherwise. Reviewers of v1 may not see v3 through a list filter.

## Answering review

- Reply inline in plain text under the quoted point, trim what you are not
  answering, and never top-post.
- Answer every comment before the next version: either change the code or say
  why not. A silently ignored comment comes back louder.
- Settle disagreements in the thread, not in the next version's changelog.

## Published history

Rebase and reword freely while a series is yours. Once a branch is published
and others build on it, or a maintainer has applied it, fix forward with new
commits or reverts instead of rewriting.
