#!/usr/bin/env python3
"""Print a path-based checklist (references to read, checks to run) for a kernel change.

The output is a Markdown checklist, not a verdict. Changed paths come from the
unstaged and staged git diff unless you pass paths or --against REV. Commands
are upstream `make` targets; if the tree documents its own build wrapper, run
the equivalent targets through that wrapper instead.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Optional

SCRIPT_DIR = Path(__file__).resolve().parent

EPILOG = """\
examples:
  triage_kernel_change.py                        # unstaged and staged diff
  triage_kernel_change.py --against origin/master
  triage_kernel_change.py drivers/hwmon/foo.c Documentation/devicetree/bindings/hwmon/acme,foo.yaml

exit codes:
  0  always; the checklist is advisory
  2  bad arguments
"""

BINDINGS_DIR = "Documentation/devicetree/bindings/"
DTS_RE = re.compile(r"^arch/([^/]+)/boot/dts/(.+)\.(dts|dtsi|dtso)$")
THERMAL_RE = re.compile(r"(?:^|[/_-])(?:thermal|cooling|hwmon|fan)(?:[/_.-]|$)")
# Build wrappers that vendor, Android and BSP kernel trees commonly ship.
WRAPPER_CANDIDATES = ("build.sh", "build/build.sh", "tools/bazel", "build/kernel/kleaf")


@dataclass
class Triage:
    kinds: list[str] = field(default_factory=list)
    references: set[str] = field(default_factory=set)
    checks: list[str] = field(default_factory=list)
    guardrails: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def git_revision(value: str) -> str:
    # git parses a leading dash as an option, and --output=FILE would write a file.
    if not value or value.startswith("-"):
        raise argparse.ArgumentTypeError(f"not a git revision: {value!r}")
    return value


def git_changed_paths(against: Optional[str] = None) -> list[str]:
    if against:
        commands = [["git", "diff", against, "--name-only", "--diff-filter=ACMRT"]]
    else:
        commands = [
            ["git", "diff", "--name-only", "--diff-filter=ACMRT"],
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMRT"],
        ]
    paths: list[str] = []
    seen: set[str] = set()
    for command in commands:
        try:
            result = subprocess.run(command, check=True, text=True, capture_output=True)
        except (OSError, subprocess.CalledProcessError) as error:
            detail = getattr(error, "stderr", "") or str(error)
            print(f"warning: {' '.join(command)} failed: {detail.strip()}", file=sys.stderr)
            continue
        for line in result.stdout.splitlines():
            path = line.strip()
            if path and path not in seen:
                seen.add(path)
                paths.append(path)
    return paths


def add_unique(items: list[str], value: str) -> None:
    if value not in items:
        items.append(value)


def find_build_wrapper() -> Optional[str]:
    """Look for a build wrapper from the cwd upward, stopping at the git root."""
    cwd = Path.cwd()
    for directory in [cwd, *cwd.parents]:
        for candidate in WRAPPER_CANDIDATES:
            if (directory / candidate).exists():
                found = directory / candidate
                return f"./{found.relative_to(cwd)}" if directory == cwd else str(found)
        if (directory / ".git").exists():
            break
    return None


def run(command: str, note: str = "") -> str:
    return f"`{command}` ({note})" if note else f"`{command}`"


def object_target(path: str) -> str:
    return str(PurePosixPath(path).with_suffix(".o"))


COMMON_CHECKS = (
    run("git diff --check"),
    run("scripts/checkpatch.pl --strict <patch-file>", "or -g <commit> for committed work"),
    run("scripts/get_maintainer.pl <patch-file>"),
)


def classify(raw_path: str) -> Triage:
    path = PurePosixPath(raw_path.replace("\\", "/")).as_posix()
    name = PurePosixPath(path).name
    lowered = path.lower()
    triage = Triage()
    refs = triage.references
    checks = triage.checks
    notes = triage.notes

    if path.startswith(BINDINGS_DIR) and path.endswith((".yaml", ".yml")):
        rel = path[len(BINDINGS_DIR) :]
        triage.kinds.append("devicetree binding")
        refs.add("devicetree.md")
        add_unique(checks, run(f"make dt_binding_check DT_SCHEMA_FILES={rel}"))
        add_unique(checks, run(f"make {rel}", "single-binding check, v7.0+"))
        add_unique(notes, "Bindings are ABI. Subject prefix is `dt-bindings: <binding dir>:` for most subsystems.")
        add_unique(notes, "Send the binding patch before the driver and DTS patches in the series.")
        add_unique(notes, "dt_binding_check needs dtschema (`pip install dtschema`); v7.2+ also runs dt-check-style.")

    if path.startswith("include/dt-bindings/"):
        triage.kinds.append("devicetree binding header")
        refs.add("devicetree.md")
        add_unique(notes, "Binding headers ship in the same patch as the binding schema that uses them.")

    dts = DTS_RE.match(path)
    if dts:
        arch, stem, suffix = dts.groups()
        triage.kinds.append("devicetree source")
        refs.add("devicetree.md")
        if suffix == "dts":
            add_unique(checks, run(f"make ARCH={arch} CHECK_DTBS=y {stem}.dtb"))
        elif suffix == "dtso":
            add_unique(checks, run(f"make ARCH={arch} CHECK_DTBS=y {stem}.dtbo"))
        else:
            add_unique(checks, run(f"make ARCH={arch} CHECK_DTBS=y <vendor>/<board>.dtb", "each board including it"))
            add_unique(
                triage.guardrails,
                "Shared .dtsi (SoC or SoM): put board-only wiring in the board .dts and leave "
                "board-dependent nodes `status = \"disabled\"` here.",
            )
        add_unique(checks, run(f"make ARCH={arch} dtbs_check", "every DTB enabled by the current .config"))
        add_unique(notes, "A plain `make <board>.dtb` runs no schema validation; keep CHECK_DTBS=y.")
        add_unique(notes, "DTS patches go through the SoC maintainer tree, not the driver tree.")

    if path.startswith(("drivers/", "sound/")) and not name.startswith(("Kconfig", "Makefile")):
        triage.kinds.append("kernel driver")
        refs.update({"drivers.md", "review.md", "testing.md"})
        if path.endswith(".c"):
            add_unique(checks, run(f"python3 {SCRIPT_DIR / 'check_kernel_api_patterns.py'} {path}"))
            add_unique(checks, run(f"make W=1 {object_target(path)}"))
            add_unique(checks, run(f"make C=1 {object_target(path)}", "sparse"))
        add_unique(checks, "probe and runtime validation on hardware or a suitable emulator")
        add_unique(
            notes,
            "Review API choice, resource lifetime, devm use, PM, locking, IRQ context, DMA, and error paths.",
        )

    if path.startswith("include/linux/"):
        triage.kinds.append("kernel internal API")
        refs.update({"drivers.md", "review.md"})
        add_unique(checks, run(f"scripts/kernel-doc -none -Wall {path}"))
        add_unique(checks, "build every caller (`git grep` the changed symbols) with W=1")
        add_unique(notes, "Internal API changes need call-site review and subsystem maintainer routing.")

    if path.startswith(("include/uapi/", "Documentation/ABI/")):
        triage.kinds.append("userspace ABI")
        refs.add("review.md")
        if path.startswith("include/uapi/"):
            add_unique(checks, run("scripts/check-uapi.sh -p <previous-release-tag>"))
        add_unique(checks, "update Documentation/ABI/ and add or adjust a userspace-facing test when feasible")
        add_unique(notes, "UAPI, sysfs, ioctl and netlink changes need compatibility review; Cc linux-api@vger.kernel.org.")

    is_config = (
        name.startswith("Kconfig")
        or re.match(r"^arch/[^/]+/configs/", path) is not None
        or name.endswith(".config")
    )
    if is_config:
        triage.kinds.append("Kconfig or kernel config")
        refs.update({"build.md", "tree.md"})
        if name.startswith("Kconfig"):
            add_unique(checks, run("make kconfig-sym-check", "v7.2+; dangling symbol references"))
        add_unique(checks, run("make olddefconfig", "then confirm the resolved .config values with scripts/diffconfig"))
        if "/configs/" in path and name.endswith("defconfig"):
            add_unique(checks, run(f"make {name} && make savedefconfig && diff defconfig {path}"))
            add_unique(
                notes,
                "Shared defconfigs affect every board built from them; prefer a board fragment "
                "(scripts/kconfig/merge_config.sh) when the tree supports one.",
            )

    if path.startswith("rust/") or path.endswith(".rs"):
        triage.kinds.append("Rust kernel code")
        refs.update({"build.md", "drivers.md"})
        add_unique(checks, run("make LLVM=1 rustavailable"))
        add_unique(checks, run("make LLVM=1 rustfmtcheck"))
        add_unique(checks, run("make LLVM=1 CLIPPY=1 <focused-target>"))
        if path.startswith("rust/"):
            add_unique(checks, run("make LLVM=1 rusttest"))
        add_unique(notes, "Minimum Rust and bindgen versions are in Documentation/process/changes.rst.")

    if path.startswith("Documentation/") and path.endswith(".rst"):
        triage.kinds.append("documentation")
        refs.add("patches.md")
        subdir = PurePosixPath(path).parts[1] if len(PurePosixPath(path).parts) > 2 else "."
        add_unique(checks, run(f"make SPHINXDIRS={subdir} htmldocs", "no new warnings"))

    if path == "MAINTAINERS":
        triage.kinds.append("MAINTAINERS entry")
        add_unique(checks, run("scripts/get_maintainer.pl --self-test=patterns"))
        add_unique(notes, "Keep entries alphabetical and make every F: pattern match real files.")

    if path.startswith("tools/testing/selftests/"):
        parts = PurePosixPath(path).parts
        target = parts[3] if len(parts) > 4 else "<target>"
        triage.kinds.append("kselftest")
        refs.add("testing.md")
        add_unique(checks, run(f"make headers && make -C tools/testing/selftests TARGETS={target} run_tests"))
        add_unique(notes, "Keep the KTAP output when using the result as evidence.")

    is_kunit = (
        name == ".kunitconfig"
        or name.endswith("_kunit.c")
        or (name.endswith("_test.c") and not path.startswith("tools/"))
        or "kunit" in lowered
    )
    if is_kunit:
        triage.kinds.append("KUnit test")
        refs.add("testing.md")
        kunitconfig = str(PurePosixPath(path).parent) if name == ".kunitconfig" else "<dir-with-.kunitconfig>"
        add_unique(checks, run(f"./tools/testing/kunit/kunit.py run --kunitconfig={kunitconfig}"))
        add_unique(checks, run("./tools/testing/kunit/kunit.py run --arch=x86_64 '<suite-glob>'", "QEMU instead of UML"))
        add_unique(notes, "Keep the KTAP output when using the result as evidence.")

    if THERMAL_RE.search(lowered):
        refs.update({"drivers.md", "testing.md"})
        add_unique(checks, "verify thermal trips, cooling maps, fan limits and fault reporting on the target")
        add_unique(notes, "Tie RPM, temperature and safety claims to the datasheet or live readings.")

    if not triage.kinds:
        triage.kinds.append("general kernel change")
    return triage


def render(paths: list[str], wrapper: Optional[str]) -> str:
    lines = ["# Kernel change triage", ""]
    if not paths:
        lines.append("No changed paths were found. Pass paths explicitly or use --against REV.")
        return "\n".join(lines) + "\n"

    lines.append("Read the nearest repo guidance (MAINTAINERS entry, subsystem maintainer docs) first.")
    lines.append("Before sending any change, read `patches.md` and run:")
    lines.extend(f"- {check}" for check in COMMON_CHECKS)
    lines.append("")
    if wrapper:
        lines.append(
            f"This tree ships a build wrapper (`{wrapper}`): read its usage and run the checks "
            "below through it instead of plain `make`."
        )
    lines.append("References are files under the skill's `references/` directory.")
    lines.append("")
    for raw_path in paths:
        triage = classify(raw_path)
        normalized = PurePosixPath(raw_path.replace("\\", "/")).as_posix()
        lines.append(f"## `{normalized}`")
        lines.append("")
        lines.append(f"- Type: {', '.join(triage.kinds)}")
        if triage.references:
            lines.append("- Read: " + ", ".join(f"`{ref}`" for ref in sorted(triage.references)))
        for title, items in (
            ("Guardrails", triage.guardrails),
            ("Checks", triage.checks),
            ("Notes", triage.notes),
        ):
            if items:
                lines.append(f"- {title}:")
                lines.extend(f"  - {item}" for item in items)
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("paths", nargs="*", help="changed paths, relative to the kernel root (default: git diff)")
    parser.add_argument(
        "--against",
        metavar="REV",
        type=git_revision,
        help="use files changed since REV (e.g. HEAD~1, origin/master) instead of the working tree diff",
    )
    args = parser.parse_args()
    paths = args.paths or git_changed_paths(args.against)
    print(render(paths, find_build_wrapper()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
