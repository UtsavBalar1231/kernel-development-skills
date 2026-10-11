#!/usr/bin/env python3
"""Index a Linux kernel Documentation/ tree into a route map and a JSONL index.

Writes kernel-doc-routes.md (compact route map to read) and kernel-doc-index.jsonl
(full per-file index to query with rg or jq, never to load whole) into one
output directory, then prints both paths. The default output directory is a
per-tree cache outside the skill, because an installed skill directory may be
read-only. Regenerate after updating the kernel tree; the route map records
the indexed kernel version so staleness is visible.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path


TEXT_NAMES = {"CodingStyle", "SubmittingPatches", "Kconfig", "Makefile"}
TEXT_SUFFIXES = {
    ".rst",
    ".txt",
    ".md",
    ".yaml",
    ".yml",
    ".json",
    ".c",
    ".h",
    ".py",
    ".sh",
}
KEYWORDS = (
    "submitting",
    "patch",
    "maintainer",
    "stable",
    "regression",
    "debug",
    "trace",
    "ftrace",
    "dynamic debug",
    "fault injection",
    "kunit",
    "kselftest",
    "ktap",
    "kasan",
    "kmsan",
    "kcsan",
    "kfence",
    "ubsan",
    "lockdep",
    "checkpatch",
    "sparse",
    "coccinelle",
    "devicetree",
    "dt-binding",
    "dt_binding_check",
    "dtbs_check",
    "driver",
    "kconfig",
    "abi",
    "sysfs",
    "uapi",
)
# Match keywords only when not preceded by a word character, so "stability"
# does not hit "abi" and "dispatch" does not hit "patch". Suffix matches such
# as "drivers" for "driver" stay intentional.
KEYWORD_RES = {
    keyword: re.compile(r"(?<![a-z0-9])" + re.escape(keyword)) for keyword in KEYWORDS
}
MAX_ROUTES_PER_KEYWORD = 12
MAX_TOP_LEVEL_DIRS = 40
CURATED_ROUTES = {
    "process": (
        "Documentation/process/submitting-patches.rst",
        "Documentation/process/submit-checklist.rst",
        "Documentation/process/coding-style.rst",
        "Documentation/process/coding-assistants.rst",
        "Documentation/process/generated-content.rst",
        "Documentation/process/deprecated.rst",
        "Documentation/process/handling-regressions.rst",
        "Documentation/process/stable-kernel-rules.rst",
        "Documentation/process/backporting.rst",
        "Documentation/process/security-bugs.rst",
        "Documentation/process/cve.rst",
        "Documentation/process/maintainer-handbooks.rst",
        "Documentation/process/maintainer-soc.rst",
        "Documentation/maintainer/index.rst",
    ),
    "debug-tests": (
        "Documentation/dev-tools/testing-overview.rst",
        "Documentation/dev-tools/kunit/index.rst",
        "Documentation/dev-tools/kselftest.rst",
        "Documentation/dev-tools/ktap.rst",
        "Documentation/process/debugging/index.rst",
        "Documentation/process/debugging/driver_development_debugging_guide.rst",
        "Documentation/process/debugging/kgdb.rst",
        "Documentation/process/debugging/gdb-kernel-debugging.rst",
        "Documentation/admin-guide/dynamic-debug-howto.rst",
        "Documentation/admin-guide/ramoops.rst",
        "Documentation/admin-guide/pstore-blk.rst",
        "Documentation/admin-guide/kdump/index.rst",
    ),
    "tracing": (
        "Documentation/trace/ftrace.rst",
        "Documentation/trace/events.rst",
        "Documentation/trace/kprobes.rst",
        "Documentation/trace/fprobe.rst",
        "Documentation/trace/histogram.rst",
    ),
    "sanitizers-static-analysis": (
        "Documentation/dev-tools/checkpatch.rst",
        "Documentation/dev-tools/sparse.rst",
        "Documentation/dev-tools/coccinelle.rst",
        "Documentation/dev-tools/context-analysis.rst",
        "Documentation/dev-tools/kasan.rst",
        "Documentation/dev-tools/kmsan.rst",
        "Documentation/dev-tools/kcsan.rst",
        "Documentation/dev-tools/kfence.rst",
        "Documentation/dev-tools/ubsan.rst",
        "Documentation/dev-tools/kmemleak.rst",
        "Documentation/locking/lockdep-design.rst",
        "Documentation/fault-injection/fault-injection.rst",
    ),
    "devicetree-drivers": (
        "Documentation/devicetree/index.rst",
        "Documentation/devicetree/bindings/writing-bindings.rst",
        "Documentation/devicetree/bindings/writing-schema.rst",
        "Documentation/devicetree/bindings/submitting-patches.rst",
        "Documentation/devicetree/bindings/dts-coding-style.rst",
        "Documentation/devicetree/bindings/ABI.rst",
        "Documentation/driver-api/index.rst",
        "Documentation/driver-api/driver-model/index.rst",
        "Documentation/core-api/cleanup.rst",
        "Documentation/core-api/symbol-namespaces.rst",
        "Documentation/driver-api/regulator.rst",
        "Documentation/driver-api/gpio/index.rst",
        "Documentation/driver-api/pin-control.rst",
        "Documentation/driver-api/i2c.rst",
        "Documentation/driver-api/spi.rst",
        "Documentation/driver-api/clk.rst",
        "Documentation/driver-api/thermal/index.rst",
        "Documentation/rust/index.rst",
    ),
    "kbuild-abi": (
        "Documentation/kbuild/index.rst",
        "Documentation/kbuild/kconfig-language.rst",
        "Documentation/kbuild/kconfig.rst",
        "Documentation/kbuild/makefiles.rst",
        "Documentation/kbuild/llvm.rst",
        "Documentation/dev-tools/checkuapi.rst",
        "Documentation/dev-tools/container.rst",
        "Documentation/admin-guide/abi.rst",
        "Documentation/ABI/README",
        "Documentation/userspace-api/index.rst",
    ),
}
# Docs that moved upstream; older (LTS, vendor) trees still have them at the old path.
PREVIOUS_LOCATIONS = {
    "Documentation/process/debugging/kgdb.rst": "Documentation/dev-tools/kgdb.rst",
    "Documentation/process/debugging/gdb-kernel-debugging.rst": "Documentation/dev-tools/gdb-kernel-debugging.rst",
}


def route_score(keyword: str, rel_path: str) -> tuple[int, str]:
    full_path = f"Documentation/{rel_path}"
    for group, paths in CURATED_ROUTES.items():
        if full_path in paths:
            return (0, f"{group}:{paths.index(full_path):03d}:{full_path}")

    lowered = rel_path.lower()
    preferred = (
        "process/",
        "dev-tools/",
        "admin-guide/",
        "trace/",
        "fault-injection/",
        "devicetree/",
        "driver-api/",
        "kbuild/",
        "maintainer/",
        "ABI/",
        "userspace-api/",
    )
    if lowered.startswith(tuple(item.lower() for item in preferred)):
        return (1, rel_path)
    if keyword.replace(" ", "-") in lowered or keyword.replace(" ", "_") in lowered:
        return (2, rel_path)
    return (3, rel_path)


def is_text_candidate(path: Path) -> bool:
    return path.name in TEXT_NAMES or path.suffix.lower() in TEXT_SUFFIXES


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def first_heading(text: str) -> str:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith((".. ", ":", "# SPDX", "*")):
            continue
        if index + 1 < len(lines):
            underline = lines[index + 1].strip()
            if underline and set(underline) <= set("=-~`^\"'#*+"):
                return stripped
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return ""


def headings(text: str, limit: int = 8) -> list[str]:
    result: list[str] = []
    lines = text.splitlines()
    for index, line in enumerate(lines[:-1]):
        title = line.strip()
        underline = lines[index + 1].strip()
        if not title or len(title) > 120:
            continue
        if underline and len(underline) >= min(3, len(title)) and set(underline) <= set("=-~`^\"'#*+"):
            if title not in result:
                result.append(title)
        if len(result) >= limit:
            break
    return result


def keyword_hits(text: str) -> list[str]:
    lowered = text.lower()
    return [keyword for keyword in KEYWORDS if KEYWORD_RES[keyword].search(lowered)]


def kernel_version(kernel_root: Path) -> str:
    """Read VERSION/PATCHLEVEL/SUBLEVEL/EXTRAVERSION from the kernel Makefile."""
    fields = {"VERSION": "", "PATCHLEVEL": "", "SUBLEVEL": "", "EXTRAVERSION": ""}
    makefile = kernel_root / "Makefile"
    try:
        for line in makefile.read_text(encoding="utf-8", errors="replace").splitlines()[:20]:
            key, _, value = line.partition("=")
            key = key.strip()
            if key in fields and not fields[key]:
                fields[key] = value.strip()
    except OSError:
        return "unknown"
    if not fields["VERSION"]:
        return "unknown"
    version = f"{fields['VERSION']}.{fields['PATCHLEVEL']}.{fields['SUBLEVEL']}"
    return version + fields["EXTRAVERSION"]


EPILOG = """\
examples:
  index_kernel_docs.py ~/src/linux
  index_kernel_docs.py . --out /tmp/kdocs

default output directory:
  ${XDG_CACHE_HOME:-$HOME/.cache}/kernel-development-skills/docs-<8 hex of sha256(kernel root realpath)>

exit codes:
  0  both files written
  1  the output directory could not be written
  2  bad arguments, or kernel_root has no Documentation/ directory
"""


def default_out_dir(kernel_root: Path) -> Path:
    cache_home = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    tree_id = hashlib.sha256(str(kernel_root.resolve()).encode()).hexdigest()[:8]
    return Path(cache_home) / "kernel-development-skills" / f"docs-{tree_id}"


def curated_route_line(kernel_root: Path, route: str) -> str:
    if (kernel_root / route).exists():
        return f"- `{route}`"
    previous = PREVIOUS_LOCATIONS.get(route)
    if previous and (kernel_root / previous).exists():
        return f"- `{previous}` (older location; newer trees use `{route}`)"
    return f"- `{route}` (not in this tree)"


def collect(docs: Path) -> tuple[list[dict[str, object]], dict[str, int], dict[str, list[str]]]:
    entries: list[dict[str, object]] = []
    dir_counts: dict[str, int] = {}
    keyword_paths: dict[str, list[str]] = {keyword: [] for keyword in KEYWORDS}

    for path in sorted(docs.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(docs)
        data = path.read_bytes()
        top = rel.parts[0] if len(rel.parts) > 1 else "."
        dir_counts[top] = dir_counts.get(top, 0) + 1

        title = ""
        file_headings: list[str] = []
        hits: list[str] = []
        if is_text_candidate(path):
            text = read_text(path)
            title = first_heading(text)
            file_headings = headings(text)
            hits = keyword_hits(text)
            for hit in hits:
                keyword_paths[hit].append(rel.as_posix())

        entries.append(
            {
                "path": f"Documentation/{rel.as_posix()}",
                "size": len(data),
                "sha256_16": hashlib.sha256(data).hexdigest()[:16],
                "title": title,
                "headings": file_headings,
                "keywords": hits,
                "is_symlink": path.is_symlink(),
            }
        )
    return entries, dir_counts, keyword_paths


def write_routes(
    routes_path: Path,
    jsonl_path: Path,
    kernel_root: Path,
    entries: list[dict[str, object]],
    dir_counts: dict[str, int],
    keyword_paths: dict[str, list[str]],
) -> None:
    with routes_path.open("w", encoding="utf-8") as out:
        out.write("# Kernel documentation routes\n\n")
        out.write(f"Indexed tree: `{kernel_root.resolve()}`\n\n")
        out.write(f"Indexed kernel version: {kernel_version(kernel_root)}\n\n")
        out.write(f"Total file entries indexed: {len(entries)}\n\n")
        out.write(f"Full machine index: `{jsonl_path}`\n\n")
        out.write("Regenerate with index_kernel_docs.py after updating the tree.\n\n")
        out.write("## Top-level counts\n\n")
        out.write("| Directory | Files |\n| --- | ---: |\n")
        sorted_counts = sorted(dir_counts.items(), key=lambda item: (-item[1], item[0]))
        for name, count in sorted_counts[:MAX_TOP_LEVEL_DIRS]:
            out.write(f"| `{name}` | {count} |\n")
        if len(sorted_counts) > MAX_TOP_LEVEL_DIRS:
            out.write(f"| ... {len(sorted_counts) - MAX_TOP_LEVEL_DIRS} more | |\n")

        out.write("\n## Curated routes\n\n")
        for group, routes in CURATED_ROUTES.items():
            out.write(f"### {group}\n\n")
            for route in routes:
                out.write(curated_route_line(kernel_root, route) + "\n")
            out.write("\n")

        out.write("## Keyword routes\n\n")
        for keyword in KEYWORDS:
            paths = sorted(keyword_paths[keyword], key=lambda value: route_score(keyword, value))
            if not paths:
                continue
            out.write(f"### {keyword}\n\n")
            for rel_path in paths[:MAX_ROUTES_PER_KEYWORD]:
                out.write(f"- `Documentation/{rel_path}`\n")
            if len(paths) > MAX_ROUTES_PER_KEYWORD:
                out.write(f"- ... {len(paths) - MAX_ROUTES_PER_KEYWORD} more; query the JSONL index\n")
            out.write("\n")

        out.write("## Querying the full index\n\n")
        out.write(
            "Do not load the JSONL file into context. Query it with `rg` or `jq`, "
            "then open only the kernel docs you need.\n\n"
        )
        out.write("```bash\n")
        out.write(f"rg '\"keywords\":.*kselftest' '{jsonl_path}'\n")
        out.write(f"rg 'cleanup\\.h|kunit' '{jsonl_path}'\n")
        out.write(f"jq -r 'select(.title | test(\"regulator\"; \"i\")) | .path' '{jsonl_path}'\n")
        out.write("```\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("kernel_root", type=Path, help="top of a Linux kernel source tree")
    parser.add_argument(
        "--out",
        type=Path,
        metavar="DIR",
        help="directory for kernel-doc-routes.md and kernel-doc-index.jsonl (default: per-tree cache)",
    )
    args = parser.parse_args()

    docs = args.kernel_root / "Documentation"
    if not docs.is_dir():
        print(
            f"error: {docs} is not a directory; pass the top of a Linux kernel source tree "
            "(the directory containing MAINTAINERS and Documentation/)",
            file=sys.stderr,
        )
        return 2

    out_dir = (args.out or default_out_dir(args.kernel_root)).resolve()
    routes_path = out_dir / "kernel-doc-routes.md"
    jsonl_path = out_dir / "kernel-doc-index.jsonl"

    entries, dir_counts, keyword_paths = collect(docs)
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        write_routes(routes_path, jsonl_path, args.kernel_root, entries, dir_counts, keyword_paths)
        with jsonl_path.open("w", encoding="utf-8") as jsonl:
            for entry in entries:
                jsonl.write(json.dumps(entry, sort_keys=True) + "\n")
    except OSError as error:
        print(f"error: cannot write to {out_dir}: {error}; pass --out with a writable directory", file=sys.stderr)
        return 1

    print(f"Indexed {len(entries)} files from Linux {kernel_version(args.kernel_root)}")
    print(f"Route map: {routes_path}")
    print(f"JSONL index: {jsonl_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
