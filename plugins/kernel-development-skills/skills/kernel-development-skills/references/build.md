# Build, configure, boot

The edit, build, boot loop: getting the config you meant, building only what
you touched, toolchains, booting in a VM, editor setup, the build checks
reviewers expect, and vendor build wrappers.

## The resolved .config is the truth

Defconfigs and fragments state intent. The `.config` in the output directory
is what was built. Check it before claiming an option is on:
`scripts/config --file <out>/.config -s FOO` prints `y`, `m`, `n`, or `undef`.

- After any edit to `.config`, by hand or by script, run `make olddefconfig`.
  An option whose `depends on` is unmet is dropped silently, so look again
  after olddefconfig, not before.
- Why is my option off? `make menuconfig`, press `/`, type the symbol. The
  result shows `Depends on:` with each term's current value (`[=n]`) and
  `Selected by`. The unmet term is the answer.
- Flip options from scripts instead of a menu:

  ```bash
  scripts/config --enable FOO --module BAR --disable BAZ --set-val LOG_BUF_SHIFT 18
  make olddefconfig
  ```

- Fragments: `make defconfig kvm_guest.config debug.config` applies each
  `<name>.config` from `kernel/configs/` or `arch/$ARCH/configs/` with
  `merge_config.sh`, then runs olddefconfig. The tree ships `debug.config`,
  `kvm_guest.config`, `hardening.config`, `rust.config`, `tiny.config`,
  `nopm.config`, and a few arch ones.
- Your own fragment: `scripts/kconfig/merge_config.sh -m .config my.frag`, then
  `make olddefconfig`. Read its output: `WARNING: Value requested for CONFIG_X
  not in final .config` means a dependency overruled you.
- Compare two configs: `scripts/diffconfig .config.old .config`.
- Changing a defconfig: `make savedefconfig` writes a minimal `defconfig` into
  the output directory. Diff it against `arch/$ARCH/configs/<name>_defconfig`
  and carry over only the lines you meant. A full `.config` is never a
  defconfig.
- After moving to a newer base, `make listnewconfig` (or `helpnewconfig`)
  shows the symbols olddefconfig is about to default for you.
- A config for the machine in front of you: `make localmodconfig` keeps only
  modules that are loaded now. For another machine, save its `lsmod` output and
  run `make LSMOD=<file> localmodconfig`.
- `make kconfig-sym-check` (since v7.2) finds references to Kconfig symbols
  that do not exist. `make W=c` (since v6.8) adds extra checks at the Kconfig
  stage.

## Build only what you touched

```bash
make -j"$(nproc)" drivers/iio/adc/foo.o   # one object
make drivers/iio/adc/                     # one in-tree directory
make drivers/iio/adc/foo.ko               # one module, including the final link
make drivers/iio/adc/foo.i                # preprocessed; .s for assembly, .lst for mixed
make <vendor>/<board>.dtb                 # one DTB; make dtbs for all of them
```

- Use `dir/` for in-tree code, not `M=dir`. `M=` treats the directory as an
  external module, and kbuild skips the kernel-doc check for external modules
  even under `W=1`.
- `O=../build-arm64` keeps each architecture and config in its own directory
  and the source tree clean. A source tree that has been built in place
  refuses `O=` builds with `The source tree is not clean, please run 'make
  mrproper'`.
- Cross-compiling: pass `ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu-` on every
  invocation, config targets included.
- Clang: `make LLVM=1` uses clang, lld, and the LLVM binutils. Use
  `LLVM=-18` for versioned binaries and `LLVM=/path/to/llvm/` for a toolchain
  outside `PATH`. Pass the same `LLVM=` value to every invocation, because
  Kconfig records compiler capabilities at config time and a mismatch builds a
  config the compiler cannot honor.
- ccache only hits when the build timestamp is fixed:
  `KBUILD_BUILD_TIMESTAMP='' make LLVM=1 CC="ccache clang"`.
- Install modules into a staging root instead of the host:
  `make modules_install INSTALL_MOD_PATH=/tmp/rootfs INSTALL_MOD_STRIP=1`.
- Minimum GCC, Clang, binutils, Python, Rust, and bindgen versions are in the
  table in `Documentation/process/changes.rst` of the target tree. A toolchain
  below them fails in confusing ways, so check there first.

## Rust

- `make LLVM=1 rustavailable` says whether the Rust toolchain is usable and, if
  not, which piece is missing or too old. Run it first: `make LLVM=1
  rust.config` requests `CONFIG_RUST=y`, and olddefconfig drops it again
  without complaint when the arch or toolchain cannot support it.
- `make LLVM=1 rustfmtcheck` checks formatting, `make LLVM=1 CLIPPY=1 <target>`
  runs Clippy, and `make LLVM=1 rusttest` runs host-side tests.
- Build Rust with full LLVM. GCC-based Rust builds are still marked
  experimental in `Documentation/rust/quick-start.rst`.

## Boot it in a VM

Anything that is not tied to a specific board (core logic, locking, error
paths, KUnit, most syzbot reproducers) reproduces faster in a VM, gets a
debugger for free, and cannot brick anything.

- virtme-ng boots the tree you just built with the host's root filesystem
  mounted read-only, in seconds. Typical use: `vng --build` to build a
  VM-friendly kernel in the current tree, `vng` to boot it, `vng -- <cmd>` to
  run one command and exit. Flags change between releases, so check
  `vng --help`.
- QEMU directly, x86_64 (needs KVM and a raw disk image with a root
  filesystem):

  ```bash
  make defconfig kvm_guest.config && make -j"$(nproc)"
  qemu-system-x86_64 -enable-kvm -cpu host -m 2G -smp 2 -nographic \
    -kernel arch/x86/boot/bzImage -append "console=ttyS0 root=/dev/vda rw" \
    -drive file=rootfs.img,format=raw,if=virtio
  ```

- QEMU, arm64 (the arm64 defconfig already has PL011, virtio-mmio, and
  virtio-pci):

  ```bash
  make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- defconfig
  make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j"$(nproc)" Image
  qemu-system-aarch64 -M virt -cpu max -m 2G -smp 2 -nographic \
    -kernel arch/arm64/boot/Image -append "console=ttyAMA0 root=/dev/vda rw" \
    -drive file=rootfs.img,format=raw,if=virtio
  ```

- `-M virt` gives you a generic machine, not your SoC. A driver for real board
  peripherals still needs the board, or a fake bus device such as `i2c-stub`
  or `gpio-sim`.
- Add `-initrd <cpio>` when there is no disk image; a busybox initramfs is
  enough for most driver and syscall tests.

## Editor and navigation

- `make compile_commands.json` after a build (it lands in the output
  directory with `O=`) gives clangd the real include paths and config macros.
  It only covers files the current config compiles.
- `make tags`, `make TAGS`, `make cscope`, or `make gtags` index the tree.
  `COMPILED_SOURCE=1 make tags` restricts the index to files the config
  actually built, which removes most of the wrong-arch matches.
- For a symbol across releases or other trees, elixir.bootlin.com indexes every
  tag.

## Build checks reviewers expect

- Every commit builds, not just the tip, so bisect stays usable:

  ```bash
  git rebase -x 'make -j"$(nproc)" W=1 drivers/iio/adc/' <base>
  ```

  The rebase stops at the first commit that fails.
- `W=1` adds warnings worth fixing and runs kernel-doc in `-none` mode on
  every compiled file. `W=2` is noisier and adds `-Wall` to kernel-doc; `W=3`
  is mostly noise. Combine levels as `W=12`. Fix every warning your change
  introduces, and leave pre-existing warnings in the file for a separate patch.
- `C=1` runs sparse on files being recompiled, `C=2` on every file. Sparse
  catches `__iomem`, `__user`, and endianness (`__le32`) mistakes the compiler
  accepts.
- Build the touched option as `=y`, `=m`, and `=n`. Built-in versus module
  exposes section mismatches (`__init` code called after boot) and missing
  `EXPORT_SYMBOL`s. The `=n` build exposes callers in other code that need
  `IS_ENABLED()` or header stubs.
- `make allmodconfig` on at least one 64-bit arch catches `depends on`
  mistakes and code that only compiles on your arch.
- `make checkstack` lists the largest stack frames. A new entry near the top
  is a review question.
- `scripts/bloat-o-meter vmlinux.old vmlinux.new` (it also takes `.o` and
  `.ko` files) shows what a change costs in text and data. Maintainers of core
  code ask for it.

## Vendor build wrappers

Vendor and product trees often build the kernel through a wrapper that picks
the toolchain, defconfig and fragments, output directory, and image packaging.
Look for one before typing `make`:

- `build.sh` or `envsetup.sh` plus a board or `lunch` step in a BSP checkout
- Android: `build/build.sh` with `BUILD_CONFIG` on older branches, or Bazel
  (Kleaf, through `tools/bazel`) in a kernel manifest checkout; targets differ
  per branch, so read that checkout's Kleaf docs
- Yocto: `bitbake virtual/kernel`, `bitbake -c menuconfig virtual/kernel`,
  `devtool modify virtual/kernel`
- Buildroot: `make linux-menuconfig` and `make linux-rebuild` from the
  Buildroot top directory

Read the wrapper before running it: find the `make` lines, the `ARCH`,
`CROSS_COMPILE` or `LLVM` values, the defconfig and fragments, the output
directory, and any post-build signing or image packing. Use the wrapper for
anything that will ship. For fast iteration you can run its `make` line by
hand with the same toolchain, arch, config, and `O=` directory; say so in the
result. The resolved `.config` lives in the wrapper's output directory, not in
the source tree.
