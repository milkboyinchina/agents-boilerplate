# TODO — planned boilerplates

Tracked future work for this collection. Newest first. Checked items move to `CHANGELOG.md` on completion.

## Planned protocols

- [ ] **`architect_protocol/`** — durable codebase cartography (not task planning). Map new or existing apps so agents can look up blueprints and progress: app/module map, dependency edges, entry points, tech-stack record, per-area progress ledger (`mapped → planned → implemented → verified`). Full boilerplate shape (spec + CLI + templates + skill). Open design points: blueprint format (mapped workspace dir vs single file), greenfield + reverse-map coverage. (See `NEW_PROTOCOL_CHECKLIST.md` when starting.)
- [ ] **`agent_builder_protocol/`** — agent scaffolding installer. Empty workspace: detect project type, generate `AGENTS.md` + rules + skills matched to the stack. Existing workspace: audit current agent config, propose upgrades (never overwrite without backup + confirm). Distinct from per-protocol inits (which only inject their own block) — this one owns whole-file composition.

## Backlog (accepted, unscheduled)

- [ ] Re-copy + idempotent re-run in `android_app_auto_tester` to pick up post-`3f4e3c8` fixes.
- [ ] Fill real tier model IDs via the add-tool workflow (blocked on vendor catalog choices, not code).

## Done (see CHANGELOG.md for details)

- [x] `green_amber_red_team_protocol/`, `handoff_protocol/`, `question_protocol/`, `tier_routing_protocol/`
- [x] Naming convention, runtime splits, packet system, defect ledger, install profiles, Q46-a, Q51-a fixes
