#!/usr/bin/env python3
"""
Concise Question Protocol Bootstrap + Validator Utility.

A zero-dependency Python 3 CLI that installs the Q1/Q1-a question
convention into any repository and lints transcripts for compliance.

Usage:
    python3 init_questions.py
    python3 init_questions.py --dry-run
    python3 init_questions.py --force
    python3 init_questions.py --check [--json]
    python3 init_questions.py --validate <file>
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

__version__ = "1.1.0"

PROTOCOL_DIR = "question_protocol"
WORKSPACE_DIR = "question_workspace"
STATE_NAME = "state.json"
REBASELINE_THRESHOLD = 99
# Pre-split state location. Frozen intentionally: detected (with mv hint), never written.
# NOTE: repo-wide renames must EXCLUDE this line.
LEGACY_STATE_PATH = f"{PROTOCOL_DIR}/{STATE_NAME}"

AGENT_DIRECTIVE_FILES = [
    "AGENTS.md",
    "CLAUDE.md",
    ".cursorrules",
    "GEMINI.md",
]

DIRECTIVE_BLOCK = """\n\
### ❓ Concise Question Protocol (`question_protocol/`)

1. **Label every question**: conversation-scoped monotonic `Q1, Q2, ...` (never reuse mid-conversation; reset only on new conversation). Single questions still use `Q1`.
2. **Label every choice**: `Qn-a/b/c...` case-insensitive — including binary (`yes/no`, `a/b`, `agree/disagree`, `proceed/cancel`). Default to **inline options** for token efficiency: `Q5. Retry? (a/backoff b/fixed-3 c/none)`.
3. **Free-form override**: accept `Qn: <text>` / `Qn. <text>` / `Qn= <text>` as aliases. Multi-select: `Q1-a,c` or `Q1-a+c`. Skip: `Qn: skip` / `skip Qn`.
4. **Delta asks**: new questions full-text once; carried opens collapse to one line (`Q2. … → shown, SHOW Q2 for full text`). Max 4 open. Late answers by original number MUST resolve.
5. **Importance flags**: `Qn!` = must-answer (persists through skip + compaction); plain `Qn` = answer-or-let-die (auto-parks if skipped, still answerable by number). User controls: `Qn! : keep asking`, `Qn: drop` kills it.
6. **Long sessions**: at >99 closed questions, PROPOSE `Archive Q1-Q99 and re-baseline to Q1?` — only on approval (archived refs `E1-Q5`).
7. **Compaction**: persist `question_workspace/state.json`; on resume `next_id = max(state, transcript max + 1)`, announce recovery and re-list `!` opens in full (plain opens IDs-only).
""".strip() + "\n"

# Matches E2-Q12-a, Q3, q1-B, Q4!, Q4: text, Q5. text, Q6= text, skip Q7
QREF_RE = re.compile(
    r"(?:(?P<epoch>[Ee]\d+)-)?[Qq](?P<num>\d+)(?P<important>!)?(?:-(?P<opt>[A-Za-z]+))?"
)
REPLY_TOKEN_RE = re.compile(
    r"^\s*(?:skip\s+)?(?:(?P<epoch>[Ee]\d+)-)?[Qq](?P<num>\d+)(?P<important>!)?"
    r"(?:-(?P<opt>[A-Za-z]+(?:\s*[,+]\s*[A-Za-z]+)*))?"
    r"\s*(?::|\.|=)?\s*(?P<rest>.*)$"
)
# Bare choice like "a) Yes" / "- Yes" / "1. Yes" without a Q prefix.
BARE_OPTION_RE = re.compile(r"^\s*(?:[-*]|\d+[.)])\s*(?:[A-Za-z]\)\s+)?.*$")
BARE_LABEL_RE = re.compile(r"^\s*(?:[-*]\s+)?[A-Za-z]\)\s+\S+")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _log(message: str, *, quiet: bool = False) -> None:
    if not quiet:
        print(message)


def _read_text(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def _resolve_protocol_dir(root: Path) -> Path:
    # Works whether cwd is the project root or inside question_protocol/.
    if root.name == PROTOCOL_DIR:
        return root
    return root / PROTOCOL_DIR


def _workspace_dir(root: Path) -> Path:
    return root / WORKSPACE_DIR


def _state_path(root: Path) -> Path:
    return _workspace_dir(root) / STATE_NAME


def _is_legacy_state(root: Path) -> bool:
    # The boilerplate copy shares the legacy path — only treat it as legacy
    # state when the file actually holds counter data (non-empty JSON object).
    legacy = root / LEGACY_STATE_PATH
    if not legacy.exists():
        return False
    try:
        data = json.loads(legacy.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    return isinstance(data, dict) and bool(data)


def _warn_legacy(root: Path) -> None:
    # stderr: stdout must stay pure JSON under --check --json.
    if _is_legacy_state(root):
        print(f"[WARN] legacy state {root / LEGACY_STATE_PATH} found. "
              "Migrate: mkdir -p question_workspace; "
              "mv question_protocol/state.json question_workspace/state.json; "
              "swap the .gitignore line to question_workspace/state.json.", file=sys.stderr)


def _read_state(root: Path) -> dict:
    path = _state_path(root)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"_corrupt": True}


def detect_agent_files(root: Path) -> list[str]:
    return [name for name in AGENT_DIRECTIVE_FILES if (root / name).exists()]


def ensure_gitignore(root: Path, *, dry_run: bool, quiet: bool) -> bool:
    """Gitignore runtime counter state in target workspaces (opt out by deleting the line)."""
    gitignore = root / ".gitignore"
    line = f"{WORKSPACE_DIR}/{STATE_NAME}"
    if line in _read_text(gitignore).splitlines():
        _log(f"[OK] .gitignore already contains {line}", quiet=quiet)
        return False
    new_content = _read_text(gitignore).rstrip("\n") + "\n" + line + "\n"
    if dry_run:
        _log(f"[DRY-RUN] Would append {line!r} to {gitignore}", quiet=quiet)
        return True
    gitignore.write_text(new_content, encoding="utf-8")
    _log(f"[UPDATE] {gitignore}", quiet=quiet)
    return True


def inject_directives(root: Path, agent_files: list[str], *, dry_run: bool, quiet: bool, force: bool = False) -> list[str]:
    changed: list[str] = []
    for name in agent_files:
        path = root / name
        existing = _read_text(path)
        if DIRECTIVE_BLOCK.strip() in existing.strip() and not force:
            _log(f"[SKIP] {name} already contains Question Protocol directives", quiet=quiet)
            continue
        if dry_run:
            _log(f"[DRY-RUN] Would append directives to {name}", quiet=quiet)
            changed.append(name)
            continue
        new_content = existing.rstrip("\n") + "\n\n" + DIRECTIVE_BLOCK
        path.write_text(new_content, encoding="utf-8")
        _log(f"[UPDATE] {name}", quiet=quiet)
        changed.append(name)
    return changed


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------

def validate_file(path: Path) -> tuple[bool, list[str]]:
    """Lint a transcript for Q-label compliance. Returns (ok, errors)."""
    errors: list[str] = []
    if not path.exists():
        return False, [f"File not found: {path}"]
    lines = path.read_text(encoding="utf-8").splitlines()

    first_seen: list[int] = []
    seen: set[int] = set()
    max_q = 0
    has_question_mark = False
    has_any_qlabel = False

    for i, line in enumerate(lines, start=1):
        if "?" in line:
            has_question_mark = True
        for m in QREF_RE.finditer(line):
            # Skip markdown headers like "## Q&A" false positives? Q&A has no digit so already excluded.
            num = int(m.group("num"))
            has_any_qlabel = True
            if num not in seen:
                seen.add(num)
                first_seen.append(num)
            max_q = max(max_q, num)

        stripped = line.strip()
        # Bare yes/no choice without Q label inside a question context.
        if re.match(r"^\s*[-*]\s+(Yes|No|Agree|Disagree|Proceed|Cancel)\s*$", line, re.IGNORECASE):
            if not QREF_RE.search(line):
                errors.append(f"line {i}: bare choice without Qn-x label: {stripped!r} (expected e.g. Q1-a)")

        # Bare "a) ..." option label without Q prefix.
        if BARE_LABEL_RE.match(line) and not QREF_RE.search(line):
            # Only flag when it looks like an option under a Q block (previous lines mention Q).
            context = "\n".join(lines[max(0, i - 4):i])
            if QREF_RE.search(context):
                errors.append(f"line {i}: bare option label without Q prefix: {stripped!r} (expected e.g. Q1-a)")

    if has_question_mark and not has_any_qlabel:
        errors.append("document asks questions (?) but contains no Qn labels")

    # Monotonic first-appearance check (repeats allowed, new numbers must increase).
    for prev, cur in zip(first_seen, first_seen[1:]):
        if cur < prev:
            errors.append(
                f"non-monotonic numbering: Q{cur} first appears after Q{prev} "
                f"(numbers must increase per conversation; skipped Qs keep original numbers)"
            )
            break

    if max_q > REBASELINE_THRESHOLD:
        # Not an error — just informational; handled by re-baseline proposal rule.
        pass

    return (len(errors) == 0), errors


def transcript_max_q(path: Path) -> int:
    text = _read_text(path)
    nums = [int(m.group("num")) for m in QREF_RE.finditer(text)]
    return max(nums) if nums else 0


# ---------------------------------------------------------------------------
# Status check
# ---------------------------------------------------------------------------

def status_check(root: Path, *, json_output: bool, quiet: bool) -> dict:
    _warn_legacy(root)
    proto = _resolve_protocol_dir(root)
    state = _read_state(root)
    agent_files = detect_agent_files(root)
    directives_ok = any(
        DIRECTIVE_BLOCK.strip() in _read_text(root / f).strip()
        for f in agent_files
    )
    result: dict = {
        "protocol_dir": str(proto),
        "protocol_exists": proto.exists(),
        "spec_exists": (proto / "QUESTION_PROTOCOL.md").exists(),
        "skill_exists": (proto / "SKILL.md").exists(),
        "workspace_dir": str(_workspace_dir(root)),
        "state_exists": _state_path(root).exists(),
        "legacy_state_found": _is_legacy_state(root),
        "next_id": state.get("next_id"),
        "epoch": state.get("epoch"),
        "open_count": len(state.get("open", [])) if isinstance(state.get("open"), list) else None,
        "gitignore_ok": f"{WORKSPACE_DIR}/{STATE_NAME}" in _read_text(root / ".gitignore").splitlines() if (root / ".gitignore").exists() else False,
        "directives_ok": directives_ok,
        "agent_files": agent_files,
        "rebaseline_threshold": REBASELINE_THRESHOLD,
    }
    if json_output:
        print(json.dumps(result, indent=2))
    else:
        _log("\n--- Question Protocol Status ---", quiet=quiet)
        for key, value in result.items():
            _log(f"  {key}: {value}", quiet=quiet)
        _log("--------------------------------\n", quiet=quiet)
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="init_questions.py",
        description="Bootstrap the Concise Question Protocol (Q1/Q1-a) and validate transcripts. See root README install profiles (minimal/standard/full).",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing to disk.")
    parser.add_argument("--force", action="store_true", help="Re-write directive block even if already present.")
    parser.add_argument("--check", action="store_true", help="Report whether the workspace is already initialized.")
    parser.add_argument("--json", action="store_true", help="Output --check results as JSON.")
    parser.add_argument("--quiet", action="store_true", help="Suppress non-essential output.")
    parser.add_argument("--validate", metavar="FILE", help="Lint a transcript file for Q-label compliance.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path.cwd()

    if args.validate:
        ok, errors = validate_file(Path(args.validate))
        if ok:
            if not args.quiet:
                print(f"✅ {args.validate}: question_protocol compliant.")
            return 0
        print(f"❌ {args.validate}: {len(errors)} violation(s):")
        for e in errors:
            print(f"  - {e}")
        return 1

    if args.check:
        status_check(root, json_output=args.json, quiet=args.quiet)
        return 0

    ensure_gitignore(root, dry_run=args.dry_run, quiet=args.quiet)

    agent_files = detect_agent_files(root)
    if agent_files:
        inject_directives(root, agent_files, dry_run=args.dry_run, quiet=args.quiet, force=args.force)
    else:
        _log(
            "[INFO] No agent directive files detected (AGENTS.md, CLAUDE.md, .cursorrules, GEMINI.md). "
            "Append the directive block from init_questions.py manually.",
            quiet=args.quiet,
        )

    if not args.quiet:
        proto = _resolve_protocol_dir(root)
        print("\n✅ Question Protocol workspace is ready.")
        print(f"   Spec: {proto / 'QUESTION_PROTOCOL.md'}")
        print("   Next step: label multi-question turns Q1, Q2... with Qn-a/b options.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
