---
name: validate-plugin
description: Runs this repository's full validation suite for the kernel-development-skills plugin (Claude and Codex validators, script compile and help checks, version consistency, description limits, and genericity and style greps). Use before calling any packaging, manifest, SKILL.md, reference, or script change done.
metadata:
  internal: true
---

Run each block from the repository root and report every command with its exit code. Report failures; do not paper over them.

```bash
P=plugins/kernel-development-skills; S=$P/skills/kernel-development-skills
claude plugin validate $P; echo "exit=$?"
claude plugin validate .; echo "exit=$?"
V=~/.codex/skills/.system
[ -f $V/skill-creator/scripts/quick_validate.py ] && { python3 $V/skill-creator/scripts/quick_validate.py $S; echo "exit=$?"; }
[ -f $V/plugin-creator/scripts/validate_plugin.py ] && { python3 $V/plugin-creator/scripts/validate_plugin.py $P; echo "exit=$?"; }
python3 -m py_compile $S/scripts/*.py; echo "py_compile exit=$?"; rm -rf $S/scripts/__pycache__
for s in $S/scripts/*.py; do python3 $s --help >/dev/null; echo "$(basename $s) --help exit=$?"; done
command -v ruff >/dev/null && { ruff check --no-cache $S/scripts; echo "ruff exit=$?"; }
for f in $(git ls-files -co --exclude-standard '*.json'); do jq empty "$f" || echo "INVALID JSON: $f"; done
gh skill publish --dry-run; echo "gh skill exit=$?"
```

Version consistency and description limits:

```bash
python3 - <<'EOF'
import json, re
P = "plugins/kernel-development-skills"
j = lambda p: json.load(open(p))
cm = j(".cursor-plugin/marketplace.json")
skill = open(f"{P}/skills/kernel-development-skills/SKILL.md").read()
fm = skill.split("---")[1]
v = {
    "plugin.json": j(f"{P}/plugin.json")["version"],
    ".claude-plugin/plugin.json": j(f"{P}/.claude-plugin/plugin.json")["version"],
    ".codex-plugin/plugin.json": j(f"{P}/.codex-plugin/plugin.json")["version"],
    ".cursor-plugin/plugin.json": j(f"{P}/.cursor-plugin/plugin.json")["version"],
    "claude marketplace": j(".claude-plugin/marketplace.json")["plugins"][0]["version"],
    "cursor marketplace metadata": cm["metadata"]["version"],
    "cursor marketplace plugin": cm["plugins"][0]["version"],
    "SKILL.md metadata": re.search(r'^\s+version:\s*"([^"]+)"', fm, re.M).group(1),
}
print("versions consistent:", len(set(v.values())) == 1, v if len(set(v.values())) > 1 else next(iter(v.values())))
d = re.search(r"^description: (.*)$", fm, re.M).group(1)
keys = re.findall(r"^([a-z-]+):", fm, re.M)
print("description chars:", len(d), "(max 1024)", "angle brackets:", any(c in d for c in "<>"))
print("frontmatter keys ok:", set(keys) <= {"name", "description", "license", "metadata", "allowed-tools"}, keys)
print("SKILL.md lines:", skill.count("\n"), "(max 500)")
EOF
```

Genericity and style (each grep should print nothing):

```bash
grep -rnI '/home/\|/Users/' plugins/
grep -rnI $'—\|–' --include='*.md' . --exclude-dir=.git --exclude-dir=.omca
for f in $S/references/*.md; do [ $(wc -l <$f) -gt 100 ] && ! grep -qiE '^## (contents|table of contents)' $f && echo "no TOC: $f"; done
```

Also check by reading the diff that no vendor-, board-, or product-specific content entered the skill. If `npx` is available and the network is up, `npx skills add . --list` should report one skill.
