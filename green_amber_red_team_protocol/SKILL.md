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

## 🚦 Traffic-Light Teaming Protocol Overview (12 commands, aliases accepted)

| Color / Team | Role | Description | Core Commands |
|:---|:---|:---|:---|
| **🟢 Green Team** | **Architect / Planner** | Plans, parks/resumes plans, QA-checks plans (any agent/model), audits implementation, bridges Red Team packets, triages verdicts, audits drift. **Touches NO production code.** | `plan-greenteam` (`plan-green`)<br>`plan-stash-greenteam` (`stash-green`)<br>`plan-resume-greenteam` (`resume-green`)<br>`review-greenteam` (`review-green`)<br>`review-amberteam` (`review-amber`)<br>`send-redteam` (`send-red`)<br>`review-redteam` (`review-red`)<br>`verify-green-amber-red-team` |
| **🟠 Amber Team** | **Developer / Implementer** | Confirms with user, writes code, runs tests, updates task statuses, fixes Red FAIL findings on re-open. | `execute-amberteam` (`exec-amber`) |
| **🔴 Red Team** | **Independent QA / Auditor** | Reads own `.protocol/redteam/inbox`, tests in an isolated sandbox, writes own `.protocol/redteam/outbox`. Never touches source. | `test-redteam` (`test-red`)<br>`finish-redteam` (`finish-red`)<br>`recheck-redteam` (`recheck-red`) |

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
- `--side green|red` to stamp `.protocol/redteam/config.yml` (omitted: keep existing, default green).

### Step 3: Create Workspace Directory Structure (Fallback)

If the script is unavailable, create the directories manually:

```bash
mkdir -p .protocol/green_amber_red_workspace/archive .protocol/green_amber_red_workspace/stash
mkdir -p .protocol/redteam/{inbox,outbox,inbox-archive,outbox-archive}
```

### Step 4: Ensure Workspace Gitignore

Prevent transient plans and packet contents from leaking into version control:

```bash
grep -qxF ".protocol/" .gitignore 2>/dev/null || echo ".protocol/" >> .gitignore
```

### Step 5: Create `.protocol/green_amber_red_workspace/README.md`

Write the standard local reference file documenting team personas, commands, and lifecycle states.

### Step 6: Inject Directives into Master Rules

Inspect which agent directive files exist in the project (`AGENTS.md`, `CLAUDE.md`, `.cursorrules`, `GEMINI.md`) and append the standard teaming directives without duplicating existing entries. If none exists, the bootstrap asks (Q1-a) to create `AGENTS.md` — same idempotency guarantees (`--yes` assumes yes for scripted installs).

---

## 📋 Required Directives to Inject

```markdown
### 🚦 Traffic-Light Team Collaboration Protocols

1. **Single Source of Truth**: All active implementation plans MUST live in `.protocol/green_amber_red_workspace/plan.md`. Every plan carries a `Plan-ID: <slug>-YYYYMMDD-HHMM` header (filename-derived, never reused) — cited in packets, defect rows, and stash listings so agent and user track the same plan.
2. **Auto-Archiving**: Before creating a new plan via `plan-greenteam`, if the current plan is `✅ COMPLETED`, move it to `.protocol/green_amber_red_workspace/archive/plan_YYYYMMDD_HHMM.md`. If it is unfinished (`📋 PLANNED` / `⏳ IN_PROGRESS`), auto-stash it to `.protocol/green_amber_red_workspace/stash/plan_<plan-id>.md` instead — announce the Plan ID + restore command. Mid-flight work (Amber executing, Red packet open): warn with both Plan IDs and require explicit confirmation first.
3. **Core Shortcuts** (aliases accepted everywhere):
   - `plan-greenteam <prompt>` (`plan-green`): Green Team drafts a fresh `.protocol/green_amber_red_workspace/plan.md` (`📋 PLANNED`, fresh Plan-ID). Touches NO source code.
   - `plan-stash-greenteam` (`stash-green`): Park the active plan to `stash/` (status + progress preserved verbatim); workspace returns to no-active-plan.
   - `plan-resume-greenteam <plan-id>` (`resume-green`): List `stash/` when no ID is given; restore the chosen plan to `plan.md` intact (a different active unfinished plan stashes first).
   - `review-greenteam` (`review-green`): Any planner QA-checks the plan (APPROVE → execute, REVISE → amend).
   - `execute-amberteam` (`exec-amber`): Amber Team inspects `.protocol/green_amber_red_workspace/plan.md`, summarizes it, and asks user: *"Should the agent proceed with executing the plan and its tasks?"*
   - `review-amberteam` (`review-amber`): Green Team audits Amber Team's git diff and automated tests before clearing completion.
   - `send-redteam` (`send-red`): Green Team builds a timestamped packet, delivers if reachable, else asks the user to carry it.
   - `review-redteam` (`review-red`): Green Team records verdict PASS (done) or FAIL (reopen → fix → re-audit), transcribes findings into `defects.md` (`OPEN`, stamped, single-writer rule), then archives the packet.
   - `verify-green-amber-red-team`: Green Team audits configs, packets, versions, then asks whether to realign.
   - Red Team (own session): `test-redteam` (`test-red`), `finish-redteam` (`finish-red`), `recheck-redteam` (`recheck-red`).
4. **Packets**: `.protocol/redteam/inbox|outbox` active (`packet_green|red_YYYYMMDD_HHMM`), archives inactive; cross-ack required; `.protocol/redteam/config.yml` declares `side:` + reachability.
```

---

## ✅ Completion Criteria

Before responding to the user, verify:
- [ ] `.protocol/green_amber_red_workspace/` exists (green side).
- [ ] `.protocol/green_amber_red_workspace/archive/` exists (green side).
- [ ] `.protocol/green_amber_red_workspace/stash/` exists (green side).
- [ ] `.gitignore` contains the single `.protocol/` line.
- [ ] `.protocol/redteam/` skeleton + `config.yml` (`side:` stamped) exist.
- [ ] `.protocol/green_amber_red_workspace/README.md` documents personas, commands, and lifecycle.
- [ ] At least one master agent directive file references the 12 Traffic-Light commands.
- [ ] `defects.md` exists green-side (from template, never overwritten); rows stamped; no red-side ledger writes.
