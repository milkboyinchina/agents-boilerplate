# AGENTS.md — agents-boilerplate workspace

Agent directives for this boilerplate collection repo.

### ❓ Concise Question Protocol (`question-protocol/`)

1. **Label every question**: conversation-scoped monotonic `Q1, Q2, ...` (never reuse mid-conversation; reset only on new conversation). Single questions still use `Q1`.
2. **Label every choice**: `Qn-a/b/c...` case-insensitive — including binary (`yes/no`, `a/b`, `agree/disagree`, `proceed/cancel`).
3. **Free-form override**: accept `Qn: <text>` / `Qn. <text>` / `Qn= <text>` as aliases. Multi-select: `Q1-a,c` or `Q1-a+c`. Skip: `Qn: skip` / `skip Qn` (stays OPEN).
4. **Re-list Open + New** with full text every ask; max 4 open. Late answers by original number MUST resolve.
5. **Long sessions**: at >99 closed questions, PROPOSE `Archive Q1-Q99 and re-baseline to Q1?` — only on approval (archived refs `E1-Q5`).
6. **Compaction**: persist `question-protocol/state.json`; on resume `next_id = max(state, transcript max + 1)`, announce recovery and re-list open Qs.
