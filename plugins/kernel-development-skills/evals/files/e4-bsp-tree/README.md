# Acme SoC board support tree

This tree is built only through `build.sh`. It sets the cross toolchain,
`ARCH`, `O=out` and the config fragments for each board, so running `make`
directly in this tree produces a configuration that does not match the
shipped image.

## Commands

- `./build.sh kconfig`: regenerate `out/.config` from
  `arch/arm64/configs/acme_defconfig` plus the board fragment
  `arch/arm64/configs/acme-evb.config`.
- `./build.sh kernel`: build `Image`, modules and DTBs into `out/`.
- `./build.sh dtbs-check`: build the board DTBs with `CHECK_DTBS=y`.

## Layout

- `arch/arm64/boot/dts/acme/acme-soc.dtsi` describes the SoC and is shared by
  every board on this SoC. Board-dependent nodes stay `status = "disabled"`
  there.
- `arch/arm64/boot/dts/acme/acme-soc-evb.dts` is the EVB board.
- `arch/arm64/configs/acme_defconfig` is shared by every board.
- `arch/arm64/configs/acme-evb.config` holds the EVB-only options.
- The SoC PWM controller driver is `CONFIG_PWM_ACME`.
