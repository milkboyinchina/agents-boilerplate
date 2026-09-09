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

---

## ⚡ Quick Start

```bash
# 1. Drop this folder into your project
python3 green_amber_red_teams_protocol/init_teams.py

# 2. Optional: seed an initial plan
python3 green_amber_red_teams_protocol/init_teams.py --init-plan "Add user authentication" --template backend
```

Or tell any AI assistant:

> *"Read `green_amber_red_teams_protocol/INITIALIZE_GREEN_AMBER_RED_TEAMS.md` and set up the Traffic-Light team protocol."*

---

## 🧭 Team Personas

| Color / Team | Persona | Responsibilities | Key Commands |
|:---|:---|:---|:---|
| **🟢 Green Team** | **Architect / Planner** | Analyzes specs, maps affected files, writes `plan.md`, and performs post-implementation audits. **Touches NO production code.** | `green-plan <prompt>`<br>`green-review` |
| **🟠 Amber Team** | **Developer / Implementer** | Inspects the plan, confirms with user, implements code changes, runs tests, and tracks task states. | `amber-check`<br>`check-plan` |
| **🔴 Red Team** | **Independent QA / Auditor** | Executes black-box tests, regression suites, and adversarial audits in an isolated sandbox. | `check-redteam`<br>`send-redteam` |

---

## 🔄 Collaboration Lifecycle

```
[User: green-plan <prompt>] ──> [🟢 Green Team drafts green_amber_red_teams/plan.md (📋 PLANNED)]
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

## 🛠️ CLI Reference

```bash
python3 green_amber_red_teams_protocol/init_teams.py [OPTIONS]
```

| Option | Description |
|:---|:---|
| `--dry-run` | Print what would be created without writing to disk. |
| `--force` | Overwrite existing `green_amber_red_teams/README.md`. |
| `--check` | Report whether the workspace is already initialized. |
| `--json` | Output `--check` results as JSON. |
| `--init-plan "Title"` | Create an initial `plan.md` with the given title. |
| `--template {generic,backend,frontend,mobile,devops}` | Plan template to use (default: generic). |
| `--quiet` | Suppress non-essential output. |

---

## 📁 What Gets Created

```
<your-project-root>/
├── .gitignore                      # appended with green_amber_red_teams/
└── green_amber_red_teams/
    ├── README.md                   # local team reference
    ├── archive/                    # completed plans
    └── plan.md                     # active implementation plan
```

If `AGENTS.md`, `CLAUDE.md`, `.cursorrules`, or `GEMINI.md` exist, the script appends standard Traffic-Light directives without duplicating them.

---

## 📚 Full Protocol Guide

See [`INITIALIZE_GREEN_AMBER_RED_TEAMS.md`](./INITIALIZE_GREEN_AMBER_RED_TEAMS.md) for the complete human-readable specification.

---

## 🤖 Agent Skill

See [`SKILL.md`](./SKILL.md) if your agent framework supports `.agents/skills/` definitions.
