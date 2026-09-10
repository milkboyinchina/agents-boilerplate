# Before / After: what each protocol changes

Skeptical? Good — that's the Red Team spirit. Below: the same work, with and
without each protocol. All files shown are plain markdown — human-readable and
followable without running anything.

*(Sections alphabetical by protocol, like everything else around here.)*

---

## 🟢 Green-Amber-Red Teams

**Without:** one session, plan/code/QC blended into chat soup, documentation only if you beg for it. Switch sessions or apps and the context evaporates.

```markdown
# Without — chat transcript (abridged, all 40 turns of it)
You: add retry with backoff to the API client
Agent: *writes code directly, no plan, no file list*
You: wait, which files did that touch? did you test it?
Agent: *scrolls up, guesses* uh, I think src/api.py? tests... probably fine?
You: *switches to another app, re-explains everything from zero*
```

**With:** the same session emits one file per team — a plan (green), coded tasks (amber), and an audit + verdict (red). New session? It reads the files and continues.

```markdown
# With — green_amber_red_workspace/plan.md (excerpt, actually committed to the flow)
> **Lifecycle Status**: `⏳ IN_PROGRESS`
| # | Task | Status | Who | Affected Files |
| 1 | Add exponential backoff | `[COMPLETED]` | Amber | src/api.py |
| 2 | Retry-path tests | `[IN_PROGRESS]` | Amber | tests/test_api.py |
# review-amberteam later appends: audit clean → ✅ COMPLETED
# review-redteam later appends: verdict PASS, packet archived
```

---

## 🔄 Handoff

**Without:** the IDE closes, the model changes, the evening ends — and tomorrow's session starts with "so… what were we doing?" followed by 20 minutes of re-briefing.

```markdown
# Without — new session, same human, zero memory
You: continue the auth work
Agent: which auth work? what was the last verified state? which files changed?
You: *pastes three chat excerpts, re-lists the files, re-states the next step*
```

**With:** last session ran `/handoff-start` (one command). New session runs `/handoff-resume` (one read) and continues from the exact Next Steps.

```markdown
# With — handoff_workspace/handoff-20260910-0037.md (excerpt)
## 2. Active Task / Plan Status
Plan status: ⏳ IN_PROGRESS | Active task: Task 2 (retry-path tests)
## 8. Next Steps
1. Run `pytest tests/test_api.py -k retry`
2. Then `review-amberteam`
```

---

## ❓ Question

**Without:** every agent interrogates you in its own house style, and your answers are paragraphs that drift — a bare "yes" could mean any of three questions, and the follow-up round is guaranteed.

```markdown
# Without — agent asks, human types an essay
Agent: Should I deploy tonight? Also what cache TTL do you want, and
  are we keeping the light theme or switching to dark?
You: hmm, not tonight — tomorrow morning would be better actually. For
  the TTL, 120 seconds I think? Not the 60 or 300 you mentioned.
  Theme... let me get back to you on that one.
Agent: sorry — the 120s was for which setting? and is theme a no?
```

**With:** identical `Q1-a`-style Q&A on every agent. Short labels, full context, skips that survive.

```markdown
# With — agent asks once, human answers in one line
Agent:
- Q5. Retry policy? (a/backoff b/fixed-3 c/none)
- Q6! Deploy to prod tonight? (a/yes b/no)
You: Q5-a, Q6: not tonight, deploy tomorrow morning
Agent: Resolved: Q5-a, Q6-custom(tomorrow AM).
```

---

## 🎚️ Tier Routing

**Without:** you hand-pick a model per task per tool, paste IDs into prompts, and every vendor rename silently breaks your setup — discovered, always, mid-task.

```markdown
# Without — Monday morning, per task, per tool
You: use claude-whatever-4.6 for this one [renamed last week, fails]
  ...switch model... okay now use gemini-flash-high for that one
  ...different app, different model name for the same thing...
```

**With:** the task declares a tier once; every tool resolves it to its own current model. A rename is a 1–2 line registry edit.

```markdown
# With — stamped once at plan time, resolved everywhere
| # | Task | Tier | Model (resolved) |
| 2 | Redesign auth flow | T3 | … # via tier default (T3) |
$ python3 tier_routing_protocol/resolve_model.py --tier T3 --tool opencode --task 2
```

---

*Token math for the curious: `README.md` → Token cost table. Figures are heuristics (~4 chars/token) — your mileage may vary.*
