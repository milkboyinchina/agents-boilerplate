# agents-boilerplate

A collection of reusable, model-agnostic agent tooling and boilerplates for AI coding assistants (Antigravity, Claude Code, Cursor, Gemini, Google AI Studio, Qwen, Codex).

Each folder is self-contained and can be copy-pasted into any workspace or repository.

---

## 📦 Available Boilerplates

| Folder | Purpose | Quick Start |
|---|---|---|
| [`green_amber_red_teams_protocol/`](./green_amber_red_teams_protocol/) | Traffic-Light Multi-Agent Teaming Protocol (Planner / Executor / Auditor) | `python3 green_amber_red_teams_protocol/init_teams.py` |
| [`handoff_protocol/`](./handoff_protocol/) | Project-Local Session Handoff Protocol (`/handoff-start`, `/handoff-resume`) | `python3 handoff_protocol/handoff.py start` |
| [`question_protocol/`](./question_protocol/) | Concise Question Protocol (`Q1`, `Q1-a`, free-form overrides) | `python3 question_protocol/init_questions.py` |
| [`tier_routing_protocol/`](./tier_routing_protocol/) | Tier Routing Protocol (`T1/T2/T3` → per-tool models, pins, weekly heartbeat) | `python3 tier_routing_protocol/resolve_model.py --install` |

---

## 🚦 Green-Amber-Red Teams

This boilerplate provides a structured collaboration protocol:

- **🟢 Green Team** — Planner / Architect: drafts `plan.md`, touches no code.
- **🟠 Amber Team** — Developer / Executor: reviews the plan, asks to proceed, writes code.
- **🔴 Red Team** — Independent QA / Auditor: adversarial black-box verification.

### Usage in any repo

```bash
# 1. Copy the boilerplate into your project
cp -r /path/to/agents-boilerplate/green_amber_red_teams_protocol ./

# 2. Run the bootstrap
python3 green_amber_red_teams_protocol/init_teams.py

# 3. Optional: create an initial plan
python3 green_amber_red_teams_protocol/init_teams.py --init-plan "Add user authentication" --template backend
```

Or tell your agent:

> *"Read `green_amber_red_teams_protocol/INITIALIZE_GREEN_AMBER_RED_TEAMS.md` and set up the Traffic-Light team protocol."*

---

## 🔄 Handoff Protocol

This boilerplate provides **project-local session continuity**:

- **Manual triggers only**: `/handoff-start` and `/handoff-resume`.
- **Single output location**: `handoff_protocol/` inside the project workspace.
- **9-field template**: captures active task, files changed, verification, rollback, blockers, and next steps.
- **Auto-detects** `green_amber_red_teams/plan.md` status when present.

### Usage in any repo

```bash
# 1. Copy the boilerplate into your project
cp -r /path/to/agents-boilerplate/handoff_protocol ./

# 2. Start a handoff
python3 handoff_protocol/handoff.py start --no-prompt

# 3. Resume later
python3 handoff_protocol/handoff.py resume

# 4. Archive when done
python3 handoff_protocol/handoff.py done
```

---

## ❓ Question Protocol

This boilerplate provides **concise multi-question turns**:

- **Conversation-scoped labels**: `Q1, Q2...` never reuse mid-conversation — skipped questions stay answerable later.
- **Choice labels**: `Q1-a/b/c` (case-insensitive), including binary `yes/no`.
- **Free-form overrides**: `Q1:`, `Q1.`, `Q1=` aliases, multi-select (`Q1-a,c`), `skip Qn`.
- **Compaction-safe**: counter in `question_protocol/state.json` + transcript scan recovery.
- **Re-baseline**: at >99 closed, agent proposes `Archive Q1-Q99 and re-baseline to Q1?` (approval only).

### Usage in any repo

```bash
# 1. Copy the boilerplate into your project
cp -r /path/to/agents-boilerplate/question_protocol ./

# 2. Run the bootstrap
python3 question_protocol/init_questions.py

# 3. Validate a transcript
python3 question_protocol/init_questions.py --validate question_protocol/examples/good_example.md
```

---

## 🎚️ Tier Routing Protocol

This boilerplate routes **task tiers to per-tool models** without hardcoding IDs:

- **Tiers, not IDs**: `T1` trivial / `T2` standard / `T3` hard — stamped per task by Green Team.
- **One ID home**: raw model IDs live only in `routing.yaml` `aliases:` (`claude-opus`, `gemini-flash` everywhere else).
- **Sticky task pins**: `/pin-model claude-sonnet` when the T3 default fails — per-task, auto-releases on completion. No session pin exists.
- **Failover, never hard-fail**: dead IDs fall down chains with loud warnings.
- **Session-free freshness**: weekly dumb cron writes `heartbeat.json`; drift → pending proposal → one `Q1-a` approval.

### Usage in any repo

```bash
# 1. Copy the boilerplate into your project
cp -r /path/to/agents-boilerplate/tier_routing_protocol ./

# 2. Bootstrap (gitignore runtime files + directives)
python3 tier_routing_protocol/resolve_model.py --install

# 3. Fill IDs via the add-tool workflow, then validate
python3 tier_routing_protocol/resolve_model.py --validate

# 4. Resolve before executing a task
python3 tier_routing_protocol/resolve_model.py --tier T2 --tool opencode --task 3

# 5. Weekly freshness signal (OS-aware install, manual fallback in cron/)
python3 tier_routing_protocol/resolve_model.py --install-cron
```

---

## 📝 Changelog

See [`CHANGELOG.md`](./CHANGELOG.md) for the agent execution log and version history.

---

## 📄 License

Provided as-is for internal agent tooling and workspace bootstrapping.
