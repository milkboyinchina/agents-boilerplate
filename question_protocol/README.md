# ❓ Concise Question Protocol

A portable, zero-dependency convention for concise multi-question turns: agents label `Q1, Q2...` and `Q1-a/b/c...`, users reply with short labels or free-form overrides.

Unlike ad-hoc questioning, this protocol is **conversation-scoped and compaction-safe**:
- `Q1, Q2...` never reuse mid-conversation — skipped questions stay answerable later.
- `Q1: / Q1. / Q1=` free-form aliases, case-insensitive options, `skip Qn` support.
- Counter survives compaction via `question_protocol/state.json` + transcript scan.
- Re-baseline at >99 closed questions, only on user approval.

---

## 💡 Why use this?

Without labeled questions, multi-question turns force you to retype full sentences, a bare "yes" is ambiguous about *which* question it answers, and skipped questions silently die — worse after compaction wipes session memory.

| Without this protocol | With this protocol |
|:---|:---|
| Retype full answers or quote blocks to stay clear | Reply `Q1-a, Q2: custom text` — short labels, full context |
| "Yes" could mean any of three questions | Every choice is `Qn-a/b` (binary included), case-insensitive |
| Skipped question is forgotten by next turn | `Qn: skip` stays OPEN; late answers by original number resolve |
| Compaction erases what was asked | Counter in `state.json` + transcript scan recovers numbering |

---

## ⚡ Quick Start

```bash
# 1. Copy this folder into your project
cp -r /path/to/agents-boilerplate/question_protocol ./

# 2. Run the bootstrap
python3 question_protocol/init_questions.py

# 3. Validate a transcript
python3 question_protocol/init_questions.py --validate question_protocol/examples/good_example.md
```

Or tell your agent:

> *"Read `question_protocol/QUESTION_PROTOCOL.md` and follow the concise question protocol for all multi-question turns."*

---

## 📁 Folder Layout

```
<project-root>/
└── question_protocol/
    ├── init_questions.py               # bootstrap + validator CLI
    ├── README.md                       # this file
    ├── QUESTION_PROTOCOL.md            # full specification
    ├── SKILL.md                        # agent skill definition
    ├── state.json                      # counter + open questions (gitignored, created on first ask)
    ├── templates/
    │   ├── question_block.md           # agent-side ask template
    │   └── answer_block.md             # user-side reply template
    └── examples/
        ├── good_example.md             # passing fixture
        └── bad_example.md              # failing fixture
```

---

## 🛠️ CLI Reference

```bash
python3 question_protocol/init_questions.py [OPTIONS]
python3 question_protocol/init_questions.py --validate <file>
```

| Option | Description |
|:---|:---|
| `--dry-run` | Print what would be created without writing to disk. |
| `--force` | Re-write directive block even if already present. |
| `--check` | Report whether the workspace is already initialized. |
| `--json` | Output `--check` / `status` results as JSON. |
| `--validate <file>` | Lint a transcript for Q-label compliance (exit 1 on violations). |
| `--quiet` | Suppress non-essential output. |

`status` is reported via `--check`: `directives_ok`, `state.json` presence, `next_id`, `epoch`, open count.

---

## 🔄 Ask / Answer Lifecycle

```
[Agent asks: Q5, Q6 with Q5-a/b options + full text]
        │
        ▼
[User replies: Q5-a, Q6: custom text  OR  Q6: skip]
        │
        ▼
[Agent resolves, confirms, updates state.json]
        │
        ▼
[Skipped Q stays OPEN, answerable later by original number]
        │
        ▼
[>99 closed → agent proposes archive + re-baseline to Q1]
```

---

## 🔗 Relationship to Other Boilerplates

* `green_amber_red_teams`: `amber-check` confirmations MUST use `Q1-a) Yes / Q1-b) No`.
* `handoff_protocol`: include Open Questions (`Qn` + status) in handoff files for resume recovery.

---

## 📚 Full Specification

See [`QUESTION_PROTOCOL.md`](./QUESTION_PROTOCOL.md) for the complete protocol guide.
