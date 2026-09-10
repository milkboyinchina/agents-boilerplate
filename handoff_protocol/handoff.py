#!/usr/bin/env python3
"""
Project-Local Session Handoff Protocol

Manual triggers:
    /handoff-start  -> python3 handoff_protocol/handoff.py start
    /handoff-resume -> python3 handoff_protocol/handoff.py resume

A zero-dependency Python 3 CLI that creates, archives, and resumes
handoff files inside the project-local `handoff_workspace/` folder.
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

__version__ = "1.1.0"

WORKSPACE_DIR = "handoff_workspace"
ARCHIVE_DIR = "archive"
TEMPLATE_NAME = "handoff_template.md"
GITIGNORE_LINE = f"{WORKSPACE_DIR}/"
# Pre-split runtime name. Frozen intentionally: detected (with mv hint), never created.
# NOTE: repo-wide renames must EXCLUDE this line.
LEGACY_WORKSPACE_DIR = "handoff_protocol"


def _is_legacy_workspace(root: Path) -> bool:
    # The boilerplate copy shares the legacy name — only treat it as a legacy
    # workspace when it actually holds handoff artifacts (files or archive/).
    legacy = root / LEGACY_WORKSPACE_DIR
    if not legacy.exists():
        return False
    if list(legacy.glob("handoff-*.md")):
        return True
    return (legacy / ARCHIVE_DIR).exists()


def _warn_legacy(root: Path) -> None:
    # stderr: stdout must stay pure JSON under status --json.
    if _is_legacy_workspace(root):
        print(f"[WARN] legacy workspace {root / LEGACY_WORKSPACE_DIR} found (pre-Q39 name). "
              "Migrate: mkdir -p handoff_workspace; "
              "mv handoff_protocol/handoff-*.md handoff_workspace/; "
              "mv handoff_protocol/archive handoff_workspace/; "
              "refresh the handoff_protocol/ boilerplate copy; "
              "swap the .gitignore line to handoff_workspace/.", file=sys.stderr)

DEFAULT_TEMPLATE = """# {title}

## 1. Session Metadata
- **Date**: {date}
- **Agent / Model**: {agent_model}
- **Trigger**: {trigger}
- **Session ID**: {session_id}

## 2. Active Task / Plan Status
{active_task}

## 3. Files Changed
```
{files_changed}
```

## 4. Recent Changes Summary
{recent_changes}

## 5. Verification Results
{verification}

## 6. Rollback Plan
{rollback}

## 7. Blockers / Risks
{blockers}

## 8. Next Steps
{next_steps}

## 9. Additional Notes
{notes}
"""


def _log(message: str, *, quiet: bool = False) -> None:
    if not quiet:
        print(message)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _write_text(path: Path, content: str, *, dry_run: bool, quiet: bool) -> None:
    if dry_run:
        _log(f"[DRY-RUN] Would write: {path}", quiet=quiet)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    _log(f"[WRITE] {path}", quiet=quiet)


def ensure_workspace(root: Path, *, dry_run: bool, quiet: bool) -> Path:
    workspace = root / WORKSPACE_DIR
    archive = workspace / ARCHIVE_DIR
    if dry_run:
        _log(f"[DRY-RUN] Would create {workspace} and {archive}", quiet=quiet)
        return workspace
    archive.mkdir(parents=True, exist_ok=True)
    _log(f"[CREATE] {workspace}", quiet=quiet)
    _log(f"[CREATE] {archive}", quiet=quiet)
    return workspace


def ensure_gitignore(root: Path, *, dry_run: bool, quiet: bool) -> bool:
    gitignore = root / ".gitignore"
    content = _read_text(gitignore)
    lines = content.splitlines()

    if GITIGNORE_LINE in lines:
        _log(f"[OK] .gitignore already contains {GITIGNORE_LINE}", quiet=quiet)
        return False

    new_content = content.rstrip("\n") + "\n" + GITIGNORE_LINE + "\n"
    if dry_run:
        _log(f"[DRY-RUN] Would append {GITIGNORE_LINE!r} to {gitignore}", quiet=quiet)
        return True
    gitignore.write_text(new_content, encoding="utf-8")
    _log(f"[UPDATE] {gitignore}", quiet=quiet)
    return True


def list_handoffs(workspace: Path, *, include_archive: bool = False) -> list[Path]:
    pattern = "handoff-*.md"
    files = sorted(workspace.glob(pattern))
    if include_archive:
        files.extend(sorted((workspace / ARCHIVE_DIR).glob(pattern)))
    return sorted(files, key=lambda p: p.name)


def find_active_handoff(workspace: Path) -> Path | None:
    files = list_handoffs(workspace, include_archive=False)
    return files[-1] if files else None


def find_latest_handoff(workspace: Path) -> Path | None:
    files = list_handoffs(workspace, include_archive=True)
    return files[-1] if files else None


def handoff_filename() -> str:
    return datetime.datetime.now().strftime("handoff-%Y%m%d-%H%M.md")


def detect_git_status(root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            text = result.stdout.strip()
            return text if text else "(no changes)"
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    return "(git not available or not a repository)"


def detect_plan_status(root: Path) -> str:
    plan = root / "green_amber_red_workspace" / "plan.md"
    if not plan.exists():
        return "No green_amber_red_workspace/plan.md detected."
    text = _read_text(plan)
    status_match = re.search(r"\*\*Lifecycle Status\*\*:\s*([^\n]+)", text)
    active_match = re.search(r"\*\*Active Task\*\*:\s*([^\n]+)", text)
    status = status_match.group(1).strip() if status_match else "unknown"
    active = active_match.group(1).strip() if active_match else "unknown"
    return f"Plan status: {status} | Active task: {active}"


def prompt_field(name: str, default: str = "") -> str:
    prompt = f"{name}"
    if default:
        prompt += f" [{default}]"
    prompt += ": "
    try:
        value = input(prompt).strip()
    except EOFError:
        value = ""
    return value if value else default


def _proto_dir(root: Path) -> Path:
    # The boilerplate copy lives beside this script in target workspaces.
    here = Path(__file__).parent
    if root in (*here.parents, here.parent):
        return here
    candidate = root / here.name
    return candidate if candidate.exists() else here


def load_template(root: Path) -> str:
    template_path = _proto_dir(root) / "templates" / TEMPLATE_NAME
    if template_path.exists():
        return _read_text(template_path)
    return DEFAULT_TEMPLATE


def build_context(args: argparse.Namespace, root: Path) -> dict[str, str]:
    ctx: dict[str, str] = {
        "title": args.title or f"Handoff {_now_str()}",
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M %Z"),
        "agent_model": args.agent_model or "",
        "trigger": "/handoff-start",
        "session_id": args.session_id or "",
        "active_task": detect_plan_status(root),
        "files_changed": detect_git_status(root),
        "recent_changes": "",
        "verification": "",
        "rollback": "",
        "blockers": "",
        "next_steps": "",
        "notes": "",
    }

    if not args.no_prompt:
        _log("\n--- Fill in handoff fields (press Enter to skip) ---")
        for key in ["agent_model", "session_id", "recent_changes", "verification", "rollback", "blockers", "next_steps", "notes"]:
            ctx[key] = prompt_field(key.replace("_", " ").title(), ctx[key])
        _log("-----------------------------------------------------\n")

    return ctx


def _now_str() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


def start_handoff(args: argparse.Namespace, root: Path) -> int:
    workspace = ensure_workspace(root, dry_run=args.dry_run, quiet=args.quiet)
    ensure_gitignore(root, dry_run=args.dry_run, quiet=args.quiet)

    active = find_active_handoff(workspace)
    if active and not args.force:
        _log(
            f"[ERROR] Active handoff already exists: {active}\n"
            "Use --force to archive it and create a new one, or run 'done' first.",
            quiet=args.quiet,
        )
        return 1

    if active and args.force:
        archive_path = workspace / ARCHIVE_DIR / active.name
        if args.dry_run:
            _log(f"[DRY-RUN] Would archive {active} -> {archive_path}", quiet=args.quiet)
        else:
            shutil.move(str(active), str(archive_path))
            _log(f"[ARCHIVE] {active} -> {archive_path}", quiet=args.quiet)

    ctx = build_context(args, root)
    template = load_template(root)
    content = template.format(**ctx)
    output = workspace / handoff_filename()
    _write_text(output, content, dry_run=args.dry_run, quiet=args.quiet)

    if not args.quiet and not args.dry_run:
        print(f"\n✅ Handoff started: {output}")
        print("   Resume later with: python3 handoff_protocol/handoff.py resume")
    return 0


def extract_section(text: str, heading: str) -> str:
    pattern = rf"## \d+\.\s*{re.escape(heading)}\n(.*?)\n(?=## \d+\.\s|$)"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""


def resume_handoff(args: argparse.Namespace, root: Path) -> int:
    workspace = root / WORKSPACE_DIR
    active = find_active_handoff(workspace)

    if not active:
        latest = find_latest_handoff(workspace)
        if latest:
            _log(f"[INFO] No active handoff. Latest archived handoff: {latest}", quiet=args.quiet)
        else:
            _log("[INFO] No handoff files found. Run 'start' first.", quiet=args.quiet)
        return 1

    text = _read_text(active)
    if args.dry_run:
        _log(f"[DRY-RUN] Would resume from {active}", quiet=args.quiet)
        return 0

    title = text.splitlines()[0].lstrip("# ").strip() if text.startswith("#") else active.name
    metadata = extract_section(text, "Session Metadata")
    active_task = extract_section(text, "Active Task / Plan Status")
    blockers = extract_section(text, "Blockers / Risks")
    next_steps = extract_section(text, "Next Steps")
    files_changed = extract_section(text, "Files Changed")
    notes = extract_section(text, "Additional Notes")

    summary = f"""\n--- Handoff Resume Summary ---
Source: {active}
Title: {title}
{metadata}

Active Task / Plan Status:
{active_task}

Files Changed:
{files_changed}

Blockers / Risks:
{blockers}

Next Steps:
{next_steps}

Additional Notes:
{notes}
------------------------------\n"""
    print(summary)
    return 0


def done_handoff(args: argparse.Namespace, root: Path) -> int:
    workspace = root / WORKSPACE_DIR
    active = find_active_handoff(workspace)

    if not active:
        _log("[INFO] No active handoff to archive.", quiet=args.quiet)
        return 0

    archive_path = workspace / ARCHIVE_DIR / active.name
    if args.dry_run:
        _log(f"[DRY-RUN] Would archive {active} -> {archive_path}", quiet=args.quiet)
        return 0

    shutil.move(str(active), str(archive_path))
    _log(f"[ARCHIVE] {active} -> {archive_path}", quiet=args.quiet)
    if not args.quiet:
        print("\n✅ Handoff archived.")
    return 0


def status_handoff(args: argparse.Namespace, root: Path) -> int:
    _warn_legacy(root)
    workspace = root / WORKSPACE_DIR
    active = find_active_handoff(workspace)
    archived = sorted((workspace / ARCHIVE_DIR).glob("handoff-*.md")) if (workspace / ARCHIVE_DIR).exists() else []

    result: dict[str, Any] = {
        "workspace": str(workspace),
        "workspace_exists": workspace.exists(),
        "legacy_workspace_found": _is_legacy_workspace(root),
        "archive_exists": (workspace / ARCHIVE_DIR).exists(),
        "gitignore_ok": GITIGNORE_LINE in _read_text(root / ".gitignore").splitlines() if (root / ".gitignore").exists() else False,
        "active_handoff": str(active) if active else None,
        "archived_count": len(archived),
        "latest_archived": str(archived[-1]) if archived else None,
    }

    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    _log("\n--- Handoff Protocol Status ---", quiet=args.quiet)
    for key, value in result.items():
        _log(f"  {key}: {value}", quiet=args.quiet)
    _log("--------------------------------\n", quiet=args.quiet)
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="handoff.py",
        description="Project-local session handoff protocol. See root README install profiles (minimal/standard/full).",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--dry-run", action="store_true", help="Preview actions without writing files.")
    parser.add_argument("--quiet", action="store_true", help="Suppress non-essential output.")

    subparsers = parser.add_subparsers(dest="command", required=True)

    start_parser = subparsers.add_parser("start", help="Create a new handoff file.")
    start_parser.add_argument("--title", help="Handoff title.")
    start_parser.add_argument("--agent-model", help="Agent/model identifier.")
    start_parser.add_argument("--session-id", help="Session identifier.")
    start_parser.add_argument("--force", action="store_true", help="Archive existing active handoff and create a new one.")
    start_parser.add_argument("--no-prompt", action="store_true", help="Skip interactive prompts; leave placeholders.")

    subparsers.add_parser("resume", help="Read the active handoff and print a resume summary.")
    subparsers.add_parser("done", help="Archive the active handoff.")

    status_parser = subparsers.add_parser("status", help="Report handoff workspace status.")
    status_parser.add_argument("--json", action="store_true", help="Output as JSON.")

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path.cwd()

    if args.command == "start":
        _warn_legacy(root)
        return start_handoff(args, root)
    if args.command == "resume":
        return resume_handoff(args, root)
    if args.command == "done":
        return done_handoff(args, root)
    if args.command == "status":
        return status_handoff(args, root)

    return 0


if __name__ == "__main__":
    sys.exit(main())
