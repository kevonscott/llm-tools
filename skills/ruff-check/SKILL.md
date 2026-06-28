---
name: ruff-check
description: Run ruff linter on Python files to find code quality and style issues
allowed-tools: BASH(ruff *)
---

Run `ruff check $ARGUMENTS` and report findings.

If no arguments are provided, run on the current directory

1. Run: `ruff check $ARGUMENTS`
2. Summarize the issues found (grouped by rule if many)
3. If the user ask to fix, run: `ruff check --fix $ARGUMENTS`