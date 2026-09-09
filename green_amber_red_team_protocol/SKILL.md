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

## 🚦 Traffic-Light Teaming Protocol Overview (10 commands, aliases accepted)

| Color / Team | Role | Description | Core Commands |
|:---|:---|:---|:---|
| **🟢 Green Team** | **Architect / Planner** | Plans, QA-checks plans (any agent/model), audits implementation, bridges Red Team packets, triages verdicts, audits drift. **Touches NO production code.** | `plan-greenteam` (`plan-green`)<br>`review-greenteam` (`review-green`)<br>`review-amberteam` (`review-amber`)<br>`send-redteam` (`send-red`)<br>`review-redteam` (`review-red`)<br>`verify-green-amber-red-team` |
| **🟠 Amber Team** | **Developer / Implementer** | Confirms with user, writes code, runs tests, updates task statuses, fixes Red FAIL findings on re-open. | `execute-amberteam` (`exec-amber`) |
| **🔴 Red Team** | **Independent QA / Auditor** | Reads own `redteam/inbox`, tests in an isolated sandbox, writes own `redteam/outbox`. Never touches source. | `test-redteam` (`test-red`)<br>`finish-redteam` (`finish-red`)<br>`recheck-redteam` (`recheck-red`) |

---

## 🛠️ Autonomous Execution Steps

When invoked, the agent MUST execute these steps in order:

### Step 1: Locate the Toolkit

If the user has already copied the `green_amber_red_team_protocol/` folder into the workspace, use it. Otherwise, create the equivalent structure manually.

### Step 2: Run the Bootstrap Script (Preferred Path)

If `green_amber_red_team_protocol/init_teams.py` exists, run it deterministically:

```bash
# Green+amber side (default)
python3 green_amber_red_team_protocol/init_teams.py

# Red side (separate workspace: exchange skeleton only)
python3 green_amber_red_team_protocol/init_teams.py --side red
```

Useful flags:
- `--dry-run` to preview changes.
- `--force` to overwrite the generated README.
- `--init-plan "Title" --template backend` to seed an initial plan (green side).
- `--side green|red` to stamp `redteam/config.yml` (omitted: keep existing, default green).

### Step 3: Create Workspace Directory Structure (Fallback)

If the script is unavailable, create the directories manually:

```bash
mkdir -p green_amber_red_workspace/archive
mkdir -p green_amber_red_team_protocol/redteam/{inbox,outbox,inbox-archive,outbox-archive}
```

### Step 4: Ensure Workspace Gitignore

Prevent transient plans and packet contents from leaking into version control:

```bash
for line in "green_amber_red_workspace/" \
  "green_amber_red_team_protocol/redteam/inbox/*" \
  "green_amber_red_team_protocol/redteam/outbox/*" \
  "green_amber_red_team_protocol/redteam/inbox-archive/*" \
  "green_amber_red_team_protocol/redteam/outbox-archive/*"; do
  grep -qxF "$line" .gitignore 2>/dev/null || echo "$line" >> .gitignore
done
```

### Step 5: Create `green_amber_red_workspace/README.md`

Write the standard local reference file documenting team personas, commands, and lifecycle states.

### Step 6: Inject Directives into Master Rules

Inspect which agent directive files exist in the project (`AGENTS.md`, `CLAUDE.md`, `.cursorrules`, `GEMINI.md`) and append the standard teaming directives without duplicating existing entries.

---

## 📋 Required Directives to Inject

```markdown
### 🚦 Traffic-Light Team Collaboration Protocols

1. **Single Source of Truth**: All active implementation plans MUST live in `green_amber_red_workspace/plan.md`.
2. **Auto-Archiving**: Before creating a new plan via `plan-greenteam`, if the current plan is `✅ COMPLETED`, move it to `green_amber_red_workspace/archive/plan_YYYYMMDD_HHMM.md`.
3. **Core Shortcuts** (aliases accepted everywhere):
   - `plan-greenteam <prompt>` (`plan-green`): Green Team drafts a fresh `green_amber_red_workspace/plan.md` (`📋 PLANNED`). Touches NO source code.
   - `review-greenteam` (`review-green`): Any planner QA-checks the plan (APPROVE → execute, REVISE → amend).
   - `execute-amberteam` (`exec-amber`): Amber Team inspects `green_amber_red_workspace/plan.md`, summarizes it, and asks user: *"Should the agent proceed with executing the plan and its tasks?"*
   - `review-amberteam` (`review-amber`): Green Team audits Amber Team's git diff and automated tests before clearing completion.
   - `send-redteam` (`send-red`): Green Team builds a timestamped packet, delivers if reachable, else asks the user to carry it.
   - `review-redteam` (`review-red`): Green Team records verdict PASS (done) or FAIL (reopen → fix → re-audit), transcribes findings into `defects.md` (`OPEN`, stamped, single-writer rule), then archives the packet.
   - `verify-green-amber-red-team`: Green Team audits configs, packets, versions, then asks whether to realign.
   - Red Team (own session): `test-redteam` (`test-red`), `finish-redteam` (`finish-red`), `recheck-redteam` (`recheck-red`).
4. **Packets**: `redteam/inbox|outbox` active (`packet_green|red_YYYYMMDD_HHMM`), archives inactive; cross-ack required; `redteam/config.yml` declares `side:` + reachability.
```

---

## ✅ Completion Criteria

Before responding to the user, verify:
- [ ] `green_amber_red_workspace/` exists (green side).
- [ ] `green_amber_red_workspace/archive/` exists (green side).
- [ ] `.gitignore` contains `green_amber_red_workspace/` + the four packet-contents lines.
- [ ] `redteam/` skeleton + `config.yml` (`side:` stamped) exist in the protocol copy.
- [ ] `green_amber_red_workspace/README.md` documents personas, commands, and lifecycle.
- [ ] At least one master agent directive file references the 10 Traffic-Light commands.
- [ ] `defects.md` exists green-side (from template, never overwritten); rows stamped; no red-side ledger writes.
