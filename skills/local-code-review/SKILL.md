---
name: local-code-review
description: Spin up a local GitHub web UI (difit) for ONE combines review of the current local diff in a browser, where the user leaves inline comments tha this Clause session reads back and action on. Use when the user ask to preview/review local changes, see a diff in a UI / code-review view, or do a lightweight local review of uncommitted work - without creating a PR/MR or running CI. Safe to run in multiple Clause sessions in parallel (each gets its own port).
allowed-tools: Base, Read
---

# Local Code Review (difit)

Give the user a GitHub/GitLab-pr-style diff viewer on their host via the open-source tool [difit](https://github.com/yoshiki-pg/difit)),
with a two-way comment loop. Much lighter than opening a real PR/MR.

**The loop:** `start` (one viewer) --> user comments in the browser --> you read the comments back --> revise the code --> `stop`.

**Helper script:** `$HOME/.claude/skills/local-code-review/local_code_review.py`.
Invoke it with the full `$HOME`-based path (below), since the working directory is the user's repo, not this skill's directory.
It only *reads* git (diff/show) and pipes the real to difit - it never mutates git, a submodule, or your working tree, so it's safe in any repo.
It is parallel safe: each start gets its own port and tracks it sown server, so stop only kills the one it started.

## 1. Start one viewer for the current diff

Run from anywhere inside the repo:

- `python3 $HOME/.claude/skills/local-code-review/local_code_review.py start`
  - For committed changes: `start <commit>` (one commit vs its parent) or `start <base> <target>` (a range e.g. `start HEAD main`).
- Give the user the printed *`URL=`* line, and keep the **`PORT=`** for steps 3-4.
  - The URL uses the host FQDN, so it works from the user's machine, not just the host.

## 2. Hand over the URL and ask for comments

- Tell the user once: it binds to `0.0.0.0` - reachable on the internal network, and you kill it in step 4
  - For loopback-only, they can VS Code port-forward and `localhost:<port>` instead.
- Ask them to leave inline comments and say when they're done.

## 3. Read the comments back

- Pull them: `python3 $HOME/.claude/skills/local-code-review/local_code_review.py comments <port>` --> json
  `{"version":N,"threads":[...]}`.
  - Each thread has `filePath`, `position.side` (`new`/`old`) + `position.line`, `codeSnapshot.content`, (the code at that line), and `messages[].body` (the note).
  -  `filePath` is the repo-relative path
    - apply edits to `<repo-root>/filePath`.
  - A `body` containing a ``` ```suggestion        block is a proposed line replacement, not a plain note.
- Summarize them back to the user (file:line + their note), then apply the ones you agree with.
  - Push back on anything that looks wrong rather than applying blindly.
- Re-run after another round as needed - comments persists while the server runs.
  (Re-running `start` rebuild the view from the current working tree.)

## 4. Stop the viewer when done - ALWAYS CLEANUP
 - Stop the viewer you started: `python3 $HOME/.claude/skills/local-code-review/local_code_review.py stop <port>`.
 - Or stop everything this skill launched at once: `python3 $HOME/.claude/skills/local-code-review/local_code_review.py stop-all`
 - Lost track? `python3 $HOME/.claude/skills/local-code-review/local_code_review.py list` shows the running viewers (port/pid/url)

Always stop viewers once the user is done reviewing (and before the session ends): They hol a network port and run with `--keep-alive`, so they never exit on their own. When in doubt, finish with `stop-all`.

## Notes

- **Prerequisite:** Node >=18. difit runs via `npx` (cached in `~/.npx/_npx`) - no global install, nothing written into the repo.
- **Theme** defaults to dark.