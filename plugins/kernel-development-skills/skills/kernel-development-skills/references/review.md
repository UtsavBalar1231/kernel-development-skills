# Reviewing a patch

Assume the patch is wrong until the message and the code agree. Spend your
attention where bugs live: error paths, teardown, concurrency, and anything
userspace can see. The same pass applies to your own patch before it goes out.

Covers: read it in this order; lifetime and teardown; context and locking;
memory and DMA; userspace boundary; power and register state; references;
devicetree and ABI; evidence to ask for; writing the review.

## Read it in this order

1. Subject and message. The prefix should match what the maintainer already
   applies (`git log --oneline -10 -- <file>`). The body should say why: the
   problem, who hits it, and why this fix is right. A message that narrates
   the diff usually hides a missing justification.
2. `Fixes:`. Run `git show <sha>` and confirm that commit introduced the bug,
   not merely touched the same lines. A wrong `Fixes:` sends the fix to the
   wrong stable trees. `git describe --contains <sha>` names the first release
   that shipped the bug.
3. Tags. Every `Reviewed-by:`, `Tested-by:`, and `Acked-by:` was given by that
   person; `Reported-by:` is followed by `Closes:` or `Link:`; an AI-assisted
   patch carries `Assisted-by:` and no agent-added `Signed-off-by:`.
4. Diffstat (`git show --stat`). Scope should match the subject. A refactor
   riding along with a fix, or a "fix" touching twelve files, gets split.
5. Code: every early return and `goto` after an acquisition first, then
   teardown, then locking and context, then the happy path.
6. ABI and devicetree surfaces.
7. Evidence: what was run, on what hardware, and what was not tested.

Before reading deeply, let the machines object:

```bash
git diff --check
scripts/checkpatch.pl --strict -g <commit>
make W=1 C=1 drivers/foo/foo.o                    # new warnings, sparse
git rebase -x 'make -j"$(nproc)" drivers/foo/' <base>   # every commit builds
```

The skill's `scripts/check_kernel_api_patterns.py <files or patch>` flags
deprecated APIs with the release each change landed in. Give it the `.patch` or
`b4 am` `.mbx` directly: it scans only the added lines and reports post-patch
line numbers, so nothing needs to be applied first.

## Lifetime and teardown

- IRQ live during teardown. `devm_request_irq()` keeps the handler registered
  until after `remove()` returns. Look for a `remove()` that gates a clock,
  asserts reset, or destroys a workqueue the handler uses. Fix: make that
  teardown devm-managed at the matching point in probe, or `disable_irq()`
  first.
- IRQ requested before its state exists. Look for `devm_request_irq()` above
  `spin_lock_init()`, `INIT_WORK()`, or regmap setup. A pending interrupt from
  the bootloader, or a shared line, fires immediately. Fix: request after
  initialization, or with `IRQF_NO_AUTOEN` and `enable_irq()` later.
- Work or timers outliving their state. Look for state freed (directly or by
  devres) with no `cancel_work_sync()`, `disable_work_sync()`, or
  `timer_shutdown_sync()` before it, or with the cancel placed while the IRQ
  that queues the work is still enabled. Fix: stop the source, then cancel,
  then free.
- Error paths unwinding wrong. Look for labels that release in a different
  order than probe acquired, a manual step without its unwind, `kfree()` on
  devm memory (double free), or `goto` mixed with `__free()` in one function.
- sysfs files outliving the driver. Look for `device_create_file()` or
  `sysfs_create_group()` in probe whose `show()` reads driver state that
  devres frees. Fix: `.dev_groups` in the driver struct, which the core
  removes before `remove()` runs.
- Freeing a registered device. After `device_register()` or
  `device_initialize()`, failure paths call `put_device()`, never `kfree()`,
  because the release callback owns the memory.
- Module unload with live callbacks. Look for notifiers, callbacks, or timers
  registered in init without the matching unregister in exit, and
  `file_operations` without `.owner = THIS_MODULE`.

## Context and locking

- Sleeping in atomic context. Look for `mutex_lock()`, `GFP_KERNEL`,
  `msleep()`, `regmap_*()` on I2C or SPI, or `*_cansleep()` GPIO calls inside
  a spinlock, a hard IRQ handler, or a timer callback. `CONFIG_DEBUG_ATOMIC_SLEEP`
  confirms it.
- Lock shared with an IRQ handler taken without disabling interrupts on the
  process side. Fix: `spin_lock_irqsave()` there. lockdep reports it as
  inconsistent lock state.
- Shared IRQ handler that always claims the interrupt. With `IRQF_SHARED`,
  the handler checks its own status register and returns `IRQ_NONE` when
  nothing is pending. Always returning `IRQ_HANDLED` hides a stuck line and
  another device's storm; always returning `IRQ_NONE` gets the line disabled
  with "irq N: nobody cared".
- Lockless fields read with plain loads. Look for a flag polled in a loop, or
  written in one context and read in another without a lock. Fix:
  `READ_ONCE()` and `WRITE_ONCE()`, or a lock. `data_race()` only annotates
  intentionally racy statistics. KCSAN finds these.

## Memory and DMA

- DMA to the stack. With `CONFIG_VMAP_STACK` the stack is not DMA-able at all,
  and SPI and some I2C controllers DMA transfer buffers. Fix: heap buffers or
  a properly aligned member of the state struct.
- DMA buffer sharing a cache line. A DMA buffer embedded in a struct next to
  fields the CPU writes during the transfer corrupts on non-coherent
  architectures. Fix: `__aligned(ARCH_DMA_MINALIGN)` (`IIO_DMA_MINALIGN` in
  IIO), placed last in the struct.
- Unchecked mappings. Every `dma_map_single()` and `dma_map_page()` needs
  `dma_mapping_error()`; with an IOMMU or swiotlb, mapping fails.
  `CONFIG_DMA_API_DEBUG` reports "device driver failed to check map error".
- Size arithmetic that can overflow. Look for `kmalloc(n * size)`,
  `sizeof(*s) + n * sizeof(e)`, and counts from userspace or the device. Fix:
  `kmalloc_array()`, `kcalloc()`, `struct_size()`, `size_mul()`,
  `check_add_overflow()`.
- Endianness. Device registers and descriptors read into `u32` without
  conversion work on little-endian hosts and break on big-endian ones. Fix:
  `__le32` or `__be32` types with `le32_to_cpu()` and friends; `make C=1`
  then reports every mismatch as a restricted-type warning.

## Userspace boundary

- Double fetch. Look for a length or header read from user memory twice:
  validated in the first copy, used from the second. Fix: copy once
  (`memdup_user()`), then validate and use the kernel copy.
- Unbounded copies. `copy_from_user()` length checked against the destination
  size, not trusted from the caller.
- Info leak. A struct copied to userspace with uninitialized members or
  padding leaks kernel memory. Fix: `memset(&s, 0, sizeof(s))` before filling;
  `= {}` does not guarantee cleared padding.
- Speculative indexing. A user-controlled index used after a bounds check
  needs `idx = array_index_nospec(idx, ARRAY_SIZE(tbl));` between the check
  and the access.
- New uAPI structs. Explicit `__u32`/`__u64` types, no implicit padding,
  64-bit alignment, and reserved fields checked to be zero so the interface
  can grow.

## Power and register state

- `pm_runtime_get_sync()` raises the usage count even when it fails, so an
  error path that returns without a put leaves the device powered forever.
  Fix: `pm_runtime_resume_and_get()`.
- Register state lost across suspend. Look for a regmap cache with no
  `regcache_cache_only()`, `regcache_mark_dirty()`, and `regcache_sync()`
  around a power cut.
- Clocks and regulators enabled in probe but not disabled on a later error or
  in remove. Fix: the `devm_*_get_enabled()` helpers, or an explicit unwind.

## References

- Device node leaks. `of_get_child_by_name()`, `of_parse_phandle()`,
  `of_find_*()`, and `fwnode_get_named_child_node()` return a reference.
  Breaking out of `for_each_child_of_node()` leaks one. Fix: `__free(device_node)`,
  `__free(fwnode_handle)`, or the `_scoped` iterators (cleanup.h since v6.5),
  or an explicit put on every exit.
- Refcount imbalance. Every `get_device()`, `kref_get()`, and
  `try_module_get()` has exactly one put on every path. `refcount_t: underflow`
  in a log is the symptom.

## Devicetree and ABI

- The binding patch comes before the driver and DTS that use it, passes
  `make dt_binding_check DT_SCHEMA_FILES=<file>`, and has the DT maintainers on
  Cc. Compatibles are specific (`vendor,device`), and properties describe
  hardware, not driver configuration.
- Board wiring lives in the board `.dts`, not the SoC `.dtsi`. The DTS passes
  `make CHECK_DTBS=y <vendor>/<board>.dtb`.
- Anything under `include/uapi/`, sysfs, ioctl, netlink, and module
  parameters that deployments use is ABI: documented under
  `Documentation/ABI/`, backward compatible, and tested. debugfs is not ABI,
  and nothing should depend on it.
- Removing or renaming a DT property or compatible breaks every deployed
  DTB; old forms stay accepted.

## Evidence to ask for

- Probe and remove: the probe log, plus an unbind/bind loop under KASAN.
- Locking: a run with `CONFIG_PROVE_LOCKING`.
- Power: runtime suspend and resume cycles, and system suspend when in scope.
- DMA: data integrity under load.
- Build: `W=1` and sparse clean on touched files, and every commit building.
- A plain statement of what was not tested and why. Missing evidence is a
  question for the author, not a reason to assume.

## Writing the review

Reply inline, quote only the hunk you mean, and raise one issue per comment.
Say whether each point blocks the patch. A `Reviewed-by:` belongs to a person
who read the whole patch and stands behind it; an agent never offers or adds
one on anyone's behalf.
