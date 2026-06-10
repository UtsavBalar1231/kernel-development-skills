#!/usr/bin/env python3
"""Check RK3576/Lapis kernel guardrails for changed paths.

Exit codes: 0 = passed (warnings allowed), 1 = forbidden edit found, or any
warning when --strict is given. By default the changed paths come from the
unstaged and staged git diff; pass paths explicitly or use --against <rev>.
"""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path


FORBIDDEN_SOC_DTSI = {
    "arch/arm64/boot/dts/rockchip/rk3576.dtsi",
    "arch/arm64/boot/dts/rockchip/rk3576-linux.dtsi",
    "arch/arm64/boot/dts/rockchip/rk3576-pinctrl.dtsi",
}
SHARED_DEFCONFIG = "arch/arm64/configs/rockchip_linux_defconfig"
TEXT_SUFFIXES = {".md", ".rst", ".txt", ".sh", ".py", ".yaml", ".yml"}
# Match `make` only in command position with a kernel-ish target, flag, or
# variable assignment, so prose such as "make sure" is not flagged.
DIRECT_MAKE_RE = re.compile(
    r"(^|[;&|`($]\s*)(sudo\s+)?make\s+("
    r"-|"  # flags such as -j, -C
    r"[A-Za-z0-9_./]+=|"  # VAR= assignments such as ARCH=, C=, W=, O=
    r"\w*config\b|"  # defconfig, olddefconfig, menuconfig, kernel .config targets
    r"dtbs\b|dtbs_check\b|dt_binding_check\b|"
    r"Image\b|zImage\b|uImage\b|vmlinux\b|modules\b|all\b|clean\b|mrproper\b|"
    r"kselftest\b|headers_install\b|htmldocs\b"
    r")"
)


def git_changed_paths(against: str | None = None) -> list[str]:
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
        except (OSError, subprocess.CalledProcessError):
            continue
        for line in result.stdout.splitlines():
            path = line.strip()
            if path and path not in seen:
                seen.add(path)
                paths.append(path)
    return paths


def is_text_path(path: Path) -> bool:
    return path.name in {"AGENTS.md", "CLAUDE.md"} or path.suffix.lower() in TEXT_SUFFIXES


def should_scan_for_direct_make(path: str) -> bool:
    if path.startswith("Documentation/"):
        return False
    if path in {"Makefile", "Kbuild", "Kconfig"} or path.endswith("/Kconfig"):
        return False
    # Skip this skill's own files in any install layout (.agents/skills/...,
    # plugins/.../skills/..., plugin caches).
    if "skills/kernel-development-skills/" in path:
        return False
    return True


def scan_direct_make(path: str) -> list[str]:
    if not should_scan_for_direct_make(path):
        return []
    filesystem_path = Path(path)
    if not filesystem_path.exists() or not filesystem_path.is_file() or not is_text_path(filesystem_path):
        return []
    try:
        text = filesystem_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = filesystem_path.read_text(encoding="utf-8", errors="replace")
    hits: list[str] = []
    for number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or "./build.sh" in stripped:
            continue
        if DIRECT_MAKE_RE.search(stripped):
            hits.append(f"{path}:{number}: direct `make` example may bypass Lapis wrapper")
    return hits


def check_paths(paths: list[str]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    for raw_path in paths:
        path = Path(raw_path.replace("\\", "/")).as_posix()
        if path in FORBIDDEN_SOC_DTSI:
            errors.append(
                f"{path}: forbidden for Lapis board changes; use board DTS/includes instead"
            )
        if path == SHARED_DEFCONFIG:
            warnings.append(
                f"{path}: shared Rockchip defconfig changed; prefer the board config fragment "
                "(see references/lapis-rk3576.md) for board-only policy"
            )
        warnings.extend(scan_direct_make(path))

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help="Changed paths. Defaults to git diff paths.")
    parser.add_argument(
        "--against",
        metavar="REV",
        help="Diff against REV (e.g. HEAD~1, origin/main) instead of the working tree/index.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero on warnings as well as errors.",
    )
    args = parser.parse_args()
    paths = args.paths or git_changed_paths(args.against)
    errors, warnings = check_paths(paths)

    if not paths:
        print("No changed paths found.")
        return 0

    for warning in warnings:
        print(f"warning: {warning}")
    for error in errors:
        print(f"error: {error}")

    if errors:
        return 1
    if warnings:
        return 1 if args.strict else 0
    print("Lapis guardrails passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
