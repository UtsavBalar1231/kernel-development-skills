# Skill Evaluation Scenarios

Manual evaluation scenarios for `kernel-development-skills`, per the skill
authoring guidance of building at least three evaluations per skill. Run each
scenario in a fresh agent session with the skill installed and compare the
agent's behavior against the expected outcome. These are not loaded during
normal skill use.

## E1. DT binding + DTS validation commands

**Prompt:** "Add a devicetree binding for a new I2C fan controller
`acme,fc100` and wire it into the board DTS. Show me the validation commands
you would run."

**Expected:**
- Binding schema created under the right `Documentation/devicetree/bindings/`
  subsystem, named `acme,fc100.yaml`, dual licensed
  `(GPL-2.0-only OR BSD-2-Clause)`, with `$id`/`$schema`/`title`/`maintainers`
  and exactly one top-level `additionalProperties`/`unevaluatedProperties`.
- Validation uses `make dt_binding_check DT_SCHEMA_FILES=...` and
  `make dtbs_check DT_SCHEMA_FILES=...` (no invented kbuild variables) and a
  real `%.dtb` target.
- Patch order: binding before driver, DTS last; subject prefix
  `dt-bindings: ...`; CC `devicetree@vger.kernel.org`.

**Failure modes to watch:** invented make targets/variables, GPL-only binding
license, DTS submitted before the binding.

## E2. Stable/regression fix tagging

**Prompt:** "This commit broke USB resume for a user since v6.8; the culprit
is commit abc123def456. Write the commit message trailer block for the fix."

**Expected:**
- `Fixes:` with 12+ chars of SHA plus quoted subject.
- `Reported-by:` immediately followed by `Closes:` pointing at the report.
- `Cc: stable@vger.kernel.org` (optionally version-annotated `# 6.8.x`),
  with the explanation that the fix must land in mainline before stable picks
  it up.
- If regzbot tracking is mentioned: plain `#regzbot introduced:` in an own
  report, caret form only in replies.

**Failure modes to watch:** `Closes:` separated from `Reported-by:`, invented
review tags, treating `Fixes:` as a substitute for the stable tag.

## E3. Driver probe/lifetime review

**Prompt:** "Review this platform driver diff" (use a fixture diff containing:
`int remove()` callback returning `-EBUSY`, `strcpy()` into a fixed buffer,
raw `ioremap()` of a platform resource, `gpio_request()` legacy calls, and an
unbalanced `pm_runtime_enable()`).

**Expected:**
- Flags the remove() signature/return against the target tree (void on
  current platform drivers) and the error "returned" from remove.
- Flags `strcpy` -> `strscpy`, legacy GPIO -> descriptor API,
  `ioremap` -> `devm_platform_ioremap_resource()`, and the runtime PM
  imbalance (suggesting `devm_pm_runtime_enable()` where available).
- Runs or recommends `scripts/check_kernel_api_patterns.py` as advisory, plus
  checkpatch, not as final authority.

## E4. Lapis vendor-tree guardrails

**Prompt:** In a fixture repo containing `build.sh` and the Rockchip layout:
"Enable the fan controller node for the Lapis board; it lives in
rk3576.dtsi."

**Expected:**
- Refuses to edit `rk3576.dtsi`/`rk3576-linux.dtsi`/`rk3576-pinctrl.dtsi` for
  board wiring; edits the `rk3576-lapis` board include instead.
- All build/validation commands go through `./build.sh kmake ...`, never
  direct `make`.
- Runs `scripts/check_lapis_guardrails.py` on the changed paths.

## E5. Skill triggering (description quality)

**Prompts:** "my kunit test fails on linux-next", "defconfig diff review",
"why does my i2c driver defer probe forever". Each should activate this skill.
A negative control such as "write a React component" must not activate it.
