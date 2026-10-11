# Debugging by symptom

Start from what the kernel already told you. Keep the first splat, because
everything after it is usually fallout. Reproduce before theorizing, and change
one thing at a time.

Covers: get the evidence first; oops or panic; warnings and splats; device does
not probe; hangs, lockups, and stalls; memory corruption and use after free;
races; dies early in boot; suspend and resume; slow or high latency; worked
before: bisect; tracing toolbox; debug kernels; post-mortem.

## Get the evidence first

- The whole log from boot, as text: `dmesg`, `journalctl -k -b -1` for the
  previous boot, or the serial console. A photo of a screen loses the first
  oops, which is the one that matters.
- The exact build: `uname -r`, the commit (`git describe`), and the config
  (`/proc/config.gz` with `CONFIG_IKCONFIG_PROC`, or the build's `.config`).
- Taint: `cat /proc/sys/kernel/tainted`, decoded by
  `tools/debugging/kernel-chktaint`. `D` means an oops already happened and `W`
  means a warning already fired, so the report in front of you is not the
  first problem. Scroll up.
- Debug info in the crashing build (`CONFIG_DEBUG_INFO_*`). Without it, none of
  the decoders below can name a line.

## Oops or panic

Read these lines of the first oops, in order:

1. The cause: `BUG: kernel NULL pointer dereference, address: ...`,
   `Unable to handle kernel paging request at virtual address ...` (arm64), or
   `general protection fault, probably for non-canonical address ...` (x86).
2. `Oops: ... [#1]`: `#1` is the first. A higher number means you are reading
   fallout.
3. `RIP:` (x86) or `pc :` and `lr :` (arm64): the faulting function and offset.
4. `Call Trace:`. Frames printed with a leading `?` are stale stack contents
   the unwinder could not confirm; do not build a theory on them.

The fault address says a lot before you open any source:

| Address looks like | Usually means |
| --- | --- |
| small, such as `0x10` or `0x58` | NULL struct pointer; the value is the member offset. `pahole -C <struct> vmlinux` or `gdb vmlinux -ex 'ptype /o struct <name>'` names the member |
| `0x6b6b6b6b6b6b6b6b` | `POISON_FREE`: use after free of slab memory (with slab poisoning on) |
| `0x5a5a5a5a5a5a5a5a` | `POISON_INUSE`: allocated but never initialized |
| `0xdead000000000100` or `...122` (x86_64) | `LIST_POISON1`/`LIST_POISON2`: a list entry used after `list_del()` |
| non-canonical on x86_64 | a corrupted pointer, very often one of the poison values above |

Decode against the exact `vmlinux` and modules that crashed:

```bash
scripts/decode_stacktrace.sh vmlinux auto < oops.txt    # file:line for every frame; auto finds modules
scripts/faddr2line vmlinux foo_probe+0x58/0x1a0         # one frame
scripts/faddr2line drivers/foo/foo.ko foo_irq+0x1c/0x90 # a frame inside a module
scripts/decodecode < oops.txt                           # disassemble Code:, marks the trapping instruction
```

`Kernel panic - not syncing: Fatal exception` is the consequence, not the
cause. Boot with `oops=panic` and `panic=0` only when you want the box to stop
at the first oops for capture.

## Warnings and splats

A `WARNING:` line names the file and line of a `WARN_ON()`. Read that source
line first: its condition is the bug report.

| Splat | What it means | Usual fix |
| --- | --- | --- |
| `BUG: sleeping function called from invalid context` | a sleeping call (mutex, `GFP_KERNEL`, `msleep()`, `regmap` on a sleeping bus) under a spinlock, RCU read lock, or in hard IRQ; the trace names the caller | threaded IRQ, move the work to a workqueue, or a non-sleeping primitive. Needs `CONFIG_DEBUG_ATOMIC_SLEEP` to be reported |
| `BUG: scheduling while atomic` | same class, caught at schedule time | as above |
| `possible circular locking dependency detected` | lockdep saw two paths take the same locks in opposite order; it reports on the first occurrence, before any real deadlock | pick one order and enforce it; the two chains in the report are the two paths |
| `inconsistent {HARDIRQ-ON-W} -> {IN-HARDIRQ-W} usage` | a lock taken in IRQ context is also taken elsewhere with IRQs enabled | `spin_lock_irqsave()` on the process-context side |
| `refcount_t: underflow; use-after-free.` | a put without a matching get | find the extra put; the trace shows who |
| `list_add corruption` or `list_del corruption` | double add, double delete, or use after free (`CONFIG_DEBUG_LIST`) | treat as memory corruption |
| `ODEBUG: free active ... object type: timer_list` (or `work_struct`) | freeing memory that holds a live timer or work item (`CONFIG_DEBUG_OBJECTS_*`) | cancel synchronously before freeing |

## Device does not probe

Walk the chain from build to bind, and stop at the first broken link:

1. Built and loaded: `zgrep CONFIG_FOO /proc/config.gz`, `modinfo foo`,
   `lsmod | grep foo`, `ls /sys/bus/platform/drivers/foo`.
2. A device exists: `ls /sys/bus/platform/devices/`. Dump the DT the kernel
   actually booted with, not the one you think you flashed:
   `dtc -I fs -O dts /sys/firmware/devicetree/base > live.dts`. Check the node
   is there and `status = "okay"`.
3. It matches: the node's `compatible` against the driver's `of_device_id`
   table, and `cat /sys/bus/platform/devices/<dev>/modalias`. Module autoload
   also needs `MODULE_DEVICE_TABLE()`.
4. Probe ran and deferred or failed:

   ```bash
   cat /sys/kernel/debug/devices_deferred   # deferred devices with the dev_err_probe() reason
   dmesg | grep -iE '<dev>|probe'           # -517 is -EPROBE_DEFER
   ```

   Boot with `dyndbg="file drivers/base/dd.c +p"` to log every probe attempt.
5. A supplier is missing: fw_devlink holds a consumer until its clocks,
   regulators, pinctrl, GPIOs, and PHYs probe. `ls /sys/class/devlink/` lists
   the links. Booting with `fw_devlink=permissive` is a diagnostic only: if the
   device then probes, the real fix is the missing supplier driver or DT
   reference.

Iterate without rebooting:

```bash
echo <dev> > /sys/bus/platform/drivers/foo/unbind
echo <dev> > /sys/bus/platform/drivers/foo/bind
```

An unbind/bind loop under KASAN is also the cheapest way to find teardown bugs.

## Hangs, lockups, and stalls

| Message | Meaning |
| --- | --- |
| `INFO: task foo:123 blocked for more than 120 seconds` | a task stuck in uninterruptible sleep; something it waits on (lock, completion, I/O) never arrives. The trace shows the wait |
| `watchdog: BUG: soft lockup - CPU#3 stuck for 22s!` | a CPU looping in the kernel without scheduling: a busy loop with preemption off, or a missing `cond_resched()` |
| `hard LOCKUP` | interrupts disabled too long, caught by the NMI watchdog |
| `rcu: INFO: rcu_sched detected stalls` | a CPU or task not passing a quiescent state: looping with preemption or IRQs off, or an over-long RCU read-side section |

While the machine still answers, ask it (root can always write
`/proc/sysrq-trigger`, whatever `kernel.sysrq` says):

```bash
echo w > /proc/sysrq-trigger   # blocked (D state) tasks with stacks
echo t > /proc/sysrq-trigger   # every task
echo l > /proc/sysrq-trigger   # backtrace of every active CPU
cat /proc/<pid>/stack
```

When it does not answer, send sysrq over the serial console (break, then the
key), or make the detectors panic (`softlockup_panic=1`, `hung_task_panic=1`)
and capture with pstore or kdump. Suspect a deadlock: build with
`CONFIG_PROVE_LOCKING`, which usually names the inversion on the first run even
when the hang itself is rare.

## Memory corruption and use after free

- KASAN first (`CONFIG_KASAN=y`). A `BUG: KASAN: slab-use-after-free in ...`
  report carries three stacks: the bad access, `Allocated by`, and
  `Freed by`. The freed-by stack is usually the answer.
- On a kernel you cannot rebuild, boot with `slab_debug=FZPU` (`slub_debug=` on
  older trees): sanity checks, red zones, poisoning, and owner tracking.
- For long soak runs or production, KFENCE (`CONFIG_KFENCE`) samples
  allocations cheaply.
- Leaks: `CONFIG_DEBUG_KMEMLEAK`, then
  `echo scan > /sys/kernel/debug/kmemleak; cat /sys/kernel/debug/kmemleak`.
  Page leaks: `page_owner=on` with `CONFIG_PAGE_OWNER`.
- Refcounted objects freed too early: `CONFIG_DEBUG_KOBJECT_RELEASE` delays the
  release so late users crash loudly.

## Races

- Make a rare race deterministic by widening the window: drop a temporary
  `msleep(100)` (or `mdelay()` in atomic context) between the two steps you
  suspect. It never goes into the patch.
- `CONFIG_KCSAN` reports data races as `BUG: KCSAN: data-race in a / b`.
- `CONFIG_PROVE_LOCKING` for ordering, `CONFIG_DEBUG_OBJECTS_TIMERS` and
  `_WORK` for objects freed while still armed.
- Shake the scheduler: `preempt=full` on `PREEMPT_DYNAMIC` kernels, CPU
  hotplug (`echo 0 > /sys/devices/system/cpu/cpu1/online`), `taskset`, and
  load on other CPUs.

## Dies early in boot

- Get output earlier: `earlycon` (uses the DT `stdout-path`, or name the UART
  explicitly), `keep_bootcon`, `ignore_loglevel`, `loglevel=8`. On x86,
  `earlyprintk=serial,ttyS0,115200`.
- `initcall_debug` prints every initcall with its duration; the last line
  before silence is your suspect. `initcall_blacklist=foo_init` skips it to
  confirm.
- Check what the bootloader really passed: `/proc/cmdline` and the DTB
  (`/sys/firmware/fdt`) on a boot that works.
- A reset with no message at all is often not software: hardware watchdog,
  PMIC brownout, or thermal shutdown. Check those before bisecting.

## Suspend and resume

```bash
echo 1 > /sys/power/pm_debug_messages
echo devices > /sys/power/pm_test && echo mem > /sys/power/state   # stop after device suspend, then resume
rtcwake -m mem -s 10                                               # one automated cycle
cat /sys/power/pm_wakeup_irq                                       # what woke it
```

Boot with `no_console_suspend` to keep the console alive, and `initcall_debug`
to time each device's suspend and resume callback.
`tools/power/pm-graph/sleepgraph.py` turns a cycle into a timeline.

For runtime PM, read `/sys/devices/.../power/runtime_status` and
`runtime_usage`. A usage count that never returns to zero is a missing put.

## Slow or high latency

- CPU time: `perf top`, `perf record -g`, then `perf report`.
- Scheduling and locks: `perf sched latency`, `perf lock contention`.
- A specific kernel path:
  `trace-cmd record -p function_graph -g foo_irq_handler`, then
  `trace-cmd report`.
- Interrupts or preemption held off: the `irqsoff` and `preemptoff` tracers;
  the worst case lands in `tracing_max_latency`.
- Which function turned a call into an error: `retsnoop`.

## Worked before: bisect

```bash
git bisect start <bad> <good>
cp .config ../bisect.config
# each step: cp ../bisect.config .config && make olddefconfig, build, boot, test
git bisect run ./test.sh       # exit 0 good, 125 skip, 1 to 127 otherwise bad
git bisect skip                # this step fails for an unrelated reason
git bisect log > bisect.log
```

- Hold the config fixed; `olddefconfig` gives new symbols their defaults
  instead of prompting.
- A flaky reproducer makes bisect lie. Run each step several times before
  marking it good.
- `git bisect start --first-parent` finds which merge brought the bug in, which
  is the quickest first pass across a merge window.
- Confirm the culprit by reverting it on top of the bad commit. If the bug
  stays, the bisect was wrong.

## Tracing toolbox

```bash
echo 'module foo +p' > /proc/dynamic_debug/control     # dev_dbg()/pr_debug() at runtime
echo 'file drivers/foo/* +p' > /proc/dynamic_debug/control
cd /sys/kernel/tracing
echo function_graph > current_tracer
echo foo_probe > set_graph_function
echo 1 > events/i2c/enable                              # existing tracepoints beat new printk
cat trace_pipe
```

- For probe-time messages, use the boot form: `foo.dyndbg=+p` or
  `dyndbg="file drivers/foo/* +p"`.
- `trace_printk()` writes to the trace buffer, not the console, so it is cheap
  enough for hot paths. It prints a warning banner at boot and never goes into
  a patch.
- `ftrace_dump_on_oops` dumps the trace buffer when the kernel oopses: the last
  thing before the crash, for free.
- Enable events from boot with `trace_event=i2c:*,regmap:*`; add `tp_printk` to
  send them to the console when the box dies before you can read tracefs.
- `bpftrace` for one-off questions on kernels with BPF and BTF; `drgn` to poke
  live kernel data structures or a vmcore with Python.

## Debug kernels

`make defconfig debug.config` (or `make debug.config` on top of an existing
`.config`) merges `kernel/configs/debug.config` and runs `olddefconfig`. It
turns on KASAN, lockdep (`PROVE_LOCKING`, `PROVE_RCU`), `DEBUG_ATOMIC_SLEEP`,
`DEBUG_OBJECTS`, kmemleak, UBSAN, `SLUB_DEBUG_ON`, and `PANIC_ON_OOPS`, so the
first oops stops the machine. It is slow, and the slowdown can hide timing
bugs. When a heavy debug build makes the bug vanish, add options one at a time
instead.

| Option | Catches | Note |
| --- | --- | --- |
| `KASAN_GENERIC` | out of bounds, use after free | any arch with support, high overhead; `KASAN_HW_TAGS` on arm64 MTE is cheap |
| `KMSAN` | uninitialized reads | Clang only, x86_64 and s390, excludes KASAN and KCSAN |
| `KCSAN` | data races | x86_64, arm64, s390, powerpc, 64-bit mips, xtensa |
| `UBSAN` (`_BOUNDS`, `_SHIFT`, `_INTEGER_WRAP`) | undefined behavior | `UBSAN_TRAP` to stop instead of warn |
| `KFENCE` | sampled memory errors | cheap enough for production |
| `PROVE_LOCKING`, `DEBUG_ATOMIC_SLEEP` | lock order, IRQ-context misuse, sleeping in atomic | run every locking change under these |
| `FAULT_INJECTION` (`FAILSLAB`, `FAIL_PAGE_ALLOC`, `FAIL_FUNCTION`) | untested error paths | `FAIL_FUNCTION` needs `FUNCTION_ERROR_INJECTION` |

Confirm an option exists for your architecture in `arch/<arch>/Kconfig`
(`HAVE_ARCH_KASAN` and friends) before blaming the config.

## Post-mortem

- pstore for boards that reset before you can read the log:
  `CONFIG_PSTORE_RAM` with a `ramoops` reserved-memory node, or
  `reserve_mem=2M:4096:oops ramoops.mem_name=oops`. After reboot, read
  `/sys/fs/pstore/`.
- kdump captures the whole memory image; analyze with `crash` or
  `drgn -c vmcore`.
- kgdb on hardware: `kgdboc=ttyS0,115200 kgdbwait`, then `gdb vmlinux` and
  `target remote /dev/ttyUSB0`. In QEMU: add `-s -S` and boot with `nokaslr`,
  then `target remote :1234`. `make scripts_gdb` builds the `lx-*` helpers
  (`lx-dmesg`, `lx-symbols`, `lx-ps`). The docs moved to
  `Documentation/process/debugging/` in v6.14; older trees keep them under
  `Documentation/dev-tools/`.
