# Kernel Documentation Routes

Kernel root: generated from the local kernel checkout used by the maintainer.

Total file entries indexed: 9048

Full machine index: regenerate `assets/kernel-doc-index.jsonl` locally when needed. It is intentionally not committed.

## Top-Level Counts

| Directory | Files |
| --- | ---: |
| `devicetree` | 5039 |
| `ABI` | 571 |
| `userspace-api` | 414 |
| `admin-guide` | 375 |
| `translations` | 368 |
| `driver-api` | 304 |
| `networking` | 235 |
| `hwmon` | 219 |
| `filesystems` | 127 |
| `arm` | 74 |
| `gpu` | 68 |
| `RCU` | 54 |
| `core-api` | 54 |
| `virt` | 53 |
| `scsi` | 52 |
| `sound` | 50 |
| `trace` | 47 |
| `features` | 45 |
| `i2c` | 45 |
| `mm` | 45 |
| `x86` | 44 |
| `process` | 41 |
| `input` | 37 |
| `fb` | 36 |
| `bpf` | 34 |
| `dev-tools` | 31 |
| `powerpc` | 31 |
| `power` | 28 |
| `usb` | 28 |
| `firmware-guide` | 25 |
| `security` | 23 |
| `PCI` | 21 |
| `arm64` | 21 |
| `leds` | 20 |
| `block` | 18 |
| `crypto` | 18 |
| `locking` | 18 |
| `tools` | 18 |
| `.` | 17 |
| `misc-devices` | 17 |
| ... 45 more | |

## Curated Routes

### process

- `Documentation/process/submitting-patches.rst`
- `Documentation/process/submit-checklist.rst`
- `Documentation/process/coding-style.rst`
- `Documentation/process/handling-regressions.rst`
- `Documentation/process/stable-kernel-rules.rst`
- `Documentation/process/maintainer-handbooks.rst`
- `Documentation/maintainer/index.rst`

### debug-tests

- `Documentation/dev-tools/testing-overview.rst`
- `Documentation/dev-tools/kunit/index.rst`
- `Documentation/dev-tools/kselftest.rst`
- `Documentation/dev-tools/ktap.rst`
- `Documentation/admin-guide/dynamic-debug-howto.rst`
- `Documentation/admin-guide/ramoops.rst`
- `Documentation/admin-guide/kdump/index.rst`
- `Documentation/dev-tools/kgdb.rst`
- `Documentation/dev-tools/gdb-kernel-debugging.rst`

### tracing

- `Documentation/trace/ftrace.rst`
- `Documentation/trace/events.rst`
- `Documentation/trace/kprobes.rst`
- `Documentation/trace/fprobe.rst`
- `Documentation/trace/histogram.rst`

### sanitizers-static-analysis

- `Documentation/dev-tools/checkpatch.rst`
- `Documentation/dev-tools/sparse.rst`
- `Documentation/dev-tools/coccinelle.rst`
- `Documentation/dev-tools/kasan.rst`
- `Documentation/dev-tools/kmsan.rst`
- `Documentation/dev-tools/kcsan.rst`
- `Documentation/dev-tools/kfence.rst`
- `Documentation/dev-tools/kmemleak.rst`
- `Documentation/fault-injection/fault-injection.rst`

### devicetree-drivers

- `Documentation/devicetree/index.rst`
- `Documentation/devicetree/bindings/writing-schema.rst`
- `Documentation/devicetree/bindings/submitting-patches.rst`
- `Documentation/devicetree/bindings/dts-coding-style.rst`
- `Documentation/driver-api/index.rst`
- `Documentation/driver-api/driver-model/index.rst`
- `Documentation/driver-api/regulator.rst`
- `Documentation/driver-api/gpio/index.rst`
- `Documentation/driver-api/pin-control.rst`
- `Documentation/driver-api/i2c.rst`
- `Documentation/driver-api/spi.rst`
- `Documentation/driver-api/clk.rst`
- `Documentation/driver-api/thermal/index.rst`

### kbuild-abi

- `Documentation/kbuild/index.rst`
- `Documentation/kbuild/kconfig-language.rst`
- `Documentation/kbuild/kconfig.rst`
- `Documentation/kbuild/makefiles.rst`
- `Documentation/admin-guide/abi.rst`
- `Documentation/ABI/README`
- `Documentation/userspace-api/index.rst`


## Keyword Routes

### submitting

- `Documentation/devicetree/bindings/submitting-patches.rst`
- `Documentation/dev-tools/checkpatch.rst`
- `Documentation/admin-guide/bug-hunting.rst`
- `Documentation/admin-guide/devices.rst`
- `Documentation/admin-guide/media/saa7134.rst`
- `Documentation/admin-guide/reporting-issues.rst`
- `Documentation/admin-guide/security-bugs.rst`
- `Documentation/devicetree/bindings/index.rst`
- `Documentation/devicetree/bindings/writing-bindings.rst`
- `Documentation/driver-api/dmaengine/provider.rst`
- `Documentation/driver-api/dmaengine/pxa_dma.rst`
- `Documentation/driver-api/gpio/using-gpio.rst`
- ... 28 more; query JSONL for exact routes

### patch

- `Documentation/admin-guide/README.rst`
- `Documentation/admin-guide/bug-bisect.rst`
- `Documentation/admin-guide/bug-hunting.rst`
- `Documentation/admin-guide/cgroup-v1/blkio-controller.rst`
- `Documentation/admin-guide/cgroup-v1/cgroups.rst`
- `Documentation/admin-guide/cgroup-v1/cpusets.rst`
- `Documentation/admin-guide/cgroup-v1/memory.rst`
- `Documentation/admin-guide/cifs/authors.rst`
- `Documentation/admin-guide/device-mapper/dm-queue-length.rst`
- `Documentation/admin-guide/device-mapper/dm-service-time.rst`
- `Documentation/admin-guide/devices.rst`
- `Documentation/admin-guide/devices.txt`
- ... 28 more; query JSONL for exact routes

### maintainer

- `Documentation/dev-tools/testing-overview.rst`
- `Documentation/dev-tools/checkpatch.rst`
- `Documentation/dev-tools/kcsan.rst`
- `Documentation/admin-guide/auxdisplay/cfag12864b.rst`
- `Documentation/admin-guide/auxdisplay/ks0108.rst`
- `Documentation/admin-guide/blockdev/zram.rst`
- `Documentation/admin-guide/bug-bisect.rst`
- `Documentation/admin-guide/bug-hunting.rst`
- `Documentation/admin-guide/devices.rst`
- `Documentation/admin-guide/kernel-per-CPU-kthreads.rst`
- `Documentation/admin-guide/perf/hisi-pmu.rst`
- `Documentation/admin-guide/ras.rst`
- ... 28 more; query JSONL for exact routes

### stable

- `Documentation/dev-tools/kselftest.rst`
- `Documentation/admin-guide/abi.rst`
- `Documentation/dev-tools/checkpatch.rst`
- `Documentation/admin-guide/README.rst`
- `Documentation/admin-guide/abi-stable.rst`
- `Documentation/admin-guide/abi-testing.rst`
- `Documentation/admin-guide/bcache.rst`
- `Documentation/admin-guide/bug-hunting.rst`
- `Documentation/admin-guide/cgroup-v1/cpusets.rst`
- `Documentation/admin-guide/cgroup-v1/memory.rst`
- `Documentation/admin-guide/cgroup-v2.rst`
- `Documentation/admin-guide/cputopology.rst`
- ... 28 more; query JSONL for exact routes

### regression

- `Documentation/dev-tools/kselftest.rst`
- `Documentation/dev-tools/kgdb.rst`
- `Documentation/process/submitting-patches.rst`
- `Documentation/process/handling-regressions.rst`
- `Documentation/process/stable-kernel-rules.rst`
- `Documentation/admin-guide/bug-bisect.rst`
- `Documentation/admin-guide/index.rst`
- `Documentation/admin-guide/pm/amd-pstate.rst`
- `Documentation/admin-guide/reporting-issues.rst`
- `Documentation/admin-guide/reporting-regressions.rst`
- `Documentation/driver-api/acpi/linuxized-acpica.rst`
- `Documentation/driver-api/firmware/firmware-usage-guidelines.rst`
- ... 28 more; query JSONL for exact routes

### debug

- `Documentation/admin-guide/dynamic-debug-howto.rst`
- `Documentation/admin-guide/LSM/Smack.rst`
- `Documentation/admin-guide/LSM/Yama.rst`
- `Documentation/admin-guide/README.rst`
- `Documentation/admin-guide/acpi/initrd_table_override.rst`
- `Documentation/admin-guide/blockdev/floppy.rst`
- `Documentation/admin-guide/blockdev/zram.rst`
- `Documentation/admin-guide/btmrvl.rst`
- `Documentation/admin-guide/bug-hunting.rst`
- `Documentation/admin-guide/cgroup-v1/blkio-controller.rst`
- `Documentation/admin-guide/cgroup-v1/memory.rst`
- `Documentation/admin-guide/cifs/authors.rst`
- ... 28 more; query JSONL for exact routes

### trace

- `Documentation/admin-guide/ramoops.rst`
- `Documentation/admin-guide/LSM/Smack.rst`
- `Documentation/admin-guide/LSM/Yama.rst`
- `Documentation/admin-guide/blockdev/paride.rst`
- `Documentation/admin-guide/bug-hunting.rst`
- `Documentation/admin-guide/cgroup-v1/freezer-subsystem.rst`
- `Documentation/admin-guide/cifs/usage.rst`
- `Documentation/admin-guide/devices.txt`
- `Documentation/admin-guide/hw-vuln/core-scheduling.rst`
- `Documentation/admin-guide/hw-vuln/spectre.rst`
- `Documentation/admin-guide/kdump/gdbmacros.txt`
- `Documentation/admin-guide/kdump/kdump.rst`
- ... 28 more; query JSONL for exact routes

### ftrace

- `Documentation/admin-guide/ramoops.rst`
- `Documentation/dev-tools/kgdb.rst`
- `Documentation/trace/ftrace.rst`
- `Documentation/trace/events.rst`
- `Documentation/trace/kprobes.rst`
- `Documentation/trace/fprobe.rst`
- `Documentation/trace/histogram.rst`
- `Documentation/admin-guide/kernel-parameters.rst`
- `Documentation/admin-guide/kernel-parameters.txt`
- `Documentation/admin-guide/perf-security.rst`
- `Documentation/admin-guide/pm/intel_pstate.rst`
- `Documentation/admin-guide/pstore-blk.rst`
- ... 24 more; query JSONL for exact routes

### dynamic debug

- `Documentation/admin-guide/dynamic-debug-howto.rst`
- `Documentation/admin-guide/media/ipu3.rst`
- `Documentation/core-api/printk-index.rst`
- `Documentation/networking/devlink/ice.rst`

### fault injection

- `Documentation/fault-injection/fault-injection.rst`
- `Documentation/admin-guide/kernel-parameters.txt`
- `Documentation/fault-injection/nvme-fault-injection.rst`
- `Documentation/process/4.Coding.rst`
- `Documentation/i2c/gpio-fault-injection.rst`
- `Documentation/filesystems/f2fs.rst`
- `Documentation/sound/designs/procfile.rst`

### kunit

- `Documentation/dev-tools/testing-overview.rst`
- `Documentation/dev-tools/kunit/index.rst`
- `Documentation/dev-tools/ktap.rst`
- `Documentation/dev-tools/kasan.rst`
- `Documentation/dev-tools/kmsan.rst`
- `Documentation/dev-tools/kfence.rst`
- `Documentation/admin-guide/kernel-parameters.txt`
- `Documentation/dev-tools/index.rst`
- `Documentation/dev-tools/kunit/api/index.rst`
- `Documentation/dev-tools/kunit/api/resource.rst`
- `Documentation/dev-tools/kunit/api/test.rst`
- `Documentation/dev-tools/kunit/architecture.rst`
- ... 16 more; query JSONL for exact routes

### kselftest

- `Documentation/dev-tools/testing-overview.rst`
- `Documentation/dev-tools/kselftest.rst`
- `Documentation/dev-tools/ktap.rst`
- `Documentation/process/handling-regressions.rst`
- `Documentation/admin-guide/pm/amd-pstate.rst`
- `Documentation/dev-tools/index.rst`
- `Documentation/dev-tools/kunit/architecture.rst`
- `Documentation/dev-tools/kunit/faq.rst`
- `Documentation/process/maintainer-pgp-guide.rst`
- `Documentation/bpf/bpf_devel_QA.rst`
- `Documentation/bpf/s390.rst`
- `Documentation/livepatch/callbacks.rst`
- ... 2 more; query JSONL for exact routes

### ktap

- `Documentation/dev-tools/kunit/index.rst`
- `Documentation/dev-tools/ktap.rst`
- `Documentation/dev-tools/index.rst`
- `Documentation/dev-tools/kunit/architecture.rst`

### kasan

- `Documentation/dev-tools/testing-overview.rst`
- `Documentation/dev-tools/kasan.rst`
- `Documentation/dev-tools/kfence.rst`
- `Documentation/admin-guide/kernel-parameters.txt`
- `Documentation/admin-guide/mm/memory-hotplug.rst`
- `Documentation/dev-tools/index.rst`
- `Documentation/dev-tools/kunit/run_wrapper.rst`
- `Documentation/dev-tools/kunit/style.rst`
- `Documentation/arm64/kasan-offsets.sh`
- `Documentation/features/debug/KASAN/arch-support.txt`
- `Documentation/powerpc/kasan.txt`
- `Documentation/translations/zh_CN/dev-tools/kasan.rst`
- ... 11 more; query JSONL for exact routes

### kmsan

- `Documentation/dev-tools/kmsan.rst`
- `Documentation/dev-tools/index.rst`

### kcsan

- `Documentation/dev-tools/testing-overview.rst`
- `Documentation/dev-tools/kcsan.rst`
- `Documentation/dev-tools/index.rst`
- `Documentation/translations/zh_CN/dev-tools/index.rst`
- `Documentation/translations/zh_CN/dev-tools/testing-overview.rst`

### kfence

- `Documentation/dev-tools/testing-overview.rst`
- `Documentation/dev-tools/kfence.rst`
- `Documentation/dev-tools/index.rst`
- `Documentation/translations/zh_CN/dev-tools/index.rst`
- `Documentation/translations/zh_CN/dev-tools/testing-overview.rst`

### ubsan

- `Documentation/dev-tools/testing-overview.rst`
- `Documentation/dev-tools/index.rst`
- `Documentation/dev-tools/ubsan.rst`
- `Documentation/process/deprecated.rst`
- `Documentation/atomic_t.txt`
- `Documentation/translations/it_IT/process/deprecated.rst`
- `Documentation/translations/zh_CN/dev-tools/index.rst`
- `Documentation/translations/zh_CN/dev-tools/testing-overview.rst`

### lockdep

- `Documentation/dev-tools/testing-overview.rst`
- `Documentation/process/submit-checklist.rst`
- `Documentation/dev-tools/checkpatch.rst`
- `Documentation/admin-guide/kernel-parameters.txt`
- `Documentation/admin-guide/sysctl/kernel.rst`
- `Documentation/process/4.Coding.rst`
- `Documentation/process/maintainer-tip.rst`
- `Documentation/RCU/lockdep-splat.rst`
- `Documentation/RCU/lockdep.rst`
- `Documentation/features/locking/lockdep/arch-support.txt`
- `Documentation/locking/lockdep-design.rst`
- `Documentation/RCU/Design/Data-Structures/Data-Structures.rst`
- ... 28 more; query JSONL for exact routes

### checkpatch

- `Documentation/devicetree/bindings/submitting-patches.rst`
- `Documentation/kbuild/makefiles.rst`
- `Documentation/process/submitting-patches.rst`
- `Documentation/process/submit-checklist.rst`
- `Documentation/dev-tools/checkpatch.rst`
- `Documentation/dev-tools/index.rst`
- `Documentation/driver-api/media/maintainer-entry-profile.rst`
- `Documentation/maintainer/maintainer-entry-profile.rst`
- `Documentation/process/5.Posting.rst`
- `Documentation/process/license-rules.rst`
- `Documentation/process/maintainer-netdev.rst`
- `Documentation/gpu/introduction.rst`
- ... 15 more; query JSONL for exact routes

### sparse

- `Documentation/dev-tools/testing-overview.rst`
- `Documentation/driver-api/pin-control.rst`
- `Documentation/dev-tools/sparse.rst`
- `Documentation/admin-guide/cifs/todo.rst`
- `Documentation/admin-guide/device-mapper/zero.rst`
- `Documentation/admin-guide/ext4.rst`
- `Documentation/admin-guide/jfs.rst`
- `Documentation/admin-guide/kdump/kdump.rst`
- `Documentation/admin-guide/kdump/vmcoreinfo.rst`
- `Documentation/admin-guide/mm/memory-hotplug.rst`
- `Documentation/dev-tools/index.rst`
- `Documentation/devicetree/bindings/media/amlogic,gx-vdec.yaml`
- ... 28 more; query JSONL for exact routes

### coccinelle

- `Documentation/dev-tools/testing-overview.rst`
- `Documentation/dev-tools/coccinelle.rst`
- `Documentation/dev-tools/index.rst`
- `Documentation/process/4.Coding.rst`
- `Documentation/translations/it_IT/process/4.Coding.rst`
- `Documentation/translations/zh_CN/dev-tools/index.rst`
- `Documentation/translations/zh_CN/dev-tools/testing-overview.rst`
- `Documentation/translations/zh_CN/process/4.Coding.rst`
- `Documentation/translations/zh_TW/process/4.Coding.rst`

### devicetree

- `Documentation/admin-guide/ramoops.rst`
- `Documentation/dev-tools/checkpatch.rst`
- `Documentation/admin-guide/kernel-parameters.rst`
- `Documentation/devicetree/bindings/ABI.rst`
- `Documentation/devicetree/bindings/arm/actions.yaml`
- `Documentation/devicetree/bindings/arm/airoha.yaml`
- `Documentation/devicetree/bindings/arm/altera.yaml`
- `Documentation/devicetree/bindings/arm/altera/socfpga-clk-manager.yaml`
- `Documentation/devicetree/bindings/arm/amazon,al.yaml`
- `Documentation/devicetree/bindings/arm/amlogic.yaml`
- `Documentation/devicetree/bindings/arm/amlogic/amlogic,meson-gx-ao-secure.yaml`
- `Documentation/devicetree/bindings/arm/amlogic/amlogic,meson-mx-secbus2.yaml`
- ... 28 more; query JSONL for exact routes

### dt-binding

- `Documentation/devicetree/bindings/arm/arm,coresight-catu.yaml`
- `Documentation/devicetree/bindings/arm/arm,coresight-cti.yaml`
- `Documentation/devicetree/bindings/arm/arm,trace-buffer-extension.yaml`
- `Documentation/devicetree/bindings/arm/firmware/linaro,optee-tz.yaml`
- `Documentation/devicetree/bindings/arm/mediatek/mediatek,audsys.txt`
- `Documentation/devicetree/bindings/arm/mediatek/mediatek,bdpsys.txt`
- `Documentation/devicetree/bindings/arm/mediatek/mediatek,camsys.txt`
- `Documentation/devicetree/bindings/arm/mediatek/mediatek,ethsys.txt`
- `Documentation/devicetree/bindings/arm/mediatek/mediatek,g3dsys.txt`
- `Documentation/devicetree/bindings/arm/mediatek/mediatek,hifsys.txt`
- `Documentation/devicetree/bindings/arm/mediatek/mediatek,imgsys.txt`
- `Documentation/devicetree/bindings/arm/mediatek/mediatek,infracfg.yaml`
- ... 28 more; query JSONL for exact routes

### dt_binding_check

- `Documentation/devicetree/bindings/writing-schema.rst`
- `Documentation/devicetree/bindings/submitting-patches.rst`

### dtbs_check

- `Documentation/devicetree/bindings/writing-schema.rst`

### driver

- `Documentation/admin-guide/README.rst`
- `Documentation/admin-guide/acpi/fan_performance_states.rst`
- `Documentation/admin-guide/acpi/initrd_table_override.rst`
- `Documentation/admin-guide/acpi/ssdt-overlays.rst`
- `Documentation/admin-guide/aoe/aoe.rst`
- `Documentation/admin-guide/aoe/todo.rst`
- `Documentation/admin-guide/auxdisplay/cfag12864b.rst`
- `Documentation/admin-guide/auxdisplay/ks0108.rst`
- `Documentation/admin-guide/binderfs.rst`
- `Documentation/admin-guide/blockdev/floppy.rst`
- `Documentation/admin-guide/blockdev/paride.rst`
- `Documentation/admin-guide/blockdev/ramdisk.rst`
- ... 28 more; query JSONL for exact routes

### kconfig

- `Documentation/dev-tools/testing-overview.rst`
- `Documentation/dev-tools/kgdb.rst`
- `Documentation/dev-tools/checkpatch.rst`
- `Documentation/dev-tools/kasan.rst`
- `Documentation/dev-tools/kcsan.rst`
- `Documentation/dev-tools/kfence.rst`
- `Documentation/admin-guide/README.rst`
- `Documentation/admin-guide/bootconfig.rst`
- `Documentation/admin-guide/kernel-parameters.txt`
- `Documentation/admin-guide/kernel-per-CPU-kthreads.rst`
- `Documentation/admin-guide/laptops/thinkpad-acpi.rst`
- `Documentation/admin-guide/mm/zswap.rst`
- ... 28 more; query JSONL for exact routes

### abi

- `Documentation/admin-guide/abi.rst`
- `Documentation/admin-guide/LSM/SafeSetID.rst`
- `Documentation/admin-guide/LSM/Smack.rst`
- `Documentation/admin-guide/LSM/index.rst`
- `Documentation/admin-guide/abi-obsolete.rst`
- `Documentation/admin-guide/abi-removed.rst`
- `Documentation/admin-guide/abi-stable.rst`
- `Documentation/admin-guide/abi-testing.rst`
- `Documentation/admin-guide/bcache.rst`
- `Documentation/admin-guide/blockdev/drbd/index.rst`
- `Documentation/admin-guide/blockdev/ramdisk.rst`
- `Documentation/admin-guide/blockdev/zram.rst`
- ... 28 more; query JSONL for exact routes

### sysfs

- `Documentation/admin-guide/acpi/cppc_sysfs.rst`
- `Documentation/admin-guide/acpi/fan_performance_states.rst`
- `Documentation/admin-guide/acpi/index.rst`
- `Documentation/admin-guide/acpi/initrd_table_override.rst`
- `Documentation/admin-guide/aoe/aoe.rst`
- `Documentation/admin-guide/aoe/status.sh`
- `Documentation/admin-guide/bcache.rst`
- `Documentation/admin-guide/blockdev/zram.rst`
- `Documentation/admin-guide/cputopology.rst`
- `Documentation/admin-guide/device-mapper/cache.rst`
- `Documentation/admin-guide/devices.rst`
- `Documentation/admin-guide/ext4.rst`
- ... 28 more; query JSONL for exact routes

### uapi

- `Documentation/dev-tools/checkpatch.rst`
- `Documentation/admin-guide/gpio/sysfs.rst`
- `Documentation/admin-guide/kernel-parameters.rst`
- `Documentation/admin-guide/media/ipu3.rst`
- `Documentation/admin-guide/media/rkisp1.rst`
- `Documentation/admin-guide/media/v4l-drivers.rst`
- `Documentation/admin-guide/sysrq.rst`
- `Documentation/devicetree/bindings/input/input-reset.txt`
- `Documentation/driver-api/cxl/memory-devices.rst`
- `Documentation/driver-api/dma-buf.rst`
- `Documentation/driver-api/firewire.rst`
- `Documentation/driver-api/generic-counter.rst`
- ... 28 more; query JSONL for exact routes

### rockchip

- `Documentation/admin-guide/kernel-parameters.txt`
- `Documentation/admin-guide/media/platform-cardlist.rst`
- `Documentation/admin-guide/media/rkisp1.rst`
- `Documentation/devicetree/bindings/arm/cpus.yaml`
- `Documentation/devicetree/bindings/arm/rockchip.yaml`
- `Documentation/devicetree/bindings/arm/rockchip/pmu.yaml`
- `Documentation/devicetree/bindings/ata/snps,dwc-ahci.yaml`
- `Documentation/devicetree/bindings/clock/clk-pvtm.txt`
- `Documentation/devicetree/bindings/clock/rockchip,clk-out.yaml`
- `Documentation/devicetree/bindings/clock/rockchip,px30-cru.yaml`
- `Documentation/devicetree/bindings/clock/rockchip,rk1808-cru.txt`
- `Documentation/devicetree/bindings/clock/rockchip,rk3036-cru.yaml`
- ... 28 more; query JSONL for exact routes

### rk3576

- `Documentation/devicetree/bindings/arm/rockchip.yaml`
- `Documentation/devicetree/bindings/clock/rockchip,rk3576-cru.yaml`
- `Documentation/devicetree/bindings/display/rockchip/rockchip,analogix-dp.yaml`
- `Documentation/devicetree/bindings/i3c/rockchip,i3c-master.yaml`
- `Documentation/devicetree/bindings/mailbox/rockchip-mailbox.txt`
- `Documentation/devicetree/bindings/media/i2c/lt7911d.txt`
- `Documentation/devicetree/bindings/net/rockchip-dwmac.yaml`

### lapis

- `Documentation/devicetree/bindings/arm/rockchip.yaml`
- `Documentation/devicetree/bindings/misc/fpc,fpc2534.yaml`
- `Documentation/devicetree/bindings/power/supply/pamir-ai,lapis-charge-manager.yaml`
- `Documentation/devicetree/bindings/usb/awinic,aw35615.yaml`

### pamir

- `Documentation/devicetree/bindings/arm/rockchip.yaml`
- `Documentation/devicetree/bindings/display/panel/sharp,ls027b7dh01.yaml`
- `Documentation/devicetree/bindings/leds/worldsemi,ws2812b-spi.yaml`
- `Documentation/devicetree/bindings/misc/fpc,fpc2534.yaml`
- `Documentation/devicetree/bindings/misc/pamir-ai,hwinfo.yaml`
- `Documentation/devicetree/bindings/net/nfc/st,st25dv04k.yaml`
- `Documentation/devicetree/bindings/power/supply/pamir-ai,lapis-charge-manager.yaml`
- `Documentation/devicetree/bindings/regulator/silergy,sy6862c.yaml`
- `Documentation/devicetree/bindings/usb/awinic,aw35615.yaml`
- `Documentation/devicetree/bindings/vendor-prefixes.yaml`
- `Documentation/devicetree/bindings/watchdog/rockchip,rk806-wdt.yaml`

### denali

- `Documentation/devicetree/bindings/mtd/denali,nand.yaml`

## Full Index Usage

Do not load the full JSONL into context. Query it with `rg`, `jq`, or a short script, then open only the relevant kernel docs.

Examples:

```bash
rg '"keywords":.*kselftest' assets/kernel-doc-index.jsonl
rg 'rk3576|lapis|pwm-fan' assets/kernel-doc-index.jsonl
```
