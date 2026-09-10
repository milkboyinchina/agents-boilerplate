# TODO — planned boilerplates

Tracked future work for this collection. Newest first. Checked items move to `CHANGELOG.md` on completion.

## Planned structural changes

- [ ] **`.protocol/` runtime consolidation** — move all runtime state under one hidden dir: `green_amber_red_workspace/`, `handoff_workspace/`, `question_workspace/`, `tier_routing_workspace/`, and the `redteam/` exchange dirs all relocate under `.protocol/`; sources (`*_protocol/`) stay at root, tracked. Single `.gitignore` line (`.protocol/`) replaces ~10 granular ones. Open: whether `redteam/` exchange moves too (Q58), gitignore form (Q59). Broad but mechanical: 4 CLI path constants, `--check` keys, cron reinstall, doc sweep, third migration wave with legacy detection (same one-version-grace pattern).

## Planned protocols

- [ ] **`architect_protocol/`** — durable codebase cartography (not task planning). Map new or existing apps so agents can look up blueprints and progress: app/module map, dependency edges, entry points, tech-stack record, per-area progress ledger (`mapped → planned → implemented → verified`). Full boilerplate shape (spec + CLI + templates + skill). Open design points: blueprint format (mapped workspace dir vs single file), greenfield + reverse-map coverage. (See `NEW_PROTOCOL_CHECKLIST.md` when starting.)
- [ ] **`agent_builder_protocol/`** — agent scaffolding installer. Empty workspace: detect project type, generate `AGENTS.md` + rules + skills matched to the stack. Existing workspace: audit current agent config, propose upgrades (never overwrite without backup + confirm). Distinct from per-protocol inits (which only inject their own block) — this one owns whole-file composition.
- [ ] **`memory_protocol/`** — long-term agent memory across sessions. Handoff preserves one interrupted session; compaction still wipes everything learned across missions. Append-only memory store (decisions, preferences, lessons) + recall rules. Compounds every other protocol.
- [ ] **`decision_protocol/`** — architecture decision records (ADRs). Numbered records with status (`proposed → accepted → superseded`) + templates. Green plans capture *what*; this captures *why*. Pairs with `architect_protocol` (decisions annotate the map).
- [ ] **`release_protocol/`** — release gates. Version bump, changelog entry, migration notes, rollout/rollback checklist, green-verdict-required-to-ship. The collection builds and verifies but never *ships* — this defines releasable.
- [ ] **`onboarding_protocol/`** — guided codebase tour for new agents/contributors, generated from the architect map. Cheapest to build *after* architect lands; weak standalone — schedule accordingly.

## Backlog (accepted, unscheduled)

- [ ] Re-copy + idempotent re-run in `android_app_auto_tester` to pick up post-`3f4e3c8` fixes.
- [ ] Fill real tier model IDs via the add-tool workflow (blocked on vendor catalog choices, not code).
- [ ] Reinstall/upgrade flow is now documented (root README Quick Start: pull/re-copy + re-run inits, idempotent by contract, changelog carries migrations). Keep it true: every future path rename must ship its migration commands in the changelog entry, and every init must stay re-runnable without data loss.

## Done (see CHANGELOG.md for details)

- [x] `green_amber_red_team_protocol/`, `handoff_protocol/`, `question_protocol/`, `tier_routing_protocol/`
- [x] Naming convention, runtime splits, packet system, defect ledger, install profiles, Q46-a, Q51-a fixes
