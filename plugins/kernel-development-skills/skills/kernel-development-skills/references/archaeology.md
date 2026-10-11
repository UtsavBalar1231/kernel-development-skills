# Code archaeology

Before changing code, find out why it looks the way it does, who owns it, and
how the last person to solve this problem did it. The answer to "why is this
here" is usually in a commit message or a mailing-list thread, and it is
cheaper to read than to rediscover.

Covers: why a line exists; when a symbol appeared or vanished; which release
has a commit; following fixes; the thread behind a commit; searching lore; who
owns the code; learning from another driver; looking across versions; finding
documentation.

## Why is this line here

```bash
git blame -w -C -C -L 120,140 drivers/foo/bar.c  # ignore whitespace, follow code moved or copied from other files
git blame <sha>^ -- drivers/foo/bar.c             # step past a commit to the version before it
git show <sha>                                    # read the message, not only the diff
git log -L :foo_probe:drivers/foo/bar.c           # every change to one function
git log --follow -p -- drivers/foo/bar.c          # history across renames
```

Blame often stops at a mechanical commit: a whitespace fix, a rename, or a
treewide API conversion. Step past it with `<sha>^` until you reach the commit
that made the decision. When that message only says "fix", follow its `Link:`
tag to the thread.

## When a symbol appeared or vanished

```bash
git log -S'devm_clk_get_enabled' --oneline -- include/   # added or removed the string
git log -G'remove_new\s*=' --oneline -- drivers/gpio/     # any diff line matching the regex
git log --diff-filter=A --oneline -- drivers/foo/bar.c    # the commit that created the file
git log --grep='quirk' -i --oneline -- drivers/foo/       # search commit messages
git show v6.1:include/linux/timer.h | grep -n timer_delete   # a file at any tag, no checkout
```

`-S` finds commits that change how many times the string occurs, which is
exactly introduction and removal. `-G` also finds edits that keep the count the
same.

## Which release has it

```bash
git describe --contains <sha>              # v6.5-rc1~123^2~4: merged during the v6.5 merge window
git tag --contains <sha> | sort -V | head -1
```

`vX.Y-rc1~...` means the commit arrived with the vX.Y merge window, and
`vX.Y-rc4~...` means it came in as a fix later in that cycle. A stable
backport has a different SHA. Find it by the upstream SHA, which the backport
cites in its `commit <sha> upstream.` line, or by subject:

```bash
git log --oneline --grep=<upstream-sha> stable/linux-6.1.y
git log --oneline -F --grep='<exact subject>' v6.1..stable/linux-6.1.y
```

## Following fixes

- `git log --oneline --grep=<first 12 hex of sha>` lists every commit that
  names it: the `Fixes:` tags aimed at it, and reverts of it. Run it on
  anything you are about to build on or backport, because fixes to fixes are
  common.
- Walk the other way too. The `Fixes:` tag of the commit you are reading points
  at the change that broke things, and that change usually explains the shape
  of the fix.

## The thread behind a commit

- Most commits applied with current tooling carry
  `Link: https://patch.msgid.link/<message-id>`, and older ones
  `Link: https://lore.kernel.org/r/<message-id>`. Open it. The review there
  explains choices that look strange in the code, and the cover letter's
  changelog shows what earlier versions tried and why reviewers rejected it.
- Pull the whole thread or series locally with b4:

  ```bash
  b4 mbox <message-id>     # the full thread as an mbox
  b4 am <message-id>       # the series as an applicable mbox, with trailers collected
  b4 shazam <message-id>   # apply the series to the current branch
  ```

  Flags vary between b4 releases; check `b4 <command> --help`.

## Searching lore

https://lore.kernel.org/all/ archives every kernel list, and its search takes
public-inbox prefixes:

| Prefix | Matches |
| --- | --- |
| `s:` | subject |
| `f:` | From |
| `a:` | To, Cc, and From |
| `b:` | body, including text attachments |
| `nq:` | body text that is not quoted |
| `dfn:` | a file name in a diff |
| `dfb:`, `dfa:` | added, removed diff lines |
| `dfhh:` | hunk header context, usually a function name |
| `d:`, `rt:` | date range (git approxidate), received time |
| `patchid:` | `git patch-id --stable` output |

Queries that pay off:

- `dfn:drivers/iio/adc/foo.c` finds every patch that touched the file,
  including ones that never merged. The rejected ones show what this
  maintainer refuses.
- `dfb:devm_clk_get_enabled AND dfn:drivers/i2c/` finds who started using an
  API in a subsystem, and what reviewers said about it.
- `s:"PATCH" AND dfn:drivers/foo/ AND d:1.year.ago..` finds what changed in the
  area recently, including work in flight that your patch would conflict with.

`lei` runs the same queries from the command line into a local maildir, for
example
`lei q -I https://lore.kernel.org/all/ -o ~/Mail/foo 'dfn:drivers/foo/bar.c AND rt:2.weeks.ago..'`.
Check `lei q --help`.

## Who owns this

```bash
scripts/get_maintainer.pl -f drivers/foo/bar.c        # for a file
scripts/get_maintainer.pl 0001-foo-fix.patch           # for a patch; also matches K: content patterns
scripts/get_maintainer.pl --nogit-fallback -f drivers/foo/bar.c
git log -20 --format='%(trailers:key=Reviewed-by,valueonly)' -- drivers/foo/ | sort | uniq -c | sort -rn
```

When no MAINTAINERS entry matches, `get_maintainer.pl` falls back to recent
committers by default. Those people can review, but they cannot apply the
patch. `--nogit-fallback` turns the guessing off, so you can see that nobody
formally owns the file. The trailer query shows who actually reviews in the
area.

| MAINTAINERS field | What it tells you |
| --- | --- |
| `M:` | who applies patches |
| `R:` | designated reviewers; Cc them |
| `L:` | the list the patch has to reach |
| `S:` | `Supported`, `Maintained`, `Odd Fixes`, `Orphan`, `Obsolete`. Odd Fixes or Orphan means slow or no review, so route through the parent subsystem |
| `T:` | the tree to base on |
| `P:` | the subsystem profile: subject prefix, branches, timing, extra checks. Read it before the first patch |
| `F:`, `X:`, `N:`, `K:` | the files, exclusions, path regexes, and content regexes the entry covers |
| `B:`, `C:`, `W:`, `Q:` | bug tracker, chat, web page, patchwork |

`grep '^P:' MAINTAINERS` lists every subsystem profile. Many are in-tree
`Documentation/process/maintainer-*.rst` files, and some are URLs.

For the subject prefix, use what the maintainer has actually been applying,
not something built from the path: `git log --oneline -10 -- <file>`.

## Learning from another driver

- Pick a sibling in the same subsystem and on the same bus, merged recently,
  with a `Reviewed-by:` or `Acked-by:` from the current maintainer:

  ```bash
  git log --oneline --diff-filter=A -- 'drivers/iio/adc/*.c' | head   # newest drivers in the directory
  ```

- Copying an old driver imports patterns reviewers now reject: `.remove_new`,
  integer GPIOs, `SIMPLE_DEV_PM_OPS()`, open-coded unwinds. Old drivers stay in
  the tree because nobody converted them, not because anyone endorses their
  style.
- Read the review thread of the sibling's first version. The maintainer's
  complaints there are the ones you will get.

## Across versions

- `https://elixir.bootlin.com/linux/<tag>/source/<path>` and
  `.../linux/<tag>/ident/<symbol>` answer "does 6.1 have this helper" without a
  checkout. For the tree you are in, trust `git grep` instead: vendor trees
  diverge from every upstream tag.
- `git diff v6.1..v6.6 -- include/linux/<header>.h` shows how an API changed
  between the release you ship and the one you are reading about.

## Finding documentation

- `git grep -ln '<term>' Documentation/` in the target tree. Vendor trees and
  old releases differ from docs.kernel.org.
- The bundled `python3 scripts/index_kernel_docs.py <kernel_root> [--out DIR]`
  builds a route map and a JSONL index of the tree's `Documentation/`, then
  prints both paths. Query the JSONL with `rg` or `jq` rather than reading it
  whole.
- Docs move between releases. `kgdb.rst` and `gdb-kernel-debugging.rst` moved
  from `Documentation/dev-tools/` to `Documentation/process/debugging/` in
  v6.14. Per-architecture docs moved under `Documentation/arch/` gradually
  between v6.4 and v6.7.
