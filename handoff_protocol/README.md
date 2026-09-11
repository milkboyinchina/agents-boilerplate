# 🔄 Project-Local Session Handoff Protocol

A portable, zero-dependency protocol for pausing and resuming AI agent sessions within a single project workspace.

Unlike global quota-based handoffs, this protocol is **manual**:
- `/handoff-start` — capture the current state.
- `/handoff-resume` — continue from the last handoff.

All handoff files live inside the project-local `.protocol/handoff_workspace/` folder, which is automatically gitignored.

---

## 💡 Why use this?

Without session handoffs, every interruption (closed IDE, model switch, paused task) destroys context: the next session re-asks everything, re-reads the codebase, and risks redoing or contradicting prior work.

| Without this protocol | With this protocol |
|:---|:---|
| Interrupted session = lost state, re-explain from zero | `/handoff-start` captures 9 fields: task, files, verification, rollback, next steps |
| New agent guesses where work stopped | `/handoff-resume` continues from exact Next Steps in one command |

*Token verdict: ~40–60% when interrupted (one file + one read vs full re-brief); net-negative for tiny tasks. Full table: [`README.md`](../README.md).* Before/after transcripts: [`COMPARISON.md`](../COMPARISON.md).
| Switching models means re-briefing the replacement | Handoff file is model-agnostic — any agent resumes it |

---

## ⚡ Quick Start

```bash
# Place the collection per root README Quick Start, then run from workspace root.
# 1. Start a handoff
python3 agents-boilerplate/handoff_protocol/handoff.py start --no-prompt

# 2. Later, resume from it
python3 agents-boilerplate/handoff_protocol/handoff.py resume

# 3. When the task is complete, archive the handoff
python3 agents-boilerplate/handoff_protocol/handoff.py done
```
Standalone fallback (project can't carry the collection): copy this folder to root (`cp -r agents-boilerplate/handoff_protocol ./`) and run the same commands without the `agents-boilerplate/` prefix.

Or tell your agent:

> *"Read `handoff_protocol/HANDOFF_PROTOCOL.md` and use `/handoff-start` and `/handoff-resume` for session continuity."*

---

## 📁 Folder Layout

```
<project-root>/
├── .gitignore                              # contains .protocol/ (single line)
└── .protocol/handoff_workspace/
    ├── handoff.py                          # CLI
    ├── README.md                           # this file
    ├── HANDOFF_PROTOCOL.md                 # full specification
    ├── SKILL.md                            # agent skill definition
    ├── templates/
    │   └── handoff_template.md             # 9-field template
    ├── handoff-YYYYMMDD-HHMM.md            # active handoff
    └── archive/
        └── handoff-YYYYMMDD-HHMM.md        # completed handoffs
```

---

## 🛠️ CLI Reference

```bash
python3 handoff_protocol/handoff.py [OPTIONS] <COMMAND>
```

| Command | Description |
|---|---|
| `start` | Create a new active handoff file. |
| `resume` | Print a resume summary from the active handoff. |
| `done` | Move the active handoff to `.protocol/handoff_workspace/archive/`. |
| `status` | Show whether an active handoff exists. |

| Option | Description |
|---|---|
| `--dry-run` | Preview actions without writing files. |
| `--quiet` | Suppress non-essential output. |

### `start` options

| Option | Description |
|---|---|
| `--title` | Handoff title. |
| `--agent-model` | Agent/model identifier. |
| `--session-id` | Session identifier. |
| `--force` | Archive an existing active handoff and create a new one. |
| `--no-prompt` | Skip interactive prompts; leave placeholders. |

---

## 🔄 Lifecycle

```
[User: /handoff-start]
        │
        ▼
[python3 handoff_protocol/handoff.py start]
        │
        ▼
[.protocol/handoff_workspace/handoff-YYYYMMDD-HHMM.md created]
        │
        ▼
[session ends or pauses]
        │
        ▼
[new session: /handoff-resume]
        │
        ▼
[python3 handoff_protocol/handoff.py resume]
        │
        ▼
[agent reads handoff and continues]
        │
        ▼
[when done: python3 handoff_protocol/handoff.py done]
        │
        ▼
[handoff moved to .protocol/handoff_workspace/archive/]
```

---

## 🔗 Relationship to Green-Amber-Red Teams

This handoff protocol is **complementary** to the Traffic-Light teaming protocol:

- `.protocol/green_amber_red_workspace` structures **planning, execution, and auditing** across agents.
- `.protocol/handoff_workspace` preserves **session continuity** when a single agent session pauses or resumes.

The `handoff.py start` command auto-detects `.protocol/green_amber_red_workspace/plan.md` status and includes it in the handoff file.

---

## 📚 Full Specification

See [`HANDOFF_PROTOCOL.md`](./HANDOFF_PROTOCOL.md) for the complete protocol guide.
