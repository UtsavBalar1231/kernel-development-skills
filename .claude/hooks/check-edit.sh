#!/bin/sh
# PostToolUse check for Write/Edit. Exit 2 sends stderr back to Claude.
f=$(jq -r '.tool_input.file_path // .tool_response.filePath // empty')
[ -n "$f" ] && [ -f "$f" ] || exit 0

case "$f" in
*/plugins/*/scripts/*.py)
	python3 -m py_compile "$f" || exit 2
	rm -rf "$(dirname "$f")/__pycache__"
	;;
*.json)
	jq empty "$f" || exit 2
	;;
esac

case "$f" in
*/plugins/*)
	if grep -nE '/home/|/Users/' "$f" >&2; then
		echo "local absolute path in shipped file $f; use a relative or placeholder path" >&2
		exit 2
	fi
	;;
esac
exit 0
