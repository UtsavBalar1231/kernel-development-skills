# Device Tree And Driver Reference

## Table Of Contents

- Source map
- Devicetree rules
- Binding workflow
- DTS workflow
- Driver workflow
- Kconfig and build integration
- ABI and userspace
- Review checklist

## Source Map

Local docs to check first:

- `Documentation/devicetree/index.rst`
- `Documentation/devicetree/bindings/`
- `Documentation/devicetree/bindings/writing-schema.rst`
- `Documentation/devicetree/bindings/submitting-patches.rst`
- `Documentation/devicetree/bindings/dts-coding-style.rst`
- `Documentation/driver-api/`
- `Documentation/driver-api/driver-model/`
- `Documentation/driver-api/firmware/`
- `Documentation/driver-api/gpio/`
- `Documentation/driver-api/i2c.rst`
- `Documentation/driver-api/spi.rst`
- `Documentation/driver-api/pin-control.rst`
- `Documentation/driver-api/pwm.rst`
- `Documentation/driver-api/regulator.rst`
- `Documentation/driver-api/clk.rst`
- `Documentation/driver-api/pm/`
- `Documentation/core-api/`
- `Documentation/admin-guide/abi.rst`
- `Documentation/ABI/`

Current upstream references:

- https://docs.kernel.org/devicetree/bindings/writing-schema.html
- https://docs.kernel.org/devicetree/bindings/submitting-patches.html
- https://docs.kernel.org/devicetree/bindings/dts-coding-style.html
- https://docs.kernel.org/driver-api/
- https://docs.kernel.org/driver-api/driver-model/
- https://docs.kernel.org/process/stable-api-nonsense.html

If a repository provides a kernel build wrapper, use it for every build target.
In the RK3576/Lapis tree, replace upstream-style `make` examples with
`./build.sh kmake ...`.

## Devicetree Rules

- DTS describes hardware, not the current Linux driver implementation.
- A `compatible` used in DTS must be documented in a binding, even when the current driver does not match on that exact string.
- Bindings are ABI. Avoid incompatible changes to existing properties.
- Put binding patches before driver code that uses them; put DTS changes after bindings and driver support unless a subsystem explicitly requests otherwise.
- Keep board DTS changes in the board file or board include. Do not patch SoC `.dtsi` files for board-only wiring.
- Use existing common properties before inventing vendor-specific properties.
- For vendor-specific properties, include type references and descriptions in schema.

## Binding Workflow

1. Search existing bindings for the device class and vendor.
2. If adding a new binding, create YAML schema under the correct `Documentation/devicetree/bindings/` subsystem.
3. Include SPDX, `$id`, `$schema`, `title`, `maintainers`, `description` when useful, `properties`, `required`, and exactly one top-level `additionalProperties` or `unevaluatedProperties`.
4. Use two-space YAML indentation; use four-space indentation in DTS examples.
5. Keep examples minimal and focused on the binding.
6. Validate schema and examples:

```bash
make dt_binding_check DT_SCHEMA_FILES=<path/to/schema.yaml>
```

If this repo requires a wrapper, use the wrapper equivalent.

## DTS Workflow

1. Identify the active DTS include chain for the board.
2. Confirm every compatible and property is documented by a binding.
3. Match naming, ordering, labels, and phandle style in nearby DTS.
4. Confirm GPIO polarity, regulators, clocks, resets, interrupts, pinctrl, supplies, and bus addresses against schematic/datasheet.
5. Validate targeted DTB:

```bash
make dtbs_check DT_SCHEMA_FILES=<schema-or-subsystem> DTB_CHECKER_FLAGS=-m
make <board>.dtbs
```

Use repo wrappers when required.

6. Boot hardware when possible and verify probe logs and runtime nodes.

## Driver Workflow

Before editing:

- Read the subsystem API docs and two nearby drivers with similar hardware.
- Identify ownership/lifetime model: devm, refcounting, firmware node, runtime PM, regulators, clocks, resets, IRQs, DMA, workqueues, locks.
- Check whether the hardware needs regmap, nvmem, pinctrl, IIO, hwmon, regulator, power_supply, media, DRM, input, netdev, or another subsystem interface instead of a private API.

Implementation rules:

- Probe should fail loudly enough to diagnose real hardware/configuration errors, but use `dev_err_probe()` for deferred probe paths.
- Order resources so failure and remove paths are natural: regulators/clocks/resets/pinctrl before device enable, IRQs after state is initialized.
- Use runtime PM when the hardware has meaningful idle states and the subsystem expects it.
- Avoid sleeping in atomic context and check locking around callbacks.
- Use endian, alignment, and DMA APIs instead of open-coding assumptions.
- Do not expose debugfs/sysfs knobs as ABI unless they are documented and supportable.

## Kconfig And Build Integration

- Place Kconfig symbols in the subsystem where the driver lives.
- Keep dependencies exact: bus, regmap, GPIO, IRQ, PM, COMMON_CLK, REGULATOR, OF, I2C, SPI, MFD, or architecture constraints as needed.
- Use `select` sparingly for library helpers; prefer `depends on` for user-visible subsystems.
- Add Makefile objects next to related drivers.
- Build-test as built-in and module when supported.
- For vendor board config work, change the board fragment/overlay when one exists and confirm the resolved `.config`; do not treat a fragment diff as final truth.

## ABI And Userspace

Treat these as compatibility surfaces:

- `include/uapi/`
- sysfs files, documented under `Documentation/ABI/`
- ioctl numbers and structs
- netlink families and attributes
- tracepoints once consumed externally
- devicetree bindings
- module parameters used by deployments

Any ABI addition needs documentation, tests when feasible, and a compatibility story.

## Review Checklist

- Binding exists and validates before DTS use.
- DTS matches hardware source of truth and active board file.
- Driver uses subsystem APIs rather than private policy.
- Probe/remove/error paths are deterministic and logged.
- Power, clock, reset, IRQ, and pinctrl ordering is defensible.
- Kconfig dependencies are sufficient for all build modes.
- ABI/user-visible changes are documented and tested.
