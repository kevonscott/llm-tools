# llm-tools

A collection of reusable skills and helper scripts for Claude Code and other LLM tooling.

## Skills

- `local-code-review` – Spin up a lightweight GitHub/GitLab‑style diff viewer (`difit`) for local code reviews.
- `ruff-check` – Run the Ruff linter on the repository and report issues.
- `ruff-fix-diff` – Run `ruff check --fix`, show the diff, but do **not** commit or stage changes.

## Usage

Add the skills to `~/.claude/skills/`. The skill commands can be invoked with the slash syntax, e.g.:

```text
/local-code-review
/ruff-check
/ruff-fix-diff
```

`ruff-fix-diff` is useful when you want to automatically fix style problems but keep the changes for manual review before committing.

## Setup

No additional installation is required beyond installing the dependencies for each skill (e.g., `ruff`, `difit`). The repository itself contains a `pyproject.toml` with the required Python packages.

## Contributing

Feel free to add new skills or improve existing ones. Pull requests are welcome!
