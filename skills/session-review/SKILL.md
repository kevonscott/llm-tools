---
name: session-review
description: Review the current (or a given) Claude session for workflow improvements - repeated prompts that should become skills or CLAUDE.md rules, and redundant or ineffective instructions in ~/.claude markdown. Use when the user ask to review a session, improve their workflow, or audit their instruction files.
allowed-tools: Bash(python3 *), Read, Edit, Write
---

# Session Review

Analyze a Claude Code session transcript to make the user's future workflow smoother, then propose concrete changes to their skills and instruction files.

## Step 1 - Extract the session signal

Run the extractor. With no argument it resolves the **current** session from `$CLAUDE_CODE_SESSION_ID`; pass a transcript path to review a different one.

```bash
python3 ~/.claude/skills/session-review/extract_session.py
```

The report gives your: cleaned chronological **user prompts**, **slash commands/skills** invoked, **tools-use** and **Bash** frequency, the full list of Bash command lines, and **friction signals** (interruptions, denials).

## Step 2 - Read the current instruction surface

Read every markdown instruction file so recommendations account for what already exists (do not duplicate existing rules):

- `~/.claude/CLAUDE.md` and the files it `@`-imports
- `~/.claude/skills/*/SKILL.md` - existing skills (avoid reinventing them)
- Any `CLAUDE.md` in the current project directory

## Step 3 - Analyze

Work through these lenses against the extracted signal:

1. **Repeated prompting --> automation.** Find instructions, context, or corrections the user supplied more than once (across this session, and recognizably the kind of thing they'd repeat across sessions). Each is a candidate for either:
   - a **new skill** ( a repeatable multi-step procedure or a check), or
   - a **CLAUDE.md / imported-mud rule** (a standing preference or constant).

2. **Friction.** Inspect interruptions, denials, and back-and-forth. What instruction, permission, or default would have prevented the correction?

3. **Repeated command rituals.** Look at the full Bash command lines for multi-step sequences run more than once - candidates for a skill or helper script

4. **Markdown effectiveness & redundancy.** Audit the instruction files:
   - Rules that contradict each other or duplicated across files (e.g. the same git rule in both `CLAUDE.md` and other markdown files - consolidate.
   - Rules that were stated but **not followed** this session - were there unclear, buried, or wrongly scoped? Tighten or relocate them.
   - Verbose passages that could be shorted without losing meaning.

Be specific and evidence-based: cite the prompts number or command that justifies each finding. Prefer a few high-value changes over a long list.

## Step 4 - Report and propose

Present findings grouped as:

- **New Skills** - name, one-line description, what it would do, evidence.
- **Instruction changes** - extract file + the add/edit/remove, with rationale.
- **Memory candidates** - durable facts/preferences worth saving to memory.

Number each finding so it can be referenced (1, 2, 3, ...). For each instruction change, show the concrete before/after edit.

## Step 5 - Ask which to implement, then apply

**Never apply anything automatically** - instruction files and skills shape all future sessions, so the user chooses. After presenting the numbered findings, ask the user **which tasks they want to implement (if any)** using the `AskUserQuestion` tool: one multi-select question whose options are the numbered findings (plus the implicit option to pick none). Keep option labels short and map them back to the finding numbers.

Then implement **only** the selected items:

- New skills - Create `~/.claude/skills/<name>/SKILL.md` (and any helper files).
- Instruction changes - Apply with the Edit/Write to the exact file shown.
- Memory candidates - Write to the memory directory and add the `MEMORY.md` pointer line, per the memory rules.

If the user selects nothing, stop without changes. After applying, briefly confirm what was changed.

## Notes

- The extractor only reads test the user typed; tool results and system reminders are stripped, so prompts reflect genuine user intents.
- A single short session yields little signal - say so rather than inventing findings. Offer to review a stronger past transcript (pass its path) instead.
