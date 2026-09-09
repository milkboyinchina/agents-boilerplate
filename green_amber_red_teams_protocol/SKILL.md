---
name: initialize-teams
description: Bootstraps the Traffic-Light Multi-Agent Teaming Protocol (Green Team Planner, Amber Team Executor, Red Team QA) in any repository or workspace. Use whenever the user asks to initialize, bootstrap, or set up green/amber/red teams, traffic light teaming, or agent collaboration workflows.
---

# Initialize Green, Amber, Red Teams Skill

Use this skill whenever the user says:
- *"Initialize green amber red teams"*
- *"Set up traffic light teaming method"*
- *"Bootstrap team workflow"*

---

## 🚦 Traffic-Light Teaming Protocol Overview

| Color / Team | Role | Description | Core Commands |
|:---|:---|:---|:---|
| **🟢 Green Team** | **Architect / Planner** | Analyzes requirements, maps affected files, writes `plan.md`, and conducts post-implementation audits. **Touches NO production code.** | `green-plan <prompt>`<br>`green-review` |
| **🟠 Amber Team** | **Developer / Implementer** | Inspects the plan, confirms with user, writes code, runs tests, and updates task statuses. | `amber-check`<br>`check-plan` |
| **🔴 Red Team** | **Independent QA / Auditor** | Operates in an isolated sandbox or test harness for adversarial audits and regression verification. | `check-redteam`<br>`send-redteam` |

---

## 🛠️ Autonomous Execution Steps

When invoked, the agent MUST execute these steps in order:

### Step 1: Locate the Toolkit

If the user has already copied the `green_amber_red_teams_protocol/` folder into the workspace, use it. Otherwise, create the equivalent structure manually.

### Step 2: Run the Bootstrap Script (Preferred Path)

If `green_amber_red_teams/init_teams.py` exists, run it deterministically:

```bash
python3 green_amber_red_teams_protocol/init_teams.py
```

Useful flags:
- `--dry-run` to preview changes.
- `--force` to overwrite the generated README.
- `--init-plan "Title" --template backend` to seed an initial plan.

### Step 3: Create Workspace Directory Structure (Fallback)

If the script is unavailable, create the directories manually:

```bash
mkdir -p green_amber_red_teams/archive
```

### Step 4: Ensure Workspace Gitignore

Prevent transient implementation plans from leaking into version control:

```bash
grep -qxF "green_amber_red_teams/" .gitignore 2>/dev/null || echo "green_amber_red_teams/" >> .gitignore
```

### Step 5: Create `green_amber_red_teams/README.md`

Write the standard local reference file documenting team personas, commands, and lifecycle states.

### Step 6: Inject Directives into Master Rules

Inspect which agent directive files exist in the project (`AGENTS.md`, `CLAUDE.md`, `.cursorrules`, `GEMINI.md`) and append the standard teaming directives without duplicating existing entries.

---

## 📋 Required Directives to Inject

```markdown
### 🚦 Traffic-Light Team Collaboration Protocols

1. **Single Source of Truth**: All active implementation plans MUST live in `green_amber_red_teams/plan.md`.
2. **Auto-Archiving**: Before creating a new plan via `green-plan`, if the current plan is `✅ COMPLETED`, move it to `green_amber_red_teams/archive/plan_YYYYMMDD_HHMM.md`.
3. **Core Shortcuts**:
   - `green-plan <prompt>`: Green Team drafts a fresh `green_amber_red_teams/plan.md` (`📋 PLANNED`). Touches NO source code.
   - `amber-check`: Amber Team inspects `green_amber_red_teams/plan.md`, summarizes it, and asks user: *"Should the agent proceed with executing the plan and its tasks?"*
   - `check-plan`: Reports current lifecycle status, task completion states, and active blockers.
   - `green-review`: Green Team audits Amber Team's git diff and automated tests before clearing completion.
   - `send-redteam`: Packages recent changes for independent Red Team sandbox verification.
   - `check-redteam`: Reads Red Team defect reports and presents an actionable remediation matrix.
```

---

## ✅ Completion Criteria

Before responding to the user, verify:
- [ ] `green_amber_red_teams/` exists.
- [ ] `green_amber_red_teams/archive/` exists.
- [ ] `.gitignore` contains `green_amber_red_teams/`.
- [ ] `green_amber_red_teams/README.md` documents personas, commands, and lifecycle.
- [ ] At least one master agent directive file references the 6 Traffic-Light shortcuts.
