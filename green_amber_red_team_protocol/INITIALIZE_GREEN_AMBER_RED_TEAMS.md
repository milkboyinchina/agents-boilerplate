# 🚦 Traffic-Light Teaming Protocol Initialization Guide

> **Quick Start**: In any new repo, copy the `green_amber_red_team_protocol/` folder and run:
> ```bash
> python3 green_amber_red_team_protocol/init_teams.py
> ```
> Then tell your AI assistant: *"Read `green_amber_red_team_protocol/INITIALIZE_GREEN_AMBER_RED_TEAMS.md` and set up the teams."*

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

Copy the `green_amber_red_team_protocol/` folder into the target repository root:

```bash
cp -r /path/to/agents-boilerplate/green_amber_red_team_protocol ./
```

### Step 2: Run the Bootstrap Script

```bash
# Green+amber side (plan workspace + redteam exchange skeleton)
python3 green_amber_red_team_protocol/init_teams.py

# Red side (in the SEPARATE red workspace: exchange skeleton only, no plan dirs)
python3 green_amber_red_team_protocol/init_teams.py --side red
```

This creates (green side):
- `green_amber_red_workspace/` directory
- `green_amber_red_workspace/archive/` subdirectory
- `green_amber_red_workspace/README.md`
- `redteam/` exchange skeleton (inbox/outbox + archives) + `redteam/config.yml` (`side: green`)
- Appends `green_amber_red_workspace/` and `redteam/` packet contents to `.gitignore`
- Appends Traffic-Light directives to `AGENTS.md`, `CLAUDE.md`, `.cursorrules`, or `GEMINI.md` if present

Red side (`--side red`): only the `redteam/` skeleton + `config.yml` (`side: red`) + brief/report templates + packet gitignore lines. Commands refuse when run on the wrong side (each refusal names the correct workspace).

Use `--dry-run` to preview changes without writing:

```bash
python3 green_amber_red_team_protocol/init_teams.py --dry-run
```

### Step 3: Seed an Initial Plan (Optional)

```bash
python3 green_amber_red_team_protocol/init_teams.py --init-plan "Add user authentication" --template backend
```

Available templates: `generic`, `backend`, `frontend`, `mobile`, `devops`.

---

## 🚀 Command Reference (aliases accepted everywhere)

### `plan-greenteam <prompt>` (alias `plan-green`)
- **Role**: 🟢 Green Team
- Creates or overwrites `green_amber_red_workspace/plan.md` with status `📋 PLANNED`.
- Auto-archives any existing `✅ COMPLETED` plan to `green_amber_red_workspace/archive/plan_YYYYMMDD_HHMM.md`.
- Overwriting a `📋 PLANNED` or `⏳ IN_PROGRESS` plan discards live work: warn the user and require explicit confirmation first.
- Lists exact affected files and effort estimates in a task table.
- **Does NOT modify source code.**

### `review-greenteam` (alias `review-green`)
- **Role**: 🟢 Green Team — any agent or model playing planner (this is what keeps planning agent-agnostic across sessions and models).
- QA-checks the plan: is it good or bad, revise or not?
- **APPROVE** → Amber may execute. **REVISE** → Green amends the plan, then re-reviews. Loop until APPROVE.

### `execute-amberteam` (alias `exec-amber`)
- **Role**: 🟠 Amber Team
- Reads `green_amber_red_workspace/plan.md`.
- Evaluates dependencies and affected files.
- Outputs a concise executive summary.
- **Asks user:** *"Should the agent proceed with executing the plan and its tasks?"* — the confirmation gate survives the rename; "execute" never means "skip approval".
- Upon confirmation, switches header to `⏳ IN_PROGRESS` and begins coding.

### `review-amberteam` (alias `review-amber`)
- **Role**: 🟢 Green Team (Auditor)
- Runs when Amber Team finishes coding.
- Inspects `git diff`, static analysis, and unit tests.
- If clean: updates plan status to `✅ COMPLETED` and prompts user to dispatch Red Team.
- If defects found: flags tasks as `[ERROR]` or `[INCOMPLETE]` with remediation instructions.

### `send-redteam` (alias `send-red`)
- **Role**: 🟢 Green Team (audit-gate handoff)
- Runs after `review-amberteam` passes and the user confirms dispatching Red Team.
- If `redteam_enabled: false` in `redteam/config.yml`: reply "red team is not available" and stop.
- Builds a timestamped packet `packet_green_YYYYMMDD_HHMM/` in this workspace's `redteam/inbox/`: brief (stamped), artifacts, defect-report template, plan-version citation, cross-ack of the previous packet done (or explicitly still-open).
- New packet per mission cycle; append only for same-cycle top-ups. Always inform the user either way.
- Delivery: `redteam_accessible: true` → copy to the red workspace's `redteam/inbox/`; `false` → ask the user to carry it (brief stamps `return_to:` so the path is concrete).
- Amber Team stays out of the QA loop: the team that passed review hands off, the team that wrote the code does not.

### Red Team commands (own session, own workspace copy, `side: red`)

Red Team testing happens in an **isolated session** with zero developer bias. Red works only inside its own `redteam/` folders and never touches source.

### `test-redteam` (alias `test-red`)
- **Role**: 🔴 Red Team
- Reads own `redteam/inbox` latest packet, makes a test plan, runs black-box tests.
- Sequential dual-red (high-risk opt-in): B reads A's outbox findings from its own inbox copy, then tests adversarially against them too.

### `finish-redteam` (alias `finish-red`)
- **Role**: 🔴 Red Team
- Writes the verdict packet `packet_red_YYYYMMDD_HHMM/` to own `redteam/outbox/`: filled defect report (PASS/FAIL + matrix), cross-ack of the inbound green packet done, author-tagged sections (append, never rewrite prior findings).
- Reachable workspace: Green pulls it at `review-redteam`. Air-gap: hand it to the carrier for `return_to:`.

### `recheck-redteam` (alias `recheck-red`)
- **Role**: 🔴 Red Team
- Reads own inbox + outbox, diffs inbox findings against the packet's open-defects snapshot (never duplicate an already-reported defect), then asks the user: plan a retest, or take other action? Never auto-starts a new test cycle.

### Defect ledger (`green_amber_red_workspace/defects.md`, green side)

Single-writer-per-field, append-only history. **Red writes findings** — via defect reports only, never this file. **Green transcribes** findings here at `review-redteam` and owns every fix-lifecycle field (`ACKED → IN_FIX → FIXED → VERIFIED → CLOSED`, each stamped who + when + packet ref). Amber's fixes flip linked task rows; Green reconciles. Reopening a `CLOSED` defect creates a NEW row referencing the old ID. Template: `templates/defect_ledger.md`; created empty by init (never overwritten). Red-side visibility comes through per-packet open-defect snapshots — `recheck-redteam` diffs before reporting so sequential teams never duplicate. IDs: `BUG-YYYYMMDD-NNN` + severity.

### `review-redteam` (alias `review-red`)
- **Role**: 🟢 Green Team inspection (Red Team keeps no narrative control)
- Collects the report: reachable workspace → copy red `outbox` packet into green `outbox`; air-gap → user drops it there; validate the brief stamp on intake.
- Displays the defect remediation matrix and records the verdict (see below).
- Transcribes every finding into `defects.md` (`OPEN`, stamped found-by/at + packet ref) and reconciles Amber task rows on fix (`ACKED → IN_FIX → FIXED → VERIFIED → CLOSED`, every transition stamped).
- Then archives inbox + outbox packets to their `*-archive` folders (only acked-done packets; unacked → warn + ask).

### Red Team verdict handling

- **PASS** → plan stays `✅ COMPLETED`. Packets archived. Next `plan-greenteam` archives the plan normally.
- **FAIL** → Green Team reopens affected tasks as `[ERROR]` or `[INCOMPLETE]`, flips Lifecycle Status back to `⏳ IN_PROGRESS`, and hands to Amber Team for fixes. Amber fixes, `review-amberteam` re-audits, and the Red Team gate (`send-redteam` → tests → `finish-redteam` → `review-redteam`) re-runs.
- `✅ COMPLETED` means *implementation complete and Green-audited*; the Red Team gate is a separate verdict on top, never a silent second completion.

### `verify-green-amber-red-team` (no alias — always spelled out)
- **Role**: 🟢 Green Team drift audit. Convention checklist (no CLI yet):
- Verify Amber side: plan schema, directive blocks match boilerplate version, CLI `--check` green.
- Verify Red side: brief version vs templates, packet states (staged-undelivered, delivered-no-report + age, archived-complete), wrong-side evidence (wrong-infix packets), `config.yml` side/reachability sanity.
- Verify ledger: findings without IDs, transitions missing who/when/packet stamps, `FIXED`-but-never-`VERIFIED` aging, red-side ledger writes (forbidden — findings travel via reports only).
- Present a drift matrix and ask the user (`Q1-a` style): realign? Realignment = re-issue brief, re-inject directives, archive orphans — only on approval.

### Red Team packet exchange (`redteam/`)

Both sides carry this layout (created by `init_teams.py --side green|red`):

```
<protocol-copy>/redteam/
├── config.yml            # side: green|red, redteam_enabled, redteam_accessible,
│                         # redteam_path, return_to  (LOCAL values per copy)
├── inbox/                # ACTIVE inbound packets (contents gitignored)
├── outbox/               # ACTIVE outbound packets (contents gitignored)
├── inbox-archive/        # acked-done packets (contents gitignored)
└── outbox-archive/       # acked-done packets (contents gitignored)
```

* Active = in inbox/outbox; inactive = in archives. Latest packet = active mission.
* Isolation default: **isolated dir**; high-risk: **air-gap**; low-risk fast loops may share. Switchable in `config.yml`; documented per mission.
* Sequential dual-red: Green → A → user carries A-outbox → B inbox → B `recheck-redteam` → test → `finish-redteam` appends; either FAIL = FAIL (fail-closed, Green arbitrates).

---

## 📋 Standard `green_amber_red_workspace/plan.md` Template

When `plan-greenteam` creates a plan, it MUST follow this format:

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

- [ ] Folder `green_amber_red_workspace/` exists in project root.
- [ ] Subfolder `green_amber_red_workspace/archive/` exists.
- [ ] `.gitignore` contains `green_amber_red_workspace/`.
- [ ] `green_amber_red_workspace/README.md` documents team personas and commands.
- [ ] Master agent directives reference the 10 commands + aliases: `plan-greenteam` (`plan-green`), `review-greenteam` (`review-green`), `execute-amberteam` (`exec-amber`), `review-amberteam` (`review-amber`), `send-redteam` (`send-red`), `verify-green-amber-red-team`, `review-redteam` (`review-red`), `test-redteam` (`test-red`), `finish-redteam` (`finish-red`), `recheck-redteam` (`recheck-red`).
- [ ] `redteam/` skeleton exists with `config.yml` (`side:` stamped); packet contents gitignored.
- [ ] `defects.md` exists green-side (from template, never overwritten); every row stamped; no red-side ledger writes.

---

## 🤝 Coexistence with Session Handoff Rules

This protocol is **complementary** to per-session handoff rules (e.g., OpenCode's `handoff.md`).

- `handoff.md` preserves context when a single session is interrupted.
- `green_amber_red_workspace` structures planning and execution across multiple agents and sessions.

Both can be active in the same workspace without conflict.

---

## 🔌 Existing-sandbox adapter note (e.g. ERP QA sandbox)

Sandboxes built before this standard keep their layout and triggers — the mission brief *declares* local equivalents instead of renaming working infrastructure:

| Standard field | ERP sandbox equivalent |
|:---|:---|
| `DEFECT_REPORT.md` verdict | `TEST_DEFECTS_REPORT.md` § verdict + `DEFECT_FIX_CHECKLIST.md` Bug rows |
| Defect ID `BUG-YYYYMMDD-NNN` | `BUG-2026-P*-*` hybrid IDs (map 1:1 at transcribe time) |
| Fix lifecycle states | Checklist `Status`: `❌ OPEN` → `⏳ FIXED`/`✅ VERIFIED` (+ `Fix Commit`) |
| `test-redteam` trigger | `amber-code` (new code ready for QA) |
| `recheck-redteam` trigger | `read-fix` / `verify-fix` / `check-fix` (re-test fixed bugs) |

Green transcribes ERP Bug rows into `defects.md` using the same who/when/packet stamps; ERP keeps its files.
