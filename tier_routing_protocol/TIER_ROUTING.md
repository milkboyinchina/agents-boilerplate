# 🎚️ Tier Routing Protocol Specification

> **Quick Start**: In any project, copy the `tier_routing_protocol/` folder and run:
> ```bash
> python3 tier_routing_protocol/resolve_model.py --install
> ```
> Then tell your agent: *"Follow `tier_routing_protocol/TIER_ROUTING.md` — tasks declare tiers, never model IDs."*

This document defines a **tier-indirection model router** for workspaces shared by several agentic tools (opencode, antigravity, codex, devin, …) whose model catalogs change regularly.

Core rule: **a raw model ID appears in exactly one place — `routing.yaml` `aliases:`.** Tasks, plans, slash commands, and chat history reference only tiers (`T1/T2/T3`) and portable aliases (`claude-opus`). Model deprecation then means editing 1–2 lines, never hunting through commands.

---

## 1. Tiers (tool-neutral, written once)

| Tier | Use for | Typical shape |
|:---|:---|:---|
| **T1** | Trivial: formatting, single-file edits, Q&A, doc touch-ups | Fast/cheap model, small context OK |
| **T2** | Standard: multi-file features, refactors, test coverage | Balanced model, large context |
| **T3** | Hard: architecture, hairy debugging, security, open-ended design | Strongest reasoning available |

Tiers are capability descriptors, not models. They never change when vendors rename models.

---

## 2. Registry (`routing.yaml`) — the single source of truth

Two halves:

* `tiers:` — the table above, machine-readable (never per-tool).
* `tools:` — open map, one section per tool (`opencode:`, `antigravity:`, …). Each section maps tiers to **aliases** and carries a `discover:` hint plus a `verified:` date.
* `aliases:` — portable names → per-tool concrete IDs + `fallbacks:` (alias-level) + `verified:` date.

Adding codex/devin = appending one named block (see §8 `add-tool` workflow). Keep to the file's documented YAML subset — `--validate` rejects anything outside it.

---

## 3. Resolution precedence (later wins, always logged)

1. `routing.yaml` tier default for the tool.
2. `--force-tier T3` (one-shot CLI flag).
3. Env `MODEL_ROUTE_OVERRIDE` (`T1/T2/T3` or an alias).
4. **Task pin** (`/pin-model <alias>`) — binds to Amber's active task ID, auto-releases on `[COMPLETED]`, removable early via `/unpin`. No session-wide pin exists by design (a forgotten pin would silently steer later tasks).

Every resolve prints which layer won: `resolved claude-opus via pin[task-3]`. A revert to defaults is therefore always visible, never silent.

---

## 4. Failover (nothing hard-fails on deprecation)

* Dead tier default → next alias in that tier's `fallbacks:` chain.
* Dead pin → fail over **with a loud warning** (`pin claude-opus unreachable → fell back to T3 default`). Sticky never means stuck on a corpse.
* Unknown tool section → `defaults:` capabilities apply with `--lenient` (warn) or error with `--strict`.

---

## 5. Slash commands (aliases only, never IDs)

* `/hard-fix` — force T3 + strongest reasoning for this resolve (unpinned, one-shot). The hardened successor to hardcoded `/hard-fix-sonnet`.
* `/pin-model <alias>` — e.g. `/pin-model claude-opus`. Pins the alias to the active task (T3 default keeps failing → pin Sonnet/Opus and stay there until the task completes).
* `/unpin` — release the active task's pin early.

---

## 6. Freshness without sessions (weekly dumb cron + change-triggered propose)

* **Dumb cron (~zero tokens):** a plain script follows each tool's `discover: {models_file: <path>}` hint, hashes the live ID lists, and overwrites exactly one file: `tier_routing_protocol/heartbeat.json` (gitignored). Exit `0` written / `2` drift vs previous heartbeat / `1` all tools failed.
* **Agent read (one file, ~zero tokens):** hash matches registry → done. Hash drifted → agent diffs, writes `routing_updates/pending-YYYYMMDD.md` (committed), and asks the Q9-a approval turn (`Q1. Apply? Q1-a) Yes`). Only deltas are edited; `verified:` dates bumped; `--validate` must pass before landing.
* **Stale heartbeat = unknown:** `last_check` older than ~10 days (host asleep, cron dead) → agent checks live directly instead of trusting it.
* **Cron proposes, never applies.** The weekly job cannot corrupt, conflict with, or dirty anything reviewable.
* **Free guards:** resolving is a local script call (no LLM). Per-resolve staleness warnings (`--stale-after 30d` default) plus the optional pre-commit hook (`--validate --fail-on-stale`) catch rot at commit time for free.

---

## 7. No-models-file fallback (Q13-a)

`discover:` is file-path-only. If a tool exposes no models file (or the path is missing at cron time):

1. Cron records `{"ok": false, "error": "…"}` for that tool, keeps any previous snapshot, still writes the heartbeat.
2. The agent — on reading it, or during `add-tool`/refresh — raises a question_protocol turn: `Qn. <tool> has no models file. Qn-a) Point at a different file (reply Qn: <path>) / Qn-b) Paste the model list manually (one-time snapshot, gets a verified: date) / Qn-c) Mark manual-only (cron skips it; freshness via warnings + pre-commit hook)`.

---

## 8. `add-tool` workflow (opencode/antigravity ship first; codex/devin are appends)

1. Append `tools: {<name>: {models: {T1,T2,T3 → aliases}, discover: {models_file}, verified: <today>}}`.
2. Fill any missing `aliases: → ids:` entries for the new tool (placeholders fail `--validate` until filled or marked manual).
3. Run `--validate` + `refresh --dry-run`; commit registry + heartbeat baseline.

---

## 9. Scheduler install (OS-aware, exact-manual fallback)

`--install-cron` detects the OS via stdlib `platform.system()`:

* **Linux** → marker-tagged crontab line (`# tier-routing-heartbeat`), idempotent by marker grep.
* **macOS** → launchd plist (`com.tierrouting.heartbeat.plist`) + `launchctl load`.
* **Windows** → `schtasks /Create` (guarded to Windows only).

Every path is wrapped: on failure (or skip), init prints the exact manual command **and** leaves committed docs under `cron/` (`linux_cronjob_command.md`, `macos_launchd_command.md`, `windows_scheduler_command.md`) so copy-paste works verbatim. Scheduler failure never fails the bootstrap. `--check` reports scheduler presence per platform; `--install-cron` / `--uninstall-cron` are re-runnable. See `cron/` docs.

---

## 10. Gitignore (init-managed, manual opt-out)

Bootstrap appends (idempotent, skip-if-present):

* `tier_routing_protocol/heartbeat.json` — weekly cron output.
* `tier_routing_protocol/routing_state.json` — pins + resolver state.

The folder itself stays committed. `routing_updates/pending-*.md` stays committed (review trail). Remove the lines from `.gitignore` if you want runtime state versioned. `--check` reports `gitignore_ok`.

---

## 11. Relationship to other protocols

* **Green-Amber-Red Teams**: Green Team stamps a Tier per task-row in `plan.md` (see `templates/plan_tier_row.md`); Amber resolves via `resolve_model.py --tier <T> --tool <name> --task <id>` before executing.
* **Handoff Protocol**: handoff files record active tier + resolved model + active pin so a resumed session recovers routing without re-asking.
* **Question Protocol**: refresh approvals and no-models-file branches use `Q1/Q1-a` turns.

---

## 12. Verification checklist

- [ ] Tasks/plans/commands contain no raw model IDs (`--validate` enforces).
- [ ] `--tier T2 --tool opencode` resolves; layer attribution printed.
- [ ] Dead ID fails over with warning; unknown tool obeys `--lenient`/`--strict`.
- [ ] `/pin-model` binds per-task, auto-releases on `[COMPLETED]`, `/unpin` releases early; no session pin exists.
- [ ] Stale registry warns (`--stale-after`); `--validate --fail-on-stale` fails.
- [ ] `refresh --cron` writes only a pending proposal, never `routing.yaml`.
- [ ] Heartbeat is the cron's sole output; >10-day-old heartbeat treated as unknown.
- [ ] `.gitignore` contains both runtime files after bootstrap; `--check` green.
