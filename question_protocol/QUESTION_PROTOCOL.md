# ❓ Question Protocol Specification

> **Quick Start**: In any project, copy the `question_protocol/` folder and run:
> ```bash
> python3 question_protocol/init_questions.py
> ```
> Then tell your agent: *"Follow `question_protocol/QUESTION_PROTOCOL.md` for all multi-question turns."*

This document defines a **concise, label-based question/answer convention** so users can reply with short `Q1-a`-style answers and agents can still resolve full context — including skips, late answers, long sessions, and context compaction.

---

## 1. Purpose

Without labels, multi-question turns force users to retype full sentences or quote blocks. With labels:

* Agent asks once with clear labels.
* User replies concisely (`Q1-a, Q2: custom text`).
* Agent resolves each label back to the original question — even if the user skipped, answered late, or the session was compacted.

---

## 2. Core Rules

### Rule 1 — Number questions `Q1, Q2, ...` (conversation-scoped, monotonic)

* Numbering is **per conversation, monotonically increasing**. Never reuse a number mid-conversation.
* Reset to `Q1` **only** on a new conversation (new session / `/clear` / explicit new task).
* A single question still uses `Q1` so replies are always parseable.
* Numbers stay short to type: `Q47-a` is 5 chars, `Q123-a` is 6 chars. Recall (not typing) is the real cost — solved by Rule 5.

### Rule 2 — Label every choice `Qn-a, Qn-b, ...` (case-insensitive)

* **Any** choice list gets labels — including binary ones (`yes/no`, `a/b`, `agree/disagree`, `proceed/cancel`).
* Casing is **not enforced**: `Q1-a`, `Q1-A`, `q1-a` all mean the same. Agents MUST normalize to lowercase before resolving.
* Default to **inline options** (one line, ~60% fewer tokens than block layout):
```markdown
Q1. Deploy now? (a/yes, deploy b/no, wait)
```
Block layout stays allowed for long or complex options:
```markdown
Q1. Deploy now?
- Q1-a) Yes, deploy
- Q1-b) No, wait
```

### Rule 3 — Free-form override (all three separators accepted)

If no choice fits, reply with free text using **any** of these (they are aliases):

* `Q1: I want dark mode with SSO`
* `Q1. I want dark mode with SSO`
* `Q1= I want dark mode with SSO`

Agents MUST treat the text after the separator as a custom answer, never as an error.

### Rule 4 — Multi-select and skip

* Multi-select: `Q1-a,c` or `Q1-a+c` (comma or plus, case-insensitive).
* Skip explicitly so the agent knows it is deferred, not ignored:
  * `Q2: skip` or `skip Q2`
* A skipped question stays **OPEN** and remains answerable later by its original number (e.g. answering `Q2: ...` three turns later still resolves to the same question).

### Rule 5 — Delta asks (new full-text once, carried opens collapse)

New questions are asked full-text (inline options) exactly once. Carried opens
collapse to one short line — the user already saw the full text:

```markdown
**Open:**
- Q2. Cache TTL? → shown last turn, reply SHOW Q2 for full text

**New:**
- Q5. Retry policy? (a/backoff b/fixed-3 c/none)
- Q6! Deploy to prod tonight? (a/yes b/no)
```

* Full text is mandatory on: first ask, post-compaction recovery, new session, changed options, or `SHOW Qn` request.
* Question titles stay ≤ ~60 chars; detail lives in the first full ask, not in re-lists.
* Max **4 open** questions at a time. If more accumulate, agent MUST ask which to park/close first.
* User never answers from memory — always copy the visible `Qn` label.

### Rule 6 — Importance flags (`!` = must-answer, plain = answer-or-let-die)

The agent marks importance **at ask time**: `Q6!` must be answered; plain `Q2`
may be answered or left to die.

* **Skipped plain question** → auto-parked: stays answerable by number (numbers
  never reuse, so `Q2: …` three turns later still resolves), but stops
  re-listing and is excluded from compaction carry. Token cost after the ask: zero.
* **Skipped `!` question** → full persistence: stays OPEN, delta re-listed,
  carried through `state.json` + handoff + compaction recovery.
* User controls the flag: `Q2! : keep asking me` upgrades to persistent,
  citing a parked number resurrects it, `Q2: drop` kills it explicitly.
* Unmarked defaults to plain: a wrongly-expired question costs a cheap re-ask,
  a wrongly-persisted one costs N turns of re-list tax — fail toward cheap.

---

## 3. Agent Parse-Back Obligation

On receiving a reply, the agent MUST:

1. Normalize each token: lowercase, accept `:` / `.` / `=` separators, accept `,` / `+` multi-select.
2. Map every `Qn` / `Qn-x` back to its original question text. If a label is unknown, ask for clarification — never silently drop custom text.
3. Confirm resolution tersely (IDs + outcomes; full mapping only on ambiguity):
```markdown
Resolved: Q1-a, Q2-custom(120s), Q3!-open.
```
4. Update `.protocol/question_workspace/state.json` (`next_id`, open/closed status).

---

## 4. Long Sessions — Re-baseline at Q99 (user-approved only)

* When closed question count exceeds **99**, the agent PROPOSES (never auto-executes):
  > *"Archive Q1-Q99 and re-baseline to Q1?"*
* Only on explicit user approval:
  1. Move `Q1-Q99` to archive in `state.json` under epoch `E1`.
  2. Reset counter to `Q1` for the new epoch (`E2`).
  3. Old refs become `E1-Q5` style and rarely need typing.
* Validator accepts both `Qn[-x]` (current epoch) and `En-Qn[-x]` (archived epoch).

---

## 5. Compaction Survival

Question state is file-backed so context summarization (`/compact`, `/clear` summaries, model switches) does not lose the counter:

* State file: `.protocol/question_workspace/state.json` (gitignored after bootstrap):
```json
{"next_id": 6, "epoch": 2, "open": [{"id": "Q2", "text": "Cache TTL?"}], "archived_epochs": ["E1"]}
```
* Recovery rule on resume (`/handoff-resume` or fresh session):
  1. Read `state.json` + active `.protocol/handoff_workspace/` handoff (Open Questions section, if present).
  2. Scan visible transcript for highest `Qn` / `En-Qn`.
  3. `next_id = max(state.next_id, transcript_max + 1, handoff_max + 1)`.
  4. Announce: `Recovered at Qx (epoch En), y open carried over.` Then re-list open Qs with original numbers and full text.
* If sources conflict (file says Q10, transcript has Q14), take the max and log a warning.

---

## 6. Relationship to Other Protocols

* **Green-Amber-Red Teams**: `execute-amberteam` ("Should the agent proceed?") MUST use this protocol (`Q1-a) Yes, proceed / Q1-b) No`) instead of a bare yes/no.
* **Handoff Protocol**: `handoff.py start` SHOULD include an Open Questions section (question IDs + status) so a resumed session can recover the counter.

---

## 7. Verification Checklist

- [ ] Multi-question turns use `Q1, Q2, ...` monotonic per conversation.
- [ ] Every choice list (including binary) has `Qn-a/b/c` labels.
- [ ] `Qn:`, `Qn.`, `Qn=` free-form all resolve.
- [ ] `skip Qn` / `Qn: skip` keeps the question open.
- [ ] Late answer (`Q2` answered 3 turns later) resolves correctly.
- [ ] Delta asks: new full-text once, carried opens collapsed; max 4 open enforced.
- [ ] Importance flags: `!` persists through skip + compaction, plain auto-parks but stays answerable by number.
- [ ] Re-baseline proposed at >99 closed, only on approval, old refs as `En-Qn`.
- [ ] Counter recovers after compaction via `state.json` + transcript scan.
