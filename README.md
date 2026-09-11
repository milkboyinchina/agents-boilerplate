# agents-boilerplate

So you're CTO-ing a team of AIs now. Congratulations — middle management, but the employees are tireless and the coffee budget is zero.

This is a collection of reusable, model-agnostic agent tooling and boilerplates for AI coding assistants (Antigravity, Claude Code, Cursor, Gemini, Google AI Studio, Qwen, Codex).

Each folder is self-contained — your agent can copy any of them into a project and implement it there. New here? Skim [`COMPARISON.md`](./COMPARISON.md) first: before/after transcripts per protocol, so you can see what changes before installing anything.

---

## ⚡ Quick Start

```bash
# 1. Place the collection inside your workspace (clone, Download ZIP, or copy the folder in)
git clone https://github.com/milkboyinchina/agents-boilerplate.git

# 2. Keep it out of your project's commits (add to .gitignore if it exists —
#    create it if it doesn't; each init CLI below also ensures this line)
agents-boilerplate/
```

```markdown
# 3. Ask your agent to implement it
Single protocol:
"Read `agents-boilerplate/question_protocol/README.md` and implement it in this workspace."

Multiple:
"Read `agents-boilerplate/green_amber_red_team_protocol/README.md` and `agents-boilerplate/handoff_protocol/README.md` and implement both."

Lazy (let the table below choose):
"Read `agents-boilerplate/README.md` and implement the boilerplates I ask for."
```

```bash
# 4. Agent runs the init — you verify with --check
python3 agents-boilerplate/question_protocol/init_questions.py --check
```

Standalone fallback (project can't carry the collection): copy one protocol folder to root instead — `cp -r agents-boilerplate/question_protocol ./` — then follow that protocol's README with root-level paths.

### Install profiles (pick one sentence, skip the interrogation)

Fresh installs used to start with five scoping questions. Don't answer them — pick a profile instead; the agent expands it locally. Defaults are recorded here so no agent re-derives them.

| Profile | Installs | Defaults |
|:---|:---|:---|
| `minimal` | green plan workspace | No seeded plan, no red side, no cron |
| `standard` | green + question + handoff CLIs (tier not installed; add it in `full`) | No seeded plan, no red side, no cron |
| `full` | everything: green + question + handoff + tier registry (as-is) + red side + cron | Seed title asked once, red topology asked once, cron installed. Tier IDs stay TODO placeholders until the add-tool workflow (`TIER_ROUTING.md` §8) fills them — bare `--validate` passes with stale warnings; `resolve` fails loudly (`no live ID`, exit 1) and `--validate --fail-on-stale` exits 1 |

```markdown
"Install the minimal profile from agents-boilerplate."
"Install the standard profile from agents-boilerplate."
"Install the full profile from agents-boilerplate (red side: same-machine second workspace)."
```

Deviations are one clause: *"standard profile, but seed the plan 'Auth API' with the backend template"* — still one sentence, not five questions.

### Reinstall / upgrade (already installed? read this)

Upgrades are boring on purpose — everything is idempotent:

```bash
# 1. Refresh the collection (pull, re-copy, or re-download over the old one)
git -C agents-boilerplate pull   # or: cp -r /fresh/agents-boilerplate ./agents-boilerplate

# 2. Re-run the inits you already ran — same commands, same flags
python3 agents-boilerplate/green_amber_red_team_protocol/init_teams.py
python3 agents-boilerplate/question_protocol/init_questions.py
# ... and so on per installed protocol
```

What survives: plans, ledgers, handoffs, pins, counters, packet archives, and `AGENTS.md` blocks (re-runs print `[SKIP]`/`[OK]`, never duplicate or overwrite — except `--force`, which you asked for). What changes: CLI behavior, templates, and directive wording pick up the new version. If a release renames paths, its `CHANGELOG.md` entry carries the exact migration commands — follow that entry, then re-run the inits.

---

## 📦 Available Boilerplates

| Folder | Purpose |
|---|---|
| [`green_amber_red_team_protocol/`](./green_amber_red_team_protocol/) | Traffic-Light Multi-Agent Teaming Protocol (Planner / Executor / Auditor) |
| [`handoff_protocol/`](./handoff_protocol/) | Project-Local Session Handoff Protocol (`/handoff-start`, `/handoff-resume`) |
| [`question_protocol/`](./question_protocol/) | Concise Question Protocol (`Q1`, `Q1-a`, free-form overrides) |
| [`tier_routing_protocol/`](./tier_routing_protocol/) | Tier Routing Protocol (`T1/T2/T3` → per-tool models, pins, weekly heartbeat) |

What changes for you (your mileage may vary — figures below are heuristics, not invoices):

- `green_amber_red_team_protocol/` — **No more code-first surprises: every task is planned, confirmed, then audited.**
- `handoff_protocol/` — **Interruptions stop costing context: pause and resume any session in one command.**
- `question_protocol/` — **Answer five questions in one short line — skips and late replies included.**
- `tier_routing_protocol/` — **Right model per task automatically — no hand-picking, no rot when vendors rename.**

See [`COMPARISON.md`](./COMPARISON.md) for before/after transcripts per protocol.

### Token cost: with vs without

Methodology: ~4 chars/token heuristic for a "typical mission" baseline; actuals vary by model, tokenizer, question length, and session habits — **your mileage may vary**, treat percentages as directional. Single trivial questions are net-negative for every protocol (just ask bare yes/no); fixed directive blocks (~8 lines each) amortize to noise over a real session.

| Protocol | Without (est.) | With (est.) | Saving | Pros / cons |
|:---|:---|:---|:---|:---|
| Green | ~250–450/mission (re-scope chat + redoing wrong-scope work) | ~180–330 (plan written once + confirm) | ~25–40% | + kills scope-creep and redo; − plan file bigger than trivial tasks |
| Handoff | ~300–500 per interruption (full re-brief + re-answers) | ~230–370 once (9-field file + resume read) | ~40–60% when interrupted | + rescues complex work; − file bigger than tiny tasks |
| Question | ~300–400 per 3-Q turn (retyped answers + clarification rounds) | ~90–100 (short labels + terse echo) | ~65–75% | + more upfront ask formatting, − tiny replies, unambiguous, skip-safe |
| Tier | ~50–100/task hand-picking + 100s on wrong-model retries | ~20/resolve, registry amortized | ~50–80% | + right model automatically, no rename rot; − registry fill + staleness upkeep |

---

## 🚦 Green-Amber-Red Teams

Three agents walk into a codebase. Thanks to this protocol, they don't all start coding. This boilerplate provides a structured collaboration protocol:

- **🟢 Green Team** — Planner / Architect: drafts `plan.md`, touches no code.
- **🟠 Amber Team** — Developer / Executor: reviews the plan, asks to proceed, writes code.
- **🔴 Red Team** — Independent QA / Auditor: adversarial black-box verification via timestamped packets.

12 commands (aliases accepted) — see the command table in `green_amber_red_team_protocol/README.md`.

### Usage

See [Quick Start](#-quick-start): copy the folder, then run `python3 green_amber_red_team_protocol/init_teams.py` (add `--init-plan "Title" --template backend` to seed a plan; `--side red` in the red workspace).

Or tell your agent:

> *"Read `green_amber_red_team_protocol/INITIALIZE_GREEN_AMBER_RED_TEAMS.md` and set up the Traffic-Light team protocol."*

---

## 🔄 Handoff Protocol

Your agent has the memory of a goldfish after a context window. This boilerplate provides **project-local session continuity**:

- **Manual triggers only**: `/handoff-start` and `/handoff-resume`.
- **Single output location**: `.protocol/handoff_workspace/` inside the project workspace.
- **9-field template**: captures active task, files changed, verification, rollback, blockers, and next steps.
- **Auto-detects** `.protocol/green_amber_red_workspace/plan.md` status when present.

### Usage

See [Quick Start](#-quick-start): copy the folder, then `python3 handoff_protocol/handoff.py start --no-prompt` (`resume` to continue, `done` to archive).

---

## ❓ Question Protocol

Five questions, one short line, zero "wait, which question was that?" This boilerplate provides **concise multi-question turns**:

- **Conversation-scoped labels**: `Q1, Q2...` never reuse mid-conversation — skipped questions stay answerable later.
- **Choice labels**: `Q1-a/b/c` (case-insensitive), including binary `yes/no`.
- **Free-form overrides**: `Q1:`, `Q1.`, `Q1=` aliases, multi-select (`Q1-a,c`), `skip Qn`.
- **Compaction-safe**: counter in `.protocol/question_workspace/state.json` + transcript scan recovery.
- **Re-baseline**: at >99 closed, agent proposes `Archive Q1-Q99 and re-baseline to Q1?` (approval only).

### Usage

See [Quick Start](#-quick-start): copy the folder, then run `python3 question_protocol/init_questions.py` (validate with `--validate question_protocol/examples/good_example.md`).

---

## 🎚️ Tier Routing Protocol

Stop hand-picking models like you're drafting fantasy football. This boilerplate routes **task tiers to per-tool models** without hardcoding IDs:

- **Tiers, not IDs**: `T1` trivial / `T2` standard / `T3` hard — stamped per task by Green Team.
- **One ID home**: raw model IDs live only in `routing.yaml` `aliases:` (`claude-opus`, `gemini-flash` everywhere else).
- **Sticky task pins**: `/pin-model claude-sonnet` when the T3 default fails — per-task, auto-releases on completion. No session pin exists.
- **Failover, never hard-fail**: dead IDs fall down chains with loud warnings.
- **Session-free freshness**: weekly dumb cron writes `heartbeat.json`; drift → pending proposal → one `Q1-a` approval.

### Usage

See [Quick Start](#-quick-start): copy the folder, then `python3 tier_routing_protocol/resolve_model.py --install` (fill IDs via add-tool, `--validate`, resolve per task, `--install-cron` for freshness).

---

## 🗺️ Future roadmap

Structural change in progress (tracked in [`TODO.md`](./TODO.md), item 1): all runtime state lives under a hidden `.protocol/` dir — one `.gitignore` line instead of ~10, and a clean workspace root.

Six protocols on the drawing board (tracked in [`TODO.md`](./TODO.md) — design questions open, nothing built yet):

- **`architect_protocol/`** — durable codebase cartography: map new or existing apps so agents can look up blueprints and track progress per area. (Transient `plan.md` tells you the mission; this tells you the terrain.)
- **`agent_builder_protocol/`** — agent scaffolding installer: populate empty workspaces (or upgrade existing ones) with the right `AGENTS.md`, rules, and skills for the stack.
- **`memory_protocol/`** — long-term memory across sessions: handoff saves one session, this one remembers everything learned across missions.
- **`decision_protocol/`** — decision records: green plans capture *what*, this captures *why* (numbered, statused, annotated onto the architect map).
- **`release_protocol/`** — release gates: version, changelog, migration notes, rollout/rollback — the definition of shippable this collection currently lacks.
- **`onboarding_protocol/`** — guided codebase tours for newcomers, generated from the architect map (builds after architect lands).

---

## 📝 Changelog

See [`CHANGELOG.md`](./CHANGELOG.md) for the agent execution log and version history.

---

## 📄 License

Provided as-is for internal agent tooling and workspace bootstrapping.
