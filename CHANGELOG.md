# agents-boilerplate: Changelog & Agent Execution Log

All changes to this boilerplate collection MUST be logged here in **reverse-chronological order**.

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
