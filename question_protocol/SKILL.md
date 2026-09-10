---
name: question_protocol
description: Asks concise labeled multi-question turns (Q1, Q2 with Q1-a/b options) and resolves short user replies including free-form overrides, skips, and late answers. Use whenever asking more than one question, offering choices, or resuming questions after compaction.
---

# Question Protocol Skill

Use this skill whenever you need to ask the user anything with choices, or ask more than one question in a turn.

---

## 🎯 Scope

This protocol is **conversation-scoped and compaction-safe**:
- `Q1, Q2...` never reuse mid-conversation; reset only on new conversation.
- Options are `Qn-a/b/c` case-insensitive (binary choices included).
- Free-form: `Qn:`, `Qn.`, `Qn=` are aliases. Multi-select: comma or plus. Skip: `Qn: skip` / `skip Qn`.
- Counter persists in `question_workspace/state.json`; recover via transcript scan after compaction.

---

## 🛠️ Autonomous Execution Steps

### Step 1: Locate or bootstrap

If `question_protocol/init_questions.py` exists, ensure directives are installed:

```bash
python3 question_protocol/init_questions.py --check
```

If not initialized, run the bootstrap (or manually append the directive block from `init_questions.py` to `AGENTS.md` / `CLAUDE.md` / `.cursorrules` / `GEMINI.md`). With no directive file present, the bootstrap asks (Q1-a) to create `AGENTS.md` (`--yes` assumes yes for scripted installs).

### Step 2: Ask with labels (delta + inline + importance)

Follow `templates/question_block.md`. Every choice — including yes/no — gets `Qn-a/b` labels, **inline** by default (`Q5. Retry? (a/backoff b/fixed-3 c/none)`; block layout only for long options). New questions full-text once; carried opens collapse to one line (`Q2. … → shown, SHOW Q2 for full text`). Mark importance at ask time: `Qn!` = must-answer, plain = answer-or-let-die. Titles ≤ ~60 chars. Max 4 open.

### Step 3: Resolve replies

1. Normalize: lowercase, strip optional `!`, accept `: / . / =` separators, `,` / `+` multi-select.
2. Map every `Qn[!]` / `Qn-x` / `En-Qn-x` to its question text. Unknown label → ask for clarification, never drop custom text.
3. Confirm tersely: `Resolved: Q1-a, Q2-custom(120s), Q3!-open.` Full mapping only on ambiguity.
4. Update `state.json` (`next_id`, open/closed). Plain skips auto-park (answerable, not re-listed, excluded from carry); `!` skips stay OPEN. Honor `Qn: drop` (kill), upgrades (`Qn! : …`), and resurrections by number.
5. `SHOW Qn` → re-show that question full-text immediately.

### Step 4: Long sessions and compaction

* At >99 closed questions, PROPOSE `Archive Q1-Q99 and re-baseline to Q1?` — only on approval. Archived refs become `E1-Q5`.
* After compaction/resume: read `state.json` + handoff Open Questions + scan transcript for max `Qn`; `next_id = max(all)+1`; announce `Recovered at Qx (epoch En), y open carried over` and re-list `!` opens in full (plain opens IDs-only).

---

## ✅ Completion Criteria

- [ ] Multi-question turns labeled `Q1, Q2...` monotonic per conversation.
- [ ] All choice lists (binary included) labeled `Qn-a/b/c`.
- [ ] Free-form (`: / . / =`), multi-select (`, / +`), and `skip Qn` all resolve.
- [ ] Late answers by original number resolve; delta re-lists used; `!` persists, plain auto-parks.
- [ ] `state.json` updated; re-baseline only on approval; recovery announced after compaction.
