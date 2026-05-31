# RK3576 Lapis Kernel Reference

## Table Of Contents

- Scope
- Required repo rules
- Active DTS
- Defconfig layering
- Build and validation commands
- Hardware source-of-truth order
- Thermal and fan policy
- Common traps

## Scope

Use this reference for RK3576/Lapis-style vendor kernels with Rockchip BSP
layout, Lapis board DTS files, and a repo-provided `build.sh` wrapper. Confirm
the active repo guidance before applying these board-specific rules.

## Required Repo Rules

- Never run kernel `make` directly in this checkout.
- Use the root wrapper:

```bash
./build.sh kernel
./build.sh kernel-config
./build.sh kmake <target>
```

The wrapper loads `RK_*` environment and the correct aarch64 toolchain from `prebuilts/gcc/linux-x86/aarch64/`.

- Do not edit these upstream SoC files for board work:

```text
arch/arm64/boot/dts/rockchip/rk3576.dtsi
arch/arm64/boot/dts/rockchip/rk3576-linux.dtsi
arch/arm64/boot/dts/rockchip/rk3576-pinctrl.dtsi
```

- Do not enable kernel options that break held rootfs hardware-accelerated packages (`libmali`, `rknpu2`, `rkaiq`) unless rebuilding those packages is in scope.
- Preserve existing dirty files unless the user explicitly scopes them in.

## Active DTS

Active board surface:

```text
arch/arm64/boot/dts/rockchip/rk3576-rk806.dtsi
arch/arm64/boot/dts/rockchip/rk3576-lapis.dtsi
arch/arm64/boot/dts/rockchip/rk3576-lapis-thermal.dtsi
arch/arm64/boot/dts/rockchip/rk3576-lapis-video.dtsi
arch/arm64/boot/dts/rockchip/rk3576-lapis.dts
```

The top-level compatible is:

```text
compatible = "pamir-ai,lapis", "rockchip,rk3576";
```

Use `rk3576-lapis.dtsi` for board pinmux, power rails, and peripherals. Use `rk3576-lapis-video.dtsi` for display, DSI, HDMI, and camera readability split.
Use `rk3576-lapis-thermal.dtsi` for board thermal zones, cooling maps, and fan
policy when it is present in the include chain.

## Defconfig Layering

Known layering:

```text
Base:        arch/arm64/configs/rockchip_linux_defconfig
SoC overlay: arch/arm64/configs/rk3576.config
Board:       arch/arm64/configs/rk3576-pamir.config or selected via RK_KERNEL_CFG / RK_KERNEL_CFG_FRAGMENTS in board defconfig
```

For matching checkouts, treat the root `output/.config` as resolved Kconfig truth when it exists. Treat `arch/arm64/configs/rk3576-pamir.config` as the board intent surface. Avoid editing `rockchip_linux_defconfig` for Lapis-only policy unless the user explicitly asks for a shared default change.

## Build And Validation Commands

Use wrapper commands from the repo root or from the symlinked kernel path if the wrapper is present:

```bash
./build.sh kernel-config
./build.sh kmake olddefconfig
./build.sh kmake dt_binding_check
./build.sh kmake dtbs_check
./build.sh kmake <target>
./build.sh kernel
```

For source-only checks:

```bash
git diff --check
scripts/checkpatch.pl --strict <patch-file>
scripts/get_maintainer.pl <changed-files-or-patch>
```

If wrapper targets differ, inspect `./build.sh` rather than falling back to direct `make`.

Board serial console defaults to 1500000 baud unless current boot logs or board
docs prove otherwise.

## Hardware Source-Of-Truth Order

For Lapis board audits and bring-up:

1. Schematic PDF and datasheets from the board/vendor tree.
2. Active DTS: `rk3576-lapis.dtsi`, `rk3576-lapis-video.dtsi`, `rk3576-lapis.dts`.
3. Binding schema under `Documentation/devicetree/bindings/`.
4. Driver implementation and subsystem docs.
5. Resolved kernel config, usually `output/.config`.
6. Local runtime/testing matrices: `linux-docs/testing/data/peripherals/*.tests.json`.
7. Hardware boot logs and measured behavior.

Do not treat older Denali/Pamir names as current without checking the live path.

For power domain changes, check the repo helper when available:

```bash
device/rockchip/common/scripts/check-power-domain.sh
```

## Thermal And Fan Policy

For Lapis thermal/fan work:

- Keep hard fan ceilings in kernel/U-Boot policy, not only userspace service logic.
- Cross-check DTS `pwm-max`, `cooling-levels`, thermal trips, and cooling maps with the driver and measured behavior.
- Treat tach/RPM claims as unverified until tied to schematic, datasheet, or live readings such as `fan1_input` and `fan2_input`.
- Expose limit and fault state to userspace where the platform service needs observability, but do not let userspace bypass the board safety cap.
- Validate both the pre-Linux path and Linux runtime path when changing thermal guard behavior.

## Common Traps

- Editing SoC `.dtsi` for board-only wiring will be overwritten on sync and is the wrong abstraction.
- A compatible string in DTS without a binding is a real review problem, even if the local driver probes.
- `rk3576-lapis` is the current board naming in active DTS; older docs may still contain Denali/Pamir naming.
- Config fragments are intent, not proof. Confirm the resolved `.config`.
- Shared Rockchip defconfig changes have a larger blast radius than board fragment edits.
- A full kernel build is expensive; use targeted wrapper builds first, then broaden before final claims.
- Vendor kernels can carry local ABI dependencies from rootfs packages, firmware, and out-of-tree userspace.
