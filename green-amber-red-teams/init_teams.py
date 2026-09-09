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

__version__ = "1.0.0"

WORKSPACE_DIR = "green_amber_red_teams"
ARCHIVE_DIR = "archive"
README_NAME = "README.md"
PLAN_NAME = "plan.md"
GITIGNORE_LINE = f"{WORKSPACE_DIR}/"

AGENT_DIRECTIVE_FILES = [
    "AGENTS.md",
    "CLAUDE.md",
    ".cursorrules",
    "GEMINI.md",
]

DIRECTIVE_BLOCK = """\n\
### 🚦 Traffic-Light Team Collaboration Protocols

1. **Single Source of Truth**: All active implementation plans MUST live in `{workspace}/plan.md`.
2. **Auto-Archiving**: Before creating a new plan via `green-plan`, if the current plan is `✅ COMPLETED`, move it to `{workspace}/archive/plan_YYYYMMDD_HHMM.md`.
3. **Core Shortcuts**:
   - `green-plan <prompt>`: Green Team drafts a fresh `{workspace}/plan.md` (`📋 PLANNED`) detailing all affected files. Touches NO source code.
   - `amber-check`: Amber Team inspects `{workspace}/plan.md`, summarizes it, and asks the user: *"Should the agent proceed with executing the plan and its tasks?"*
   - `check-plan`: Inspects and reports current progress, task statuses, and active blockers from `{workspace}/plan.md`.
   - `green-review`: Green Team audits Amber Team's git diff and automated tests before clearing completion.
   - `send-redteam`: Packages recent changes, schemas, and binaries for independent Red Team sandbox verification.
   - `check-redteam`: Reads Red Team defect reports and presents an actionable remediation matrix.
""".format(workspace=WORKSPACE_DIR)

WORKSPACE_README = """# 🚦 Traffic-Light Multi-Agent Teaming Workspace (`{workspace}/`)

This directory is strictly **gitignored** and serves as the single source of truth for active implementation plans and multi-agent coordination.

---

## 🧭 Team Personas & Commands

| Color / Team | Persona | Responsibilities | Key Commands |
|:---|:---|:---|:---|
| **🟢 Green Team** | **Architect / Planner** | Analyzes specs, maps affected files, writes `plan.md`, and performs post-implementation audits. **Touches NO production code.** | `green-plan <prompt>`<br>`green-review` |
| **🟠 Amber Team** | **Developer / Implementer** | Inspects the plan, confirms with user, implements code changes, runs tests, and tracks task states. | `amber-check`<br>`check-plan` |
| **🔴 Red Team** | **Independent QA / Auditor** | Executes black-box tests, regression suites, and adversarial audits in an isolated sandbox. | `check-redteam`<br>`send-redteam` |

---

## 🔄 End-to-End Collaboration Lifecycle

```
[User: green-plan <prompt>] ──> [🟢 Green Team drafts {workspace}/plan.md (📋 PLANNED)]
                                               │
[User: amber-check] ─────────> [🟠 Amber Team reviews feasibility & asks to proceed]
                                               │
                                 [User confirms: "proceed"]
                                               │
                                 [🟠 Amber Team executes code & marks tasks [COMPLETED]]
                                               │
[User: green-review] ────────> [🟢 Green Team verifies git diff & automated tests]
                                               │
                                 [Audit clean? ──Yes──> Status: ✅ COMPLETED]
                                               │
[User: send-redteam] ────────> [🔴 Red Team receives fresh artifacts for sandbox audit]
                                               │
[User: check-redteam] ───────> [Inspect independent test reports & defect matrix]
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


def ensure_gitignore(root: Path, *, dry_run: bool, quiet: bool) -> bool:
    gitignore = root / ".gitignore"
    if not gitignore.exists():
        content = ""
    else:
        content = _read_text(gitignore)

    if GITIGNORE_LINE in content.splitlines():
        _log(f"[OK] .gitignore already contains {GITIGNORE_LINE}", quiet=quiet)
        return False

    new_content = content.rstrip("\n") + "\n" + GITIGNORE_LINE + "\n"
    if dry_run:
        _log(f"[DRY-RUN] Would append {GITIGNORE_LINE!r} to {gitignore}", quiet=quiet)
        return True
    gitignore.write_text(new_content, encoding="utf-8")
    _log(f"[UPDATE] {gitignore}", quiet=quiet)
    return True


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
        _log(f"[SKIP] {plan_path} already exists; use green-plan or archive it first", quiet=quiet)
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

    result: dict = {
        "workspace_dir": str(workspace),
        "workspace_exists": workspace.exists(),
        "archive_exists": (workspace / ARCHIVE_DIR).exists(),
        "gitignore_ok": GITIGNORE_LINE in _read_text(gitignore).splitlines() if gitignore.exists() else False,
        "readme_exists": (workspace / README_NAME).exists(),
        "plan_exists": plan_path.exists(),
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
        description="Bootstrap the Green/Amber/Red multi-agent teaming workspace in any repository.",
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
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path.cwd()

    if args.check:
        status_check(root, json_output=args.json, quiet=args.quiet)
        return 0

    ensure_dirs(root, dry_run=args.dry_run, quiet=args.quiet)
    ensure_gitignore(root, dry_run=args.dry_run, quiet=args.quiet)
    generate_readme(root, force=args.force, dry_run=args.dry_run, quiet=args.quiet)

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
        print("\n✅ Traffic-Light team workspace is ready.")
        print(f"   Plan file: {root / WORKSPACE_DIR / PLAN_NAME}")
        print(f"   Next step: run `green-plan <prompt>` or `amber-check`.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
