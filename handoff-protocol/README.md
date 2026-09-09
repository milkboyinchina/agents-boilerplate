# 🔄 Project-Local Session Handoff Protocol

A portable, zero-dependency protocol for pausing and resuming AI agent sessions within a single project workspace.

Unlike global quota-based handoffs, this protocol is **manual**:
- `/handoff-start` — capture the current state.
- `/handoff-resume` — continue from the last handoff.

All handoff files live inside the project-local `handoff-protocol/` folder, which is automatically gitignored.

---

## ⚡ Quick Start

```bash
# 1. Copy this folder into your project
cp -r /path/to/agents-boilerplate/handoff-protocol ./

# 2. Start a handoff
python3 handoff-protocol/handoff.py start --no-prompt

# 3. Later, resume from it
python3 handoff-protocol/handoff.py resume

# 4. When the task is complete, archive the handoff
python3 handoff-protocol/handoff.py done
```

Or tell your agent:

> *"Read `handoff-protocol/HANDOFF_PROTOCOL.md` and use `/handoff-start` and `/handoff-resume` for session continuity."*

---

## 📁 Folder Layout

```
<project-root>/
├── .gitignore                              # contains handoff-protocol/
└── handoff-protocol/
    ├── handoff.py                          # CLI
    ├── README.md                           # this file
    ├── HANDOFF_PROTOCOL.md                 # full specification
    ├── SKILL.md                            # agent skill definition
    ├── templates/
    │   └── handoff-template.md             # 9-field template
    ├── handoff-YYYYMMDD-HHMM.md            # active handoff
    └── archive/
        └── handoff-YYYYMMDD-HHMM.md        # completed handoffs
```

---

## 🛠️ CLI Reference

```bash
python3 handoff-protocol/handoff.py [OPTIONS] <COMMAND>
```

| Command | Description |
|---|---|
| `start` | Create a new active handoff file. |
| `resume` | Print a resume summary from the active handoff. |
| `done` | Move the active handoff to `handoff-protocol/archive/`. |
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
[python3 handoff-protocol/handoff.py start]
        │
        ▼
[handoff-protocol/handoff-YYYYMMDD-HHMM.md created]
        │
        ▼
[session ends or pauses]
        │
        ▼
[new session: /handoff-resume]
        │
        ▼
[python3 handoff-protocol/handoff.py resume]
        │
        ▼
[agent reads handoff and continues]
        │
        ▼
[when done: python3 handoff-protocol/handoff.py done]
        │
        ▼
[handoff moved to handoff-protocol/archive/]
```

---

## 🔗 Relationship to Green-Amber-Red Teams

This handoff protocol is **complementary** to the Traffic-Light teaming protocol:

- `green-amber-red-teams` structures **planning, execution, and auditing** across agents.
- `handoff-protocol` preserves **session continuity** when a single agent session pauses or resumes.

The `handoff.py start` command auto-detects `green_amber_red_teams/plan.md` status and includes it in the handoff file.

---

## 📚 Full Specification

See [`HANDOFF_PROTOCOL.md`](./HANDOFF_PROTOCOL.md) for the complete protocol guide.
