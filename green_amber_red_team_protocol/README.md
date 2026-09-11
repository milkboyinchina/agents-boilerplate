# 🚦 Traffic-Light Multi-Agent Teaming Toolkit

A portable, zero-dependency bootstrap for the **Green/Amber/Red** multi-agent teaming protocol.

Copy this folder into any repository, run `init_teams.py`, and start using structured AI collaboration.

---

## 💡 Why use this?

Its biggest advantage is making the workspace **agent- and tool-agnostic**: `plan.md` plus a zero-dependency CLI plus skill files work identically under Antigravity, Claude Code, Cursor, Gemini, or anything else — switching tools mid-project costs nothing. Without a teaming protocol, agents jump straight into code: no written plan, scope creep mid-task, untested changes, and every new session rebuilds context from scratch.

| Without this protocol | With this protocol |
|:---|:---|
| Locked into one agent's chat memory and formats — switching tools restarts everything | Plan, lifecycle, and commands live in files any agent reads; teams hand off across tools |
| Agent codes from a chat prompt — plan lives in conversation history | Green Team writes `plan.md`: exact files, effort, verification steps |
| "Just do it" executes immediately, surprises included | Amber Team summarizes the plan and asks before touching code |
| Done means "code written", bugs found later by you | Green Team audits diff + tests; Red Team adversarially verifies in a sandbox |

*Token verdict: ~25–40% per mission (plan once vs re-scoping in chat); net-negative below trivial — don't plan a one-line fix. Full table: [`README.md`](../README.md).* Before/after transcripts: [`COMPARISON.md`](../COMPARISON.md).

---

## ⚡ Quick Start

```bash
# Place the collection per root README Quick Start, then run from workspace root.
# Green+amber side:
python3 agents-boilerplate/green_amber_red_team_protocol/init_teams.py

# Optional: seed an initial plan
python3 agents-boilerplate/green_amber_red_team_protocol/init_teams.py --init-plan "Add user authentication" --template backend

# Red side: place the collection in the red workspace, then init there
python3 agents-boilerplate/green_amber_red_team_protocol/init_teams.py --side red
```
Standalone fallback (project can't carry the collection): copy this folder to root (`cp -r agents-boilerplate/green_amber_red_team_protocol ./`) and run the same commands without the `agents-boilerplate/` prefix.

Or tell any AI assistant:

> *"Read `green_amber_red_team_protocol/INITIALIZE_GREEN_AMBER_RED_TEAMS.md` and set up the Traffic-Light team protocol."*

---

## 🧭 Team Personas

| Color / Team | Persona | Responsibilities | Key Commands |
|:---|:---|:---|:---|
| **🟢 Green Team** | **Architect / Planner** | Analyzes specs, maps affected files, writes `plan.md`, audits implementation, runs the Red Team handoff, triages verdicts, and audits drift. **Touches NO production code.** | `plan-greenteam`<br>`review-greenteam`<br>`review-amberteam`<br>`send-redteam`<br>`review-redteam`<br>`verify-green-amber-red-team` |
| **🟠 Amber Team** | **Developer / Implementer** | Confirms with user, implements code changes, runs tests, tracks task states, and fixes Red Team FAIL findings on re-open. | `execute-amberteam` |
| **🔴 Red Team** | **Independent QA / Auditor** | Reads own `.protocol/redteam/inbox`, tests in an isolated sandbox, writes own `.protocol/redteam/outbox`. Never touches source. | `test-redteam`<br>`finish-redteam`<br>`recheck-redteam` |

---

## 🔄 Collaboration Lifecycle

```
[User: plan-greenteam <prompt>] ──> [🟢 Green Team drafts .protocol/green_amber_red_workspace/plan.md (📋 PLANNED)]
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
[User: verify-green-amber-red-team] → [🟢 Drift audit (configs, packets, versions) → Q1-a realign]
```

---

## 📟 Command Reference (owner → alphabetical)

| Owner | Command | Alias | Role |
|:---|:---|:---|:---|
| 🟠 Amber | `execute-amberteam` | `exec-amber` | Confirm → code → mark tasks; fixes Red FAIL findings on re-open |
| 🟢 Green | `plan-greenteam <prompt>` | `plan-green` | Draft fresh `plan.md` (`📋 PLANNED`, Plan-ID stamped); unfinished active plan auto-stashes |
| 🟢 Green | `plan-resume-greenteam <id>` | `resume-green` | List `stash/` / restore parked plan to `plan.md` intact |
| 🟢 Green | `plan-stash-greenteam` | `stash-green` | Park active `plan.md` → `stash/` (status + progress intact) |
| 🟢 Green | `review-amberteam` | `review-amber` | Audit Amber's diff + tests → `✅ COMPLETED` or flag defects |
| 🟢 Green | `review-greenteam` | `review-green` | Plan QA by any agent/model: APPROVE → execute, REVISE → amend + re-review |
| 🟢 Green | `review-redteam` | `review-red` | Read defect report → verdict PASS/FAIL → reopen flow → archive packet |
| 🟢 Green | `send-redteam` | `send-red` | Build + stage packet, deliver if reachable else user-carry |
| 🟢 Green | `verify-green-amber-red-team` | — | Drift audit (configs, packets, versions) → `Q1-a` realign turn |
| 🔴 Red | `finish-redteam` | `finish-red` | Done → outbox packet for Green (+ cross-ack) |
| 🔴 Red | `test-redteam` | `test-red` | Plan packet → run tests in isolated session |
| 🔴 Red | `recheck-redteam` | `recheck-red` | Read own inbox + outbox → ask user: retest plan or other action |

---

## 📦 Red Team packet exchange (`.protocol/redteam/`)

Both sides carry this layout (created by `init_teams.py --side green|red`):

```
.protocol/redteam/
├── config.yml            # side: green|red, reachability, redteam_enabled, return_to (LOCAL values)
├── inbox/                # ACTIVE inbound packets
├── outbox/               # ACTIVE outbound packets
├── inbox-archive/        # acked-done packets
└── outbox-archive/       # acked-done packets
```

(Everything under `.protocol/` is gitignored by the single `.protocol/` line.)

* Packets: `packet_green_YYYYMMDD_HHMM/` (green→red) and `packet_red_YYYYMMDD_HHMM/` (red→green). Location = state: inbox/outbox is active, archives are inactive.
* Handshake: a new packet must declare the previous packet done (or explicitly still-open); only acked-done packets archive.
* Reachability: `redteam_accessible: true` + `redteam_path` → Green copies both ways; `false` → user carries (brief stamps `return_to:` so the path is always concrete).
* Kill switch: `redteam_enabled: false` → `send-redteam`/`review-redteam` reply "red team is not available" and stop.
* Risk tiers: default **isolated dir**, high-risk **air-gap**, low-risk fast loops may share a workspace — chosen per mission, switchable in `config.yml`.
* Sequential dual-red (high-risk opt-in): Green → A → user carries A-outbox → B inbox → B `recheck-redteam` → test → `finish-redteam` appends (author-tagged, never rewrites A); either FAIL = FAIL.
* Defect ledger: `.protocol/green_amber_red_workspace/defects.md` (green side; template `templates/defect_ledger.md`). Red writes findings via reports only — never the ledger; Green transcribes at `review-redteam` and owns fix fields (`OPEN→ACKED→IN_FIX→FIXED→VERIFIED→CLOSED`, all stamped). IDs: `BUG-YYYYMMDD-NNN` + Plan-ID (findings map to the exact plan across stash/resume cycles).

---

## 🛡️ QC layers — when does Layer 3 run?

* **Layer 1 — Amber self-test** (unit tests, builder's own checks): always, pre-review. Biased by construction.
* **Layer 2 — Green audit** (`review-amberteam`): always, the architect's gate. Biased toward the plan.
* **Layer 3 — Red independent** (packet → tests → verdict): runs when **any** hold — user-facing surface, risky change (security, payments, prod behavior, migrations), or **code-privacy concern** (the verifying model shares/trains on data). Red is black-box by construction (no source access), so Layer 3 is simultaneously the strongest check *and* the lowest-exposure one — sensitive verification goes through red precisely so source never enters a data-sharing model chat.

---

## 🛠️ CLI Reference

```bash
python3 green_amber_red_team_protocol/init_teams.py [OPTIONS]
```

| Option | Description |
|:---|:---|
| `--dry-run` | Print what would be created without writing to disk. |
| `--force` | Overwrite existing `.protocol/green_amber_red_workspace/README.md`. |
| `--check` | Report whether the workspace is already initialized. |
| `--json` | Output `--check` results as JSON. |
| `--init-plan "Title"` | Create an initial `plan.md` with the given title. |
| `--template {generic,backend,frontend,mobile,devops}` | Plan template to use (default: generic). |
| `--quiet` | Suppress non-essential output. |
| `--side {green,red}` | Workspace side (default: keep existing, else green). Red skips the plan workspace. |
| `--backup` | Snapshot runtime + manifest into a root-level tar.gz bundle. |
| `--restore <bundle>` | Restore from a bundle (merge; `--force` overwrites). |
| `--uninstall [--skip-backup]` | Archive-first removal (backup, drop runtime, extract directives). |

---

## 📁 What Gets Created

`--side green` (default) in `<your-project-root>/`:

```
├── .gitignore                      # += .protocol/ (single line covers all runtime)
└── .protocol/
    ├── green_amber_red_workspace/
    │   ├── README.md               # local team reference
    │   ├── archive/                # completed plans
    │   ├── stash/                  # unfinished parked plans (ls stash/ = unfinished count)
    │   └── plan.md                 # active implementation plan (Plan-ID header)
    └── redteam/
        ├── config.yml              # side: green, reachability, kill switch
        ├── inbox/ + outbox/        # active packets
        └── inbox-archive/ + outbox-archive/
```

`--side red` in the red workspace: only the `.protocol/redteam/` skeleton + `config.yml` (`side: red`) + brief/report templates (templates stay in the protocol copy). No plan workspace.

If `AGENTS.md`, `CLAUDE.md`, `.cursorrules`, or `GEMINI.md` exist, the script appends standard Traffic-Light directives without duplicating them.

---

## 📚 Full Protocol Guide

See [`INITIALIZE_GREEN_AMBER_RED_TEAMS.md`](./INITIALIZE_GREEN_AMBER_RED_TEAMS.md) for the complete human-readable specification.

---

## 🤖 Agent Skill

See [`SKILL.md`](./SKILL.md) if your agent framework supports `.agents/skills/` definitions.
