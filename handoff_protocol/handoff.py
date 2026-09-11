#!/usr/bin/env python3
"""
Project-Local Session Handoff Protocol

Manual triggers:
    /handoff-start  -> python3 handoff_protocol/handoff.py start
    /handoff-resume -> python3 handoff_protocol/handoff.py resume

A zero-dependency Python 3 CLI that creates, archives, and resumes
handoff files inside the project-local `.protocol/handoff_workspace/` folder.
"""

from __future__ import annotations

import argparse
import datetime
import io
import json
import re
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path
from typing import Any

__version__ = "1.2.0"

# Stable key for versions.json + backup bundles.
PROTOCOL_KEY = "handoff"

RUNTIME_ROOT = ".protocol"  # all runtime state lives here (single .gitignore line)
WORKSPACE_LEAF = "handoff_workspace"  # pre-consolidation name: legacy detect + migrate
WORKSPACE_DIR = f"{RUNTIME_ROOT}/{WORKSPACE_LEAF}"
ARCHIVE_DIR = "archive"
TEMPLATE_NAME = "handoff_template.md"
GITIGNORE_LINE = f"{RUNTIME_ROOT}/"
STALE_GITIGNORE_LINES = (f"{WORKSPACE_LEAF}/",)
# Pre-split runtime name. Frozen intentionally: detected (with mv hint), never created.
# NOTE: repo-wide renames must EXCLUDE this line.
LEGACY_WORKSPACE_DIR = "handoff_protocol"

AGENT_DIRECTIVE_FILES = [
    "AGENTS.md",
    "CLAUDE.md",
    ".cursorrules",
    "GEMINI.md",
]

# Version marker wrapper: upgrades REPLACE same-key stale blocks instead of
# accumulating them. Manual pastes (unmarked core) are recognized and left alone.
_DIRECTIVE_CORE = """### 🔄 Session Handoff Protocol (`.protocol/handoff_workspace/`)

Manual triggers only: `/handoff-start` captures state (`handoff.py start`), `/handoff-resume` continues it (`handoff.py resume`), `done` archives. All files stay project-local and gitignored.
"""

DIRECTIVE_BLOCK = (f"\n<!-- protocol-block:{PROTOCOL_KEY} v{__version__} -->\n"
                   f"{_DIRECTIVE_CORE}"
                   f"<!-- /protocol-block:{PROTOCOL_KEY} -->\n")


def _block_pattern() -> re.Pattern:
    return re.compile(rf"<!-- protocol-block:{re.escape(PROTOCOL_KEY)} v(.*?) -->"
                      r".*?"
                      rf"<!-- /protocol-block:{re.escape(PROTOCOL_KEY)} -->",
                      re.DOTALL)


def _has_block(text: str) -> bool:
    """Current marked block, manual-paste core, or any stale marked version."""
    stripped = text.strip()
    return (DIRECTIVE_BLOCK.strip() in stripped
            or _DIRECTIVE_CORE.strip() in stripped
            or _block_pattern().search(text) is not None)


def _replace_stale_block(text: str) -> tuple[str, str | None]:
    """Swap a same-protocol older-versioned block for the current one.
    Returns (new_text, old_version). No markers → (text, None)."""
    pattern = _block_pattern()
    match = pattern.search(text)
    if not match:
        return text, None
    if DIRECTIVE_BLOCK.strip() in text.strip():
        return text, None  # current version already present
    return pattern.sub(lambda _: DIRECTIVE_BLOCK.strip(), text, count=1), match.group(1)


def detect_agent_files(root: Path) -> list[str]:
    return [name for name in AGENT_DIRECTIVE_FILES if (root / name).exists()]


def inject_directives(root: Path, agent_files: list[str], *, dry_run: bool, quiet: bool) -> list[str]:
    changed: list[str] = []
    for name in agent_files:
        path = root / name
        existing = _read_text(path)
        if DIRECTIVE_BLOCK.strip() in existing.strip():
            _log(f"[SKIP] {name} already contains Handoff directives", quiet=quiet)
            continue
        replaced, old_version = _replace_stale_block(existing)
        if old_version is not None:
            if dry_run:
                _log(f"[DRY-RUN] Would replace stale v{old_version} directives in {name}", quiet=quiet)
                changed.append(name)
                continue
            path.write_text(replaced.rstrip("\n") + "\n", encoding="utf-8")
            _log(f"[UPDATE] {name} (replaced stale v{old_version} directives)", quiet=quiet)
            changed.append(name)
            continue
        if _DIRECTIVE_CORE.strip() in existing.strip():
            _log(f"[SKIP] {name} already contains Handoff directives (manual paste)", quiet=quiet)
            continue
        if dry_run:
            _log(f"[DRY-RUN] Would append directives to {name}", quiet=quiet)
            changed.append(name)
            continue
        path.write_text(existing.rstrip("\n") + "\n\n" + DIRECTIVE_BLOCK, encoding="utf-8")
        _log(f"[UPDATE] {name}", quiet=quiet)
        changed.append(name)
    return changed


def _maybe_create_directives(root: Path, *, dry_run: bool, quiet: bool, assume_yes: bool = False) -> bool:
    """Q46-a: no directive file exists — ask (default yes) to create AGENTS.md.
    Non-interactive stdin (piped/CI) never blocks: falls back to INFO + skip,
    unless --yes was passed (scripted installs)."""
    target = root / "AGENTS.md"
    if dry_run:
        _log(f"[DRY-RUN] Would ask to create {target} with the protocol block", quiet=quiet)
        return False
    answer = "a" if assume_yes else "b"
    if not assume_yes and sys.stdin.isatty() and not quiet:
        print("Q1. No directive file found (AGENTS.md/CLAUDE.md/.cursorrules/GEMINI.md). "
              "Create AGENTS.md with the protocol block? (a/yes b/no, I'll copy manually) [a]: ")
        try:
            answer = (input().strip().lower() or "a")
        except EOFError:
            answer = "b"
    if answer not in ("a", "yes", "y"):
        _log("[INFO] Skipped AGENTS.md creation — copy the block manually when ready.", quiet=quiet)
        return False
    target.write_text("# AGENTS.md\n\n" + DIRECTIVE_BLOCK, encoding="utf-8")
    _log(f"[CREATE] {target} (protocol block installed)", quiet=quiet)
    return True


def _is_legacy_workspace(root: Path) -> bool:
    # The boilerplate copy shares the legacy name — only treat it as a legacy
    # workspace when it actually holds handoff artifacts (files or archive/).
    legacy = root / LEGACY_WORKSPACE_DIR
    if not legacy.exists():
        return False
    if list(legacy.glob("handoff-*.md")):
        return True
    return (legacy / ARCHIVE_DIR).exists()


def _dual_presence(root: Path) -> Path | None:
    """A stale same-named local copy coexists with agents-boilerplate/. Returns its path, else None."""
    script_dir = Path(__file__).parent.resolve()
    candidate = (root / script_dir.name).resolve()
    if candidate.exists() and candidate != script_dir:
        return root / script_dir.name
    return None


def _warn_dual_presence(root: Path) -> None:
    # stderr: stdout must stay pure JSON under status --json.
    dup = _dual_presence(root)
    if dup is not None:
        print(f"[WARN] dual presence: {dup} duplicates the invoked collection copy. "
              "Choose: (a) reference — delete the local copy, keep agents-boilerplate/; "
              "(b) vendor — run the local copy instead. Proceeding with the invoked copy.",
              file=sys.stderr)


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

    wanted = [GITIGNORE_LINE]
    if (root / "agents-boilerplate").exists():
        wanted.append("agents-boilerplate/")
    kept = [ln for ln in lines if ln not in STALE_GITIGNORE_LINES]
    pruned = [ln for ln in lines if ln in STALE_GITIGNORE_LINES]
    missing = [ln for ln in wanted if ln not in kept]
    if not missing and not pruned:
        _log("[OK] .gitignore already covers .protocol/ runtime", quiet=quiet)
        return False

    if dry_run:
        for ln in missing:
            _log(f"[DRY-RUN] Would append {ln!r} to {gitignore}", quiet=quiet)
        for ln in pruned:
            _log(f"[DRY-RUN] Would prune stale {ln!r} from {gitignore}", quiet=quiet)
        return True
    gitignore.write_text("\n".join(kept + [ln for ln in missing if ln not in kept]).rstrip("\n") + "\n", encoding="utf-8")
    for ln in pruned:
        _log(f"[PRUNE] stale {ln!r} superseded by {GITIGNORE_LINE!r}", quiet=quiet)
    _log(f"[UPDATE] {gitignore}", quiet=quiet)
    return True


def migrate_legacy_runtime(root: Path, *, dry_run: bool, quiet: bool) -> None:
    """One-way move of the pre-consolidation workspace into .protocol/.
    Whole-dir mv (contents preserved); both-sides-present = WARN, manual merge."""
    legacy = root / WORKSPACE_LEAF
    new = root / WORKSPACE_DIR
    if legacy.exists() and not new.exists():
        if dry_run:
            _log(f"[DRY-RUN] Would migrate {legacy} -> {new}", quiet=quiet)
        else:
            new.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(legacy), str(new))
            _log(f"[MIGRATE] {legacy} -> {new} (handoffs, archive intact)", quiet=quiet)
    elif legacy.exists() and new.exists():
        print(f"[WARN] both {legacy} and {new} exist — merge manually, then drop the legacy dir.",
              file=sys.stderr)


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
    plan = root / ".protocol" / "green_amber_red_workspace" / "plan.md"
    if not plan.exists():
        return "No .protocol/green_amber_red_workspace/plan.md detected."
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
        rel = Path(__file__).resolve().relative_to(root.resolve()) \
            if root.resolve() in Path(__file__).resolve().parents else Path("handoff_protocol/handoff.py")
        print(f"   Resume later with: python3 {rel.as_posix()} resume")
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


VERSIONS_NAME = "versions.json"
BACKUP_PREFIX = "protocol-backup"


def _versions_path(root: Path) -> Path:
    return root / RUNTIME_ROOT / VERSIONS_NAME


def read_versions(root: Path) -> dict:
    try:
        data = json.loads(_read_text(_versions_path(root)))
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def stamp_version(root: Path, *, dry_run: bool, quiet: bool) -> None:
    """Record this protocol's code version in .protocol/versions.json (merged —
    other protocols' keys are never touched)."""
    if dry_run:
        _log(f"[DRY-RUN] Would stamp {PROTOCOL_KEY}={__version__} in {_versions_path(root)}",
             quiet=quiet)
        return
    _versions_path(root).parent.mkdir(parents=True, exist_ok=True)
    versions = read_versions(root)
    if versions.get(PROTOCOL_KEY) == __version__:
        _log(f"[OK] version already stamped ({PROTOCOL_KEY}={__version__})", quiet=quiet)
        return
    versions[PROTOCOL_KEY] = __version__
    _versions_path(root).write_text(json.dumps(versions, indent=2) + "\n", encoding="utf-8")
    _log(f"[STAMP] {PROTOCOL_KEY}={__version__} in {_versions_path(root)}", quiet=quiet)


def _runtime_dirs(root: Path) -> list[Path]:
    return [root / WORKSPACE_DIR]


def _backup_name() -> str:
    return f"{BACKUP_PREFIX}-{PROTOCOL_KEY}-{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.tar.gz"


def backup_runtime(root: Path, *, dry_run: bool, quiet: bool) -> Path | None:
    """Snapshot runtime dirs + a manifest into a root-level tar.gz bundle."""
    existing = [d for d in _runtime_dirs(root) if d.exists()]
    agent_files = detect_agent_files(root)
    with_block = [f for f in agent_files if _has_block(_read_text(root / f))]
    gi_lines = _read_text(root / ".gitignore").splitlines() if (root / ".gitignore").exists() else []
    manifest = {
        "protocol": PROTOCOL_KEY,
        "version": __version__,
        "created": datetime.datetime.now().isoformat(timespec="seconds"),
        "paths": sorted(str(d.relative_to(root)) for d in existing),
        "directive_files": with_block,
        "gitignore_had_protocol_line": GITIGNORE_LINE in gi_lines,
    }
    target = root / _backup_name()
    if dry_run:
        _log(f"[DRY-RUN] Would write backup {target} "
             f"({len(existing)} dir(s), {len(with_block)} directive file(s))", quiet=quiet)
        return target
    if not existing:
        _log("[INFO] No runtime dirs to back up (manifest-only bundle).", quiet=quiet)
    with tarfile.open(target, "w:gz") as tar:
        data = json.dumps(manifest, indent=2).encode("utf-8")
        info = tarfile.TarInfo("manifest.json")
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
        for d in existing:
            tar.add(str(d.relative_to(root)), arcname=str(d.relative_to(root)))
    _log(f"[BACKUP] {target} ({', '.join(manifest['paths']) or 'manifest only'})", quiet=quiet)
    return target


def _extract_member(tar: tarfile.TarFile, member: tarfile.TarInfo, path: Path) -> None:
    try:
        tar.extract(member, path=path, filter="data")
    except TypeError:  # Python < 3.12 without backport
        tar.extract(member, path=path)


def restore_bundle(root: Path, bundle: str, *, force: bool, dry_run: bool, quiet: bool) -> int:
    """Restore files from a backup bundle (merge; --force overwrites)."""
    path = Path(bundle)
    if not path.exists():
        print(f"[ERROR] backup bundle not found: {path}")
        return 1
    with tarfile.open(path, "r:gz") as tar:
        members = [m for m in tar.getmembers() if m.name != "manifest.json"]
        if dry_run:
            for m in members:
                dest = root / m.name
                action = "overwrite" if (dest.exists() and force) else ("keep" if dest.exists() else "restore")
                _log(f"[DRY-RUN] Would {action}: {dest}", quiet=quiet)
            return 0
        kept, restored, overwritten = 0, 0, 0
        for m in members:
            dest = root / m.name
            existed = dest.exists()
            if existed and not force:
                kept += 1
                continue
            _extract_member(tar, m, root)
            if existed:
                overwritten += 1
            else:
                restored += 1
    _log(f"[RESTORE] {path}: {restored} restored, {overwritten} overwritten, {kept} kept.",
         quiet=quiet)
    ensure_gitignore(root, dry_run=False, quiet=quiet)
    for name in detect_agent_files(root):
        inject_directives(root, [name], dry_run=False, quiet=quiet)
    stamp_version(root, dry_run=False, quiet=quiet)
    return 0


def remove_directives(root: Path, *, dry_run: bool, quiet: bool) -> list[str]:
    """Extract this protocol's directive block (any version) from agent files.
    Never deletes files."""
    pattern = _block_pattern()
    changed = []
    for name in detect_agent_files(root):
        path = root / name
        text = _read_text(path)
        if DIRECTIVE_BLOCK.strip() not in text.strip() and not pattern.search(text):
            continue
        if dry_run:
            _log(f"[DRY-RUN] Would remove directives from {name}", quiet=quiet)
            changed.append(name)
            continue
        new_text = pattern.sub("\n", text)
        new_text = new_text.replace(DIRECTIVE_BLOCK, "\n")
        new_text = re.sub(r"\n{3,}", "\n\n", new_text).strip() + "\n"
        path.write_text(new_text, encoding="utf-8")
        _log(f"[REMOVE] directives from {name}", quiet=quiet)
        changed.append(name)
    return changed


def uninstall_protocol(root: Path, *, skip_backup: bool, dry_run: bool, quiet: bool) -> int:
    """Archive-first removal: backup bundle, drop runtime dirs, extract directives,
    drop own versions key. The `.protocol/` gitignore line is pruned only when
    `.protocol/` ends up empty. Re-run is a no-op (exit 0)."""
    installed = (any(d.exists() for d in _runtime_dirs(root))
                 or remove_directives(root, dry_run=True, quiet=True)
                 or PROTOCOL_KEY in read_versions(root))
    if not installed:
        _log(f"[OK] {PROTOCOL_KEY} not installed — nothing to remove.", quiet=quiet)
        return 0
    bundle = None
    if not skip_backup:
        bundle = backup_runtime(root, dry_run=dry_run, quiet=quiet)
    elif dry_run:
        _log("[DRY-RUN] Would skip backup (--skip-backup)", quiet=quiet)
    else:
        _log("[WARN] --skip-backup: runtime data will be destroyed without an archive.", quiet=quiet)
    for d in _runtime_dirs(root):
        if d.exists():
            if dry_run:
                _log(f"[DRY-RUN] Would remove {d}", quiet=quiet)
            else:
                shutil.rmtree(d)
                _log(f"[REMOVE] {d}", quiet=quiet)
    remove_directives(root, dry_run=dry_run, quiet=quiet)
    if not dry_run:
        versions = read_versions(root)
        versions.pop(PROTOCOL_KEY, None)
        if versions:
            _versions_path(root).write_text(json.dumps(versions, indent=2) + "\n", encoding="utf-8")
        elif _versions_path(root).exists():
            _versions_path(root).unlink()
        runtime_root = root / RUNTIME_ROOT
        if runtime_root.exists() and not any(runtime_root.iterdir()):
            runtime_root.rmdir()
            _log(f"[REMOVE] empty {runtime_root}", quiet=quiet)
        gi = root / ".gitignore"
        lines = _read_text(gi).splitlines() if gi.exists() else []
        if GITIGNORE_LINE in lines and not (root / RUNTIME_ROOT).exists():
            remaining = [ln for ln in lines if ln != GITIGNORE_LINE]
            if "".join(remaining).strip():
                gi.write_text("\n".join(remaining).rstrip("\n") + "\n", encoding="utf-8")
            else:
                gi.unlink()
                _log(f"[REMOVE] {gi} (only held the .protocol/ line)", quiet=quiet)
            _log(f"[PRUNE] {GITIGNORE_LINE!r} (.protocol/ gone)", quiet=quiet)
    if bundle is not None and not dry_run:
        _log(f"[ARCHIVE] runtime preserved in {bundle} — delete it to complete the uninstall.",
             quiet=quiet)
    return 0


def status_handoff(args: argparse.Namespace, root: Path) -> int:
    _warn_legacy(root)
    pre = root / WORKSPACE_LEAF
    if pre.exists():
        print(f"[WARN] pre-consolidation runtime {pre} found. "
              f"Migrate: mv {WORKSPACE_LEAF} {WORKSPACE_DIR}, re-run handoff init.", file=sys.stderr)
    workspace = root / WORKSPACE_DIR
    active = find_active_handoff(workspace)
    archived = sorted((workspace / ARCHIVE_DIR).glob("handoff-*.md")) if (workspace / ARCHIVE_DIR).exists() else []

    dup = _dual_presence(root)
    result: dict[str, Any] = {
        "workspace": str(workspace),
        "workspace_exists": workspace.exists(),
        "dual_presence": str(dup) if dup else None,
        "legacy_workspace_found": _is_legacy_workspace(root),
        "pre_consolidation_runtime_found": (root / WORKSPACE_LEAF).exists(),
        "code_version": __version__,
        "installed_version": read_versions(root).get(PROTOCOL_KEY),
        "version_ok": read_versions(root).get(PROTOCOL_KEY) == __version__,
        "archive_exists": (workspace / ARCHIVE_DIR).exists(),
        "gitignore_ok": GITIGNORE_LINE in _read_text(root / ".gitignore").splitlines() if (root / ".gitignore").exists() else False,
        "directives_ok": any(_has_block(_read_text(root / f))
                             for f in detect_agent_files(root)),
        "active_handoff": str(active) if active else None,
        "archived_count": len(archived),
        "latest_archived": str(archived[-1]) if archived else None,
        "directives_hint": (None if detect_agent_files(root) else
                            "No directive file found — run start and answer Q1-a to create AGENTS.md."),
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
        epilog="Global flags (--dry-run, --quiet, --yes) precede the subcommand: "
               "handoff.py --yes start --no-prompt (not: start --no-prompt --yes).",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--dry-run", action="store_true", help="Preview actions without writing files.")
    parser.add_argument("--quiet", action="store_true", help="Suppress non-essential output.")
    parser.add_argument("--yes", action="store_true", help="Assume yes to prompts (e.g. create AGENTS.md). For scripted installs.")

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

    subparsers.add_parser("backup", help="Snapshot runtime + manifest into a root-level tar.gz bundle.")
    restore_parser = subparsers.add_parser("restore", help="Restore files from a backup bundle (merge; --force overwrites).")
    restore_parser.add_argument("bundle", help="Path to a protocol-backup-handoff-*.tar.gz bundle.")
    restore_parser.add_argument("--force", action="store_true", help="Overwrite existing files.")
    uninstall_parser = subparsers.add_parser("uninstall", help="Archive-first removal: backup bundle, drop runtime, extract directives.")
    uninstall_parser.add_argument("--skip-backup", action="store_true",
                                  help="Destroy runtime without archiving (explicit data loss).")

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path.cwd()

    if args.command == "backup":
        backup_runtime(root, dry_run=args.dry_run, quiet=args.quiet)
        return 0
    if args.command == "restore":
        return restore_bundle(root, args.bundle, force=args.force, dry_run=args.dry_run,
                              quiet=args.quiet)
    if args.command == "uninstall":
        return uninstall_protocol(root, skip_backup=args.skip_backup, dry_run=args.dry_run,
                                  quiet=args.quiet)
    if args.command == "start":
        _warn_dual_presence(root)
        _warn_legacy(root)
        migrate_legacy_runtime(root, dry_run=args.dry_run, quiet=args.quiet)
        stamp_version(root, dry_run=args.dry_run, quiet=args.quiet)
        agent_files = detect_agent_files(root)
        if agent_files:
            inject_directives(root, agent_files, dry_run=args.dry_run, quiet=args.quiet)
        else:
            _maybe_create_directives(root, dry_run=args.dry_run, quiet=args.quiet, assume_yes=args.yes)
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
