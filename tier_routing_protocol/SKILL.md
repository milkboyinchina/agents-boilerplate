---
name: tier_routing_protocol
description: Resolves task tiers (T1/T2/T3) to per-tool model IDs via routing.yaml, manages task pins, and runs registry refresh. Use when assigning models to tasks, pinning Sonnet/Opus for failing T3 work, or refreshing stale model mappings.
---

# Tier Routing Skill

Tasks declare tiers. Only `routing.yaml` `aliases:` holds raw model IDs. Never invent, hardcode, or repeat a model ID in plans, commands, or chat.

---

## 🛠️ Autonomous Execution Steps

### Step 0: Install (once per workspace)

`python3 tier_routing_protocol/resolve_model.py --install` (with no directive file present, it asks Q1-a to create `AGENTS.md`; `--yes` assumes yes for scripted installs).

### Step 1: Assign (Green Team plans, Amber Team resolves)

Green Team stamps Tier per task-row (`templates/plan_tier_row.md`). Before executing, Amber resolves:

```bash
python3 tier_routing_protocol/resolve_model.py --tier <T1|T2|T3> --tool <opencode|antigravity|…> --task <id>
```

Log the attribution line (`via …`) into the task row. A revert to defaults must always be visible. Exit `3` means routing is disabled for that scope — proceed with manual model selection, do not treat it as failure. Check `--check` for the winning enable/disable source.

### Step 2: Pin when the default keeps failing

T3 default failing (e.g. Antigravity's `gemini-flash` high variant)? Pin — never hand-edit a model ID:

```bash
python3 tier_routing_protocol/resolve_model.py pin claude-sonnet --task <id>
```

Pins bind per-task and auto-release on `[COMPLETED]`; `/unpin --task <id>` releases early. Aliases only — unknown alias aborts with the valid list.

### Step 3: Refresh the registry (propose → approve → apply)

1. Check: `resolve_model.py --validate` (add `--fail-on-stale` in CI/pre-commit).
2. If stale/drifted: `resolve_model.py refresh` (or `--cron` non-interactive) → writes `routing_updates/pending-*.md`, never edits `routing.yaml`.
3. Ask the Q9-a turn: `Q1. Apply refresh? Q1-a) Yes` with the diff quoted.
4. On `Q1-a`: edit delta lines only, bump `verified:` dates, re-run `--validate`.

### Step 4: No-models-file branch (Q13-a)

If heartbeat/discovery reports a tool with no `models_file`, ask — never guess:

```markdown
Q1. <tool> exposes no models file for the cron.
- Q1-a) Point at a different file (reply Q1: <path>)
- Q1-b) Paste the model list manually (one-time snapshot)
- Q1-c) Mark manual-only (cron skips; warnings + pre-commit hook cover freshness)
```

### Step 5: Add a tool (codex, devin, …)

Append one `tools:` section (tiers → aliases, `discover.models_file`, `verified:`), fill `aliases.*.ids.<tool>` (placeholders fail `--validate` until filled or the tool is marked manual), run `--validate` + `refresh --dry-run`, commit.

---

## ✅ Completion Criteria

- [ ] No raw model ID outside `routing.yaml` `aliases:`.
- [ ] Every executed task logged its resolve attribution.
- [ ] Pins are per-task with release path; no session pin exists.
- [ ] Registry edits landed only via propose → `Q1-a` → apply → `--validate` green.
