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
import json
import os
import re
import sys
from pathlib import Path
from typing import Iterable

__version__ = "1.1.0"

WORKSPACE_DIR = "green_amber_red_workspace"
# Pre-Q39 runtime name. Frozen intentionally: detected (with mv hint), never created.
# NOTE: repo-wide renames must EXCLUDE this line.
LEGACY_WORKSPACE_DIR = "green_amber_red_teams"
ARCHIVE_DIR = "archive"
README_NAME = "README.md"
PLAN_NAME = "plan.md"
GITIGNORE_LINE = f"{WORKSPACE_DIR}/"
REDTEAM_SUBDIRS = ("redteam/inbox", "redteam/outbox", "redteam/inbox-archive", "redteam/outbox-archive")
CONFIG_NAME = "redteam/config.yml"


def _proto_dir_name() -> str:
    """Folder name of the boilerplate copy this script runs from (target workspaces may rename it)."""
    return Path(__file__).parent.name


def _packet_gitignore_lines() -> list[str]:
    proto = _proto_dir_name()
    return [f"{proto}/redteam/inbox/*",
            f"{proto}/redteam/outbox/*",
            f"{proto}/redteam/inbox-archive/*",
            f"{proto}/redteam/outbox-archive/*"]

AGENT_DIRECTIVE_FILES = [
    "AGENTS.md",
    "CLAUDE.md",
    ".cursorrules",
    "GEMINI.md",
]

DIRECTIVE_BLOCK = """\n\
### 🚦 Traffic-Light Team Collaboration Protocols

1. **Single Source of Truth**: All active implementation plans MUST live in `{workspace}/plan.md`.
2. **Auto-Archiving**: Before creating a new plan via `plan-greenteam`, if the current plan is `✅ COMPLETED`, move it to `{workspace}/archive/plan_YYYYMMDD_HHMM.md`.
3. **Core Shortcuts** (aliases accepted everywhere):
   - `plan-greenteam <prompt>` (`plan-green`): Green Team drafts a fresh `{workspace}/plan.md` (`📋 PLANNED`) detailing all affected files. Touches NO source code.
   - `review-greenteam` (`review-green`): Any agent/model playing planner QA-checks the plan (APPROVE → execute, REVISE → amend + re-review).
   - `execute-amberteam` (`exec-amber`): Amber Team inspects `{workspace}/plan.md`, summarizes it, and asks the user: *"Should the agent proceed with executing the plan and its tasks?"*
   - `review-amberteam` (`review-amber`): Green Team audits Amber Team's git diff and automated tests before clearing completion.
   - `send-redteam` (`send-red`): Green Team builds a timestamped packet in `redteam/inbox`, delivers it if the red workspace is reachable, else asks the user to carry it.
   - `review-redteam` (`review-red`): Green Team reads the defect report, records verdict PASS (stays `✅ COMPLETED`) or FAIL (reopen, back to `⏳ IN_PROGRESS`, Amber fixes, re-audit), then archives the packet.
   - `verify-green-amber-red-team`: Green Team audits configs, packet states, and versions, then asks whether to realign.
   - Red Team (own session): `test-redteam` (`test-red`) plans + tests a packet; `finish-redteam` (`finish-red`) writes the outbox verdict; `recheck-redteam` (`recheck-red`) revisits inbox + outbox and asks what to do next.
4. **Packets**: `redteam/inbox|outbox` hold ACTIVE timestamped packets (`packet_green|red_YYYYMMDD_HHMM`); `*-archive` holds inactive ones. New packets cross-ack the previous packet done; only acked-done packets archive. `redteam/config.yml` declares `side:` (green|red), reachability, and the redteam kill switch.
""".format(workspace=WORKSPACE_DIR)

WORKSPACE_README = """# 🚦 Traffic-Light Multi-Agent Teaming Workspace (`{workspace}/`)

This directory is strictly **gitignored** and serves as the single source of truth for active implementation plans and multi-agent coordination.

---

## 🧭 Team Personas & Commands

| Color / Team | Persona | Responsibilities | Key Commands |
|:---|:---|:---|:---|
| **🟢 Green Team** | **Architect / Planner** | Analyzes specs, maps affected files, writes `plan.md`, audits implementation, runs the Red Team handoff, and triages Red Team verdicts. **Touches NO production code.** | `plan-greenteam`<br>`review-greenteam`<br>`review-amberteam`<br>`send-redteam`<br>`review-redteam`<br>`verify-green-amber-red-team` |
| **🟠 Amber Team** | **Developer / Implementer** | Inspects the plan, confirms with user, implements code changes, runs tests, tracks task states, and fixes Red Team FAIL findings on re-open. | `execute-amberteam` |
| **🔴 Red Team** | **Independent QA / Auditor** | Executes black-box tests, regression suites, and adversarial audits in an isolated sandbox. Reads own `redteam/inbox`, writes own `redteam/outbox`. | `test-redteam`<br>`finish-redteam`<br>`recheck-redteam` |

---

## 🔄 End-to-End Collaboration Lifecycle

```
[User: plan-greenteam <prompt>] ──> [🟢 Green Team drafts {workspace}/plan.md (📋 PLANNED)]
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
    if dry_run:
        _log(f"[DRY-RUN] Would create directories: {workspace}, {archive}", quiet=quiet)
        return
    archive.mkdir(parents=True, exist_ok=True)
    _log(f"[CREATE] {workspace}", quiet=quiet)
    _log(f"[CREATE] {archive}", quiet=quiet)


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
    if not gitignore.exists():
        content = ""
    else:
        content = _read_text(gitignore)

    wanted = [GITIGNORE_LINE] if side == "green" else []
    wanted += _packet_gitignore_lines()
    if (root / "agents-boilerplate").exists():
        wanted.append("agents-boilerplate/")
    missing = [ln for ln in wanted if ln not in content.splitlines()]
    if not missing:
        _log("[OK] .gitignore already covers team workspace + packet contents", quiet=quiet)
        return False

    new_content = content.rstrip("\n") + "\n" + "\n".join(missing) + "\n"
    if dry_run:
        for ln in missing:
            _log(f"[DRY-RUN] Would append {ln!r} to {gitignore}", quiet=quiet)
        return True
    gitignore.write_text(new_content, encoding="utf-8")
    _log(f"[UPDATE] {gitignore}", quiet=quiet)
    return True


def _proto_dir(root: Path) -> Path:
    # The boilerplate copy lives beside this script in target workspaces.
    here = Path(__file__).parent
    if here.name == _proto_dir_name() and root in (*here.parents, here.parent):
        return here
    candidate = root / _proto_dir_name()
    return candidate if candidate.exists() else here


def _read_config_side(proto: Path) -> str | None:
    text = _read_text(proto / CONFIG_NAME)
    match = re.search(r"^side:\s*(green|red)\s*$", text, re.MULTILINE)
    return match.group(1) if match else None


def ensure_redteam(root: Path, *, side: str, dry_run: bool, quiet: bool) -> None:
    """Create the redteam/ exchange skeleton + config.yml (side-stamped) in the
    boilerplate copy. Packet contents are gitignored; skeleton + config are tracked."""
    proto = _proto_dir(root)
    for sub in REDTEAM_SUBDIRS:
        target = proto / sub
        if dry_run:
            _log(f"[DRY-RUN] Would create directory: {target}", quiet=quiet)
        else:
            target.mkdir(parents=True, exist_ok=True)
    _log(f"[CREATE] {proto / 'redteam'} skeleton", quiet=quiet)
    cfg = proto / CONFIG_NAME
    existing = _read_config_side(proto)
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
return_to: redteam/outbox
"""


def generate_readme(root: Path, *, force: bool, dry_run: bool, quiet: bool) -> bool:
    readme = root / WORKSPACE_DIR / README_NAME
    if readme.exists() and not force:
        _log(f"[SKIP] {readme} already exists (use --force to overwrite)", quiet=quiet)
        return False
    return _write_text(readme, WORKSPACE_README, dry_run=dry_run, quiet=quiet)


def detect_agent_files(root: Path) -> list[str]:
    return [name for name in AGENT_DIRECTIVE_FILES if (root / name).exists()]


def inject_directives(root: Path, agent_files: Iterable[str], *, dry_run: bool, quiet: bool) -> list[str]:
    changed: list[str] = []
    for name in agent_files:
        path = root / name
        existing = _read_text(path)
        if DIRECTIVE_BLOCK.strip() in existing.strip():
            _log(f"[SKIP] {name} already contains Traffic-Light directives", quiet=quiet)
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
        _log(f"[SKIP] {plan_path} already exists; use plan-greenteam or archive it first", quiet=quiet)
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
# Status check
# ---------------------------------------------------------------------------

def status_check(root: Path, *, json_output: bool, quiet: bool) -> dict:
    workspace = root / WORKSPACE_DIR
    plan_path = workspace / PLAN_NAME
    gitignore = root / ".gitignore"
    proto = _proto_dir(root)
    gi_lines = _read_text(gitignore).splitlines() if gitignore.exists() else []
    packet_lines = _packet_gitignore_lines()

    legacy = root / LEGACY_WORKSPACE_DIR
    if legacy.exists():
        # stderr: stdout must stay pure JSON under --json.
        print(f"[WARN] legacy workspace {legacy} found (pre-Q39 name). "
              "Migrate: mv green_amber_red_teams green_amber_red_workspace, re-run init, "
              "drop the stale .gitignore line.", file=sys.stderr)
    result: dict = {
        "workspace_dir": str(workspace),
        "workspace_exists": workspace.exists(),
        "legacy_workspace_found": legacy.exists(),
        "archive_exists": (workspace / ARCHIVE_DIR).exists(),
        "gitignore_ok": GITIGNORE_LINE in gi_lines,
        "packet_gitignore_ok": all(ln in gi_lines for ln in packet_lines),
        "side": _read_config_side(proto),
        "redteam_skeleton_ok": all((proto / sub).exists() for sub in REDTEAM_SUBDIRS),
        "readme_exists": (workspace / README_NAME).exists(),
        "plan_exists": plan_path.exists(),
        "ledger_exists": (workspace / LEDGER_NAME).exists(),
        "agent_files": detect_agent_files(root),
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
        "--side",
        choices=["green", "red"],
        default=None,
        help="Workspace side: green (plan workspace + exchange skeleton) or red "
             "(exchange skeleton only). Omitted: keep existing config, default green.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path.cwd()

    if args.check:
        status_check(root, json_output=args.json, quiet=args.quiet)
        return 0

    proto = _proto_dir(root)
    side = args.side or _read_config_side(proto) or "green"
    if side == "green":
        ensure_dirs(root, dry_run=args.dry_run, quiet=args.quiet)
        ensure_ledger(root, dry_run=args.dry_run, quiet=args.quiet)
        generate_readme(root, force=args.force, dry_run=args.dry_run, quiet=args.quiet)
    else:
        _log("[INFO] Red side: skipping plan workspace (exchange skeleton only).", quiet=args.quiet)
    ensure_gitignore(root, dry_run=args.dry_run, quiet=args.quiet, side=side)
    ensure_redteam(root, side=side, dry_run=args.dry_run, quiet=args.quiet)

    agent_files = detect_agent_files(root)
    if agent_files:
        inject_directives(root, agent_files, dry_run=args.dry_run, quiet=args.quiet)
    else:
        _log(
            "[INFO] No agent directive files detected (AGENTS.md, CLAUDE.md, .cursorrules, GEMINI.md). "
            "Inject Traffic-Light protocols manually into your agent rules.",
            quiet=args.quiet,
        )

    if args.init_plan:
        generate_plan(root, args.init_plan, args.template, dry_run=args.dry_run, quiet=args.quiet)

    if not args.quiet and not args.json:
        print(f"\n✅ Traffic-Light team workspace is ready (side: {side}).")
        if side == "green":
            print(f"   Plan file: {root / WORKSPACE_DIR / PLAN_NAME}")
            print("   Next step: run `plan-greenteam <prompt>` or `execute-amberteam`.")
        else:
            print(f"   Exchange: {_proto_dir(root) / 'redteam'} (side: red)")
            print("   Next step: wait for an inbox packet, then run `test-redteam`.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
