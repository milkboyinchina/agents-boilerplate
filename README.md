# agents-boilerplate

A collection of reusable, model-agnostic agent tooling and boilerplates for AI coding assistants (Antigravity, Claude Code, Cursor, Gemini, Google AI Studio, Qwen, Codex).

Each folder is self-contained and can be copy-pasted into any workspace or repository.

---

## 📦 Available Boilerplates

| Folder | Purpose | Quick Start |
|---|---|---|
| [`green-amber-red-teams/`](./green-amber-red-teams/) | Traffic-Light Multi-Agent Teaming Protocol (Planner / Executor / Auditor) | `python3 green-amber-red-teams/init_teams.py` |
| [`handoff-protocol/`](./handoff-protocol/) | Project-Local Session Handoff Protocol (`/handoff-start`, `/handoff-resume`) | `python3 handoff-protocol/handoff.py start` |
| [`question-protocol/`](./question-protocol/) | Concise Question Protocol (`Q1`, `Q1-a`, free-form overrides) | `python3 question-protocol/init_questions.py` |

---

## 🚦 Green-Amber-Red Teams

The first boilerplate provides a structured collaboration protocol:

- **🟢 Green Team** — Planner / Architect: drafts `plan.md`, touches no code.
- **🟠 Amber Team** — Developer / Executor: reviews the plan, asks to proceed, writes code.
- **🔴 Red Team** — Independent QA / Auditor: adversarial black-box verification.

### Usage in any repo

```bash
# 1. Copy the boilerplate into your project
cp -r /path/to/agents-boilerplate/green-amber-red-teams ./

# 2. Run the bootstrap
python3 green-amber-red-teams/init_teams.py

# 3. Optional: create an initial plan
python3 green-amber-red-teams/init_teams.py --init-plan "Add user authentication" --template backend
```

Or tell your agent:

> *"Read `green-amber-red-teams/INITIALIZE_GREEN_AMBER_RED_TEAMS.md` and set up the Traffic-Light team protocol."*

---

## 🔄 Handoff Protocol

The second boilerplate provides **project-local session continuity**:

- **Manual triggers only**: `/handoff-start` and `/handoff-resume`.
- **Single output location**: `handoff-protocol/` inside the project workspace.
- **9-field template**: captures active task, files changed, verification, rollback, blockers, and next steps.
- **Auto-detects** `green-amber-red-teams/plan.md` status when present.

### Usage in any repo

```bash
# 1. Copy the boilerplate into your project
cp -r /path/to/agents-boilerplate/handoff-protocol ./

# 2. Start a handoff
python3 handoff-protocol/handoff.py start --no-prompt

# 3. Resume later
python3 handoff-protocol/handoff.py resume

# 4. Archive when done
python3 handoff-protocol/handoff.py done
```

---

## ❓ Question Protocol

The third boilerplate provides **concise multi-question turns**:

- **Conversation-scoped labels**: `Q1, Q2...` never reuse mid-conversation — skipped questions stay answerable later.
- **Choice labels**: `Q1-a/b/c` (case-insensitive), including binary `yes/no`.
- **Free-form overrides**: `Q1:`, `Q1.`, `Q1=` aliases, multi-select (`Q1-a,c`), `skip Qn`.
- **Compaction-safe**: counter in `question-protocol/state.json` + transcript scan recovery.
- **Re-baseline**: at >99 closed, agent proposes `Archive Q1-Q99 and re-baseline to Q1?` (approval only).

### Usage in any repo

```bash
# 1. Copy the boilerplate into your project
cp -r /path/to/agents-boilerplate/question-protocol ./

# 2. Run the bootstrap
python3 question-protocol/init_questions.py

# 3. Validate a transcript
python3 question-protocol/init_questions.py --validate question-protocol/examples/good-example.md
```

---

## 📝 Changelog

See [`CHANGELOG.md`](./CHANGELOG.md) for the agent execution log and version history.

---

## 📄 License

Provided as-is for internal agent tooling and workspace bootstrapping.
