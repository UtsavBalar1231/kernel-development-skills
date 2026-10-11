# Writing driver code

Copy the newest well-reviewed driver in the same subsystem, not the oldest one
that looks similar; old drivers carry patterns reviewers now reject. Anything
below marked "since vX.Y" may not exist in your tree, so check it first with
`git grep -n '<symbol>' include/` and fall back to what neighboring drivers in
that tree do.

Covers: know what can sleep where; probe in this order; teardown runs
backwards, and devres runs last; use the subsystem, not a private interface;
firmware properties and hardware truth; Kconfig and Makefile; power management;
errors and logging; scoped cleanup; exports and namespaces; API changes by
version; Rust drivers.

## Know what can sleep where

- Hard IRQ handlers, timer callbacks (softirq), spinlock and RCU read-side
  sections cannot sleep: no mutex, no `GFP_KERNEL`, no `msleep()`, no regmap
  on I2C or SPI, no `gpiod_set_value_cansleep()`.
- Devices on a sleeping bus (I2C, SPI, GPIO expanders) need a threaded IRQ:
  `devm_request_threaded_irq(dev, irq, NULL, foo_irq_thread, IRQF_ONESHOT, ...)`.
  A NULL primary handler without `IRQF_ONESHOT` fails with "Threaded irq
  requested with handler=NULL and !ONESHOT".
- Work items and threaded handlers run in process context and may sleep.
- Data shared with a hard IRQ handler: `spin_lock_irqsave()` on the process
  side, plain `spin_lock()` in the handler. Data shared only with a threaded
  handler or between process contexts: a mutex.
- Put `might_sleep()` at the top of helpers that may sleep. With
  `CONFIG_DEBUG_ATOMIC_SLEEP` it reports atomic callers even on runs where the
  helper happens not to block.
- `GFP_ATOMIC` is a last resort. Move the allocation out of the atomic section
  first, because atomic allocations fail under memory pressure.

## Probe in this order

1. Allocate state: `st = devm_kzalloc(dev, sizeof(*st), GFP_KERNEL)`, then
   `platform_set_drvdata()` (or `i2c_set_clientdata()`, `spi_set_drvdata()`)
   before anything can call back into the driver.
2. Acquire resources: `devm_platform_ioremap_resource()`, regmap, clocks,
   resets, regulators, GPIOs. Return supplier errors unchanged through
   `dev_err_probe()`, so `-EPROBE_DEFER` propagates and its reason shows in
   `/sys/kernel/debug/devices_deferred`.
3. Initialize everything a callback can touch: locks, completions, work items
   (`devm_mutex_init()` since v6.10, `INIT_WORK()`).
4. Power up and bring the hardware to a known state: deassert reset, enable
   clocks, read the ID register. If a fallback compatible is meant to bind
   newer parts, warn on an unexpected ID instead of failing; some maintainers
   (IIO among them) ask for exactly that.
5. Request the IRQ. If the hardware may already be asserting it, request with
   `IRQF_NO_AUTOEN` and call `enable_irq()` once ready.
6. Register with the subsystem last (`devm_iio_device_register()`,
   `devm_hwmon_device_register_with_info()`, ...). From that moment userspace
   can call you.

Per-compatible data comes from `device_get_match_data()`; i2c drivers also have
`i2c_get_match_data()` (since v6.5) and `i2c_client_get_device_id()` (since
v6.2). Pair `.of_match_table` with `MODULE_DEVICE_TABLE(of, ...)`: without it
the driver still works built-in and silently never autoloads as a module.

## Teardown runs backwards, and devres runs last

On unbind the driver core removes the `.dev_groups` attributes, calls your
`remove()`, and only then releases devres entries in reverse order of
acquisition (`drivers/base/dd.c`). Consequences:

- A devm-requested IRQ and a devm-registered subsystem device are still live
  while `remove()` runs. If `remove()` gates a clock, asserts reset, or
  destroys a workqueue that the handler or a callback uses, a late interrupt
  or userspace call hits dead hardware. Either register that teardown with
  `devm_add_action_or_reset()` at the matching point in probe, or call
  `disable_irq()` and unregister first in `remove()`.
- Keep probe either fully devm-managed, or devm for a strict prefix followed by
  manual steps. A manual step in the middle of devm acquisitions inverts the
  teardown order.
- Devres frees memory and releases resources. It does not cancel work, stop
  timers, quiesce DMA, or order hardware shutdown. Stop the source first (the
  IRQ), then `disable_work_sync()` (since v6.10; it also blocks requeueing) or
  `cancel_work_sync()`, then `timer_shutdown_sync()` (since v6.2), then free.
- `remove()` cannot fail. Its return type is `void` on current trees (see the
  table below), and on older trees the return value is ignored anyway.
- `.shutdown` runs on reboot and kexec: stop DMA and interrupts, free nothing.
- Prove it with an unbind/bind loop and a module unload under KASAN.

## Use the subsystem, not a private interface

Sensors and ADCs go to IIO or hwmon, voltage control to regulator, thermal
readings and cooling to thermal, buttons and touch to input, batteries and
chargers to power_supply, LEDs to leds, panels and bridges to DRM, cameras to
media, calibration data to nvmem, and clock, reset, pinctrl, or GPIO providers
to their frameworks. Reviewers will ask for it, userspace tools already speak
the subsystem ABI, and every private char device or sysfs file becomes ABI you
maintain forever.

- regmap pays for itself when it brings locking, caching, endianness, or
  variant handling. New caches use `REGCACHE_MAPLE`; `REGCACHE_FLAT_S` (since
  v6.19) when the cache must never allocate at runtime; `REGCACHE_RBTREE` is
  legacy. Use `devm_regmap_field_alloc()` for bitfields that move between
  variants.
- MMIO goes through `readl()`/`writel()` on `void __iomem *`. Read back after a
  posted write when the hardware needs completion before you continue.
- GPIOs are descriptors with logical values. Active-low belongs in the DT
  flags; never invert in the driver.
- Clocks and supplies that stay on for the device lifetime:
  `devm_clk_get_enabled()`, `devm_clk_get_optional_enabled()`,
  `devm_clk_bulk_get_all_enabled()`, `devm_regulator_get_enable()`,
  `devm_regulator_get_enable_optional()`, `devm_regulator_bulk_get_enable()`.
  Disabling a regulator does not mean the rail turned off; it may be shared.
- DMA: call `dma_set_mask_and_coherent()` before mapping, check every
  `dma_mapping_error()`, never DMA to the stack, and give a DMA buffer
  embedded in a struct its own cache line (`__aligned(ARCH_DMA_MINALIGN)`, or
  `IIO_DMA_MINALIGN` in IIO), placed last.

## Firmware properties and hardware truth

- Read properties with `device_property_read_u32()` and friends and walk
  children with the fwnode helpers, so the driver works with DT, ACPI, and
  software nodes. Use `of_*()` only when the subsystem is OF-only.
- A missing optional property returns an error; set the default explicitly
  instead of letting an uninitialized variable through.
- Board policy (voltages, limits, timings) belongs in DT or firmware, not in
  `#define`s in a reusable driver.
- When sources disagree, trust them in this order: schematic and datasheet,
  the DTS actually compiled (its live include chain), the binding, the driver,
  the resolved `.config`, then runtime evidence. A probe success line proves
  the driver bound, not that the hardware works. Board and product names in
  old docs drift, so confirm file names against the include chain.
- Hard thermal, power, and current limits belong in kernel or bootloader
  policy (trip points, regulator constraints), not only in a userspace daemon
  that can crash. When you change one, check the pre-Linux path too.

## Kconfig and Makefile

```text
config SENSORS_FOO
	tristate "Acme FOO temperature sensor"
	depends on I2C
	select REGMAP_I2C
	help
	  Say Y here to enable support for the Acme FOO temperature
	  sensor and its alert interrupt.

	  To compile this driver as a module, choose M here: the
	  module will be called foo.
```

- `depends on` for buses and subsystems; `select` only for library symbols
  without dependencies of their own (`REGMAP_I2C`, `CRC32`), because `select`
  ignores the selected symbol's dependencies and yields configs that fail to
  build.
- Add `|| COMPILE_TEST` to architecture or platform dependencies when the
  driver allows it, so build bots compile it on every arch and report your
  warnings before users do.
- `tristate` unless the code cannot be a module. No `default y` for a new
  driver. checkpatch wants a help text of at least four lines.
- `obj-$(CONFIG_SENSORS_FOO) += foo.o` in the subsystem Makefile, in its
  existing sort order. Build it `=y`, `=m`, and with each dependency off.

## Power management

- Declare ops with macros, not `#ifdef CONFIG_PM`:
  `DEFINE_SIMPLE_DEV_PM_OPS()` with `.pm = pm_sleep_ptr(&ops)` for system sleep
  only; `DEFINE_RUNTIME_DEV_PM_OPS()` with `.pm = pm_ptr(&ops)` for runtime PM;
  `SYSTEM_SLEEP_PM_OPS()` and `RUNTIME_PM_OPS()` inside a hand-written
  `struct dev_pm_ops`. The pointer macros let the compiler drop unused
  callbacks without `__maybe_unused`.
- Enable with `devm_pm_runtime_enable()`, or
  `devm_pm_runtime_set_active_enabled()` (since v6.16) when the device starts
  powered.
- Take references with `pm_runtime_resume_and_get()`.
  `pm_runtime_get_sync()` raises the usage count even when it fails, so every
  error path after it has to put. Scoped forms: `guard(pm_runtime_active)`
  since v6.18, `PM_RUNTIME_ACQUIRE()` since v6.19 (always followed by
  `PM_RUNTIME_ACQUIRE_ERR()`).
- Since v6.17 `pm_runtime_put_autosuspend()` marks the device busy itself; on
  older trees call `pm_runtime_mark_last_busy()` first. Since v7.0
  `pm_runtime_put()` returns `void`.
- A device that loses power across suspend loses its registers:
  `regcache_cache_only(map, true)` on the way down, `regcache_mark_dirty()` and
  `regcache_sync()` on the way up.
- Watch `/sys/devices/.../power/runtime_status` and `runtime_usage` while
  testing; a usage count that never drops back means a missing put.

## Errors and logging

- Return the errno you received. Remapping a supplier error to `-EINVAL` hides
  `-EPROBE_DEFER` and breaks deferred probe.
- `dev_err_probe()` in probe; `dev_warn_probe()` (since v6.13),
  `dev_err_ptr_probe()` and `dev_err_cast_probe()` (since v6.11) for the other
  shapes. Since v6.18 `devm_request_irq()` and `devm_request_threaded_irq()`
  log their own failure, so return the error without wrapping it.
- `dev_err_ratelimited()` on paths a device or user can trigger repeatedly.
  `dev_dbg()` for diagnostics; dynamic debug turns it on when needed.
- `WARN_ON_ONCE()` only for states that mean the kernel itself is broken. A
  warning that userspace or a device can trigger is a bug in its own right:
  syzbot reports it as a crash and `panic_on_warn` machines reboot.
- No `BUG()` or `BUG_ON()` in drivers; a local fault must not take down the
  machine.

## Scoped cleanup

`<linux/cleanup.h>` (since v6.5) gives `guard()` and `scoped_guard()` for
locks, `__free()` for allocations and references (`__free(device_node)`,
`__free(fwnode_handle)`), `no_free_ptr()` and `return_ptr()` to hand ownership
out, and `ACQUIRE()` with `ACQUIRE_ERR()` since v6.17. Two rules reviewers
enforce: never mix `goto` unwinding and cleanup helpers in one function, and
declare a `__free()` variable where it is assigned, not as `= NULL` at the top,
because cleanup order follows declaration order. Child iteration has scoped
forms (`for_each_child_of_node_scoped()`,
`device_for_each_child_node_scoped()`) that drop the reference on early exit.

## Exports and namespaces

- Since v6.13 namespaces are string literals: `EXPORT_SYMBOL_NS_GPL(sym, "FOO")`
  and `MODULE_IMPORT_NS("FOO")`. Older trees take a bare token.
- The PM export macros still take a bare token and stringify it:
  `EXPORT_NS_GPL_DEV_PM_OPS(foo_pm_ops, FOO)`. Mixing the two forms is a
  common build break.
- To restrict a symbol to named in-tree modules,
  `EXPORT_SYMBOL_FOR_MODULES(sym, "mod1,mod-*")` (GPL only). It was
  `EXPORT_SYMBOL_GPL_FOR_MODULES` in v6.16 and renamed in v6.17.

## API changes by version

| Old | New | When |
| --- | --- | --- |
| platform `int (*remove)()`, `.remove_new` | `void (*remove)()` | void since v6.11; `.remove_new` existed v6.3 to v6.12, deleted in v6.13 |
| i2c two-argument `.probe`, `.probe_new` | one-argument `.probe(struct i2c_client *)` | since v6.3; `.probe_new` removed in v6.6; i2c `remove()` void since v6.1 |
| spi `int remove()` | `void remove()` | since v5.18 |
| `del_timer()`, `del_timer_sync()` | `timer_delete()`, `timer_delete_sync()`, `timer_shutdown_sync()` for teardown | new names since v6.2; old ones removed in v6.15 |
| `try_to_del_timer_sync()` | `timer_delete_sync_try()` | renamed in v6.16 |
| `from_timer()` | `timer_container_of()` | v6.16 |
| `hrtimer_init()` then `.function =` | `hrtimer_setup()` | since v6.13; `hrtimer_init()` removed in v6.15 |
| `system_wq`, `system_unbound_wq` | `system_percpu_wq`, `system_dfl_wq` | v6.17 |
| `alloc_workqueue(name, 0, n)` | pass `WQ_PERCPU` or `WQ_UNBOUND` explicitly | `WQ_PERCPU` since v6.17; omitting both WARNs since v7.2. On older trees `0` means per-CPU |
| `create_workqueue()` and friends | `alloc_workqueue()`, `alloc_ordered_workqueue()` | |
| `kmalloc(sizeof(*p), ...)` | `kmalloc_obj(*p)` family (GFP optional) | since v7.0; no devm variant, keep `devm_kzalloc(dev, sizeof(*st), ...)` |
| `kmalloc(n * size, ...)` | `kmalloc_array()`, `kcalloc()`, `struct_size()`, `size_mul()` | |
| zero- or one-element trailing arrays | flexible array plus `__counted_by()` | |
| `strncpy()` | `strscpy()`, `strscpy_pad()`, `memtostr()`, `strtomem()` | removed in v7.2 |
| `strlcpy()`, `strcpy()` | `strscpy()` | `strlcpy()` removed in v6.8 |
| `simple_strto*()` | `kstrto*()` | |
| `sprintf()` in sysfs `show()` | `sysfs_emit()`, `sysfs_emit_at()` | |
| `kmap()`, `kmap_atomic()` | `kmap_local_page()` | |
| `%pK` in printk | `%pK` only in procfs or sysfs file content | |
| integer `gpio_*()`, `of_get_named_gpio()` | `devm_gpiod_get*()` | legacy API needs `CONFIG_GPIOLIB_LEGACY` and `devm_gpio_request()` is gone since v6.17; `<linux/of_gpio.h>` removed in v7.1; legacy API moved to `<linux/gpio/legacy.h>` in v7.2 |
| `gpiod_set_value*()` returning `void` | returns `int`; check it where the line can fail | since v6.15 |
| `SIMPLE_DEV_PM_OPS()`, `UNIVERSAL_DEV_PM_OPS()`, `SET_*_PM_OPS()` | `DEFINE_SIMPLE_DEV_PM_OPS()`, `DEFINE_RUNTIME_DEV_PM_OPS()` | |
| `MODULE_IMPORT_NS(FOO)` | `MODULE_IMPORT_NS("FOO")` | v6.13 |
| `REGCACHE_RBTREE`, `REGCACHE_FLAT` | `REGCACHE_MAPLE`, `REGCACHE_FLAT_S` | `REGCACHE_FLAT_S` since v6.19 |
| fake platform device for a virtual device | `faux_device` (`<linux/device/faux.h>`) | since v6.14 |
| `BUG_ON()` for validation | return an error | |

Sources: `Documentation/process/deprecated.rst`,
`Documentation/core-api/printk-formats.rst` (for `%pK`),
`scripts/checkpatch.pl`, and the headers named in each row.

## Rust drivers

Bus abstractions live in `rust/kernel/` (`platform.rs`, `i2c.rs`, `pci.rs`,
`usb.rs`, `auxiliary.rs`, `faux.rs`), with working examples in
`samples/rust/rust_driver_*.rs` and docs under `Documentation/rust/`. Whether a
Rust driver is welcome is the subsystem maintainer's call; ask before writing
one.
