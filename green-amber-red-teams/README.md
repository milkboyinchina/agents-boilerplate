# 🚦 Traffic-Light Multi-Agent Teaming Toolkit

A portable, zero-dependency bootstrap for the **Green/Amber/Red** multi-agent teaming protocol.

Copy this folder into any repository, run `init_teams.py`, and start using structured AI collaboration.

---

## ⚡ Quick Start

```bash
# 1. Drop this folder into your project
python3 green-amber-red-teams/init_teams.py

# 2. Optional: seed an initial plan
python3 green-amber-red-teams/init_teams.py --init-plan "Add user authentication" --template backend
```

Or tell any AI assistant:

> *"Read `green-amber-red-teams/INITIALIZE_GREEN_AMBER_RED_TEAMS.md` and set up the Traffic-Light team protocol."*

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
python3 green-amber-red-teams/init_teams.py [OPTIONS]
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
