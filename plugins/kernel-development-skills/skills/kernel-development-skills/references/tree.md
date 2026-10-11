# Which tree you are in

Every tree has its own rules for what to base on, how to build, and what you
may change. Work out which one you are in before you edit anything.

Covers: identifying the tree; mainline, linux-next, and subsystem trees; the
release cycle; stable and LTS; Android common kernels; vendor BSP trees and
build wrappers; config layering; vendor ABI coupling; someone else's dirty
tree.

## Identify it

```bash
make kernelversion             # what the Makefile claims, e.g. 6.1.141
git describe --tags            # nearest tag and distance from it
git remote -v; git branch -vv  # where it came from and what it tracks
git log --oneline -5           # a single huge "import" commit means flattened vendor history
```

| Clue | Usually means |
| --- | --- |
| `vX.Y-rcN` or `vX.Y` tags from torvalds/linux.git | mainline |
| `next-YYYYMMDD` tags | linux-next |
| a remote under `git.kernel.org/pub/scm/linux/kernel/git/<maintainer>/` | a subsystem tree |
| `vX.Y.Z` tags, a `linux-X.Y.y` branch | stable or LTS |
| `android<N>-X.Y` branch, `build.config.*` files at the top level | Android common kernel |
| one squashed import commit, a `build.sh` nearby, product names in `arch/*/configs/` | vendor BSP |

Before trusting any upstream habit in a vendor tree, measure how far it is from
the upstream release it claims to be:

```bash
git remote add stable https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git
git fetch stable tag v6.1.141 --no-tags        # the tag matching make kernelversion
git log --oneline v6.1.141..HEAD | wc -l       # vendor commits on top, when history is intact
git diff --stat v6.1.141 HEAD | tail -1        # still works when history was flattened
```

A large delta means every upstream API or pattern needs checking against the
local code first: `git grep` the symbol, and copy the local pattern when the
tree never adopted the upstream one.

## Mainline, linux-next, and subsystem trees

- Subsystem maintainers apply patches, not Linus, and most want work prepared
  against their own tree (`submitting-patches.rst`). Base on the tree in the
  MAINTAINERS `T:` line for your files, on the branch the subsystem profile
  (the `P:` line) names. Branch names vary: `for-next`, `togreg` for IIO,
  `net-next`.
- linux-next (`next-YYYYMMDD`) merges every subsystem's next branch and is
  rebuilt daily. Test against it to catch conflicts before the merge window.
  Do not base a patch on it, because the maintainer has no stable commit to
  apply it to.
- Networking runs two trees: `net` for fixes and `net-next` for features. The
  subject names the target:
  `git format-patch --subject-prefix='PATCH net-next'`. Other subsystems have
  their own fixes and next split, and the profile says which branch is which.
- A fix for something merged this cycle goes to the subsystem's fixes branch,
  not its next branch, so it reaches the current release.

## The release cycle

- After each release, a merge window of about two weeks ends with `-rc1`.
  Weekly `-rc` releases follow until about `-rc7`, then the release: 9 to 10
  weeks in all (`Documentation/process/2.Process.rst`).
- Features reach mainline only through the merge window, and only from
  subsystem trees that already carried them. Maintainers close their next
  branches as it approaches: `net-next` is closed for the whole window, and the
  tip maintainers want large series in mergeable shape at least a week before
  it opens. A feature sent during the window waits until after `-rc1`, and
  often has to be resent.
- After `-rc1`, only fixes go to mainline. Drivers for new hardware that touch
  no existing code are the usual exception.
- To see where the cycle is, look at mainline's newest tag: a bare `vX.Y` means
  the merge window is open, and `-rcN` means stabilization.
- RFC postings are welcome at any point, for example
  `--subject-prefix='RFC net-next'`.

## Stable and LTS

- Stable and longterm trees take only fixes that are already in mainline.
  Which series are maintained and when each ends:
  https://www.kernel.org/releases.json. An end-of-life series gets no more
  fixes, so a product still on one has to carry every fix itself.
- Upstream reviews features against mainline. A feature developed on an LTS
  branch is a downstream decision, and porting it forward is the submitter's
  job.

## Android common kernels

- Android common kernel branches are named `android<release>-<kernel version>`,
  for example `android15-6.6`, and carry an upstream LTS plus Android patches.
- GKI freezes a Kernel Module Interface (KMI) for each branch. Vendor modules
  may use only the symbols on the branch's symbol lists. Changes that alter
  exported structs or symbols after the freeze are refused, or go through that
  branch's KMI update process. Check the branch's own documentation on
  source.android.com before touching anything exported.
- Patch subjects record origin: `UPSTREAM:`, `BACKPORT:`, `FROMGIT:`,
  `FROMLIST:`, and `ANDROID:` for downstream-only changes (ChromeOS kernels use
  `CHROMIUM:` instead). Follow the convention the branch already uses; it is
  how the next rebase decides what to drop. Fixes go upstream first and come
  back as `UPSTREAM:` or `BACKPORT:`.

## Vendor BSP trees and build wrappers

Look for the wrapper before you run `make`:

- BSP scripts at the repository root or a parent directory: `build.sh`,
  `envsetup.sh`, usually with a board or product selection step.
- Android: `build/build.sh` with `BUILD_CONFIG=` on older branches, Kleaf
  (Bazel) on newer ones.
- Yocto: `bitbake virtual/kernel`, `bitbake -c menuconfig virtual/kernel`,
  `bitbake -c diffconfig virtual/kernel` to turn your menuconfig changes into a
  fragment, and `devtool modify <kernel-recipe>` for an editable source tree.
  Check the Yocto manual for your release.
- Buildroot: `make linux-menuconfig`, `make linux-update-defconfig`, and
  `make linux-rebuild`, from the Buildroot top directory.

When a wrapper exists, use it to configure, build, and check DTBs, and read it
to find the `make` goal, toolchain, `O=` directory, and fragments it uses. A
bare `make` in such a tree picks the host compiler or the wrong config, or
writes build output into the source tree. If you must bypass the wrapper, reuse
its toolchain prefix and a separate `O=` directory, and say that you did.

## Config layering

- Defconfigs and fragments state intent. The resolved `.config` in the build
  output directory is what was built, and `/proc/config.gz` on the target is
  what is running. Check the resolved file before claiming an option is on.
- An option that silently disappears has an unmet `depends on`. `merge_config.sh`
  prints `WARNING: Value requested for CONFIG_X not in final .config`. Search
  for the symbol in `make menuconfig` (press `/`) to see the dependency it is
  missing.

```bash
make <fragment>.config                 # merge kernel/configs/ or arch/$ARCH/configs/<fragment>, then olddefconfig
scripts/kconfig/merge_config.sh -m .config a.config b.config && make olddefconfig
scripts/config --enable FOO --module BAR --disable BAZ && make olddefconfig
scripts/config --state FOO             # y, m, n, or undef
scripts/diffconfig old.config .config  # what actually changed
make savedefconfig                     # minimal defconfig in the output dir; copy it over arch/*/configs/<name>
```

Put a product or board change in its own fragment instead of the shared vendor
defconfig: the shared one builds every product.

## Vendor ABI coupling

- Prebuilt GPU, NPU, ISP, and codec libraries, firmware, out-of-tree modules,
  and the bootloader all encode assumptions about this kernel. Leave the UAPI,
  DT properties, config options, and module interfaces they rely on alone
  unless rebuilding them is in scope.
- A config change that alters a struct layout or an exported symbol's CRC
  breaks prebuilt modules. With `CONFIG_MODVERSIONS`, loading fails with
  `disagrees about version of symbol`. Without it, the module may load and
  corrupt memory.
- Bootloaders commonly edit the DTB at boot: memory, reserved memory, MAC
  addresses, `/chosen`. The running devicetree is not the `.dtb` you built.

## Someone else's dirty tree

Vendor and bring-up checkouts often carry uncommitted work. Run
`git status --short` before you start and again at the end, and leave changes
you did not make alone: no `git stash`, `git checkout --`, or cleanup. Build
the smallest target first (one object, module, or dtb), then broaden.
