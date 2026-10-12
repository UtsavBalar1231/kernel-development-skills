# Stable, backports, and security fixes

Fixes for kernels people already run.

Covers: does it belong in stable; getting a fix there; stable mail you will
get; is the fix already there; backporting; vendor and LTS intake; security
bugs.

## Does it belong in stable

The rules are in `stable-kernel-rules.rst`, and the stable team applies them
literally:

- It, or an equivalent fix, is already in mainline. Stable never carries a fix
  mainline lacks, because users would regress when they upgrade.
- It is obviously correct and tested.
- It is at most 100 lines, with context.
- It fixes a real bug that bothers people (oops, hang, data corruption, real
  security issue, hardware quirk, build error), or it only adds a device ID.
- It is not a "this could be a problem" fix. A theoretical race needs an
  explanation of how it can be hit. Spelling and whitespace cleanups never
  qualify.

Notable performance fixes for distro users are possible, but a distribution
kernel maintainer sends them, with the user-visible impact spelled out.

When you name specific series (options 2 and 3 below), the fix has to be in,
or headed to, every newer supported series too. A fix backported to 6.1.y but
not 6.6.y regresses everyone who upgrades from one to the other.

## Getting a fix there

Option 1, strongly preferred: tag the patch when you send it for mainline.

```text
Cc: stable@vger.kernel.org
```

A correct `Fixes:` lets the stable team work out which series need it, so
version annotations are usually unnecessary. When they are needed:

```text
Cc: <stable@vger.kernel.org> # 6.1.x
Cc: <stable@vger.kernel.org> # 6.1.x: a1f84a3: sched: Check for idle
Cc: <stable@vger.kernel.org> # after -rc3
Cc: <stable@vger.kernel.org> # see patch description, needs adjustments for <= 6.3
Cc: <stable+noautosel@kernel.org> # reason goes here, and must be present
```

- The `<sha>: <subject>` form lists prerequisites in cherry-pick order. Patches
  earlier in the same series that are themselves tagged do not need listing.
- `# after -rc3` delays pickup until the fix has had some mainline exposure.
- `stable+noautosel` keeps AUTOSEL and Fixes-scanning scripts away from a
  change that must not be backported. The reason is mandatory.
- For an unpublished vulnerability use `Cc: stable@kernel.org` instead. Mail to
  that address goes nowhere, so `git send-email` cannot leak the fix early.

Option 2: the fix is already merged. Mail `stable@vger.kernel.org` with the
subject, the mainline commit ID, why it qualifies, and the series you want.

Option 3: it needs adjusting for older series. Send the backport itself (see
the changelog format under Backporting).

## Stable mail you will get

- An ACK or NAK for a submitted patch, possibly days later.
- Review mails titled like `[PATCH 6.6 000/150] 6.6.55-rc1 review`. They
  give a response deadline, and the committee has 48 hours to object. Test
  the -rc on your hardware and reply with `Tested-by:`, or object if a patch
  should not be there.
- AUTOSEL mails (`[PATCH AUTOSEL ...]`): a tool proposing your untagged fix
  for stable. Reply quickly if it should not go back.
- "FAILED: patch ... failed to apply to X-stable tree": the stable team wants a
  backport from you. Use the mail as data: it names the commit, the series,
  and possible prerequisites. Its suggested commands end with `git commit -s`
  and `git send-email`, which belong to the human submitter. Fetch the stable
  branch, cherry-pick with `-x` in a separate worktree
  (`git worktree add ../linux-6.1.y FETCH_HEAD`) so the current branch stays
  as it was, and prepare the result as option 3.

The queue lives in `stable-queue.git`, releases in `stable/linux.git`
(branches `linux-6.6.y` and so on), and release candidates in
`linux-stable-rc.git`, which is rebased constantly and only meant for CI.

## Is the fix already there

```bash
git describe --contains <sha>                         # first mainline tag containing it, e.g. v6.8-rc3~12^2
git log --oneline --grep=<sha12> linux-6.6.y          # stable backports quote the upstream SHA
git log --oneline -i --grep='<subject words>' <branch> # vendor trees often drop the SHA
```

A stable backport has its own SHA, so `git tag --contains <upstream-sha>` in a
linux-stable clone only finds mainline tags. Grep the message instead.

## Backporting

`backporting.rst` is the long version; these are the moves that matter.

- Do not `git am` a mailed patch onto an old tree. Apply it where it applies
  cleanly (mainline, or `b4 am -g -3 <message-id>` to guess the base), then
  `git cherry-pick -x` it across, so git sees moved code and gives real
  conflict markers instead of `.rej` files.
- Before resolving a conflict, find what changed underneath it:

  ```bash
  git log HEAD..<commit>^ -- <path>
  git log -L:'\<function\>':<path> HEAD..<commit>^
  git log -G'<regex>' HEAD..<commit>^ -- <path>
  git blame <commit>^ -- <path>
  ```

  A true prerequisite gets backported as its own commit, ahead of the fix. An
  incidental change gets resolved around.
- Read the whole function, not just the hunk: `git show -W`, `git diff -W`.
  The classic backport bug is a `goto` label, `return`, or `break` that is
  correct upstream and wrong in the old function, outside the conflict.
- If upstream factored code into a helper, the old tree may need the fix in
  every place the helper replaced. `git grep` for the pattern.
- Compare your result to the original side by side:

  ```bash
  colordiff -yw -W 200 <(git diff -W <upstream>^-) <(git diff -W HEAD^-) | less -SR
  ```

- Build the touched objects (`make path/to/file.o`), then a full build, then
  run it. A clean cherry-pick can still be wrong when another change to the
  same file had no textual overlap.

Changelog for a stable submission:

```text
<original subject>

[ Upstream commit <mainline sha> ]

<original changelog>
[ <what conflicted and how it was resolved> ]
```

Older series used `commit <sha> upstream.` on that line. The human submitter
adds their own `Signed-off-by:` after reviewing the backport, and nothing goes
to the list until they say yes. Send one submission per stable series, each
tested on that series, with the series in the subject:
`git send-email --subject-prefix='PATCH 6.1.y'`.

## Vendor and LTS intake

- Take whole stable releases (merge or rebase onto the `v6.6.x` tag) instead
  of cherry-picking CVE fixes. `cve.rst` explains why: stable releases are
  tested together, and many bugs are fixed by several commits on top of each
  other.
- Merge conflicts during intake are your vendor delta. Resolve them by reading
  the upstream change, the same way as a backport.
- Mark vendor-local commits the way the tree already does (subject prefix or
  trailer) so the next rebase can find them.
- Track EOL dates in https://www.kernel.org/releases.json. An EOL branch gets
  no stable fixes, no kernel CVEs, and falls outside the threat model.
- When a regression is reported against a stable or LTS release, check
  mainline first. If mainline has it too, fix mainline; the stable team will
  not.

## Security bugs

Decide whether it is a vulnerability before treating it as one.
`threat-model.rst` excludes:

- actions by root, or by a user who already holds the capability involved
  (`CAP_SYS_ADMIN`, `CAP_NET_ADMIN`, and so on)
- bugs reachable only with debug features (KASAN, LOCKDEP, FAULT_INJECTION),
  staging drivers, out-of-tree modules, or EOL kernels
- crafted filesystem images, fake or out-of-spec devices, and anything that
  needs physical access or hardware modification
- hardening bypasses with no demonstrated exploit, and small leaks such as
  struct padding or kernel pointers. Pointer leaks still get reported and
  fixed, as normal bugs.

Everything excluded is a normal bug and goes to the normal lists.

A real vulnerability, per `security-bugs.rst`:

- Send it to the affected subsystem's maintainers
  (`scripts/get_maintainer.pl --no-l --no-r --pattern-depth 1 <file>`), not to
  a public list, and Cc `security@kernel.org`. That Cc is mandatory when there
  are two or fewer recipients.
- A bug found with AI assistance must be treated as public, because the same
  bug usually surfaces from several researchers at once. The fix goes to the
  maintainers and the list. The report and reproducer go to the maintainers
  only. Say that a reproducer exists, and share it only when a maintainer
  asks.
- Report a clearly trivial, publicly discoverable issue directly on the public
  lists.
- The report needs four things:
  - the affected version, as a commit ID or exact kernel.org version ("latest
    mainline" and distro versions are rejected)
  - a description with traces
  - a reproducer as source, never a binary
  - the triggering conditions (config, sysctls, permissions)
- Write it in plain text, short, summary first, with no Markdown, HTML, or
  attachments. State impact as verifiable fact ("any user can gain
  `CAP_NET_ADMIN`"), not speculation.
- An agent preparing a report reads `security-bugs.rst` and
  `threat-model.rst` first. It works on current mainline with the commit ID
  noted, and starts the report with a temporary recipients section for the
  human to check and remove. The human sends it.
- Embargo: fixes for public bugs ship immediately. An undisclosed one can be
  held at most 7 days (14 by exception), and only for rollout logistics. Do
  not contact linux-distros until maintainers have accepted a fix, and do not
  Cc both lists at once.

CVEs come from the kernel CNA, not the security team. They are assigned
automatically once a fix lands in a stable tree, only for actively supported
branches, and announced on linux-cve-announce (`cve.rst`). Mail
`cve@kernel.org` only to request one for a fix already in a released tree.
