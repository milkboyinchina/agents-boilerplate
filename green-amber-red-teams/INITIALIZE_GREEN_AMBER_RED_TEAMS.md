# 🚦 Traffic-Light Teaming Protocol Initialization Guide

> **Quick Start**: In any new repo, copy the `green-amber-red-teams/` folder and run:
> ```bash
> python3 green-amber-red-teams/init_teams.py
> ```
> Then tell your AI assistant: *"Read `green-amber-red-teams/INITIALIZE_GREEN_AMBER_RED_TEAMS.md` and set up the teams."*

This guide provides a standardized instruction set for any AI coding assistant to bootstrap the **Traffic-Light Multi-Agent Teaming Protocol (Green / Amber / Red)** into any codebase or workspace.

---

## 🧭 Why Traffic Light?

| Signal | Color / Team | Functional Persona | Operational Meaning |
|:---|:---|:---|:---|
| 🟢 | **Green Team** | **Architect / Planner** | *"Green = Go Plan"* — Evaluates specs, maps affected files, drafts `plan.md`, and audits code. **Touches NO production code.** |
| 🟠 | **Amber Team** | **Developer / Executor** | *"Amber = Caution / In-Progress"* — Inspects the plan, confirms with user, writes code, runs tests, and logs task states. |
| 🔴 | **Red Team** | **Independent QA / Auditor** | *"Red = Stop / Attack & Verify"* — Tests from an isolated sandbox or outside environment with zero developer bias. |

---

## 🛠️ Step-by-Step Initialization Protocol

### Step 1: Copy the Toolkit

Copy the `green-amber-red-teams/` folder into the target repository root:

```bash
cp -r /path/to/agents-boilerplate/green-amber-red-teams ./
```

### Step 2: Run the Bootstrap Script

```bash
python3 green-amber-red-teams/init_teams.py
```

This creates:
- `green_amber_red_teams/` directory
- `green_amber_red_teams/archive/` subdirectory
- `green_amber_red_teams/README.md`
- Appends `green_amber_red_teams/` to `.gitignore`
- Appends Traffic-Light directives to `AGENTS.md`, `CLAUDE.md`, `.cursorrules`, or `GEMINI.md` if present

Use `--dry-run` to preview changes without writing:

```bash
python3 green-amber-red-teams/init_teams.py --dry-run
```

### Step 3: Seed an Initial Plan (Optional)

```bash
python3 green-amber-red-teams/init_teams.py --init-plan "Add user authentication" --template backend
```

Available templates: `generic`, `backend`, `frontend`, `mobile`, `devops`.

---

## 🚀 Command Reference

### `green-plan <prompt>`
- **Role**: 🟢 Green Team
- Creates or overwrites `green_amber_red_teams/plan.md` with status `📋 PLANNED`.
- Auto-archives any existing `✅ COMPLETED` plan to `green_amber_red_teams/archive/plan_YYYYMMDD_HHMM.md`.
- Lists exact affected files and effort estimates in a task table.
- **Does NOT modify source code.**

### `amber-check`
- **Role**: 🟠 Amber Team
- Reads `green_amber_red_teams/plan.md`.
- Evaluates dependencies and affected files.
- Outputs a concise executive summary.
- **Asks user:** *"Should the agent proceed with executing the plan and its tasks?"*
- Upon confirmation, switches header to `⏳ IN_PROGRESS` and begins coding.

### `check-plan`
- **Role**: Universal Progress Inspector
- Inspects `green_amber_red_teams/plan.md`.
- Summarizes overall status, active task, and any `[ERROR]`, `[INCOMPLETE]`, or `[BLOCKED]` items.

### `green-review`
- **Role**: 🟢 Green Team (Auditor)
- Runs when Amber Team finishes coding.
- Inspects `git diff`, static analysis, and unit tests.
- If clean: updates plan status to `✅ COMPLETED` and prompts user to dispatch Red Team.
- If defects found: flags tasks as `[ERROR]` or `[INCOMPLETE]` with remediation instructions.

### `send-redteam`
- **Role**: 🔴 Red Team Handoff
- Packages recent changes, OpenAPI schemas, compiled binaries, and updates the QA sandbox.

### `check-redteam`
- **Role**: 🔴 Red Team Inspection
- Reads independent test reports and displays a defect remediation matrix.

---

## 📋 Standard `green_amber_red_teams/plan.md` Template

When `green-plan` creates a plan, it MUST follow this format:

```markdown
# [Feature / Fix Goal]
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
[Exact commands to run to prove correctness]
```

---

## ✅ Initialization Verification Checklist

- [ ] Folder `green_amber_red_teams/` exists in project root.
- [ ] Subfolder `green_amber_red_teams/archive/` exists.
- [ ] `.gitignore` contains `green_amber_red_teams/`.
- [ ] `green_amber_red_teams/README.md` documents team personas and commands.
- [ ] Master agent directives reference the 6 shortcuts: `green-plan`, `amber-check`, `check-plan`, `green-review`, `send-redteam`, `check-redteam`.

---

## 🤝 Coexistence with Session Handoff Rules

This protocol is **complementary** to per-session handoff rules (e.g., OpenCode's `handoff.md`).

- `handoff.md` preserves context when a single session is interrupted.
- `green-amber-red-teams` structures planning and execution across multiple agents and sessions.

Both can be active in the same workspace without conflict.
