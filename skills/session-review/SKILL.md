---
name: session-review
description: Review the current (or a given) Claude session for workflow improvements - repeated prompts that shouldbecome skills or CLAUDE.md rules, and redundant or ineffective instructions in ~/.claude markdown. Use when the user ask to review a session, improve their workflow, or audit their instruction files.
allowed-tools: Bash(python3 *), Read, Edit, Write
---

# Session Review

Analyze a Claude Code session transcript to make the user's future workflow smoother, then propose concrete changes to their skills and instruction files.

## Step 1 - Extract the session signal

Run the extractor. With no argument it resolves the **current** session from `$CLAUDE_CODE_SESSION_ID`; pass a transcript path to review a fifferent one.

```bash
python3 ~/.claude/skills/session-review/extract_session.py
```

The report gives your: cleaned chronological **user prompts**, **slask commands/skills** invoked, **tools-use** and **Bash** frequency, the full list of Bash command lines, and **friction signals** (interruptions, denials).

## Step 2 - Read the current instruction surface

Read every markdown instruction file so recommendations account for what already exists (do not duplicate existing rules):

- `~/.claude/CLAUDE.md` and the files it `@`-imports
- `~/.claude/skills/*/SKILL.md` - existing skills (avoid reinventing them)
- Any `CLAUDE.md` in the current project directory

## Step 3 - Analyze

Work through these lenses against theextracted signal:

1. **Repeated prompting --> automation.** Find instructions, context, or corrections the user supplied more than once (across this session, and recognizably the kind of thing they'd repear across sessions). Each is a cantidate for either:
   - a **new skill** ( a repeatable multi-step procedure or a check), or
   - a **CLAUDE.md / imported-mud rule** (a standing preference or constant).

2. **Friction.** Inspect interruptions, denials, and back-and-forth. What instruction, permission, or default would have prevented the correction?

3. **Repeated command rituals.** Look at the full Bash command lines for multi-step sequences run more than once - candidates for a skill or helper script

4. **Markdown effectiveness & redundancy.** Audit the instruction files:
   - Rules that contradict each other or dupliucate across files (e.g. the same git rule in both `CLAUDE.md` and other markdown files - consolidate.
   - Rules that were stated but **not followed** this session - were thre unclear, burried, or wrongly scoped? Tighten or relocate them.
   - Verbose passages that could be shorted without losing meaning.

Be specific and evidence-based: cite the prompts number or command that justifies each finding. Prefer a few high-value changes over a long list.

## Step 4 - Report and propose

Present findings grouped as:

- **New Skills** - name, one-line description, what it would do, evidence.
- **Instruction changes** - extract file + the add/edit/remove, with rationale.
- **Memory candidates** - durable facts/prefences worth saving to memory.

Number each finding so it can be referenced (1, 2, 3, ...). For each instruction change, show the concrete befor/after edit.

## Step 5 - Ask which to implement, then apply

**Never apply anyting automatically** - instruction files and skills shape all future sessions, so the user chooses. After presenting the numbered findings, ask the user **which tasks they want to imlplement (if any)** using the `AskUserQuestion` tool: one multi-select quention whose options are the numbered findings (plus the implicit option to pick none). Keep option labels short and map them back to the finding numbers.
