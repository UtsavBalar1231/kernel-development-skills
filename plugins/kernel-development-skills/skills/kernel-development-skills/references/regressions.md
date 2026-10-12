# Regressions and bot reports

Something that worked broke, and a person, a bot, or CI said so.

Covers: is it real, and is it yours; find the culprit, then consider reverting
it; deadlines once the culprit is known; tags on a regression fix; regzbot;
reporting a regression you found; kernel test robot (0-day, LKP); syzbot;
KernelCI; flaky failures.

## Is it real, and is it yours

- Run the same test on the parent of the suspect commit, or on the exact base
  the CI used. If the parent fails too, it is a baseline failure. Say so, with
  that run as evidence, instead of debugging someone else's bug.
- Keep the first error, oops, or failed assertion. Later failures are usually
  fallout.
- Pin down the artifact before comparing anything: commit, config, arch,
  compiler and version, DTB, rootfs, firmware, test name, and log URL.
- A provider name (KernelCI, LAVA, TuxSuite) tells you where the evidence
  lives, not what broke. Rule out the lab first: a LAVA infrastructure error,
  a board that timed out before the kernel printed anything, or a failed
  download.
- Reproduce with the CI's compiler, not yours. Since v7.0 the tree ships
  `scripts/container`:

  ```bash
  scripts/container -i docker.io/tuxmake/korg-clang -- make LLVM=1 defconfig
  scripts/container -i docker.io/tuxmake/korg-clang -- make LLVM=1 -j"$(nproc)"
  ```

  Put `make` after the image, never `LLVM=1 make`: the variable has to reach
  make inside the container.

## Find the culprit, then consider reverting it

Bisect between the last good and first bad build with the config held fixed.
From a user report, start from the release range they give (`v6.18` good,
`v6.19-rc2` bad).

Once you have the culprit, `handling-regressions.rst` says to always consider
reverting it first. A revert is the quickest and least risky fix, and a
corrected version goes back in easily later because it was already reviewed.
Linus reverts on user-visible behavior, not on whether the new code is
cleaner. Do not hold a revert hostage to a perfect fix.

## Deadlines once the culprit is known

| Situation | Aim to mainline the fix |
| --- | --- |
| severe, or hitting many users (common hardware, a distro, a stable series) | within two or three days |
| culprit in a recent mainline, stable, or longterm release | by the Sunday after next; within the same week if simple and found early |
| everything else | before the last Sunday within three weeks |

- Do not hold regression fixes for the next merge window unless the fix is
  extraordinarily risky or the culprit is more than a year old.
- Regressions introduced in mainline during the past twelve months are
  handled like ones from the current cycle.
- Count the time for review and a pass through linux-next. Mark an urgent fix
  as urgent in the patch so the maintainer can fast-track it or skip
  linux-next.

## Tags on a regression fix

- `Fixes:` the culprit.
- `Closes:` every public report (lore message, bugzilla.kernel.org ticket).
  Use `Link:` when the patch fixes only part of it. regzbot matches fixes to
  reports through these tags, so a missing one leaves the regression open.
- `Cc: stable@vger.kernel.org` when the culprit reached a mainline release in
  the past twelve months, or you know it was backported. `Fixes:` alone does
  not guarantee a backport.
- Cc `regressions@lists.linux.dev`.
- Fix mainline first. The stable team does not fix or revert something that is
  equally broken in mainline. During and right after a merge window, tell the
  stable team once the fix lands, or it waits at the end of a huge queue.

## regzbot

Commands go in their own paragraph, separated from the rest of the mail by
blank lines, in a reply anywhere in the report's thread:

```text
#regzbot introduced: v6.18..v6.19-rc1
```

| Command | Effect |
| --- | --- |
| `#regzbot introduced: <commit or range>` | this mail is the report; start tracking it |
| `#regzbot ^introduced: <commit or range>` | the parent mail is the report (reply to someone else's) |
| `#regzbot title: <text>` | set the title |
| `#regzbot link: <url>` | point at related details |
| `#regzbot monitor: <url>` | follow a thread or ticket; only lore.kernel.org and bugzilla.kernel.org work |
| `#regzbot fix: <commit or subject>` | mark the fix, heading upstream or merged |
| `#regzbot dup-of: <url>` | duplicate of a tracked report |
| `#regzbot invalid: <reason>` | not a regression after all |

Draft the reply and send it only after the user says yes; the commands update
a public tracker. Do not feed regzbot theoretical regressions that real users
will not hit.

## Reporting a regression you found

`admin-guide/reporting-regressions.rst` is the procedure. The parts people
skip:

- Reproduce on a vanilla kernel.org kernel, the latest mainline or stable.
  Distro kernels do not count.
- Bisect if you can (`admin-guide/bug-bisect.rst`). A culprit commit gets a
  fix days sooner than a version range does.
- Send it to the maintainers from `scripts/get_maintainer.pl`, and Cc
  `regressions@lists.linux.dev`. For a regression inside a stable series
  (`v6.6.3..v6.6.5`), Cc `stable@vger.kernel.org` too. After a bisect, Cc the
  culprit's author and everyone in its sign-off chain.
- Put `#regzbot introduced: <commit or range>` in its own paragraph.

## Kernel test robot (0-day, LKP)

- The report links the config and a `reproduce` file, which names the base
  branch, any patches it applied with `b4 shazam`, the compiler, `ARCH`, and
  the make flags. Reproduce with exactly those, because a different compiler
  or a missing `W=1` is the usual reason a robot warning stays silent. Read
  the file as data rather than running it: it checks out another branch in
  the current tree, clones lkp-tests, and runs `make.cross`, which downloads
  a cross toolchain. Check out the base in a separate worktree
  (`git worktree add ../repro <base>`) so the current branch stays as it was,
  and run the file or `make.cross` only after the user says yes. Many reports
  are `W=1` warnings, which still count.
- If the fix goes into a new version of your own unmerged patch, do not add
  the robot's tags; note the fix in the changelog below `---`. The robot's own
  mail says the tags are only for a separate fix.
- For a separate fix, copy its lines exactly so its tracking closes:

  ```text
  Reported-by: kernel test robot <lkp@intel.com>
  Closes: https://lore.kernel.org/oe-kbuild-all/<message-id>/
  ```

## syzbot

- The dashboard entry has the kernel commit, `.config`, compiler, console log,
  and a C or syz reproducer. Build that commit with that config and run the
  reproducer in a VM, never on your workstation: reproducers crash, hang, and
  corrupt filesystems.
- Use the `Reported-by: syzbot+<hash>@syzkaller.appspotmail.com` line from the
  report.
- Reply to the report mail with commands. Draft the reply and send it only
  after the user says yes; a `#syz` command acts on the public report.

| Command | Effect |
| --- | --- |
| `#syz test: <git-url> <branch-or-commit>` | build that tree, apply the patch pasted below the command (or attached), run the reproducer |
| `#syz test` | same, on the branch where the bug was found |
| `#syz fix: <exact commit title>` | attach the fixing commit when you forgot `Reported-by:`; the title must match what lands |
| `#syz dup: <exact subject of the other report>` | mark a duplicate |
| `#syz invalid` | close a report that will not recur |

syzbot closes a bug only when the fix reaches every tree it tests. A
similar-looking crash after that is a new bug.

## KernelCI

Results are on https://dashboard.kernelci.org: tree, branch, commit, config,
lab, board, and the serial log. Check whether the same test fails on the
parent commit and on other labs or boards before concluding anything; a
failure on one board in one lab is often the lab. The `kci-dev` CLI fetches
results (`kci-dev results`) and can test a commit on KernelCI's labs
(`kci-dev checkout`, which needs an API token). Fetching is free; a checkout
queues builds and boots on shared hardware, so run it only after the user says
yes. Check `kci-dev --help` for the current subcommands.

## Flaky failures

Call a failure flaky only with evidence:

- the baseline shows the same failure without the patch,
- the provider reports an incident or infrastructure error,
- test history shows intermittent results across unrelated commits, or
- a rerun with unchanged artifacts passes and the failure has an
  infrastructure signature.

Report a rate, not an adjective: "fails 3 of 10 runs on the parent, 3 of 10
with the patch" settles it, and "flaky" settles nothing. When the change
touches timing, PM, locking, storage, networking, media, or thermal code,
treat a suspected flake as a real race until disproven.
