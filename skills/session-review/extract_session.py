#!/usr/bin/env python3
"""Distill a Claude Code session transcript into a review signal.

Extracts the information needed to review and improve a workflow from a
Claude Code ``.jsonl`` transcript: the real user prompts, slash-command and
skill invocations, tool- and Bash-usage frequency, and friction signals such as
interruptions and permission denials.

With no path argument, it resolves the *current* session transcript from
``$CLAUDE_CODE_SESSION_ID`` and the cwd-derived project directory.

Usage
-----
    extract_session.py [transcript.jsonl]
"""

import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

# Synthetic wrappers that appear inside user messages but are not types prompts.
_SYNTHETIC_PREFIXES = (
    "<command-name>",
    "<command-message>",
    "<command-args>",
    "<local-command-stdout>",
    "<local-command-stderr>",
    "<local-command-caveat>",
)
_COMMAND_NAME_RE = re.compile(r"<command-name>([^<]+)</command-name>")
_SYSTEM_REMINDER_RE = re.compile(r"<system-reminder>.*?</system-reminder>", re.DOTALL)
_FRICTION_RE = re.compile(
    r"\[Request interrupted[^\]]*\]"
    r"|The user doesn't want to (?:proceed|take) this action"
    r"|tool use was rejected"
    r"The use doesn't want to proceed"
)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for transcript extraction."""
    parser = argparse.ArgumentParser(
        description=(
            "Distill a Claude Code session transcript into a review signal."
        )
    )
    parser.add_argument(
        "transcript",
        nargs="?",
        help="Path to a transcript jsonl file. Defaults to current session.",
    )
    return parser.parse_args()


def resolve_transcript(transcript_arg: str | None) -> Path:
    """Return the transcript path from an explicit arg or the current session

    Parameters
    ----------
    transcript_arg
        Optional explicit transcript path argument.

    Returns
    -------
        Path to the resolved ``jsonl`` transcript
    """
    if transcript_arg:
        return Path(transcript_arg)

    projects_base = Path(os.environ["HOME"]) / ".claude" / "projects"

    # Locate the current session's transcript by its globally-unique
    # if across ALL project directories. Each project dir is keyed to the
    # directory the session was launched from, which can differ from the  cwd
    # at run time (e.g. after cd-ing into a dir), so we much not assume the
    # cwd-derived project dir holds the transcript.
    session_id = os.environ.get("CLAUDE_CODE_SESSION_ID")
    if session_id:
        matches = list(projects_base.glob(f"*/{session_id}.jsonl"))
        if matches:
            return matches[0]

    raise FileNotFoundError(
        "No transcript and session_id found from 'CLAUDE_CODE_SESSION_ID' env."
        "Pass an explicit session path."
    )


def iter_records(transcript: Path) -> Any:
    """Yield parsed json records from a transcript, skipping malformed lines.

    Parameters
    ----------
    transcript
        Path to the `.jsonl` transcript file.
    """
    with transcript.open(encoding="utf-8") as ts:
        for line in ts:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                yield json.loads(stripped)
            except json.JSONDecodeError:
                print(f"WARNING: Unable to decode transcript line: {stripped}.")
                continue


def _text_blocks(content: str | list[Any]) -> list[str]:
    """Return all plain-text fragments from the message ``content`` field.

    Parameters
    ----------
    content
        Either string (legacy form) or a list of content blocks.

    Returns
    -------
        Text fragments. tool-result and non-text blocks are ignored.
    """
    if isinstance(content, str):
        return [content]
    if isinstance(content, list):
        return [
            block["text"]
            for block in content
            if isinstance(block, dict)
            and block.get("type") == "text"
            and isinstance(block.get("text"), str)
        ]
    return []


def clean_prompt(text: str) -> str:
    """Strip synthetic wrappers and system reminders from a user prompt."""
    if text.lstrip().startswith(_SYNTHETIC_PREFIXES):
        return ""
    return _SYSTEM_REMINDER_RE.sub("", text).strip()


def analyze(transcript: Path) -> str:
    """Build the full review report for a transcript

    Parameters
    ----------
    transcript
        Path to the transcript json file

    Returns
    -------
        A markdown report covering prompts, commands, tool usage an friction.
    """
    prompts: list[str] = []
    slash_commands: Counter[str] = Counter()
    tools: Counter[str] = Counter()
    bash_verbs: Counter[str] = Counter()
    bash_lines: list[str] = []
    friction: Counter[str] = Counter()
    message_count: int = 0

    for record in iter_records(transcript=transcript):
        message_count += 1
        record_type = record.get("type")
        content = record.get("message", {}).get("content")

        if record_type == "user":
            for fragment in _text_blocks(content=content):
                for command in _COMMAND_NAME_RE.findall(fragment):
                    slash_commands[command.strip()] += 1
                cleaned = clean_prompt(fragment)
                if cleaned:
                    prompts.append(cleaned)
                    for match in _FRICTION_RE.findall(cleaned):
                        friction[match] += 1
        elif record_type == "assistant" and isinstance(content, list):
            for block in content:
                if not isinstance(block, dict) or block.get("type") != "tool_use":
                    continue
                name = block.get("name", "?")
                tools[name] += 1
                if name == "Bash":
                    command = (block.get("input", {}) or {}).get("command", "")
                    if command:
                        bash_lines.append(command)
                        bash_verbs[command.strip().split(None, 1)[0]] += 1
    return _render(
        transcript=transcript,
        message_count=message_count,
        prompts=prompts,
        slash_commands=slash_commands,
        tools=tools,
        bash_verbs=bash_verbs,
        bash_lines=bash_lines,
        friction=friction,
    )


def _render(
    transcript: Path,
    message_count: int,
    prompts: list[str],
    slash_commands: Counter[str],
    tools: Counter[str],
    bash_verbs: Counter[str],
    bash_lines: list[str],
    friction: Counter[str],
) -> str:
    """Format the collected signal as a Markdown report.

    Parameters
    ----------
    transcript
        Source transcript path.
    message_count
        Total number of transcript records parsed.
    prompts
        Cleaned chronological user prompts.
    slash_commands
        Counts of slash-command / skill invocations.
    tools
        Counts of tool-use calls by tool name.
    bash_verbs
        Counts of Bash commands by leading verb.
    bash_lines
        Full Bash command lines, in order.
    friction
        Counts of interruption / denial signals.

    Returns
    -------
        The  rendered Markdown report.
    """
    out: list[str] = []

    def _counter_section(
        tittle: str, counter: Counter[str], limit: int | None = None
    ) -> None:
        out.append(f"## {tittle}")
        items = counter.most_common(limit)
        if not items:
            out.append("(None)")
        else:
            out.extend(f"  {count:4d}  {name}" for name, count in items)
        out.append("")

    out.append("#  Session review source")
    out.append(f"transcript: {transcript}")
    out.append(f"messages:   {message_count}")
    out.append(f"prompts:    {len(prompts)}")
    out.append("")

    out.append("##  User prompts (chronological)")
    for index, prompt in enumerate(prompts, start=1):
        out.append(f"\n--- prompt {index} ---")
        out.append(prompt)
    out.append("")

    _counter_section("Slash commands & skills invoked", slash_commands)
    _counter_section("Tool-use frequency", tools)
    _counter_section("Bash commands run (by leading verb)", bash_verbs, limit=30)

    out.append("##  Full Bash command lines")
    out.extend(f"  $ {line}" for line in bash_lines) if bash_lines else out.append(
        "(None)"
    )
    out.append("")

    _counter_section("Interruptions & denials (friction signal)", friction)

    return "\n".join(out)


def main():
    """Entry point to resolve the transcript path and generate report for LLM"""
    args = parse_args()
    try:
        transcript = resolve_transcript(args.transcript)
    except (FileNotFoundError, KeyError) as err:
        print(f"Error: {err}", file=sys.stderr)
        return 1

    if not transcript.is_file():
        print(f"ERROR: transcript not found: {transcript}", file=sys.stderr)
        return 1

    print(analyze(transcript=transcript))


if __name__ == "__main__":
    raise SystemExit(main())
