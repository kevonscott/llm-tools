#!/usr/bin/env python3

"""Local GitHub/GitLab-style diff review UI (difit), parallel-safe.

Spins up a browser diff viewer over the current changes and let the user leave inline comments that
a claude session reads back. Many sessions can be run at once, since each start picks its own
port and tracks its own server, so stop only kills the one it started.

This script does not mutate git or the working tree: it only reads the diff and
pipes the result to difit.
"""

import argparse
import json
import os
import random
import re
import signal
import socket
import subprocess
import sys
import time
from contextlib import ExitStack
from pathlib import Path

DIFIT_VERSION = "difit@5.0.2"
STATE_DIR = Path("/tmp/difit-review")  # per-port state/log files
PORT_MIN = 4900  # Preferred port = PORT_MIN + random(PORT_SPAN)
PORT_SPAN = 100
START_TIMEOUT = 60.0  # Seconds to wait for difit to report its port (cold npx is slow)

_NOISE = re.compile(r"EBADENGINE|npm warn|npm notice")

def _clean(text: str):
    """Return text with npm/npx engine-warning and notice lines removed."""
    return "\n".join(line for line in text.splitlines() if not _NOISE.search(line))

def _run(cmd: list[str], cwd: str | None =None) -> subprocess.CompletedProcess[str]:
    """Return cmd capturing text output"""
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
def _git_clean(cwd: str|None=None) -> bool:
    """Return True when the git working tree at 'cwd' has no un/staged changes."""
    unstaged = _run(["git", "diff", "--quiet"], cwd=cwd).returncode == 0
    staged = _run(["git", "diff", "--cached", "--quiet"], cwd=cwd).returncode == 0
    return unstaged and staged

def _git_toplevel() -> str | None:
    """Return the toplevel of the git repo containing the cwd or None."""
    proc = _run(["git", "rev-parse", "--show-toplevel"])
    top = proc.stdout.strip()
    return top if proc.returncode == 0 and top else None

def _wait_for_port(log_path: Path, proc: subprocess.Popen[bytes]) -> int|None:
    """Poll difit's 'log_path' until it reports its bound port and return it.

    Returns None if difit exits or never reports a port in time.
    """
    pattern = re.compile(r"http://localhost:(\d+)")
    deadline = time.monotonic() + START_TIMEOUT
    while time.monotonic() < deadline:
        try:
            match = pattern.search(log_path.read_text())
        except OSError:
            match = None

        if match:
            return int(match.group(1))
        if proc.poll() is not None: # difit died during startup
            return None
        time.sleep(0.5)
    return None

def _listener_pid(port: int) -> int | None:
    """Return the PID listening on 'port' (difit's node server), or None.

    difit's real server is a grandchild of npx, tracking the socket owner
    (not the npx wrapper) is what make stop reliable. The socket can lag difit
    logging its real URL, so retry briefly.
    """
    pattern = re.compile(r"pid=(\d+)")
    for _ in range(5):
        out = _run(["ss", "-ltnp", f"sport = :{port}"]).stdout
        match = pattern.search(out)
        if match:
            return int(match.group(1))
        time.sleep(0.2)
    return None


def _state_file(port: int) -> Path:
    """Return the JSON state file path for a viewer on 'port'"""
    return STATE_DIR / f"port-{port}.json"

def _alive(pid: int) -> bool:
    """Return True if a process with pid currently exists."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True

def _serve(label: str, difit_args: list[str], stdin_file: Path|None, cwd:str) -> int:
    """Launch difit detached in cwd, register it, and print its access block.

    Parameters
    ----------
    label
        Human-readable description of what is being reviewed.
    difit_args
        Positional difit arguments (refs, ``-`` for stdin, extra flags).
    stdin_file
        A unified-diff file fed to difit on stdin or None.
    cwd
        The directory difit runs in.

    Returns
    -------
    int
        Process exit code. 0 success, 1 if difit failed to start.
    """

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    base = PORT_MIN + random.randrange(PORT_SPAN)
    log_path = STATE_DIR / f"start.{os.getpid()}.log"
    # Install DIFIT if not already installed
    cmd = [
        "npx",
        "--yes",
        DIFIT_VERSION,
        *difit_args,
        "--no-open",
        "--keep-alive",
        "--host",
        "0.0.0.0",
        "--port",
        str(base),
    ]

    with ExitStack() as stack:
        logf = stack.enter_context(open(log_path, "wb"))
        stdin_fh = (
            stack.enter_context(open(stdin_file, "rb")) if stdin_file else subprocess.DEVNULL
        )
        # start_new_session detaches difit so it outlives this script and the calling Bash tool.
        # output goes to the log so the caller never blocks.
        proc = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdin=stdin_fh,
            stdout=logf,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )

    port = _wait_for_port(log_path=log_path, proc=proc)

    if port is None:
        sys.stderr.write("ERROR: difit failed to start. Log:\n")
        sys.stderr.write(_clean(text=log_path.read_text(errors="replace")) + "\n")
        log_path.unlink(missing_ok=True)
        return 1

    # Record the real socket owner (fall back to the npx pid) and the key state by the
    # actual port, so the stop/list stay correct even if the difit bumped off `base`
    pid = _listener_pid(port=port) or proc.pid
    final_log = STATE_DIR / f"port-{port}.log"
    log_path.replace(final_log)
    url = f"http://{socket.getfqdn()}:{port}/"
    _state_file(port=port).write_text(
        json.dumps(
            {
                "port": port,
                "pid": pid,
                "url": url,
                "cwd": cwd,
                "log": str(final_log),
            }
        )
    )

    print(f"PORT={port}\nPID={pid}\nURL={url}\nREF={label}\nCWD={cwd}\nLOG={final_log}")
    return 0

def cmd_start(refs: list[str]) -> int:
    """Launch a viewer over the requested *refs*.

    Parameters
    ----------
    refs
        Zero refs (working tree), one ``commit``, or two ``<base> <target>``
    """
    if len(refs) > 2:
        sys.stderr.write("ERROR: expected at most two refs")
        return 2

    return _start_repo(refs=refs)



def _start_repo(refs: list[str]) -> int:
    """Launch a viewer for a git repo in the current dir."""
    top = _git_toplevel()
    if not top:
        sys.stderr.write("ERROR: not inside a git repository!")
        return 1

    if len(refs) == 2:
        return _serve(f"{refs[1]}..{refs[0]}",[refs[0], refs[1]], stdin_file=None, cwd=top)
    if len(refs) == 1:
        return _serve(f"@ {refs[0]}",[refs[0]], stdin_file=None, cwd=top)
    if _git_clean(cwd=top):
        return _serve("HEAD", ["HEAD"], stdin_file=None, cwd=top)
    return _serve("uncommitted", [".", "--include-untracked"], stdin_file=None, cwd=top)

def cmd_comments(port:int) -> int:
    """Print the inline comments from the viewer on *port* as JSON."""
    proc = _run(
        [
            "npx",
            "--yes",
            DIFIT_VERSION,
            "comment",
            "get",
            "--port",
            str(port),
            "--format",
            "json",
        ]
    )
    print(_clean(text=(proc.stdout + proc.stderr)))
    return proc.returncode

def cmd_stop(port: int) -> int:
    """Stop the viewer on *port* (tracked pid and current socket owner)."""
    state = _state_file(port=port)
    pids: set[int] = set()
    if state.exists():
        try:
            pids.add(int(json.loads(state.read_text())["pid"]))
        except (OSError, ValueError, KeyError) as e:
            print(e)
    live = _listener_pid(port=port)
    if live:
        pids.add(live)

    killed = False
    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
            killed = True
        except (ProcessLookupError, PermissionError):
            pass
    state.unlink(missing_ok=True)
    print(
        f"Stopped difit on port {port}" if killed else f"No difit found on port {port}"
    )
    return 0

def cmd_stop_all() -> int:
    """Stop every viewer this script started."""
    states = sorted(STATE_DIR.glob("port-*.json"))
    if not states:
        print("No difit servers to stop")
        return 0
    for state in states:
        port = int(state.stem.removeprefix("port-"))
        cmd_stop(port=port)
    return 0


def cmd_list() -> int:
    """List running viewers this script started, pruning dead entries."""
    found = False
    for state in sorted(STATE_DIR.glob("port-*.json")):
        try:
            info = json.loads(state.read_text())
        except (OSError, ValueError):
            state.unlink(missing_ok=True)
            continue

        pid = info.get("pid")
        if isinstance(pid, int) and _alive(pid=pid):
            port = info["port"]
            url = info.get("url", "")
            log = info.get("log", "")
            print(f"port={port} pid={pid} url={url} log={log}")
            found = True
        else:
            state.unlink(missing_ok=True)  # prune dead entry
    if not found:
        print("No difit servers running (started via this skill)")
    return 0

def _build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog="local_code_review",
        description="Local diff review UI (difit)"
    )
    sub_parser = parser.add_subparsers(dest="command", required=True)

    p_start = sub_parser.add_parser("start", help="launch a diff viewer")
    p_start.add_argument(
        'refs', nargs="*", help="none | <commit> | <base> <target>"
    )

    p_comments = sub_parser.add_parser("comments", help="print inline comments as JSON")
    p_comments.add_argument("port", type=int)

    p_stop = sub_parser.add_parser("stop", help="stop the viewer on a port")
    p_stop.add_argument("port", type=int)

    sub_parser.add_parser("stop-all", help="stop every viewer this script started")
    sub_parser.add_parser("list", help="list running viewers this script started")
    return parser


def main() -> int:
    """Parse arguments and dispatch to the selected subcommand."""
    args = _build_parser().parse_args()
    match args.command:
        case "start":
            return cmd_start(refs=args.refs)
        case "comments":
            return cmd_comments(port=args.port)
        case "stop":
            return cmd_stop(port=args.port)
        case "stop-all":
            return cmd_stop_all()
        case "list":
            return cmd_list()
        case _:
            return 2

if __name__=="__main__":
    raise SystemExit(main())