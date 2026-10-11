# Devicetree

A binding is ABI shared with bootloaders, other operating systems, and every
older kernel, so DT review is about the hardware, not your driver. Write the
binding as if the driver did not exist, and the DTS as if all you had was the
schematic.

Covers: binding design: what DT maintainers push back on; writing and checking
a binding; DTS layering and style; overlays; what was really built and booted;
phandles, interrupts, GPIOs, pinctrl: the usual mistakes; routing and series
order.

## Binding design: what DT maintainers push back on

The full list is `Documentation/devicetree/bindings/writing-bindings.rst`; these
are the ones that cost a revision most often.

- Describe the whole device, not what your driver uses today: the IRQ goes in
  even if the driver polls, because the next driver or another OS will want it.
- No policy. Properties that tune software (buffer sizes, poll intervals,
  "enable feature X") get rejected; DT says what is wired, not how Linux should
  behave. Never mention Linux or "driver" in a binding.
- Compatibles are specific: `acme,soc1234-i2c`, not `acme,i2c-v2`; no
  wildcards or family names; no bus suffix such as `-i2c` when the parent bus
  already says it. Add a fallback only when software can bind to it unchanged.
  New features or errata get a new compatible, not a boolean property.
- Custom properties carry the vendor prefix (`acme,gain-trim`). Search bindings
  of the same device class first, because a common property often exists. A
  new vendor prefix goes into `vendor-prefixes.yaml` in its own patch.
- Units go in the name: `-microvolt`, `-microamp`, `-ohms`, `-us`, `-ms`,
  `-hz`, `-millicelsius`. A property without a standard suffix needs a `$ref`
  type, even for an enum.
- Phandle lists (`clocks`, `dmas`, `interrupts`, `resets`) have a fixed order.
  With more than one entry, add `*-names` with identical constraints, and no
  suffixes in names (`tx`, not `txirq`).
- No instance-index properties or custom aliases: a different programming model
  means a different compatible. `syscon` never stands alone, and
  `simple-mfd`/`simple-bus` only fit children that need nothing from the parent.
- Changing a shipped binding: new properties are optional and the driver keeps
  the old behavior without them (`ABI.rst`). Making a property required breaks
  every DTB in the field; an incompatible change needs a new compatible.
- A plain I2C or SPI device with only `compatible`, `reg`, and one interrupt
  does not get its own file. Add it to `trivial-devices.yaml`.

## Writing and checking a binding

Start from `example-schema.yaml`. A minimal I2C device:

```yaml
# SPDX-License-Identifier: (GPL-2.0-only OR BSD-2-Clause)
%YAML 1.2
---
$id: http://devicetree.org/schemas/iio/adc/acme,adc128.yaml#
$schema: http://devicetree.org/meta-schemas/core.yaml#

title: ACME ADC128 12-bit ADC

maintainers:
  - Jane Doe <jane@example.org>

properties:
  compatible:
    const: acme,adc128

  reg:
    maxItems: 1

  interrupts:
    maxItems: 1

  vdd-supply: true

required:
  - compatible
  - reg
  - vdd-supply

additionalProperties: false

examples:
  - |
    #include <dt-bindings/interrupt-controller/irq.h>

    i2c {
        #address-cells = <1>;
        #size-cells = <0>;

        adc@48 {
            compatible = "acme,adc128";
            reg = <0x48>;
            interrupts-extended = <&gpio2 7 IRQ_TYPE_LEVEL_LOW>;
            vdd-supply = <&vdd_3v3>;
        };
    };
```

- `$id` starts with `http://devicetree.org/schemas/` and mirrors the path under
  `bindings/`. The file is named like the compatible.
- When the schema `$ref`s another schema (an SPI device pulling in
  `/schemas/spi/spi-peripheral-props.yaml#`, a controller pulling in
  `i2c-controller.yaml`), use `unevaluatedProperties: false`; otherwise
  `additionalProperties: false`, which rejects every property a `$ref` adds.
- The example is extracted and compiled as DTS (as a `/plugin/`, so undefined
  labels such as `&vdd_3v3` are fine). Macros need their `#include` inside the
  example, and a new `include/dt-bindings/` header ships in the same patch.

```bash
pip3 install dtschema yamllint     # minimum: DT_SCHEMA_MIN_VERSION in Documentation/devicetree/bindings/Makefile
make dt_binding_check DT_SCHEMA_FILES=acme,adc128.yaml   # also /iio/adc/ or a:b colon lists
make iio/adc/acme,adc128.yaml                            # since v7.0: this binding and its example only
scripts/dtc/dt-check-style --mode=strict Documentation/devicetree/bindings/iio/adc/acme,adc128.yaml   # since v7.2
```

These targets end in `|| true`; exit status 0 proves nothing. Read the output:

| Message | Means |
| --- | --- |
| `'vdd-supply' is a required property` | the example (or a DTS) lacks something listed in `required` |
| `Additional properties are not allowed ('foo' was unexpected)` | not in `properties`; typo, missing vendor prefix, or missing `$ref` |
| `Unevaluated properties are not allowed ('foo' was unexpected)` | same, under `unevaluatedProperties`; check the referenced schemas too |
| `... does not match any of the regexes` | a node or property name fails `patternProperties` |

Since v7.2 `dt_binding_check` also runs `dt-check-style` in relaxed mode (needs
`ruamel.yaml`); new binding examples are expected to pass strict mode.

## DTS layering and style

The SoC `.dtsi` describes the die, an optional `<soc>-<som>.dtsi` or
`<soc>-common.dtsi` describes a module or a family, and `<soc>-<board>.dts`
describes this PCB (`Documentation/process/maintainer-soc.rst`). The SoC file
keeps every board-dependent block `status = "disabled"`; the board enables and
wires it through its label:

```dts
&i2c3 {
	pinctrl-names = "default";
	pinctrl-0 = <&i2c3_pins>;
	status = "okay";

	adc@48 {
		compatible = "acme,adc128";
		reg = <0x48>;
		interrupts-extended = <&gpio2 7 IRQ_TYPE_LEVEL_LOW>;
		vdd-supply = <&vcc_3v3>;
	};
};
```

- Do not edit the SoC `.dtsi` for one board. Every board that includes it
  changes, and in a vendor tree the edit conflicts on every rebase. Override
  from the board file instead: `/delete-property/ dmas;` inside a `&label`
  block, `/delete-node/ &label;` at the top level.
- Confirm which files are built before editing: the `dtb-$(CONFIG_...)` line in
  `arch/<arch>/boot/dts/<vendor>/Makefile` and the include chain from that
  `.dts`. Product names in old docs drift; the include chain does not.
- Style (`dts-coding-style.rst`): node names `[a-z0-9-]`, labels `[a-z0-9_]`,
  unit addresses in lowercase hex without leading zeros, children in unit
  address order, board `&label` blocks alphabetical (or in DTSI order, per
  platform). Properties go `compatible`, `reg`, `ranges`, standard, vendor,
  blank line, `status`, then child nodes each after a blank line. One `<>` per
  array entry. MMIO devices sit under a bus node, never at the top level.

```bash
make ARCH=arm64 defconfig
make ARCH=arm64 CHECK_DTBS=y acme/acme-soc-board.dtb                 # one board; without CHECK_DTBS=y nothing is validated
make ARCH=arm64 dtbs_check DT_SCHEMA_FILES=acme,adc128.yaml          # every enabled DTB against one schema
make ARCH=arm64 W=1 dtbs                                             # extra dtc warnings: unit_address_vs_reg, simple_bus_reg
```

- `dtbs_check` checks every DTB the current config enables, skips schemas that
  have errors (run `dt_binding_check` too), and without `DT_SCHEMA_FILES` also
  reports undocumented compatibles.
- The tree already has warnings, so judge your delta:
  `make dtbs_check 2> before.log` on the base, again after, then `diff`.
  New platform work adds no `dtbs_check` warnings; RISC-V and Samsung also
  require `W=1` clean.

## Overlays

- Overlay sources are `.dtso` since v6.2 (older trees use `.dts` with
  `/plugin/;`) and build to `.dtbo`. They start with `/dts-v1/; /plugin/;` and
  extend the base through labels (`&i2c3 { ... };`).
- A `.dtbo` alone is never schema-checked, because only `.dtb` targets run the
  validator; since v6.19 kbuild warns `.dtbo is not applied to any base`. Apply
  it to a base in the Makefile, and kbuild builds that base with `-@`:

  ```make
  dtb-$(CONFIG_ARCH_ACME) += acme-board.dtb acme-board-cam.dtbo
  acme-board-with-cam-dtbs := acme-board.dtb acme-board-cam.dtbo
  dtb-$(CONFIG_ARCH_ACME) += acme-board-with-cam.dtb
  ```
- Apply one by hand with `scripts/dtc/fdtoverlay -i base.dtb -o out.dtb
  overlay.dtbo`. `FDT_ERR_NOTFOUND` means a target label is missing from the
  base, or the base was built without `-@` and has no `__symbols__`.

## What was really built and booted

"My DTS change has no effect" is usually a bootloader loading a different DTB:
another partition, another file name, or a FIT image you did not rebuild.

```bash
dtc -I dtb -O dts -o - arch/arm64/boot/dts/acme/acme-board.dtb   # decompile the build output
dtc -I fs -O dts -o live.dts /sys/firmware/devicetree/base       # the tree the running kernel uses
cp /sys/firmware/fdt booted.dtb                                  # the blob the bootloader handed over
ARCH=arm64 scripts/dtc/dtx_diff build.dtb /proc/device-tree      # what the bootloader or overlays changed
ARCH=arm64 scripts/dtc/dtx_diff -T arch/arm64/boot/dts/acme/acme-board.dts   # each property with the file:line that set it
```

## Phandles, interrupts, GPIOs, pinctrl: the usual mistakes

- The argument count follows the provider's `#*-cells`. A GIC takes three
  (`<GIC_SPI 37 IRQ_TYPE_LEVEL_HIGH>`), most GPIO controllers two. One cell
  too few shifts every entry after it.
- `interrupts` resolves through the nearest `interrupt-parent`, which is
  usually inherited from the root (the GIC). An IRQ wired to a GPIO pin needs
  `interrupts-extended = <&gpio2 7 IRQ_TYPE_LEVEL_LOW>`; otherwise
  `interrupts = <7 ...>` quietly means GIC interrupt 7.
- The trigger type matches the wire: a level source declared as an edge loses
  interrupts, and an edge declared as level storms.
- GPIO polarity lives in DT: `reset-gpios = <&gpio1 12 GPIO_ACTIVE_LOW>`, and
  the driver uses logical values (`gpiod_set_value(reset, 1)` asserts reset).
  A driver that writes 0 to assert inverts twice; fix the DT flag.
- `pinctrl-names = "default", "sleep";` pairs with `pinctrl-0`, `pinctrl-1` in
  order. The core selects `default` itself (`init` first if present); `sleep`
  applies only when the driver calls `pinctrl_pm_select_sleep_state()`.
- `supply vdd not found, using dummy regulator` means the `vdd-supply` phandle
  is missing; acceptable only for a rail that really is always on.
- The parent's `#address-cells` and `#size-cells` decide how `reg` parses:
  `<1>`/`<0>` under I2C and SPI (`reg = <0x48>`), often `<2>`/`<2>` on a 64-bit
  SoC bus. dtc warns `reg_format` when they disagree.

## Routing and series order

- Order: binding, then driver, then DTS last or as a separate posting. DTS goes
  through the SoC tree on its own branch, and a driver maintainer never applies
  it (`bindings/submitting-patches.rst`, `maintainer-soc.rst`).
- The binding patch holds only `Documentation/devicetree/bindings/` and
  `include/dt-bindings/`. Subject: `dt-bindings: iio: adc: Add ACME ADC128`.
  ASoC, media, regulator, SCSI, SPI, and UFS reverse it
  (`spi: dt-bindings: ...`). Leave "Documentation", "doc", "YAML", and
  "binding" out of the subject.
- Send the whole series to `devicetree@vger.kernel.org` and the DT maintainers
  from `scripts/get_maintainer.pl`; the binding travels with the driver. DT
  review is mandatory for subsystem bindings (more than one device); a
  single-device binding may be taken without it after a few weeks.
- A DTS that needs a new `include/dt-bindings/` macro fails `make dtbs` in the
  SoC tree until the header lands there. Prefer literal values for datasheet
  constants, switch to the macro a release later, or base both on a shared
  immutable branch.
- Every compatible in a DTS is documented in a binding first, even if no driver
  matches it yet; checkpatch warns otherwise. `make dt_compatible_check` lists
  compatibles used in the source that no schema documents.
