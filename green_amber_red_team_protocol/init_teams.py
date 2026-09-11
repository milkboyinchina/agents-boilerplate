#!/usr/bin/env python3
"""
Traffic-Light Multi-Agent Teaming Bootstrap Utility

A zero-dependency Python 3 CLI that initializes the Green/Amber/Red team
coordination workspace in any repository or project.

Usage:
    python3 init_teams.py
    python3 init_teams.py --dry-run
    python3 init_teams.py --force
    python3 init_teams.py --check
    python3 init_teams.py --template backend --init-plan "Add user auth API"
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import io
import json
import os
import re
import shutil
import sys
import tarfile
from pathlib import Path
from typing import Iterable

__version__ = "1.2.0"

# Stable key for versions.json + backup bundles (survives protocol-copy renames).
PROTOCOL_KEY = "green-amber-red"

# All runtime state lives under .protocol/ (single .gitignore line). Sources stay
# in the protocol copy, tracked. Q58-a/Q59-a.
RUNTIME_ROOT = ".protocol"
WORKSPACE_LEAF = "green_amber_red_workspace"  # pre-consolidation name: legacy detect + migrate
WORKSPACE_DIR = f"{RUNTIME_ROOT}/{WORKSPACE_LEAF}"
# Pre-Q39 runtime name. Frozen intentionally: detected (with mv hint), never created.
# NOTE: repo-wide renames must EXCLUDE this line.
LEGACY_WORKSPACE_DIR = "green_amber_red_teams"
ARCHIVE_DIR = "archive"
STASH_DIR = "stash"
README_NAME = "README.md"
PLAN_NAME = "plan.md"
GITIGNORE_LINE = f"{RUNTIME_ROOT}/"
# Stale ignore lines pruned automatically once .protocol/ covers them.
STALE_GITIGNORE_PATTERNS = (r"^green_amber_red_workspace/$",
                            r"^.*/redteam/(inbox|outbox|inbox-archive|outbox-archive)/\*$")
REDTEAM_LEAF = "redteam"  # pre-consolidation: <protocol-copy>/redteam (legacy detect + migrate)
REDTEAM_DIR = f"{RUNTIME_ROOT}/{REDTEAM_LEAF}"
REDTEAM_SUBDIRS = ("inbox", "outbox", "inbox-archive", "outbox-archive")
CONFIG_NAME = "config.yml"


def _proto_dir_name() -> str:
    """Folder name of the boilerplate copy this script runs from (target workspaces may rename it)."""
    return Path(__file__).parent.name


def _dual_presence(root: Path) -> Path | None:
    """A stale same-named local copy coexists with agents-boilerplate/. Returns its path, else None."""
    script_dir = Path(__file__).parent.resolve()
    candidate = (root / script_dir.name).resolve()
    if candidate.exists() and candidate != script_dir:
        return root / script_dir.name
    return None


def _warn_dual_presence(root: Path) -> None:
    # stderr: stdout must stay pure JSON under --check --json.
    dup = _dual_presence(root)
    if dup is not None:
        print(f"[WARN] dual presence: {dup} duplicates the invoked collection copy. "
              "Choose: (a) reference — delete the local copy, keep agents-boilerplate/; "
              "(b) vendor — run the local copy instead. Proceeding with the invoked copy.",
              file=sys.stderr)


def _redteam_dir(root: Path) -> Path:
    """Exchange location: .protocol/redteam (Q58-a). Sources (templates, docs)
    stay in the protocol copy; only runtime (packets, config) moved out."""
    return root / REDTEAM_DIR


def _prune_stale_gitignore(lines: list[str]) -> tuple[list[str], list[str]]:
    """Drop ignore lines superseded by the single .protocol/ line. Returns
    (kept, pruned). Exact/prefix matches only — never touches user lines."""
    kept, pruned = [], []
    for ln in lines:
        if any(re.match(pat, ln) for pat in STALE_GITIGNORE_PATTERNS):
            pruned.append(ln)
        else:
            kept.append(ln)
    return kept, pruned

AGENT_DIRECTIVE_FILES = [
    "AGENTS.md",
    "CLAUDE.md",
    ".cursorrules",
    "GEMINI.md",
]

# Version marker wrapper: upgrades REPLACE same-key stale blocks instead of
# accumulating them (see _replace_stale_block). Manual pastes (unmarked core)
# are recognized and left alone.
_DIRECTIVE_CORE = """### 🚦 Traffic-Light Team Collaboration Protocols

1. **Single Source of Truth**: All active implementation plans MUST live in `{workspace}/plan.md`. Every plan carries a `Plan-ID: <slug>-YYYYMMDD-HHMM` header (filename-derived, never reused) — cited in packets, defect rows, and stash listings so agent and user track the same plan.
2. **Auto-Archiving**: Before creating a new plan via `plan-greenteam`, if the current plan is `✅ COMPLETED`, move it to `{workspace}/archive/plan_YYYYMMDD_HHMM.md`. If it is unfinished (`📋 PLANNED` / `⏳ IN_PROGRESS`), auto-stash it to `{workspace}/stash/plan_<plan-id>.md` instead — announce the Plan ID + restore command. Mid-flight work (Amber executing, Red packet open): warn with both Plan IDs and require explicit confirmation first.
3. **Core Shortcuts** (aliases accepted everywhere):
   - `plan-greenteam <prompt>` (`plan-green`): Green Team drafts a fresh `{workspace}/plan.md` (`📋 PLANNED`, fresh Plan-ID) detailing all affected files. Touches NO source code.
   - `plan-stash-greenteam` (`stash-green`): Park the active plan to `stash/` (status + progress preserved verbatim); workspace returns to no-active-plan.
   - `plan-resume-greenteam <plan-id>` (`resume-green`): List `stash/` when no ID is given; restore the chosen plan to `plan.md` intact (a different active unfinished plan stashes first).
   - `review-greenteam` (`review-green`): Any agent/model playing planner QA-checks the plan (APPROVE → execute, REVISE → amend + re-review).
   - `execute-amberteam` (`exec-amber`): Amber Team inspects `{workspace}/plan.md`, summarizes it, and asks the user: *"Should the agent proceed with executing the plan and its tasks?"*
   - `review-amberteam` (`review-amber`): Green Team audits Amber Team's git diff and automated tests before clearing completion.
   - `send-redteam` (`send-red`): Green Team builds a timestamped packet in `.protocol/redteam/inbox`, delivers it if the red workspace is reachable, else asks the user to carry it.
   - `review-redteam` (`review-red`): Green Team reads the defect report, records verdict PASS (stays `✅ COMPLETED`) or FAIL (reopen, back to `⏳ IN_PROGRESS`, Amber fixes, re-audit), then archives the packet.
   - `verify-green-amber-red-team`: Green Team audits configs, packet states, and versions, then asks whether to realign.
   - Red Team (own session): `test-redteam` (`test-red`) plans + tests a packet; `finish-redteam` (`finish-red`) writes the outbox verdict; `recheck-redteam` (`recheck-red`) revisits inbox + outbox and asks what to do next.
4. **Packets**: `.protocol/redteam/inbox|outbox` hold ACTIVE timestamped packets (`packet_green|red_YYYYMMDD_HHMM`); `*-archive` holds inactive ones. New packets cross-ack the previous packet done; only acked-done packets archive. `.protocol/redteam/config.yml` declares `side:` (green|red), reachability, and the redteam kill switch.
""".format(workspace=WORKSPACE_DIR)

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

WORKSPACE_README = """# 🚦 Traffic-Light Multi-Agent Teaming Workspace (`{workspace}/`)

This directory is strictly **gitignored** and serves as the single source of truth for active implementation plans and multi-agent coordination.

---

## 🧭 Team Personas & Commands

| Color / Team | Persona | Responsibilities | Key Commands |
|:---|:---|:---|:---|
| **🟢 Green Team** | **Architect / Planner** | Analyzes specs, maps affected files, writes `plan.md`, parks/resumes plans, audits implementation, runs the Red Team handoff, and triages Red Team verdicts. **Touches NO production code.** | `plan-greenteam`<br>`plan-stash-greenteam`<br>`plan-resume-greenteam`<br>`review-greenteam`<br>`review-amberteam`<br>`send-redteam`<br>`review-redteam`<br>`verify-green-amber-red-team` |
| **🟠 Amber Team** | **Developer / Implementer** | Inspects the plan, confirms with user, implements code changes, runs tests, tracks task states, and fixes Red Team FAIL findings on re-open. | `execute-amberteam` |
| **🔴 Red Team** | **Independent QA / Auditor** | Executes black-box tests, regression suites, and adversarial audits in an isolated sandbox. Reads own `.protocol/redteam/inbox`, writes own `.protocol/redteam/outbox`. | `test-redteam`<br>`finish-redteam`<br>`recheck-redteam` |

---

## 🔄 End-to-End Collaboration Lifecycle

```
[User: plan-greenteam <prompt>] ──> [🟢 Green Team drafts {workspace}/plan.md (📋 PLANNED, Plan-ID stamped)]
                                                │         unfinished active plan → auto-stash to stash/ (announce ID + resume cmd)
[User: plan-stash-greenteam] ───> [🟢 Park active plan.md → stash/plan_<plan-id>.md (progress intact)]
[User: plan-resume-greenteam <id>] → [🟢 Restore stashed plan → plan.md (other active plan stashes first)]
                                                │
[User: review-greenteam] ──────> [🟢 Any planner QA-checks plan: APPROVE → proceed / REVISE → amend]
                                                │
[User: execute-amberteam] ─────> [🟠 Amber Team confirms with user, codes, marks tasks [COMPLETED]]
                                                │
[User: review-amberteam] ──────> [🟢 Green Team verifies git diff & automated tests]
                                                │
                                  [Audit clean? ──Yes──> Status: ✅ COMPLETED]
                                                │
[User: send-redteam] ──────────> [🟢 Green stages packet → delivers if reachable, else user carries]
                                                │
                                  [🔴 test-redteam → tests → finish-redteam → outbox verdict]
                                                │
[User: review-redteam] ────────> [🟢 Green reads report → PASS (done) / FAIL (reopen → IN_PROGRESS → fix → re-audit)]
                                                │
[User: verify-green-amber-red-team] → [🟢 Drift audit → Q1-a realign turn]
```

---

## 📋 Status Reference

### Overall Plan Lifecycle
- `📋 PLANNED`: Staged by Green Team, pending user approval.
- `⏳ IN_PROGRESS`: Actively being coded by Amber Team.
- `✅ COMPLETED`: Fully implemented, verified, and audited by Green Team.

### Individual Task Statuses
- `[PLANNED]`: Queued for implementation.
- `[IN_PROGRESS]`: Currently active.
- `[COMPLETED]`: Code written, tested, and passing.
- `[ERROR]`: Execution failed (requires reason, trace, and patch plan).
- `[INCOMPLETE]`: Partially done (requires explanation and remaining delta).
- `[BLOCKED]`: Blocked on external dependency or hardware.
""".format(workspace=WORKSPACE_DIR)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _log(message: str, *, quiet: bool = False) -> None:
    if not quiet:
        print(message)


def _write_text(path: Path, content: str, *, dry_run: bool, quiet: bool) -> bool:
    if dry_run:
        _log(f"[DRY-RUN] Would write: {path}", quiet=quiet)
        return True
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    _log(f"[WRITE] {path}", quiet=quiet)
    return True


def _read_text(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _now_str() -> str:
    return datetime.datetime.now().strftime("%Y%m%d_%H%M")


def detect_project_type(root: Path) -> str:
    """Infer project flavor to suggest relevant verification commands."""
    files = {p.name for p in root.iterdir() if p.is_file()}
    dirs = {p.name for p in root.iterdir() if p.is_dir()}

    if "pubspec.yaml" in files or any((root / d).exists() for d in ["android", "ios"]):
        return "mobile"
    if "manage.py" in files or "pyproject.toml" in files or "requirements.txt" in files:
        return "backend"
    if "package.json" in files:
        return "frontend"
    if "docker-compose.yml" in files or "compose.yaml" in files or "Dockerfile" in files:
        return "devops"
    return "generic"


# ---------------------------------------------------------------------------
# Workspace setup
# ---------------------------------------------------------------------------

def ensure_dirs(root: Path, *, dry_run: bool, quiet: bool) -> None:
    workspace = root / WORKSPACE_DIR
    archive = workspace / ARCHIVE_DIR
    stash = workspace / STASH_DIR
    if dry_run:
        _log(f"[DRY-RUN] Would create directories: {workspace}, {archive}, {stash}", quiet=quiet)
        return
    archive.mkdir(parents=True, exist_ok=True)
    stash.mkdir(parents=True, exist_ok=True)
    _log(f"[CREATE] {workspace}", quiet=quiet)
    _log(f"[CREATE] {archive}", quiet=quiet)
    _log(f"[CREATE] {stash}", quiet=quiet)


LEDGER_NAME = "defects.md"


def ensure_ledger(root: Path, *, dry_run: bool, quiet: bool) -> None:
    """Create an empty defect ledger from the template — never overwrite an
    existing one (same guard as the plan-overwrite rule). Green side only."""
    ledger = root / WORKSPACE_DIR / LEDGER_NAME
    if ledger.exists():
        _log(f"[SKIP] {ledger} already exists (never auto-overwritten)", quiet=quiet)
        return
    template = Path(__file__).parent / "templates" / "defect_ledger.md"
    content = _read_text(template) if template.exists() else "# Defect Ledger\n"
    if dry_run:
        _log(f"[DRY-RUN] Would create {ledger} from template", quiet=quiet)
        return
    ledger.parent.mkdir(parents=True, exist_ok=True)
    ledger.write_text(content, encoding="utf-8")
    _log(f"[WRITE] {ledger}", quiet=quiet)


def ensure_gitignore(root: Path, *, dry_run: bool, quiet: bool, side: str = "green") -> bool:
    gitignore = root / ".gitignore"
    content = _read_text(gitignore) if gitignore.exists() else ""

    wanted = [GITIGNORE_LINE]  # one line covers workspace + exchange (Q59-a), both sides
    if (root / "agents-boilerplate").exists():
        wanted.append("agents-boilerplate/")
    lines = content.splitlines()
    kept, pruned = _prune_stale_gitignore(lines)
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
    new_lines = kept + [ln for ln in missing if ln not in kept]
    gitignore.write_text("\n".join(new_lines).rstrip("\n") + "\n", encoding="utf-8")
    for ln in pruned:
        _log(f"[PRUNE] stale {ln!r} superseded by {GITIGNORE_LINE!r}", quiet=quiet)
    _log(f"[UPDATE] {gitignore}", quiet=quiet)
    return True


def _proto_dir(root: Path) -> Path:
    # The boilerplate copy lives beside this script in target workspaces.
    here = Path(__file__).parent
    if here.name == _proto_dir_name() and root in (*here.parents, here.parent):
        return here
    candidate = root / _proto_dir_name()
    return candidate if candidate.exists() else here


def _read_config_side(redteam: Path) -> str | None:
    text = _read_text(redteam / CONFIG_NAME)
    match = re.search(r"^side:\s*(green|red)\s*$", text, re.MULTILINE)
    return match.group(1) if match else None


def _config_values(text: str) -> tuple[str, ...]:
    """Effective config content: value lines only (comments/blank lines ignored,
    so template comment drift never counts as customization)."""
    return tuple(sorted(ln.strip() for ln in text.splitlines()
                        if ln.strip() and not ln.strip().startswith("#")))


def _default_config_values() -> set[tuple[str, ...]]:
    """Value-line sets for untouched configs: both sides, old + new return_to."""
    bases = set()
    for side in ("green", "red"):
        for return_to in ("redteam/outbox", ".protocol/redteam/outbox"):
            bases.add(_config_values(
                f"side: {side}\nredteam_enabled: true\nredteam_accessible: false\n"
                f"redteam_path: null\nreturn_to: {return_to}\n"))
    return bases


def migrate_legacy_runtime(root: Path, *, dry_run: bool, quiet: bool) -> None:
    """One-way move of pre-consolidation runtime into .protocol/. Whole-dir mv
    (contents preserved, never copy-then-orphan). Both-sides-present = WARN and
    stop (manual merge); legacy skeleton .gitkeep files stay in place."""
    legacy_ws = root / WORKSPACE_LEAF
    new_ws = root / WORKSPACE_DIR
    if legacy_ws.exists() and not new_ws.exists():
        if dry_run:
            _log(f"[DRY-RUN] Would migrate {legacy_ws} -> {new_ws}", quiet=quiet)
        else:
            new_ws.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(legacy_ws), str(new_ws))
            _log(f"[MIGRATE] {legacy_ws} -> {new_ws} (plans, ledgers, stash intact)", quiet=quiet)
    elif legacy_ws.exists() and new_ws.exists():
        print(f"[WARN] both {legacy_ws} and {new_ws} exist — merge manually, then drop the legacy dir.",
              file=sys.stderr)


def _legacy_redteam_has_content(legacy: Path) -> bool:
    """True when the pre-consolidation exchange holds anything beyond the
    tracked skeleton (.gitkeep files + untouched template config)."""
    if not legacy.exists():
        return False
    for sub in REDTEAM_SUBDIRS:
        for item in (legacy / sub).glob("*") if (legacy / sub).exists() else []:
            if item.name != ".gitkeep":
                return True
    cfg = legacy / CONFIG_NAME
    return cfg.exists() and _config_values(_read_text(cfg)) not in _default_config_values()


def migrate_legacy_redteam(root: Path, *, dry_run: bool, quiet: bool) -> None:
    """Move pre-consolidation exchange (<protocol-copy>/redteam) into
    .protocol/redteam. Moves packet contents + config.yml only; tracked
    skeleton (.gitkeep) stays so vendor-copy diffs stay clean."""
    proto = _proto_dir(root)
    legacy = proto / REDTEAM_LEAF
    new = _redteam_dir(root)
    if not legacy.exists():
        return
    moves: list[tuple[Path, Path]] = []
    for sub in REDTEAM_SUBDIRS:
        for item in sorted((legacy / sub).glob("*")) if (legacy / sub).exists() else []:
            if item.name != ".gitkeep":
                moves.append((item, new / sub / item.name))
    legacy_cfg = legacy / CONFIG_NAME
    if legacy_cfg.exists() and not (new / CONFIG_NAME).exists():
        # Migrate only customized configs (side/reachability edits). An
        # untouched template — however commented — is equivalent to what
        # ensure_redteam stamps, so fresh vendor copies don't churn.
        if _config_values(_read_text(legacy_cfg)) not in _default_config_values():
            moves.append((legacy_cfg, new / CONFIG_NAME))
    if not moves:
        return
    for src, dst in moves:
        if dry_run:
            _log(f"[DRY-RUN] Would migrate {src} -> {dst}", quiet=quiet)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
    if not dry_run:
        _log(f"[MIGRATE] exchange {legacy} -> {new} (skeleton .gitkeep files left in place)", quiet=quiet)


def ensure_redteam(root: Path, *, side: str, dry_run: bool, quiet: bool) -> None:
    """Create the .protocol/redteam exchange skeleton + config.yml (side-stamped).
    Everything under .protocol/ is gitignored (single line); config holds LOCAL
    values so ignoring it is intended."""
    redteam = _redteam_dir(root)
    for sub in REDTEAM_SUBDIRS:
        target = redteam / sub
        if dry_run:
            _log(f"[DRY-RUN] Would create directory: {target}", quiet=quiet)
        else:
            target.mkdir(parents=True, exist_ok=True)
    _log(f"[CREATE] {redteam} skeleton", quiet=quiet)
    cfg = redteam / CONFIG_NAME
    existing = _read_config_side(redteam)
    # Never clobber reachability settings: only stamp side on fresh files, or
    # when --side was passed explicitly and differs.
    if dry_run:
        _log(f"[DRY-RUN] Would ensure {cfg} (side: {side}, existing: {existing})", quiet=quiet)
        return
    if not cfg.exists():
        _write_text(cfg, _default_config(side), dry_run=False, quiet=True)
        _log(f"[WRITE] {cfg} (side: {side})", quiet=quiet)
    elif existing is not None and existing != side:
        # --side was passed explicitly (main resolves None -> keep existing),
        # so reaching here with a mismatch means an explicit switch.
        text = re.sub(r"^side:\s*(green|red)\s*$", f"side: {side}", _read_text(cfg), flags=re.MULTILINE)
        cfg.write_text(text, encoding="utf-8")
        _log(f"[UPDATE] {cfg} (side: {existing} -> {side})", quiet=quiet)
    else:
        _log(f"[OK] {cfg} already configured (side: {existing or side})", quiet=quiet)


def _default_config(side: str) -> str:
    return f"""# Red-team exchange config — LOCAL values, edit per workspace copy.
side: {side}
redteam_enabled: true
redteam_accessible: false
redteam_path: null
return_to: .protocol/redteam/outbox
"""


def generate_readme(root: Path, *, force: bool, dry_run: bool, quiet: bool) -> bool:
    readme = root / WORKSPACE_DIR / README_NAME
    if readme.exists() and not force:
        _log(f"[SKIP] {readme} already exists (use --force to overwrite)", quiet=quiet)
        return False
    return _write_text(readme, WORKSPACE_README, dry_run=dry_run, quiet=quiet)


def detect_agent_files(root: Path) -> list[str]:
    return [name for name in AGENT_DIRECTIVE_FILES if (root / name).exists()]


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


def inject_directives(root: Path, agent_files: Iterable[str], *, dry_run: bool, quiet: bool) -> list[str]:
    changed: list[str] = []
    for name in agent_files:
        path = root / name
        existing = _read_text(path)
        if DIRECTIVE_BLOCK.strip() in existing.strip():
            _log(f"[SKIP] {name} already contains Traffic-Light directives", quiet=quiet)
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
            _log(f"[SKIP] {name} already contains Traffic-Light directives (manual paste)", quiet=quiet)
            continue
        new_content = existing.rstrip("\n") + "\n" + DIRECTIVE_BLOCK + "\n"
        if dry_run:
            _log(f"[DRY-RUN] Would append directives to {name}", quiet=quiet)
            changed.append(name)
            continue
        path.write_text(new_content, encoding="utf-8")
        _log(f"[UPDATE] {name}", quiet=quiet)
        changed.append(name)
    return changed


def archive_completed_plan(root: Path, *, dry_run: bool, quiet: bool) -> bool:
    plan = root / WORKSPACE_DIR / PLAN_NAME
    if not plan.exists():
        return False
    text = _read_text(plan)
    if "✅ COMPLETED" not in text:
        _log(f"[INFO] Existing plan is not ✅ COMPLETED; skipping archive", quiet=quiet)
        return False

    archive_name = f"plan_{_now_str()}.md"
    archive_path = root / WORKSPACE_DIR / ARCHIVE_DIR / archive_name
    if dry_run:
        _log(f"[DRY-RUN] Would archive {plan} -> {archive_path}", quiet=quiet)
        return True
    plan.rename(archive_path)
    _log(f"[ARCHIVE] {plan} -> {archive_path}", quiet=quiet)
    return True


# ---------------------------------------------------------------------------
# Plan templates
# ---------------------------------------------------------------------------

PLAN_TEMPLATES: dict[str, str] = {
    "generic": """# [Feature / Fix Goal]
> **Lifecycle Status**: `📋 PLANNED`
> **Planner (Green Team)**: <Agent Name> (Timestamp)
> **Executor (Amber Team)**: Pending
> **Active Task**: None
> **Plan-ID**: `<slug>-YYYYMMDD-HHMM` (stamped at creation; filename-derived, never reused — cited in packets, defect rows, and stash listings so agents and users track the same plan)

## 1. Problem Context & Architectural Scope
[Brief explanation of the objective, constraints, and architecture]

## 2. Execution Sequence

| # | Task | Status | Who | Affected / Edited Files | Effort | Notes / Reason |
|:--|:---|:---:|:---:|:---|:---:|:---|
| 1 | [Task 1] | `[PLANNED]` | Amber Team | • `path/to/file` | ~10m | |
| 2 | [Task 2] | `[PLANNED]` | Amber Team | • `path/to/file` | ~10m | |
| 3 | Verification & Tests | `[PLANNED]` | Amber Team | • `path/to/tests` | ~10m | |

## 3. Verification Plan
```bash
# Example verification commands
python3 -m py_compile scripts/example.py
pytest
```
""",
    "backend": """# [Backend Feature / Fix]
> **Lifecycle Status**: `📋 PLANNED`
> **Planner (Green Team)**: <Agent Name> (Timestamp)
> **Executor (Amber Team)**: Pending
> **Active Task**: None
> **Plan-ID**: `<slug>-YYYYMMDD-HHMM` (stamped at creation; filename-derived, never reused — cited in packets, defect rows, and stash listings so agents and users track the same plan)

## 1. Problem Context & Architectural Scope
[API contract, schema changes, business logic]

## 2. Execution Sequence

| # | Task | Status | Who | Affected / Edited Files | Effort | Notes |
|:--|:---|:---:|:---:|:---|:---:|:---|
| 1 | Database / Schema Migration | `[PLANNED]` | Amber Team | • `apps/<app>/models.py`<br>• `apps/<app>/migrations/` | ~15m | |
| 2 | Backend API Implementation | `[PLANNED]` | Amber Team | • `apps/<app>/views.py`<br>• `apps/<app>/serializers.py`<br>• `urls.py` | ~30m | |
| 3 | Service / Business Logic | `[PLANNED]` | Amber Team | • `apps/<app>/services.py` | ~20m | |
| 4 | Tests & Verification | `[PLANNED]` | Amber Team | • `tests/test_*.py` | ~15m | |

## 3. Verification Plan
```bash
python3 -m py_compile src/**/*.py
pytest
python manage.py migrate --check
```
""",
    "frontend": """# [Frontend Feature / Fix]
> **Lifecycle Status**: `📋 PLANNED`
> **Planner (Green Team)**: <Agent Name> (Timestamp)
> **Executor (Amber Team)**: Pending
> **Active Task**: None
> **Plan-ID**: `<slug>-YYYYMMDD-HHMM` (stamped at creation; filename-derived, never reused — cited in packets, defect rows, and stash listings so agents and users track the same plan)

## 1. Problem Context & Architectural Scope
[UI/UX changes, component architecture, state management]

## 2. Execution Sequence

| # | Task | Status | Who | Affected / Edited Files | Effort | Notes |
|:--|:---|:---:|:---:|:---|:---:|:---|
| 1 | Component / View Implementation | `[PLANNED]` | Amber Team | • `src/components/...`<br>• `src/views/...` | ~25m | |
| 2 | State / API Integration | `[PLANNED]` | Amber Team | • `src/stores/...`<br>• `src/api/...` | ~20m | |
| 3 | Styling & Responsiveness | `[PLANNED]` | Amber Team | • `src/styles/...` | ~15m | |
| 4 | Tests & Lint | `[PLANNED]` | Amber Team | • `src/**/*.test.*` | ~15m | |

## 3. Verification Plan
```bash
npm run lint
npm run test:unit
npm run build
```
""",
    "mobile": """# [Mobile Feature / Fix]
> **Lifecycle Status**: `📋 PLANNED`
> **Planner (Green Team)**: <Agent Name> (Timestamp)
> **Executor (Amber Team)**: Pending
> **Active Task**: None
> **Plan-ID**: `<slug>-YYYYMMDD-HHMM` (stamped at creation; filename-derived, never reused — cited in packets, defect rows, and stash listings so agents and users track the same plan)

## 1. Problem Context & Architectural Scope
[Flutter/Dart changes, offline sync, native integration]

## 2. Execution Sequence

| # | Task | Status | Who | Affected / Edited Files | Effort | Notes |
|:--|:---|:---:|:---:|:---|:---:|:---|
| 1 | Model / Repository Layer | `[PLANNED]` | Amber Team | • `lib/models/...`<br>• `lib/repositories/...` | ~20m | |
| 2 | UI / Screen Implementation | `[PLANNED]` | Amber Team | • `lib/screens/...`<br>• `lib/widgets/...` | ~25m | |
| 3 | Service / Native Integration | `[PLANNED]` | Amber Team | • `lib/services/...` | ~20m | |
| 4 | Tests, Lint & Build | `[PLANNED]` | Amber Team | • `test/...` | ~15m | |

## 3. Verification Plan
```bash
flutter analyze
flutter test
flutter build apk --release
```
""",
    "devops": """# [Infrastructure / DevOps Feature / Fix]
> **Lifecycle Status**: `📋 PLANNED`
> **Planner (Green Team)**: <Agent Name> (Timestamp)
> **Executor (Amber Team)**: Pending
> **Active Task**: None
> **Plan-ID**: `<slug>-YYYYMMDD-HHMM` (stamped at creation; filename-derived, never reused — cited in packets, defect rows, and stash listings so agents and users track the same plan)

## 1. Problem Context & Architectural Scope
[Networking, containers, CI/CD, orchestration]

## 2. Execution Sequence

| # | Task | Status | Who | Affected / Edited Files | Effort | Notes |
|:--|:---|:---:|:---:|:---|:---:|:---|
| 1 | Configuration Update | `[PLANNED]` | Amber Team | • `docker-compose.yml`<br>• `compose.yaml` | ~15m | |
| 2 | Proxy / Network / Secrets | `[PLANNED]` | Amber Team | • `traefik/...`<br>• `.env.example` | ~20m | |
| 3 | Deployment / CI Pipeline | `[PLANNED]` | Amber Team | • `.github/workflows/...` | ~15m | |
| 4 | Smoke Tests & Verification | `[PLANNED]` | Amber Team | • `scripts/...` | ~15m | |

## 3. Verification Plan
```bash
docker compose config
docker compose up -d
docker compose ps
curl -f http://localhost/health
```
""",
}


def generate_plan(root: Path, title: str, template: str, *, dry_run: bool, quiet: bool) -> bool:
    plan_path = root / WORKSPACE_DIR / PLAN_NAME
    if plan_path.exists():
        _log(f"[SKIP] {plan_path} already exists; use plan-greenteam (auto-stash) or plan-stash-greenteam first", quiet=quiet)
        return False

    body = PLAN_TEMPLATES.get(template, PLAN_TEMPLATES["generic"])
    if title:
        body = body.replace("[Feature / Fix Goal]", title, 1)
        for prefix in ["[Backend ", "[Frontend ", "[Mobile ", "[Infrastructure / DevOps "]:
            body = body.replace(prefix + "Feature / Fix]", f"{prefix}{title}]", 1)

    if dry_run:
        _log(f"[DRY-RUN] Would create {plan_path} (template={template})", quiet=quiet)
        return True
    return _write_text(plan_path, body, dry_run=False, quiet=quiet)


# ---------------------------------------------------------------------------
# Versions, backup/restore, uninstall
# ---------------------------------------------------------------------------

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
    other protocols' keys are never touched). Staleness becomes a --check
    output instead of a file diff."""
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
    return [root / WORKSPACE_DIR, _redteam_dir(root)]


def _backup_name() -> str:
    return f"{BACKUP_PREFIX}-{PROTOCOL_KEY}-{_now_str()}.tar.gz"


def backup_runtime(root: Path, *, dry_run: bool, quiet: bool, dest: str | None = None) -> Path | None:
    """Snapshot runtime dirs + a manifest into a root-level tar.gz bundle.
    The bundle is the archive Q61-a requires: uninstall reuses it, restore reads it."""
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
    target = Path(dest) if dest else root / _backup_name()
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
    # filter="data" (3.12+) blocks absolute paths + .. escapes in foreign bundles;
    # fallback for older interpreters without the backport.
    try:
        tar.extract(member, path=path, filter="data")
    except TypeError:
        tar.extract(member, path=path)


def restore_bundle(root: Path, bundle: str, *, force: bool, dry_run: bool, quiet: bool) -> int:
    """Restore files from a backup bundle. Merge by default (existing files kept);
    --force overwrites. Re-ensures gitignore + directives via the idempotent paths."""
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
    ensure_gitignore(root, dry_run=False, quiet=quiet, side="green")
    for name in detect_agent_files(root):
        inject_directives(root, [name], dry_run=False, quiet=quiet)
    stamp_version(root, dry_run=False, quiet=quiet)
    _log("[HINT] Directives/gitignore re-ensured; AGENTS.md creation still follows Q1-a on next init.",
         quiet=quiet)
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
    """Archive-first removal (Q61-a): backup bundle, drop runtime dirs, extract
    directives, drop own versions key. The `.protocol/` gitignore line is pruned
    only when `.protocol/` ends up empty. Re-run is a no-op (exit 0)."""
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
        if (GITIGNORE_LINE in lines and not (root / RUNTIME_ROOT).exists()):
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


# ---------------------------------------------------------------------------
# Status check
# ---------------------------------------------------------------------------

def status_check(root: Path, *, json_output: bool, quiet: bool) -> dict:
    workspace = root / WORKSPACE_DIR
    plan_path = workspace / PLAN_NAME
    gitignore = root / ".gitignore"
    gi_lines = _read_text(gitignore).splitlines() if gitignore.exists() else []

    legacy = root / LEGACY_WORKSPACE_DIR
    if legacy.exists():
        # stderr: stdout must stay pure JSON under --json.
        print(f"[WARN] legacy workspace {legacy} found (pre-Q39 name). "
              "Migrate: mv green_amber_red_teams green_amber_red_workspace, re-run init, "
              "drop the stale .gitignore line.", file=sys.stderr)
    pre_consolidation_ws = root / WORKSPACE_LEAF
    if pre_consolidation_ws.exists():
        print(f"[WARN] pre-consolidation runtime {pre_consolidation_ws} found. "
              f"Migrate: mv {WORKSPACE_LEAF} {WORKSPACE_DIR}, re-run init.", file=sys.stderr)
    legacy_redteam = _proto_dir(root) / REDTEAM_LEAF
    if _legacy_redteam_has_content(legacy_redteam):
        print(f"[WARN] pre-consolidation exchange {legacy_redteam} holds content. "
              f"Re-run init to migrate packet contents + customized config.yml to {REDTEAM_DIR}/.", file=sys.stderr)
    redteam = _redteam_dir(root)
    installed = read_versions(root).get(PROTOCOL_KEY)
    result: dict = {
        "code_version": __version__,
        "installed_version": installed,
        "version_ok": installed == __version__,
        "workspace_dir": str(workspace),
        "workspace_exists": workspace.exists(),
        "dual_presence": str(_dual_presence(root)) if _dual_presence(root) else None,
        "legacy_workspace_found": legacy.exists(),
        "pre_consolidation_runtime_found": pre_consolidation_ws.exists(),
        "archive_exists": (workspace / ARCHIVE_DIR).exists(),
        "stash_exists": (workspace / STASH_DIR).exists(),
        "gitignore_ok": GITIGNORE_LINE in gi_lines,
        "side": _read_config_side(redteam),
        "redteam_skeleton_ok": all((redteam / sub).exists() for sub in REDTEAM_SUBDIRS),
        "readme_exists": (workspace / README_NAME).exists(),
        "plan_exists": plan_path.exists(),
        "ledger_exists": (workspace / LEDGER_NAME).exists(),
        "agent_files": detect_agent_files(root),
        "directives_ok": any(_has_block(_read_text(root / f))
                             for f in detect_agent_files(root)),
        "directives_hint": (None if detect_agent_files(root) else
                            "No directive file found — run init and answer Q1-a to create AGENTS.md."),
        "project_type": detect_project_type(root),
    }

    if plan_path.exists():
        plan_text = _read_text(plan_path)
        statuses = re.findall(r"📋 PLANNED|⏳ IN_PROGRESS|✅ COMPLETED", plan_text)
        result["plan_status"] = statuses[0] if statuses else "unknown"
    else:
        result["plan_status"] = None

    if json_output:
        print(json.dumps(result, indent=2))
    else:
        _log("\n--- Traffic-Light Workspace Status ---", quiet=quiet)
        for key, value in result.items():
            _log(f"  {key}: {value}", quiet=quiet)
        _log("--------------------------------------\n", quiet=quiet)

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="init_teams.py",
        description="Bootstrap the Green/Amber/Red multi-agent teaming workspace in any repository. See root README install profiles (minimal/standard/full).",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be created without writing to disk.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing workspace README.md.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report whether the workspace is already initialized.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output --check results as JSON.",
    )
    parser.add_argument(
        "--init-plan",
        metavar="TITLE",
        help="Create an initial plan.md with the given title.",
    )
    parser.add_argument(
        "--template",
        choices=list(PLAN_TEMPLATES.keys()),
        default="generic",
        help="Plan template to use with --init-plan (default: generic).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress non-essential output.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Assume yes to prompts (e.g. create AGENTS.md). For scripted installs.",
    )
    parser.add_argument(
        "--side",
        choices=["green", "red"],
        default=None,
        help="Workspace side: green (plan workspace + exchange skeleton) or red "
             "(exchange skeleton only). Omitted: keep existing config, default green.",
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Snapshot runtime dirs + manifest into a root-level tar.gz bundle.",
    )
    parser.add_argument(
        "--restore",
        metavar="BUNDLE",
        help="Restore files from a backup bundle (merge; --force overwrites).",
    )
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Archive-first removal: backup bundle, drop runtime, extract directives.",
    )
    parser.add_argument(
        "--skip-backup",
        action="store_true",
        help="With --uninstall: destroy runtime without archiving (explicit data loss).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path.cwd()

    if args.check:
        status_check(root, json_output=args.json, quiet=args.quiet)
        return 0

    if args.backup:
        backup_runtime(root, dry_run=args.dry_run, quiet=args.quiet)
        return 0

    if args.restore:
        return restore_bundle(root, args.restore, force=args.force, dry_run=args.dry_run,
                              quiet=args.quiet)

    if args.uninstall:
        return uninstall_protocol(root, skip_backup=args.skip_backup, dry_run=args.dry_run,
                                  quiet=args.quiet)

    _warn_dual_presence(root)
    migrate_legacy_runtime(root, dry_run=args.dry_run, quiet=args.quiet)
    migrate_legacy_redteam(root, dry_run=args.dry_run, quiet=args.quiet)
    # Side resolves AFTER migration so a migrated customized config keeps its stamp.
    side = args.side or _read_config_side(_redteam_dir(root)) or "green"
    if side == "green":
        ensure_dirs(root, dry_run=args.dry_run, quiet=args.quiet)
        ensure_ledger(root, dry_run=args.dry_run, quiet=args.quiet)
        generate_readme(root, force=args.force, dry_run=args.dry_run, quiet=args.quiet)
    else:
        _log("[INFO] Red side: skipping plan workspace (exchange skeleton only).", quiet=args.quiet)
    ensure_gitignore(root, dry_run=args.dry_run, quiet=args.quiet, side=side)
    ensure_redteam(root, side=side, dry_run=args.dry_run, quiet=args.quiet)
    stamp_version(root, dry_run=args.dry_run, quiet=args.quiet)

    agent_files = detect_agent_files(root)
    if agent_files:
        inject_directives(root, agent_files, dry_run=args.dry_run, quiet=args.quiet)
    else:
        _maybe_create_directives(root, dry_run=args.dry_run, quiet=args.quiet, assume_yes=args.yes)

    if args.init_plan:
        generate_plan(root, args.init_plan, args.template, dry_run=args.dry_run, quiet=args.quiet)

    if not args.quiet and not args.json:
        print(f"\n✅ Traffic-Light team workspace is ready (side: {side}).")
        if side == "green":
            print(f"   Plan file: {root / WORKSPACE_DIR / PLAN_NAME}")
            print("   Next step: run `plan-greenteam <prompt>` or `execute-amberteam`.")
        else:
            print(f"   Exchange: {_redteam_dir(root)} (side: red)")
            print("   Next step: wait for an inbox packet, then run `test-redteam`.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
