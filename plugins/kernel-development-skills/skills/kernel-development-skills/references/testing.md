# Testing: proving it works

Picking the test by what you need to prove, writing and running KUnit and
kselftest, walking error paths with fault injection, reproducing fuzzer
reports, testing drivers without the hardware, and the evidence a maintainer
accepts.

## Pick the test by what you are proving

| You need to show | Use |
| --- | --- |
| internal logic: parsers, helpers, data structures, isolatable driver code | KUnit |
| behavior through a userspace interface: syscalls, sysfs, ioctl, netlink | kselftest |
| the driver works on the real device | a boot on hardware with probe and runtime evidence |
| error paths do not leak, double free, or crash | fault injection, under KASAN and kmemleak |
| hostile input cannot crash it | syzkaller, or the reproducer from a syzbot report |

A test that only exercises the success path proves little. Most driver bugs
live in probe failure, unbind, and suspend.

## Writing a KUnit test

Put the suite in `tests/<suite>_kunit.c` next to the code under test (for
example `lib/tests/string_kunit.c`). Prefer the `_kunit` suffix; `_test`
exists in older suites but blurs which tests are KUnit
(`Documentation/dev-tools/kunit/style.rst`).

```c
#include <kunit/test.h>

static void foo_parse_rejects_short_frame(struct kunit *test)
{
	u8 *buf = kunit_kzalloc(test, 2, GFP_KERNEL);	/* freed when the test ends */

	KUNIT_ASSERT_NOT_NULL(test, buf);
	KUNIT_EXPECT_EQ(test, foo_parse(buf, 2), -EINVAL);
}

static struct kunit_case foo_test_cases[] = {
	KUNIT_CASE(foo_parse_rejects_short_frame),
	{}
};

static struct kunit_suite foo_test_suite = {
	.name = "foo",
	.test_cases = foo_test_cases,
};
kunit_test_suite(foo_test_suite);

MODULE_DESCRIPTION("KUnit tests for foo");
MODULE_LICENSE("GPL");
```

- `KUNIT_EXPECT_*` records a failure and keeps going. `KUNIT_ASSERT_*` ends
  the case. Assert only where continuing would crash, such as a NULL buffer.
- Register cleanup with `kunit_add_action()` instead of hand-written teardown,
  so a failed assert still releases everything.
- To test a `static` function, mark it `VISIBLE_IF_KUNIT` and export it with
  `EXPORT_SYMBOL_IF_KUNIT()` from `<kunit/visibility.h>`. The test module then
  needs `MODULE_IMPORT_NS("EXPORTED_FOR_KUNIT_TESTING")`, with a bare token on
  trees before v6.13. Production builds keep the symbol static.
- Kconfig entry, per the style guide: `config FOO_KUNIT_TEST`, `tristate "..."
  if !KUNIT_ALL_TESTS`, `depends on KUNIT`, `default KUNIT_ALL_TESTS`. Depend
  on the feature under test and never `select` it, or `KUNIT_ALL_TESTS` starts
  enabling unrelated code.
- Add a `.kunitconfig` in the directory listing `CONFIG_KUNIT=y`, the test
  symbol, and its dependencies, so anyone can run the suite with one command.

## Running KUnit

```bash
./tools/testing/kunit/kunit.py run --kunitconfig=lib/kunit       # a directory's .kunitconfig
./tools/testing/kunit/kunit.py run 'foo.*'                       # filter by suite or test glob
./tools/testing/kunit/kunit.py run --arch=arm64 --cross_compile=aarch64-linux-gnu-
./tools/testing/kunit/kunit.py run --kconfig_add CONFIG_KASAN=y --kconfig_add CONFIG_PROVE_LOCKING=y
./tools/testing/kunit/kunit.py parse < dmesg.txt                 # KTAP from a real boot
```

- The default arch is UML. It is fast, but code that depends on real
  interrupts, DMA, or arch features needs `--arch` (QEMU configs live in
  `tools/testing/kunit/qemu_configs/`) or a real boot.
- Run new tests with KASAN and lockdep added at least once; a test that passes
  while corrupting memory is worse than no test.
- On a board, build the suite into the kernel or as a module, boot, and feed
  the console log to `kunit.py parse`.
- Useful extras: `--run_isolated suite`, `--raw_output=all`, `--json`,
  `--list_suites` (since v7.1), `--junit` (since v7.2). Check
  `kunit.py run --help` in the target tree; flags differ between releases.

## Kselftest

```bash
make headers                                             # tests build against the tree's uapi, not the host's
make -C tools/testing/selftests TARGETS=gpio run_tests
make TARGETS="gpio net" SKIP_TARGETS=net/forwarding summary=1 kselftest
```

- Config: each target ships `tools/testing/selftests/<target>/config`. Merge
  just yours with `scripts/kconfig/merge_config.sh -m .config
  tools/testing/selftests/gpio/config` and `make olddefconfig`.
  `make kselftest-merge` merges every target's fragment, which is rarely what
  you want.
- Running on a target box: `make -C tools/testing/selftests TARGETS=gpio
  install INSTALL_PATH=/tmp/ksft` (or `gen_tar`), copy it over, then
  `./run_kselftest.sh -l` to list, `-t gpio:<test>` to run one, and
  `-o <seconds>` to override a timeout that is too short for slow hardware.
- The build succeeds if any one target builds; pass `FORCE_TARGETS=1` to fail
  on any broken target.
- Write tests with `kselftest_harness.h`: `TEST()`, or `TEST_F()` with
  `FIXTURE()`, `FIXTURE_SETUP()`, and `FIXTURE_TEARDOWN()`, `FIXTURE_VARIANT()`
  for parameter sets, `ASSERT_*` and `EXPECT_*`, `SKIP()`, and
  `TEST_HARNESS_MAIN`.
- Detect missing features and skip (`SKIP()`, `ksft_test_result_skip()`, exit
  code `KSFT_SKIP`, which is 4) instead of failing. Stable kernels run newer
  selftests, so a test that fails on `ENOSYS` or a missing sysfs file turns
  every older branch red.

## Error paths with fault injection

Needs `CONFIG_FAULT_INJECTION`, `CONFIG_FAULT_INJECTION_DEBUG_FS`, and the
fault types you want (`CONFIG_FAILSLAB`, `CONFIG_FAIL_PAGE_ALLOC`,
`CONFIG_FAIL_FUNCTION`), per `Documentation/fault-injection/fault-injection.rst`.

- `ignore-gfp-wait` defaults to `Y` for failslab and fail_page_alloc, so
  sleeping (`GFP_KERNEL`) allocations, which is most of a probe path, are
  never failed until you set it to `N`.
- Walk every allocation in a probe, one failure at a time, with
  `/proc/self/fail-nth` (the Nth fault point in that task fails):

  ```bash
  echo N > /sys/kernel/debug/failslab/ignore-gfp-wait
  for n in $(seq 1 200); do
  	sh -c "echo $n > /proc/self/fail-nth; echo <dev> > /sys/bus/platform/drivers/foo/bind"
  	echo <dev> > /sys/bus/platform/drivers/foo/unbind 2>/dev/null
  done
  dmesg | grep -E 'KASAN|kmemleak|WARNING|BUG'
  ```

  This only reaches probe when it runs synchronously in the writing task, not
  for drivers that prefer asynchronous probe.
- Random failures for soak runs: `task-filter`, `probability`, `interval`,
  `times`, and `verbose` under `/sys/kernel/debug/failslab/`, with
  `echo 1 > /proc/<pid>/make-it-fail` to limit them to one task.
- `fail_function` forces a chosen return value from functions annotated with
  `ALLOW_ERROR_INJECTION()`; the list is in
  `/sys/kernel/debug/fail_function/injectable`. The `retval` file only takes
  unsigned values, so write errnos with `printf %#x -12 > retval`.

## Fuzzing

- A syzbot report links the kernel config, a C reproducer, and the console log.
  Reproduce with the same config (`cp config .config && make olddefconfig`),
  boot it in a VM, then build and run the reproducer inside:
  `gcc -static -pthread -o repro repro.c && ./repro`. Loop it when the bug is a
  race; a reproducer that fires one run in fifty is normal.
- A config option the report had and you do not (KASAN mode, lockdep, a
  particular driver) is the usual reason a reproducer stays silent.
- Running syzkaller yourself needs a kernel with `CONFIG_KCOV`, KASAN, and
  debug info, a VM image, and a `syz-manager` config. Field names change, so
  follow syzkaller's own `docs/linux/setup.md`. Fuzzing an ioctl interface
  needs syscall descriptions for it; without them syzkaller never reaches the
  driver.

## Testing a driver without its hardware

- I2C and SMBus: `modprobe i2c-stub chip_addr=0x48` creates a fake adapter
  with a register file at that address. Preload registers with `i2cset`, then
  bind your driver with `echo foo 0x48 > /sys/bus/i2c/devices/i2c-<N>/new_device`.
  Block transfers need the `functionality` parameter
  (`Documentation/i2c/i2c-stub.rst`).
- GPIO consumers: `gpio-sim` builds simulated chips through configfs, with
  lines you can drive and pull from userspace
  (`Documentation/admin-guide/gpio/gpio-sim.rst`).
- Everything else that is pure logic belongs in KUnit, with the register
  access behind a small function you can fake.

## Evidence a maintainer accepts

- Probe: `dmesg | grep -i foo` showing the bind with no deferral and no
  warnings, and the device under `/sys/bus/<bus>/drivers/foo/`.
- Resources as the kernel sees them: `/sys/kernel/debug/regulator/regulator_summary`,
  `/sys/kernel/debug/clk/clk_summary`, `/sys/kernel/debug/gpio`,
  `/sys/kernel/debug/pinctrl/`, and an interrupt count in `/proc/interrupts`
  that moves when the device should interrupt.
- Bus views: `i2cdetect -y <N>` (`UU` means a driver owns the address),
  `i2cdump`, `lspci -k` (driver in use), `lsusb -t`, `ethtool -i` and `-S`,
  `v4l2-ctl --all`, `media-ctl -p`.
- Before and after for anything touching power or lifetime: runtime PM state
  in `/sys/devices/.../power/runtime_status`, a suspend cycle with
  `rtcwake -m mem -s 10`, and a 100-iteration unbind/bind loop under KASAN and
  kmemleak that ends with no splat and no leak.

## Say what you did not test

Put the test setup in the changelog or below the `---` line: board or VM,
base commit, config, and the commands. Name what you could not test and why;
"compile-tested on arm64 and x86_64 allmodconfig, not run on hardware" is
acceptable when it is true and unacceptable when it is hidden. Your own
testing goes in the changelog, not in a `Tested-by:` tag, which is for other
people.
