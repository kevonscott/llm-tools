# Agent Git Operation Guidelines

## Core Principles

- **MUST** write clear, descriptive commit messages
- **NEVER** commit debug print statements or breakpoints
- **NEVER** commit credentials or sensitive data
- **NEVER** commit to master or main branches
- **NEVER** chain git commands

## CRITICAL: Command Approval

- Never run git commands without showing them to the user and waiting for explicit approval — no exceptions.

## Git Workflow

- Keep 1 commit per branch per feature. If working on the same feature, amend
  the commit instead of creating a new one.
- **ALWAYS** run pre-commit hooks before committing
