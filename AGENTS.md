# AGENTS.md — agents-boilerplate workspace

Agent directives for this boilerplate collection repo.

### ❓ Concise Question Protocol (`question_protocol/`)

1. **Label every question**: conversation-scoped monotonic `Q1, Q2, ...` (never reuse mid-conversation; reset only on new conversation). Single questions still use `Q1`.
2. **Label every choice**: `Qn-a/b/c...` case-insensitive — including binary (`yes/no`, `a/b`, `agree/disagree`, `proceed/cancel`). Default to **inline options** for token efficiency: `Q5. Retry? (a/backoff b/fixed-3 c/none)`.
3. **Free-form override**: accept `Qn: <text>` / `Qn. <text>` / `Qn= <text>` as aliases. Multi-select: `Q1-a,c` or `Q1-a+c`. Skip: `Qn: skip` / `skip Qn`.
4. **Delta asks**: new questions full-text once; carried opens collapse to one line (`Q2. … → shown, SHOW Q2 for full text`). Max 4 open. Late answers by original number MUST resolve.
5. **Importance flags**: `Qn!` = must-answer (persists through skip + compaction); plain `Qn` = answer-or-let-die (auto-parks if skipped, still answerable by number). User controls: `Qn! : keep asking`, `Qn: drop` kills it.
6. **Long sessions**: at >99 closed questions, PROPOSE `Archive Q1-Q99 and re-baseline to Q1?` — only on approval (archived refs `E1-Q5`).
7. **Compaction**: persist `question_workspace/state.json`; on resume `next_id = max(state, transcript max + 1)`, announce recovery and re-list `!` opens in full (plain opens IDs-only).

### 🎚️ Tier Routing Protocol (`tier_routing_protocol/`)

1. **Tasks declare tiers, never model IDs**: `T1` trivial, `T2` standard, `T3` hard. Green Team stamps Tier per task-row in `plan.md`.
2. **Resolve at runtime**: `python3 tier_routing_protocol/resolve_model.py --tier <T> --tool <name> --task <id>`. Raw IDs live only in `routing.yaml` `aliases:`.
3. **Precedence (later wins, always logged)**: tier default → `--force-tier` → `MODEL_ROUTE_OVERRIDE` → task pin (`/pin-model <alias>`, auto-releases on `[COMPLETED]`, `/unpin` releases early). No session pin exists.
4. **Failover, never hard-fail**: dead IDs fall down `fallbacks:` chains with a loud warning.
5. **Freshness**: weekly dumb cron writes `heartbeat.json` (sole cron output, gitignored); drift triggers a pending proposal + `Q1-a` approval turn. Stale heartbeat (>10d) = unknown, check live.

### 📏 Boilerplate Authoring Rules (this repo)

1. **Folder naming**: spaces become `_`, always append `_protocol` (e.g. `tier_routing_protocol/`, `question_protocol/`). Never kebab-case, never bare names. Runtime state dirs MUST be unmistakably distinct from source folders (e.g. `green_amber_red_workspace/` vs `green_amber_red_team_protocol/`) — one-letter differences are a defect.
2. **Listing order**: protocol-listing tables and sections are alphabetical by protocol folder name (green, handoff, question, tier). The green 10-command table keeps its own owner→alphabetical rule — different table, different sort key.
3. **README benefit section**: every boilerplate README carries `## 💡 Why use this?` right after the intro — one-line benefit plus a `Without this protocol | With this protocol` comparison table.
4. **Runtime gitignore**: each bootstrap CLI gitignores its runtime files at init (idempotent, skip-if-present); source folders stay committed. Users opt out by deleting the lines.
5. **Changelog**: every change logged in `CHANGELOG.md` reverse-chronological order; never rewrite history entries.
6. **New protocols**: follow `NEW_PROTOCOL_CHECKLIST.md` before first commit.
7. **Custom command naming**: team-scoped commands use `<verb>-<team>` with a short alias (`plan-greenteam`/`plan-green`, `exec-amber`, `send-red`); protocol-wide commands use `<verb>-<protocol>` (`verify-green-amber-red-team`, no alias). Document both forms in the canonical alias table and cover both in verification greps.
