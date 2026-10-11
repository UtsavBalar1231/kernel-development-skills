#!/usr/bin/env python3
"""Advisory scan of kernel C sources for deprecated or risky driver API patterns.

Scans .c and .h files only; comments are stripped before matching, string
literals are kept. Each message names the kernel version that introduced the
replacement API, so check it against the tree you are working in: on an older
tree the old API may still be the only option. Rules marked [heuristic] can
fire on correct code and need a human look before changing anything.

Path-scoped rules (legacy GPIO, raw ioremap) only apply when the scanned path
contains `drivers/`, so run from the kernel root or pass tree-relative paths.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Iterable, Iterator, Optional

C_SUFFIXES = {".c", ".h"}
SKIP_DIR_PARTS = {".git", ".agents", ".claude", ".codex-plugin", ".claude-plugin", "assets"}
DRIVER_PATHS = ("drivers/",)

EPILOG = """\
examples:
  check_kernel_api_patterns.py                      # files in the unstaged and staged diff
  check_kernel_api_patterns.py --against HEAD~3     # files changed since HEAD~3
  check_kernel_api_patterns.py drivers/hwmon/foo.c --json

exit codes:
  0  scan completed (findings are advisory unless --strict)
  1  findings were reported and --strict was given
  2  a path passed on the command line does not exist, or bad arguments

Replacement details and version notes: references/drivers.md
"""


@dataclass(frozen=True)
class LineRule:
    name: str
    regex: re.Pattern[str]
    message: str
    heuristic: bool = False
    path_prefixes: tuple[str, ...] = ()


@dataclass(frozen=True)
class CodeRule:
    name: str
    finder: Callable[[str], Iterable[int]]
    message: str
    heuristic: bool = False
    path_prefixes: tuple[str, ...] = ()


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    rule: str
    message: str
    heuristic: bool


LINE_RULES = (
    LineRule(
        "bug-macro",
        re.compile(r"\bBUG(?:_ON)?\s*\("),
        "avoid BUG()/BUG_ON() in driver code; return an error or WARN_ON_ONCE() and recover",
    ),
    LineRule(
        "simple-strto",
        re.compile(r"\bsimple_strto(?:l|ll|ul|ull)\s*\("),
        "simple_strto*() ignores overflow; use kstrto*()",
    ),
    LineRule(
        "strcpy",
        re.compile(r"\bstrcpy\s*\("),
        "strcpy() has no destination bounds check; use strscpy() or strscpy_pad()",
    ),
    LineRule(
        "strncpy",
        re.compile(r"\bstrncpy\s*\("),
        "strncpy() was removed in v7.2 (deprecated before that); use strscpy(), "
        "strscpy_pad(), memtostr[_pad]() or strtomem[_pad]()",
    ),
    LineRule(
        "strlcpy",
        re.compile(r"\bstrlcpy\s*\("),
        "strlcpy() was removed in v6.8; use strscpy()",
    ),
    LineRule(
        "raw-pointer-print",
        re.compile(r'"[^"\n]*%p(?![A-Za-z0-9])'),
        "raw %p prints a hashed value that is rarely useful; drop it or use a "
        "specific %p extension",
        heuristic=True,
    ),
    LineRule(
        "pk-in-printk",
        re.compile(r"\b(?:printk|pr_\w+|dev_\w+)\s*\([^;]*%pK"),
        "%pK is only for procfs/sysfs file content, never printk/dmesg output; use %p or drop the pointer",
    ),
    LineRule(
        "legacy-gpio",
        re.compile(
            r"\b(?:gpio_request(?:_one)?|gpio_free|gpio_direction_(?:input|output)|"
            r"gpio_[gs]et_value(?:_cansleep)?|gpio_to_irq|devm_gpio_request(?:_one)?|"
            r"of_get_named_gpio)\s*\(|#include\s*<linux/(?:of_gpio|gpio)\.h>"
        ),
        "legacy integer GPIO API needs CONFIG_GPIOLIB_LEGACY since v6.17 and "
        "<linux/of_gpio.h> was removed in v7.1; use devm_gpiod_get*() from <linux/gpio/consumer.h>",
        path_prefixes=DRIVER_PATHS,
    ),
    LineRule(
        "raw-ioremap",
        re.compile(r"\bioremap(?:_wc|_uc|_cache|_np)?\s*\("),
        "map platform resources with devm_platform_ioremap_resource() or devm_ioremap_resource()",
        heuristic=True,
        path_prefixes=DRIVER_PATHS,
    ),
    LineRule(
        "timer-del",
        re.compile(r"\bdel_timer(?:_sync)?\s*\("),
        "removed in v6.15: use timer_delete() or timer_delete_sync() (since v6.2), "
        "or timer_shutdown_sync() for final teardown",
    ),
    LineRule(
        "timer-del-try",
        re.compile(r"\btry_to_del_timer_sync\s*\("),
        "renamed in v6.16: use timer_delete_sync_try()",
    ),
    LineRule(
        "from-timer",
        re.compile(r"\bfrom_timer\s*\("),
        "renamed in v6.16: use timer_container_of()",
    ),
    LineRule(
        "hrtimer-init",
        re.compile(r"\bhrtimer_init(?:_on_stack|_sleeper_on_stack)?\s*\("),
        "use hrtimer_setup*() (since v6.13; hrtimer_init*() removed in v6.15)",
    ),
    LineRule(
        "remove-new",
        re.compile(r"\.remove_new\s*="),
        "platform .remove returns void since v6.11 and .remove_new was removed in v6.13; use .remove",
    ),
    LineRule(
        "i2c-probe-new",
        re.compile(r"\.probe_new\s*="),
        "i2c .probe takes one argument since v6.3 and .probe_new was removed in v6.6; use .probe "
        "(i2c_client_get_device_id() if the id is needed)",
    ),
    LineRule(
        "legacy-pm-ops",
        re.compile(
            r"\b(?:SIMPLE|UNIVERSAL)_DEV_PM_OPS\s*\("
            r"|\bSET_(?:LATE_|NOIRQ_)?(?:SYSTEM_SLEEP|RUNTIME)_PM_OPS\s*\("
        ),
        "use DEFINE_SIMPLE_DEV_PM_OPS() with pm_sleep_ptr(), or DEFINE_RUNTIME_DEV_PM_OPS() "
        "with pm_ptr() (since v5.17); drop __maybe_unused on the callbacks",
    ),
    LineRule(
        "system-wq",
        re.compile(r"\bsystem_wq\b"),
        "system_wq is being removed; use system_percpu_wq (since v6.17)",
    ),
    LineRule(
        "system-unbound-wq",
        re.compile(r"\bsystem_unbound_wq\b"),
        "treewide conversion to system_dfl_wq (since v6.17)",
        heuristic=True,
    ),
    LineRule(
        "legacy-create-wq",
        re.compile(r"\bcreate(?:_singlethread|_freezable)?_workqueue\s*\("),
        "use alloc_workqueue() or alloc_ordered_workqueue() with explicit flags",
    ),
    LineRule(
        "import-ns-bare",
        re.compile(
            r"\bMODULE_IMPORT_NS\(\s*[A-Za-z_]|\bEXPORT_SYMBOL_NS(?:_GPL)?\(\s*\w+\s*,\s*[A-Za-z_]"
        ),
        "symbol namespaces are string literals since v6.13, e.g. MODULE_IMPORT_NS(\"FOO\"); "
        "a bare token is only right if it is a macro expanding to a string",
        heuristic=True,
    ),
    LineRule(
        "export-for-modules-old",
        re.compile(r"\bEXPORT_SYMBOL_GPL_FOR_MODULES\s*\("),
        "renamed to EXPORT_SYMBOL_FOR_MODULES() in v6.17",
    ),
    LineRule(
        "kmap",
        re.compile(r"\bkmap(?:_atomic)?\s*\("),
        "kmap() and kmap_atomic() are deprecated; use kmap_local_page() (since v5.11)",
    ),
    LineRule(
        "sysfs-sprintf",
        re.compile(r"return\s+(?:s|sn|scn)printf\s*\(\s*buf\b"),
        "sysfs show() callbacks should use sysfs_emit() or sysfs_emit_at() (since v5.10)",
        heuristic=True,
    ),
    LineRule(
        "kmalloc-obj",
        re.compile(
            r"=\s*k[mz]alloc\(\s*sizeof\(\s*\*"
            r"|=\s*k(?:malloc_array|calloc)\(\s*[^,]+,\s*sizeof\(\s*\*"
        ),
        "on v7.0+ trees prefer the type-aware k[mz]alloc_obj[s]() helpers; there is no devm "
        "variant, and older trees should keep this form",
        heuristic=True,
    ),
    LineRule(
        "alloc-mul",
        re.compile(r"\bk[mz]alloc\([^;]*(?:\*\s*sizeof\b|\bsizeof\s*\([^)]*\)\s*\*)"),
        "open-coded size multiplication can overflow; use kmalloc_array(), kcalloc() or struct_size()",
    ),
    LineRule(
        "regcache-legacy",
        re.compile(r"\bREGCACHE_(?:RBTREE|FLAT)\b"),
        "new regmap users should pick REGCACHE_MAPLE, or REGCACHE_FLAT_S (since v6.19) when "
        "no runtime allocation is allowed",
        heuristic=True,
    ),
)


def strip_comments(text: str) -> str:
    """Blank out C comments, keeping string/char literals and every newline."""
    out: list[str] = []
    index = 0
    length = len(text)
    while index < length:
        char = text[index]
        if char in "\"'":
            end = index + 1
            while end < length and text[end] != char and text[end] != "\n":
                end += 2 if text[end] == "\\" else 1
            end = min(end + 1, length)
            out.append(text[index:end])
            index = end
        elif text.startswith("/*", index):
            end = text.find("*/", index + 2)
            end = length if end < 0 else end + 2
            out.append("".join("\n" if c == "\n" else " " for c in text[index:end]))
            index = end
        elif text.startswith("//", index):
            end = text.find("\n", index)
            end = length if end < 0 else end
            out.append(" " * (end - index))
            index = end
        else:
            out.append(char)
            index += 1
    return "".join(out)


def call_end(text: str, open_paren: int) -> int:
    """Return the index just past the parenthesis matching text[open_paren]."""
    depth = 0
    index = open_paren
    while index < len(text):
        char = text[index]
        if char in "\"'":
            index += 1
            while index < len(text) and text[index] != char:
                index += 2 if text[index] == "\\" else 1
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return index + 1
        index += 1
    return len(text)


def line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


ALLOC_WQ_RE = re.compile(r"\balloc_workqueue\s*\(")
WQ_PLACEMENT_RE = re.compile(r"\bWQ_(?:PERCPU|UNBOUND|BH)\b")
DEVM_IRQ_RE = re.compile(r"\bdevm_request_(?:threaded_|any_context_)?irq\s*\(")
DEVM_IRQ_ASSIGN_RE = re.compile(r"\b([A-Za-z_]\w*)\s*=\s*devm_request_(?:threaded_|any_context_)?irq\s*\(")
DEV_ERR_PROBE_RE = re.compile(r"\bdev_err_probe\s*\(")
IRQ_LOG_WINDOW_LINES = 5


def find_wq_without_placement(text: str) -> Iterator[int]:
    for match in ALLOC_WQ_RE.finditer(text):
        call = text[match.start() : call_end(text, match.end() - 1)]
        if not WQ_PLACEMENT_RE.search(call):
            yield line_of(text, match.start())


def find_irq_double_log(text: str) -> Iterator[int]:
    for match in DEV_ERR_PROBE_RE.finditer(text):
        call = text[match.start() : call_end(text, match.end() - 1)]
        if DEVM_IRQ_RE.search(call):
            yield line_of(text, match.start())
    for match in DEVM_IRQ_ASSIGN_RE.finditer(text):
        end = call_end(text, match.end() - 1)
        window = "\n".join(text[end:].split("\n")[: IRQ_LOG_WINDOW_LINES + 1])
        uses_var = re.compile(r"\bdev_err_probe\s*\([^,]*,\s*-?" + re.escape(match.group(1)) + r"\b")
        if uses_var.search(window):
            yield line_of(text, match.start())


CODE_RULES = (
    CodeRule(
        "workqueue-placement",
        find_wq_without_placement,
        "alloc_workqueue() without WQ_PERCPU, WQ_UNBOUND or WQ_BH; pass one explicitly "
        "(WQ_PERCPU exists since v6.17 and omitting both WARNs since v7.2)",
        heuristic=True,
    ),
    CodeRule(
        "irq-double-log",
        find_irq_double_log,
        "devm_request_*irq() logs its own failure via dev_err_probe() since v6.18; "
        "return the error without another dev_err_probe()",
        heuristic=True,
    ),
)


def git_changed_paths(against: Optional[str] = None) -> list[str]:
    if against:
        commands: tuple[tuple[str, ...], ...] = (
            ("git", "diff", against, "--name-only", "--diff-filter=ACMRT"),
        )
    else:
        commands = (
            ("git", "diff", "--name-only", "--diff-filter=ACMRT"),
            ("git", "diff", "--cached", "--name-only", "--diff-filter=ACMRT"),
        )
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


def is_scannable(path: Path) -> bool:
    if any(part in SKIP_DIR_PARTS for part in path.parts):
        return False
    return path.is_file() and path.suffix in C_SUFFIXES


def expand_paths(raw_paths: Iterable[str]) -> list[Path]:
    paths: list[Path] = []
    for raw_path in raw_paths:
        path = Path(raw_path)
        if path.is_dir():
            paths.extend(sorted(candidate for candidate in path.rglob("*") if is_scannable(candidate)))
        elif is_scannable(path):
            paths.append(path)
    return paths


def applies(path_prefixes: tuple[str, ...], normalized_path: str) -> bool:
    if not path_prefixes:
        return True
    return any(
        normalized_path.startswith(prefix) or f"/{prefix}" in normalized_path
        for prefix in path_prefixes
    )


def scan_file(path: Path) -> list[Finding]:
    normalized_path = path.as_posix()
    if normalized_path.startswith("./"):
        normalized_path = normalized_path[2:]
    text = strip_comments(path.read_text(encoding="utf-8", errors="replace"))
    findings: list[Finding] = []
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        for rule in LINE_RULES:
            if applies(rule.path_prefixes, normalized_path) and rule.regex.search(line):
                findings.append(Finding(normalized_path, number, rule.name, rule.message, rule.heuristic))
    for code_rule in CODE_RULES:
        if applies(code_rule.path_prefixes, normalized_path):
            for number in code_rule.finder(text):
                findings.append(
                    Finding(normalized_path, number, code_rule.name, code_rule.message, code_rule.heuristic)
                )
    findings.sort(key=lambda finding: (finding.line, finding.rule))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("paths", nargs="*", help="files or directories to scan (default: git diff paths)")
    parser.add_argument(
        "--against",
        metavar="REV",
        help="scan files changed since REV (e.g. HEAD~1, origin/master) instead of the working tree diff",
    )
    parser.add_argument("--strict", action="store_true", help="exit 1 when any finding is reported")
    parser.add_argument("--json", action="store_true", help="print findings as a JSON list on stdout")
    args = parser.parse_args()

    missing = [raw for raw in args.paths if not Path(raw).exists()]
    if missing:
        for raw in missing:
            print(
                f"error: path does not exist: {raw}; pass paths relative to the current directory "
                "(usually the kernel tree root)",
                file=sys.stderr,
            )
        return 2

    raw_paths = args.paths or git_changed_paths(args.against)
    paths = expand_paths(raw_paths)
    findings = [finding for path in paths for finding in scan_file(path)]

    if args.json:
        print(json.dumps([asdict(finding) for finding in findings], indent=2))
        if not paths:
            print("note: no .c or .h files to scan", file=sys.stderr)
    elif not raw_paths:
        print("No changed paths were found. Pass files or directories explicitly, or use --against REV.")
    elif not paths:
        print("No .c or .h files to scan.")
    elif not findings:
        print(f"No advisory kernel API pattern findings in {len(paths)} file(s).")
    else:
        print("Advisory kernel API pattern findings:")
        for finding in findings:
            tag = " [heuristic]" if finding.heuristic else ""
            print(f"- {finding.path}:{finding.line}: {finding.rule}{tag}: {finding.message}")
        print("\nReplacement details and version notes: references/drivers.md")

    return 1 if args.strict and findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
