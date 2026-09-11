# ❓ Concise Question Protocol

A portable, zero-dependency convention for concise multi-question turns: agents label `Q1, Q2...` and `Q1-a/b/c...`, users reply with short labels or free-form overrides.

Unlike ad-hoc questioning, this protocol is **conversation-scoped, token-lean, and compaction-safe**:
- `Q1, Q2...` never reuse mid-conversation — skipped questions stay answerable later.
- `Q1: / Q1. / Q1=` free-form aliases, case-insensitive options, `skip Qn` support.
- Delta asks + inline options: new questions full-text once, carried opens collapse to one line.
- Importance flags: `Qn!` persists through skip + compaction; plain skips auto-park (zero re-list cost).
- Counter survives compaction via `.protocol/question_workspace/state.json` + transcript scan.
- Re-baseline at >99 closed questions, only on user approval.

---

## 💡 Why use this?

Without labeled questions, multi-question turns force you to retype full sentences, a bare "yes" is ambiguous about *which* question it answers, and skipped questions silently die — worse after compaction wipes session memory.

| Without this protocol | With this protocol |
|:---|:---|
| Retype full answers or quote blocks to stay clear | Reply `Q1-a, Q2: custom text` — short labels, full context |
| "Yes" could mean any of three questions | Every choice is `Qn-a/b` (binary included), case-insensitive |
| Skipped question is forgotten by next turn — or re-asked forever, burning tokens | `Qn!` stays OPEN; plain skips auto-park (still answerable, zero re-list cost) |
| Compaction erases what was asked | Counter in `state.json` + transcript scan recovers numbering |

### Token cost: with vs without

Heuristic (~4 chars/token, medium questions) — **your mileage may vary** by model, tokenizer, and session habits:

| Situation | Without (est.) | With (est.) | Saving |
|:---|:---|:---|:---|
| 3 questions, all answered | ~300–400 (retyped answers + clarification round) | ~90–100 (labels + terse echo) | ~65–75% |
| Trivial skip, 10-turn session | ~30–70 (re-asked or re-listed) | 0 after the ask (auto-park) | ~100% of re-list |
| Interruption + recovery | ~300 (full re-brief) | ~50 (`!` opens re-listed) | ~80% |
| Single trivial binary Q | ~30 (bare yes/no wins) | ~35–40 | net-negative — don't invoke here |

Full before/after transcripts: [`COMPARISON.md`](../COMPARISON.md). Root rollup table: [`README.md`](../README.md).

---

## ⚡ Quick Start

```bash
# Place the collection per root README Quick Start, then run from workspace root.
# 1. Run the bootstrap
python3 agents-boilerplate/question_protocol/init_questions.py

# 2. Validate a transcript
python3 agents-boilerplate/question_protocol/init_questions.py --validate agents-boilerplate/question_protocol/examples/good_example.md
```
Standalone fallback (project can't carry the collection): copy this folder to root (`cp -r agents-boilerplate/question_protocol ./`) and run the same commands without the `agents-boilerplate/` prefix.

Or tell your agent:

> *"Read `question_protocol/QUESTION_PROTOCOL.md` and follow the concise question protocol for all multi-question turns."*

---

## 📁 Folder Layout

```
<project-root>/
├── .protocol/question_workspace/                 # RUNTIME (gitignored)
│   └── state.json                      # counter + open questions (created on first ask)
└── question_protocol/                  # SOURCE (committed): CLI + docs + templates
    ├── init_questions.py               # bootstrap + validator CLI
    ├── README.md                       # this file
    ├── QUESTION_PROTOCOL.md            # full specification
    ├── SKILL.md                        # agent skill definition
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

* `.protocol/green_amber_red_workspace`: `execute-amberteam` confirmations MUST use `Q1-a) Yes / Q1-b) No`.
* `handoff_protocol`: include Open Questions (`Qn` + status) in handoff files for resume recovery.

---

## 📚 Full Specification

See [`QUESTION_PROTOCOL.md`](./QUESTION_PROTOCOL.md) for the complete protocol guide.
