# agents-boilerplate

A collection of reusable, model-agnostic agent tooling and boilerplates for AI coding assistants (Antigravity, Claude Code, Cursor, Gemini, Google AI Studio, Qwen, Codex).

Each folder is self-contained — your agent can copy any of them into a project and implement it there.

---

## ⚡ Quick Start

```bash
# 1. Get the collection (clone or Download ZIP — no git required)
git clone https://github.com/milkboyinchina/agents-boilerplate.git

# 2. Copy the protocol(s) you want into your project
#    (copy, don't move — keeps the collection intact for next time)
cp -r /path/to/agents-boilerplate/question_protocol ./
```

```markdown
# 3. Ask your agent to implement it
Single protocol:
"Read `question_protocol/README.md` and implement it in this workspace."

Multiple:
"Read `green_amber_red_teams_protocol/README.md` and `handoff_protocol/README.md` and implement both."

Lazy (let the table below choose):
"Read `agents-boilerplate/README.md` and implement the boilerplates I ask for."
```

```bash
# 4. Agent runs the init — you verify with --check
python3 question_protocol/init_questions.py --check
```

---

## 📦 Available Boilerplates

| Folder | Purpose | Quick Start |
|---|---|---|
| [`green_amber_red_teams_protocol/`](./green_amber_red_teams_protocol/) | Traffic-Light Multi-Agent Teaming Protocol (Planner / Executor / Auditor) | `python3 green_amber_red_teams_protocol/init_teams.py` |
| [`handoff_protocol/`](./handoff_protocol/) | Project-Local Session Handoff Protocol (`/handoff-start`, `/handoff-resume`) | `python3 handoff_protocol/handoff.py start` |
| [`question_protocol/`](./question_protocol/) | Concise Question Protocol (`Q1`, `Q1-a`, free-form overrides) | `python3 question_protocol/init_questions.py` |
| [`tier_routing_protocol/`](./tier_routing_protocol/) | Tier Routing Protocol (`T1/T2/T3` → per-tool models, pins, weekly heartbeat) | `python3 tier_routing_protocol/resolve_model.py --install` |

What changes for you:

- `green_amber_red_teams_protocol/` — **No more code-first surprises: every task is planned, confirmed, then audited.**
- `handoff_protocol/` — **Interruptions stop costing context: pause and resume any session in one command.**
- `question_protocol/` — **Answer five questions in one short line — skips and late replies included.**
- `tier_routing_protocol/` — **Right model per task automatically — no hand-picking, no rot when vendors rename.**

---

## 🚦 Green-Amber-Red Teams

This boilerplate provides a structured collaboration protocol:

- **🟢 Green Team** — Planner / Architect: drafts `plan.md`, touches no code.
- **🟠 Amber Team** — Developer / Executor: reviews the plan, asks to proceed, writes code.
- **🔴 Red Team** — Independent QA / Auditor: adversarial black-box verification.

### Usage

See [Quick Start](#-quick-start): copy the folder, then run `python3 green_amber_red_teams_protocol/init_teams.py` (add `--init-plan "Title" --template backend` to seed a plan).

Or tell your agent:

> *"Read `green_amber_red_teams_protocol/INITIALIZE_GREEN_AMBER_RED_TEAMS.md` and set up the Traffic-Light team protocol."*

---

## 🔄 Handoff Protocol

This boilerplate provides **project-local session continuity**:

- **Manual triggers only**: `/handoff-start` and `/handoff-resume`.
- **Single output location**: `handoff_protocol/` inside the project workspace.
- **9-field template**: captures active task, files changed, verification, rollback, blockers, and next steps.
- **Auto-detects** `green_amber_red_teams/plan.md` status when present.

### Usage

See [Quick Start](#-quick-start): copy the folder, then `python3 handoff_protocol/handoff.py start --no-prompt` (`resume` to continue, `done` to archive).

---

## ❓ Question Protocol

This boilerplate provides **concise multi-question turns**:

- **Conversation-scoped labels**: `Q1, Q2...` never reuse mid-conversation — skipped questions stay answerable later.
- **Choice labels**: `Q1-a/b/c` (case-insensitive), including binary `yes/no`.
- **Free-form overrides**: `Q1:`, `Q1.`, `Q1=` aliases, multi-select (`Q1-a,c`), `skip Qn`.
- **Compaction-safe**: counter in `question_protocol/state.json` + transcript scan recovery.
- **Re-baseline**: at >99 closed, agent proposes `Archive Q1-Q99 and re-baseline to Q1?` (approval only).

### Usage

See [Quick Start](#-quick-start): copy the folder, then run `python3 question_protocol/init_questions.py` (validate with `--validate question_protocol/examples/good_example.md`).

---

## 🎚️ Tier Routing Protocol

This boilerplate routes **task tiers to per-tool models** without hardcoding IDs:

- **Tiers, not IDs**: `T1` trivial / `T2` standard / `T3` hard — stamped per task by Green Team.
- **One ID home**: raw model IDs live only in `routing.yaml` `aliases:` (`claude-opus`, `gemini-flash` everywhere else).
- **Sticky task pins**: `/pin-model claude-sonnet` when the T3 default fails — per-task, auto-releases on completion. No session pin exists.
- **Failover, never hard-fail**: dead IDs fall down chains with loud warnings.
- **Session-free freshness**: weekly dumb cron writes `heartbeat.json`; drift → pending proposal → one `Q1-a` approval.

### Usage

See [Quick Start](#-quick-start): copy the folder, then `python3 tier_routing_protocol/resolve_model.py --install` (fill IDs via add-tool, `--validate`, resolve per task, `--install-cron` for freshness).

---

## 📝 Changelog

See [`CHANGELOG.md`](./CHANGELOG.md) for the agent execution log and version history.

---

## 📄 License

Provided as-is for internal agent tooling and workspace bootstrapping.
