# Kernel Development Practice

Portable Agent Skill and plugin package for Linux kernel development practice:
drivers, Kconfig, devicetree bindings and DTS, debugging, tracing, CI failures,
KUnit, kselftest, regression and stable handling, maintainer routing, and
vendor/LTS kernel maintenance.

The reusable skill lives at:

```text
plugins/kernel-development-practice/skills/kernel-development-practice/
```

## Install

### Codex

From this repository root:

```bash
codex plugin marketplace add "$PWD"
codex plugin add kernel-development-practice@kernel-development-practice
```

### Claude Code

Inside Claude Code:

```text
/plugin marketplace add /path/to/kernel-development-practice-plugin
/plugin install kernel-development-practice@kernel-development-practice
```

For local development without installation:

```bash
claude --plugin-dir ./plugins/kernel-development-practice
```

### Plain Agent Skills

Copy or symlink the skill directory into the agent's supported skill path:

```bash
mkdir -p ~/.agents/skills
ln -s "$PWD/plugins/kernel-development-practice/skills/kernel-development-practice" \
  ~/.agents/skills/kernel-development-practice
```

See `adapters/major-agent-setup.md` for OpenCode, Copilot, Gemini CLI,
Cursor, Windsurf, and other instruction-file based setups.

## Regenerate Local Kernel Documentation Routes

The large JSONL documentation index is intentionally not committed. Regenerate
it against the kernel checkout you are working in:

```bash
python3 plugins/kernel-development-practice/skills/kernel-development-practice/scripts/index_kernel_docs.py \
  /path/to/linux-kernel \
  plugins/kernel-development-practice/skills/kernel-development-practice/references/doc-routes.md \
  --jsonl plugins/kernel-development-practice/skills/kernel-development-practice/assets/kernel-doc-index.jsonl
```

Query the JSONL with `rg` or `jq`, then open only the relevant kernel docs.

## Validate

```bash
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  plugins/kernel-development-practice/skills/kernel-development-practice
python3 ~/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py \
  plugins/kernel-development-practice
claude plugin validate plugins/kernel-development-practice
claude plugin validate .
python3 -m py_compile plugins/kernel-development-practice/skills/kernel-development-practice/scripts/*.py
```

Research provenance from the skill creation pass is kept in
`research/sources.tsv`; it is not loaded during normal skill use.
