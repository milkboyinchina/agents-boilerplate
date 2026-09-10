# agents-boilerplate: Changelog & Agent Execution Log

All changes to this boilerplate collection MUST be logged here in **reverse-chronological order**.

---

## 📝 [2026-09-10] Install Profiles (minimal/standard/full) Kill the Five Questions
- **Agent / Author**: Muse Spark (OpenCode)
- **Lifecycle Status**: `[COMPLETED]`
- **Scope / Components**:
  - Root README Quick Start: profile table + one-paste prompts + recorded defaults (seed-no, red-skip, cron-skip, placeholders-OK, handoff-CLI-only).
  - All four `--help` texts cross-point to the profiles (one line each, no behavior change).
- **Quality & Verification Results**:
  - `py_compile` ×4; `--help` pointers present ×4; `--check`/`--validate` green; each profile maps 1:1 onto existing commands (no new flags).

---

## 📝 [2026-09-10] Root README Humor Pass + Token Cost Tables + COMPARISON.md
- **Agent / Author**: Muse Spark (OpenCode)
- **Lifecycle Status**: `[COMPLETED]`
- **Scope / Components**:
  - Root README light-touch humor (playful headers/intros, dry procedures; commands/numbers untouched) + `### Token cost: with vs without` 5-row table (alphabetical) + methodology/YMMV note + `COMPARISON.md` link.
  - New `COMPARISON.md`: before/after transcripts per protocol (alphabetical), all files plain markdown.
  - Protocol verdict lines: question full sub-table; green/handoff/tier one-liners linking root table + COMPARISON.
  - Governance: alphabetical-listing rule added to authoring rules (green 10-command table exempt, own sort key).
- **Quality & Verification Results**:
  - Root/protocol figure consistency checked; links resolve (`COMPARISON.md`, `../README.md`, `../COMPARISON.md`); no code touched.

---

## ❓ [2026-09-10] Question Protocol: Token Efficiency (Delta + Inline + Importance)
- **Agent / Author**: Muse Spark (OpenCode)
- **Lifecycle Status**: `[COMPLETED]`
- **Scope / Components**:
  - Q42-a: delta asks (new full-text once, carried opens collapse + `SHOW Qn`), inline options default, terse resolve echo, ≤60-char titles.
  - Q43-a: `!` importance flags — `!` persists through skip + compaction, plain auto-parks (answerable, zero re-list), upgrade/resurrect/drop paths, plain-default.
  - Validator grammar accepts optional `!` (QREF + REPLY_TOKEN); SKILL resolve step strips it before mapping; template + good fixture rewritten in new form.
- **Quality & Verification Results**:
  - `py_compile` green; good fixture passes (delta + `!` + multi-select), bad fixture still fails with same 5 violations; `--check` directives + gitignore green.

---

## 📁 [2026-09-10] Q40-b: Source/`*_workspace/` Split for Handoff, Question, Tier
- **Agent / Author**: Muse Spark (OpenCode)
- **Lifecycle Status**: `[COMPLETED]`
- **Scope / Components**:
  - Uniform rule, no exceptions: `handoff_protocol/` → runtime `handoff_workspace/`; `question_protocol/state.json` → `question_workspace/state.json`; tier heartbeat/state → `tier_routing_workspace/` (`routing_updates/` stays committed in source).
  - Each CLI: version bump, legacy-dir/file detection with `mv` hints (stderr-safe JSON), template/config loads repointed at source, gitignore lines swapped, `--check` gains workspace + legacy keys.
  - Fixes found live: handoff legacy check false-positived on the source copy (now requires handoff artifacts); `pin`/`unpin` rejected `--quiet`; heartbeat crashed on a stale `proto` reference.
  - Docs swept (layouts, paths, checklists); governance already exception-free; `CHANGELOG.md` history frozen.
  - Migration prompts (ERP/sandbox): handoff rescue artifacts → `handoff_workspace/` + refresh copy; question/tier `mkdir` + `mv` + gitignore swap (all in CLI warnings).
- **Quality & Verification Results**:
  - `py_compile` ×4; old-runtime-path grep zero outside history (only intentional migration-hint strings remain).
  - Handoff: fresh start→resume→done→status on `handoff_workspace/`, second start idempotent, template loads from source copy.
  - Question: init + migrated `next_id` preserved, gitignore + directives OK, good fixture validates.
  - Tier: resolve/pin/heartbeat/refresh/stale-fixture all green on new paths; `--install` writes new gitignore lines.
  - Green init smoke unaffected (only docs changed this round for green).

---

## 🚦 [2026-09-09] Green Runtime Rename (unmistakable source/runtime split)
- **Agent / Author**: Muse Spark (OpenCode)
- **Lifecycle Status**: `[COMPLETED]`
- **Scope / Components**:
  - Runtime `green_amber_red_teams/` → `green_amber_red_workspace/` (`WORKSPACE_DIR`; source folder untouched). One-letter source/runtime similarity retired as a defect class.
  - `init_teams.py`: legacy-dir detection in `--check` (`legacy_workspace_found` + `mv` hint, one-version grace).
  - Swept all runtime refs (docs, handoff plan-detect, battery, `.gitignore:24`); source refs intact.
  - Governance: authoring rules + checklist now require unmistakably distinct runtime names.
  - Migration prompt (ERP/sandbox): `mv green_amber_red_teams green_amber_red_workspace`, re-run init, drop the stale gitignore line by hand.
- **Quality & Verification Results**:
  - Caught live during verify: sweep had overwritten `LEGACY_WORKSPACE_DIR` (self-match) + legacy WARN polluted `--json` stdout — both fixed (exclusion note in code, WARN → stderr).
  - Green temp lifecycle on new path (plan + ledger + skeleton + packet gitignore, idempotent); legacy demo warns + JSON stays clean; red temp lifecycle skeleton-only.
  - `py_compile` ×4, other three CLIs sanity-green, old-runtime-name grep zero outside history.

---

## 🚦 [2026-09-09] Green Protocol: Defect Ledger with Who/When Lifecycle
- **Agent / Author**: Muse Spark (OpenCode)
- **Lifecycle Status**: `[COMPLETED]`
- **Scope / Components**:
  - New `templates/defect_ledger.md` + live green-side `green_amber_red_teams/defects.md` (runtime, gitignored; init-created, never overwritten).
  - Single-writer-per-field: red findings via reports only, green transcribes + owns fix fields; lifecycle `OPEN→ACKED→IN_FIX→FIXED→VERIFIED→CLOSED` all stamped; IDs `BUG-YYYYMMDD-NNN`; reopening creates a new row.
  - Wired into `review-redteam` (transcribe/reconcile), `recheck-redteam` (snapshot diff), verify checklist, `--check` (`ledger_exists`), SKILL criteria, ERP adapter mapping table.
- **Quality & Verification Results**:
  - Authorship grep: every `defects.md` mention enforces green-side/red-never-writes; `py_compile` green.
  - Green temp lifecycle: ledger created from template; appended row survived re-run (never-overwrite guard); `--check` `ledger_exists: true`.
  - Red temp lifecycle (`--side red` fresh): no workspace, no ledger, skeleton true.

---

## 🚦 [2026-09-09] Green Protocol: 10-Command Rename + Red Packet System
- **Agent / Author**: Muse Spark (OpenCode)
- **Lifecycle Status**: `[COMPLETED]`
- **Scope / Components**:
  - Folder `green_amber_red_teams_protocol/` → `green_amber_red_team_protocol/` (singular `team`); runtime `green_amber_red_teams/` frozen.
  - 10 commands + aliases: `plan-greenteam`/`plan-green`, `review-greenteam`/`review-green` (agent-agnostic plan QA), `execute-amberteam`/`exec-amber` (confirm gate preserved), `review-amberteam`/`review-amber`, `send-redteam`/`send-red`, `verify-green-amber-red-team`, `review-redteam`/`review-red`, `test-redteam`/`test-red`, `finish-redteam`/`finish-red`, `recheck-redteam`/`recheck-red`. `check-plan` removed (read plan directly; drift via verify).
  - Packet exchange: `redteam/` layout both sides, `packet_green|red_YYYYMMDD_HHMM`, cross-ack handshake, append-only-same-cycle, air-gap carry paths, plan-version citation, `config.yml` (`side:`, reachability, kill switch, `return_to:`).
  - `init_teams.py` v1.1.0: `--side green|red`, redteam skeleton + stamped config, packet-contents gitignore (init-emitted in targets), side-aware `--check`, wrong-side refusal doctrine in specs.
  - Mission brief + defect-report templates (version-stamped); sequential dual-red + risk-tiered isolation documented; QC-layers rule (Layer 3 on user-facing/risky/privacy-sensitive).
  - Mirrors: README (command table, lifecycle, redteam section, QC layers), INITIALIZE, SKILL, root README, question refs, AGENTS.md command-naming rule, checklist + CONTRIBUTING hygiene notes.
  - ERP migration prompt: copy renamed folder over, re-run init both sides (`--side red` in sandbox), delete old folder, re-point custom triggers (`read-fix`/`amber-code` unaffected — brief maps them).
- **Quality & Verification Results**:
  - `py_compile` ×4 green CLIs + others green; old-name grep zero outside history (both alias forms present everywhere).
  - Green temp lifecycle: `--init-plan` → plan created; `--check` reports side green, skeleton + packet gitignore OK; re-run idempotent (`[SKIP]`/`[OK]`).
  - Red temp lifecycle: `--side red` fresh → no plan workspace, skeleton + `side: red` config + packet gitignore; side switch green→red updates config only.
  - `--check` JSON carries `side`, `packet_gitignore_ok`, `redteam_skeleton_ok` on both sides.

---

## 🚦 [2026-09-09] Green Protocol: Red Team Handoff Ownership + Verdict Flow
- **Agent / Author**: Muse Spark (OpenCode)
- **Lifecycle Status**: `[COMPLETED]`
- **Scope / Components**:
  - Clarified: Green Team runs `send-redteam` (audit-gate handoff) and `check-redteam` (reads defect report, records verdict); Red Team works in an isolated session with no shortcut.
  - Verdict handling: PASS stays `✅ COMPLETED`; FAIL reopens tasks, flips to `⏳ IN_PROGRESS`, Amber fixes, `green-review` re-audits, gate re-runs.
  - `green-plan` overwrite guard for non-completed plans (warn + confirm).
  - Mirrored across INITIALIZE doc, README (personas + lifecycle), SKILL.md, `init_teams.py` directive block + workspace template. Deployed workspaces pick it up on re-run (`--force`/fresh inject).
- **Quality & Verification Results**:
  - Role-label grep consistent (Green on both shortcuts, every mention); `py_compile` + temp `--init-plan` smoke green.

---

## 📝 [2026-09-09] CONTRIBUTING.md Forking Guide
- **Agent / Author**: Muse Spark (OpenCode)
- **Lifecycle Status**: `[COMPLETED]`
- **Scope / Components**:
  - New `CONTRIBUTING.md`: fork-and-adapt path (safe vs structural changes, source/runtime split lesson), copy-paste verification battery, upstream-sync workflow, conventions pointers, what-not-to-commit list.
- **Quality & Verification Results**:
  - Every battery command executed from the repo root: compile ×4, `--check`, both validators green; stale-name sweep clean (sole hit is the guide quoting its own command).

---

## 📝 [2026-09-09] Root README: Own-Section Quick Start + Workflow One-Liners
- **Agent / Author**: Muse Spark (OpenCode)
- **Lifecycle Status**: `[COMPLETED]`
- **Scope / Components**:
  - New `## ⚡ Quick Start` own section: download-or-clone → copy protocol(s) → ask agent with example prompts → verify with `--check`.
  - One-line workflow summaries under the boilerplate table (planned/confirmed/audited; pause-resume; one-line answers; right-model-per-task).
  - Trimmed the four duplicated per-boilerplate Usage blocks to Quick Start pointers (documented once, can't drift).
- **Quality & Verification Results**:
  - No `Usage in any repo` leftovers; section order intro → Quick Start → table → summaries verified.

---

## 📝 [2026-09-09] Tier README Refresh + Green Agnosticism Lead
- **Agent / Author**: Muse Spark (OpenCode)
- **Lifecycle Status**: `[COMPLETED]`
- **Scope / Components**:
  - Rewrote tier README `Why use this?` for a general audience (vanilla-agent framing: right-model-per-task, zero selection load, rename-proofing, failover) — removed personal `/hard-fix-sonnet` reference.
  - Scrubbed `/hard-fix-sonnet` from spec §5 + slash template (reworded to model-specific commands); verified zero hits outside history.
  - Tier README: new Enable/disable subsection (file vs env, precedence, exit 3, heartbeat-skip).
  - Green README: tool-agnosticism as the lead benefit + cross-tool handoff table row.
- **Quality & Verification Results**:
  - Repo-wide scrub grep clean; `--validate` + question `--validate` green.

---

## 🎚️ [2026-09-09] Tier Routing: Enable/Disable Kill Switches
- **Agent / Author**: Muse Spark (OpenCode)
- **Lifecycle Status**: `[COMPLETED]`
- **Scope / Components**:
  - `routing.yaml`: top-level `enabled:` + per-tool `tools.<name>.enabled:` (default true); env `TIER_ROUTING_ENABLED` / `TIER_ROUTING_<TOOL>_ENABLED` for temporary toggles (e.g. hand-picking free models in opencode).
  - Precedence file workspace → file per-tool → env workspace → env per-tool, winning source logged. Disabled scope: resolver exits `3` (select manually), `pin` refuses, heartbeat records `disabled: true` and skips, refresh leaves it alone, `--check` reports state.
  - `TIER_ROUTING.md` §13, README/SKILL exit-3 handling. Injected `AGENTS.md` block intentionally frozen.
  - Fixed: `heartbeat`/`refresh` subcommands rejected `--quiet` (argparse), which also broke the generated cron command — both accept it now.
- **Quality & Verification Results**:
  - Matrix in temp workspace: baseline 0, file-off 3, env-off 3, env-beats-file 0, pin-refusal 3, pin/unpin OK, heartbeat skip recorded, refresh proposal excluded disabled tool, re-enable instant.
  - `py_compile` + shipped `--validate`/`--check` green.

---

## 📏 [2026-09-09] README Benefit Pass + Workspace Governance
- **Agent / Author**: Muse Spark (OpenCode)
- **Lifecycle Status**: `[COMPLETED]`
- **Scope / Components**:
  - Added standard `## 💡 Why use this?` (benefit + Without/With table) to all four boilerplate READMEs.
  - Fixed stale refs: `handoff_template.md` in handoff README/SKILL, snake fixture names in question README/SKILL, `TEMPLATE_NAME` constant in `handoff.py` (was silently falling back to default template), root README ordinals, tier README cron layout (+ plist).
  - `AGENTS.md`: installed tier-routing directives via `--install`; appended Boilerplate Authoring Rules (naming, benefit section, runtime gitignore, changelog).
  - New `NEW_PROTOCOL_CHECKLIST.md` meta authoring checklist (naming, required files, benefit shape, hygiene, docs, verification).
  - `.gitignore`: added tier runtime lines (init-managed); green line unchanged (runtime name frozen).
- **Quality & Verification Results**:
  - Repo-wide grep: zero stale filenames outside `CHANGELOG.md` history.
  - `--check` green on all four CLIs; temp lifecycles re-run post-change.

---

## 📁 [2026-09-09] `_protocol` Naming Convention (green + tier renames)
- **Agent / Author**: Muse Spark (OpenCode)
- **Lifecycle Status**: `[COMPLETED]`
- **Scope / Components**:
  - `green_amber_red_teams/` → `green_amber_red_teams_protocol/` (source only; runtime `green_amber_red_teams/` frozen per Q12-b — `.gitignore` line unchanged).
  - `model_routing_protocol/` → `tier_routing_protocol/` (includes cron marker → `tier-routing-heartbeat`, plist → `com.tierrouting.heartbeat`).
  - Classified sweep: source-context refs renamed, runtime `plan.md`/workspace refs kept. `CHANGELOG.md` history untouched.
  - Migration prompt for deployed workspaces: copy renamed folders over, re-run inits (idempotent), delete old folders, commit. Green collision note: copy source to a temp path if runtime `green_amber_red_teams/` exists, run init from there, delete temp copy.
- **Quality & Verification Results**:
  - `git mv` renames staged as renames; post-sweep grep confirms remaining `green_amber_red_teams` hits are all runtime-context.

---

## 🎚️ [2026-09-09] Tier Routing Protocol Portable Boilerplate v1.0.0
- **Agent / Author**: Muse Spark (OpenCode)
- **Lifecycle Status**: `[COMPLETED]`
- **Scope / Components**:
  - Created portable `model_routing_protocol/` boilerplate: tiers (T1/T2/T3) resolve to per-tool IDs at runtime; raw IDs only in `routing.yaml` `aliases:`.
  - Planner stamps Tier per `plan.md` task-row; Amber resolves pre-execution with layer attribution.
  - Precedence: tier default → `--force-tier` → `MODEL_ROUTE_OVERRIDE` → per-task pin (`/pin-model`, auto-release on `[COMPLETED]`, `/unpin` early). No session pin.
  - Failover chains with loud warnings; `--lenient`/`--strict` for unknown tools.
  - Freshness: weekly dumb cron → `heartbeat.json` (sole output, gitignored); drift → `routing_updates/pending-*.md` + Q9-a approval; >10d heartbeat = unknown.
  - `discover.models_file` file-path-only hints (Q13-a) + no-models-file agent ask-branch; per-tool `add-tool` workflow (opencode/antigravity/codex/devin seeded).
  - OS-aware `--install-cron` (Linux cron / macOS launchd / Windows schtasks) with exact-manual fallback docs in `cron/`; init-managed gitignore (manual opt-out); `--check` covers registry/pins/gitignore/cron/directives.
- **Affected Files**: `model_routing_protocol/` (spec, `routing.yaml`, `resolve_model.py`, `SKILL.md`, `README.md`, `templates/`, `examples/`, `cron/`), `README.md`.
- **Quality & Verification Results**:
  - `py_compile resolve_model.py` → passed (after fixing subset-parser `{}`→`[]` list-block + inline `[]` bugs found by `--validate`).
  - `--validate` shipped registry → valid, 6 aliases / 4 tools + stale warnings; `--fail-on-stale` → exit 1; `--registry stale_registry.yaml` → exit 1 as designed.
  - Temp lifecycle: `--install` idempotent (`[UPDATE]`→`[SKIP]`), resolve with layer attribution, `pin`/`unpin`, `--force-tier`, `MODEL_ROUTE_OVERRIDE`, alias+tier failover chains with warnings.
  - `heartbeat` exit 0 → 2 on drift; `refresh --cron` wrote proposal only; missing-models-file Q13 branches surface per tool.

---

## 📁 [2026-09-09] Snake_case Rename + init_questions Gitignore Fix
- **Agent / Author**: Muse Spark (OpenCode)
- **Lifecycle Status**: `[COMPLETED]`
- **Scope / Components**:
  - Renamed source folders via `git mv` (history preserved): `green-amber-red-teams/` → `green_amber_red_teams/`, `handoff-protocol/` → `handoff_protocol/`, `question-protocol/` → `question_protocol/`; kebab file names → snake (`handoff_template.md`, `question_block.md`, `answer_block.md`, `good_example.md`, `bad_example.md`).
  - Swept 100+ kebab references across `*.md`/`*.py` (14 files). `CHANGELOG.md` history intentionally untouched — entries below this one reference pre-rename paths.
  - Runtime dirs frozen (Q12-b): no migration shim in CLIs. `init_questions.py` gained `ensure_gitignore` (`question_protocol/state.json`) + `gitignore_ok` in `--check`.
  - Migration prompt for deployed workspaces (ERP, QA sandbox): copy the three renamed folders over, re-run the three inits (idempotent — blocks match, not duplicated), delete old kebab folders, commit. If a target already has runtime `green_amber_red_teams/`, copy the boilerplate to a temp path, run init from there, then delete the temp copy (avoids source/runtime name collision).
- **Quality & Verification Results**:
  - Post-sweep grep: zero kebab references outside `CHANGELOG.md`.
  - `py_compile` ×3 CLIs → passed; `--validate` good/bad fixtures → pass/fail as before.

---

## ❓ [2026-09-09] Applied Question Protocol to agents-boilerplate Workspace
- **Agent / Author**: Muse Spark (OpenCode)
- **Lifecycle Status**: `[COMPLETED]`
- **Scope / Components**:
  - Created `AGENTS.md` and ran `question-protocol/init_questions.py` bootstrap (directives installed).
  - Initialized `question-protocol/state.json` (`next_id: 1`, `epoch: 1`, 0 open).
  - Gitignored `question-protocol/state.json` (runtime counter state).
- **Quality & Verification Results**:
  - `--check` → `directives_ok: true`, `state_exists: true`, `next_id: 1`, `rebaseline_threshold: 99`.
  - `--validate good-example.md` → passed.
---

## ❓ [2026-09-09] Question Protocol Portable Boilerplate v1.0.0
- **Agent / Author**: Muse Spark (OpenCode)
- **Started**: `2026-09-09T16:00:00+07:00`
- **Finished**: `2026-09-09T16:30:00+07:00`
- **Lifecycle Status**: `[COMPLETED]`
- **Scope / Components**:
  - Created portable `question-protocol/` boilerplate for concise multi-question turns.
  - Conversation-scoped monotonic `Q1, Q2...` (never reuse mid-conversation); `Q1-a/b/c` case-insensitive options including binary yes/no.
  - Free-form overrides `Q1:` / `Q1.` / `Q1=` aliases, multi-select (`,`/`+`), `skip Qn` with carryover.
  - Compaction-safe counter via `question-protocol/state.json` + transcript-max recovery + handoff integration.
  - Re-baseline at >99 closed: agent proposes `Archive Q1-Q99 and re-baseline to Q1?` (approval only, archived refs `E1-Qn`).
  - Built zero-dependency `init_questions.py` with `--dry-run`, `--force`, `--check`, `--json`, `--quiet`, `--validate`.
  - Provided `README.md`, full spec (`QUESTION_PROTOCOL.md`), skill (`SKILL.md`), templates + good/bad examples.
- **Affected Files**:
  - `README.md`
  - `CHANGELOG.md`
  - `question-protocol/init_questions.py`
  - `question-protocol/README.md`
  - `question-protocol/QUESTION_PROTOCOL.md`
  - `question-protocol/SKILL.md`
  - `question-protocol/templates/question-block.md`
  - `question-protocol/templates/answer-block.md`
  - `question-protocol/examples/good-example.md`
  - `question-protocol/examples/bad-example.md`
- **Quality & Verification Results**:
  - `python3 -m py_compile question-protocol/init_questions.py` → passed.
  - `python3 question-protocol/init_questions.py --help` → help displayed correctly.
  - `--validate good-example.md` → passed (covers Q1-a, `Q2:` free-form, `Q3: skip`, late answer, `Q4-A` uppercase, `Q4-a+c` multi-select).
  - `--validate bad-example.md` → correctly failed with 5 violations (bare Yes/No, bare `a)` labels, non-monotonic Q1-after-Q3).
  - `--check --json` / `--dry-run` → correct status output, no writes.
  - Temp-repo injection test → first run `[UPDATE]`, second run `[SKIP]` (idempotent), `--check` reports `directives_ok: true`.

---

## 🔵 [2026-09-09] Handoff Protocol Portable Boilerplate v1.0.0
- **Agent / Author**: Antigravity AI Engineering Team
- **Started**: `2026-09-09T15:07:27+07:00`
- **Finished**: `2026-09-09T15:12:18+07:00`
- **Lifecycle Status**: `[COMPLETED]`
- **Scope / Components**:
  - Created project-local `handoff-protocol/` boilerplate for session continuity.
  - Implemented manual triggers only: `/handoff-start` and `/handoff-resume`.
  - Built single CLI `handoff.py` with `start`, `resume`, `done`, `status` subcommands.
  - Provided 9-field handoff template (Session Metadata, Active Task, Files Changed, Recent Changes, Verification, Rollback, Blockers, Next Steps, Additional Notes).
  - Auto-detect `git status` and `green_amber_red_teams/plan.md` when present.
  - Gitignore `handoff-protocol/` and archive completed handoffs.
- **Affected Files**:
  - `README.md`
  - `CHANGELOG.md`
  - `handoff-protocol/handoff.py`
  - `handoff-protocol/README.md`
  - `handoff-protocol/HANDOFF_PROTOCOL.md`
  - `handoff-protocol/SKILL.md`
  - `handoff-protocol/templates/handoff-template.md`
- **Quality & Verification Results**:
  - `python3 -m py_compile handoff-protocol/handoff.py` → passed.
  - `python3 handoff-protocol/handoff.py --help` → subcommands displayed correctly.
  - Full lifecycle test in temp repo → `start`, `status --json`, `resume`, `done`, `status --json` all behaved correctly.
  - `.gitignore` auto-appended with `handoff-protocol/`.
  - Active handoff archived to `handoff-protocol/archive/` by `done`.
  - `--force` correctly archived existing active handoff before creating a new one.
  - `green_amber_red_teams/plan.md` auto-detection test → correctly extracted lifecycle status and active task.

---

## 🔴 [2026-09-09] Propagate Boilerplates to ERP Workspace & QA Sandbox
- **Agent / Author**: Antigravity AI Engineering Team
- **Started**: `2026-09-09T15:57:54+07:00`
- **Finished**: `2026-09-09T16:03:39+07:00`
- **Lifecycle Status**: `[COMPLETED]`
- **Scope / Components**:
  - Propagated `green-amber-red-teams/` and `handoff-protocol/` boilerplates to MilkTechERP workspace.
  - Removed obsolete ERP `.agents/rules/11_temporary_agent_plan_protocol.md` and `.agents/skills/initialize-teams/`.
  - Updated QA sandbox terminology to Green/Amber/Red teams.
  - Removed global OpenCode handoff config in favor of project-local protocol.
- **Affected Files**:
  - `../ERP/AGENTS.md`
  - `../ERP/.gitignore`
  - `../ERP/green_amber_red_teams/`
  - `../ERP/handoff-protocol/`
  - `../ERP/.agents/rules/11_temporary_agent_plan_protocol.md`
  - `../ERP/.agents/skills/initialize-teams/SKILL.md`
  - `~/Documents/erp_opencode_qa_sandbox/AGENTS.md`
  - `~/Documents/erp_opencode_qa_sandbox/.agents/rules/02_fix_verification_protocol.md`
  - `~/Documents/erp_opencode_qa_sandbox/skills/fix-verification/SKILL.md`
- **Quality & Verification Results**:
  - OpenCode global handoff files removed; only `local-git-guard.md` remains in `~/.config/opencode/rules/`.
  - ERP workspace handoff protocol initialized and `.gitignore` updated.
  - Sandbox active directive files verified free of Blue Team terminology.

---

## 🟠 [2026-09-09] Green-Amber-Red Teams Portable Boilerplate v1.0.0
- **Agent / Author**: Antigravity AI Engineering Team
- **Started**: `2026-09-09T14:29:46+07:00`
- **Finished**: `2026-09-09T14:35:54+07:00`
- **Lifecycle Status**: `[COMPLETED]`
- **Scope / Components**:
  - Initialized independent `agents-boilerplate` repository at `/home/milkboy/Documents/agents-boilerplate/`.
  - Created portable `green-amber-red-teams/` boilerplate.
  - Implemented zero-dependency Python 3 bootstrap CLI (`init_teams.py`) with `--dry-run`, `--force`, `--check`, `--json`, `--init-plan`, and `--template` support.
  - Added plan templates for `generic`, `backend`, `frontend`, `mobile`, and `devops`.
  - Provided `README.md`, full protocol guide (`INITIALIZE_GREEN_AMBER_RED_TEAMS.md`), and agent skill definition (`SKILL.md`).
  - Kept MilkTechERP workspace files untouched.
- **Affected Files**:
  - `README.md`
  - `.gitignore`
  - `CHANGELOG.md`
  - `green-amber-red-teams/init_teams.py`
  - `green-amber-red-teams/README.md`
  - `green-amber-red-teams/INITIALIZE_GREEN_AMBER_RED_TEAMS.md`
  - `green-amber-red-teams/SKILL.md`
  - `green-amber-red-teams/templates/*.md`
- **Quality & Verification Results**:
  - `python3 -m py_compile green-amber-red-teams/init_teams.py` → passed.
  - `python3 green-amber-red-teams/init_teams.py --help` → help displayed correctly.
  - `python3 green-amber-red-teams/init_teams.py --dry-run --init-plan "Test feature" --template backend` → all dry-run steps reported correctly.

---

*End of log.*
