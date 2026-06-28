---
name: mypy-check
description: Run mypy static type checker on Python files to find type errors
allowed-tools: Bash(mypy *)
---

Run `mypy $ARGUMENTS` and report findings

If no arguments are provided, run on the current directory

1. Run: `mypy $ARGUMENTS`
2. Summarize the type errors found (grouped by file if many)
3. For each error, explain what the issue is anf suggest a fix