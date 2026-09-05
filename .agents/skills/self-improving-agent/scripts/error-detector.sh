#!/usr/bin/env bash
# Error detector: runs after a Bash tool use. Reads CLAUDE_TOOL_OUTPUT
# (a JSON array of tool result blocks) and reminds to log if an error is detected.
OUT="${CLAUDE_TOOL_OUTPUT:-}"

has_error() {
  # Match common error signals in the tool output string.
  printf '%s' "$OUT" | grep -Eqi \
    '"error":\s*true|exitCode":[^0]|"isError":\s*true|\b(error|Error|Exception|Traceback|failed|Failed|cannot|Not a directory|No such file|permission denied|ENOTDIR|EACCES)\b'
}

if has_error; then
  echo "<error-detected>"
  echo "A command may have failed. If this is a non-obvious or recurring error, log it to .learnings/ERRORS.md with reproduction steps."
  echo "</error-detected>"
fi
