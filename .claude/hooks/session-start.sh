#!/bin/bash
# SessionStart hook for cfo-cli — installs the package (with all extras) so that
# tests, linters and the AI providers all work in Claude Code on the web.
set -euo pipefail

# Only run in the remote (web) environment; local dev installs deps manually.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "$CLAUDE_PROJECT_DIR"

# Editable install with dev + both AI extras. Idempotent and re-runnable.
# Installing every extra avoids the recurring "module 'openai'/'anthropic' not
# found" surprise when exercising the ai command group.
pip install -e ".[dev,ai,openai]"

# Branch-discipline reminder: this repo develops on a feature branch and merges
# into main. Surface the current branch so work doesn't accidentally land on main.
echo "cfo-cli: on git branch '$(git rev-parse --abbrev-ref HEAD)'"
