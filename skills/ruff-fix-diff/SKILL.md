---
name: ruff-fix-diff
description: Run ruff check --fix, display diff, no commit
allowed-tools: Base, Bash
---

# ruff-fix-diff

This skill runs `ruff check --fix` on the repository, shows a diff, and leaves the changes unstaged.

It **does not** commit or stage the changes; you can manually commit afterwards if desired.

## Usage

```
`/ruff-fix-diff`
```

The skill will:

1. Run ruff check --fix, display diff, no commit.
2. If changes were made, display a unified diff via `git diff`.
3. Exit without staging or committing.

This respects the user's preference not to commit automatically.

```python
from __future__ import annotations

import subprocess
import sys

def run() -> int:
    """Run the Ruff auto‑fix routine and display the diff. No commits performed."""
    try:
        ruff_cmd = ["ruff", "check", "--fix"]
        result = subprocess.run(ruff_cmd, capture_output=True, text=True, check=False)
        if result.returncode == 0 and not result.stdout:
            print("No style changes needed.")
            return 0

        diff_cmd = ["git", "diff"]
        diff_res = subprocess.run(diff_cmd, capture_output=True, text=True, check=False)
        if diff_res.returncode != 0:
            print("Error obtaining diff:\n", diff_res.stderr, file=sys.stderr)
            return 1

        if not diff_res.stdout:
            print("Ruff reported changes but no diff available.")
            return 0

        print("Ruff style fixes applied. Diff:\n")
        print(diff_res.stdout)
        return 0

    except Exception as e:
        print("Unexpected error:\n", str(e), file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(run())
```
