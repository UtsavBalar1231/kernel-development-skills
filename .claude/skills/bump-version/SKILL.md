---
name: bump-version
description: Sets the kernel-development-skills version in all eight manifest and SKILL.md locations, then validates. Use when releasing or when asked to bump or change the plugin version.
disable-model-invocation: true
argument-hint: <x.y.z>
metadata:
  internal: true
---

Bump the plugin version to `$ARGUMENTS`. Run every step from the repository root.

1. Stop and ask if `$ARGUMENTS` is not `MAJOR.MINOR.PATCH`. Read the current version:

   ```bash
   OLD=$(jq -r .version plugins/kernel-development-skills/.claude-plugin/plugin.json); NEW="$ARGUMENTS"; echo "$OLD -> $NEW"
   ```

2. Update the JSON fields. The manifests round-trip through `jq` unchanged, so this touches only the version lines:

   ```bash
   P=plugins/kernel-development-skills
   set_v() { f=$1; shift; tmp=$(mktemp); jq --arg v "$NEW" "$@" "$f" >"$tmp" && mv "$tmp" "$f"; }
   set_v $P/plugin.json '.version = $v'
   set_v $P/.claude-plugin/plugin.json '.version = $v'
   set_v $P/.codex-plugin/plugin.json '.version = $v'
   set_v $P/.cursor-plugin/plugin.json '.version = $v'
   set_v .claude-plugin/marketplace.json '.plugins[0].version = $v'
   set_v .cursor-plugin/marketplace.json '.metadata.version = $v | .plugins[0].version = $v'
   ```

3. Edit `metadata.version` in `plugins/kernel-development-skills/skills/kernel-development-skills/SKILL.md` to `"$NEW"` with the Edit tool. Leave `.agents/plugins/marketplace.json` alone; it has no version field.

4. Confirm exactly eight hits for the new version and none for the old one:

   ```bash
   F="$P/plugin.json $P/.claude-plugin/plugin.json $P/.codex-plugin/plugin.json $P/.cursor-plugin/plugin.json .claude-plugin/marketplace.json .cursor-plugin/marketplace.json $P/skills/kernel-development-skills/SKILL.md"
   echo "new: $(cat $F | grep -oF "\"$NEW\"" | wc -l) (want 8)  old: $(cat $F | grep -oF "\"$OLD\"" | wc -l) (want 0)"
   ```

5. Run `/validate-plugin`, then show `git diff --stat`. Do not commit unless asked.
