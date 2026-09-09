# Contributing & Forking Guide

This collection is built to be forked. Each folder is self-contained: copy what you need, adapt it, keep it verifiable. This guide shows how to do that without silently diverging from upstream.

Normative rules live in [`AGENTS.md`](./AGENTS.md) (workspace directives) and [`NEW_PROTOCOL_CHECKLIST.md`](./NEW_PROTOCOL_CHECKLIST.md) (new-protocol requirements). This file doesn't duplicate them — it links them.

---

## 1. Fork and adapt

```bash
# 1. Fork on GitHub (or clone directly for private use)
git clone https://github.com/milkboyinchina/agents-boilerplate.git
cd agents-boilerplate

# 2. Copy only what you need into your project
cp -r question_protocol /path/to/your-project/
```

**What's safe to change in your fork:**

* Boilerplate folder names — but follow the naming rule: spaces become `_`, always append `_protocol`.
* Registry contents (`routing.yaml` IDs, aliases, tool sections) — that's your data.
* CLI defaults (thresholds, cadence) to match your team.

**What must stay structurally intact:**

* The **source vs runtime split**: every boilerplate is source `*_protocol/` (tracked) plus runtime `*_workspace/` (gitignored) with unmistakably different names — `green_amber_red_team_protocol/` vs `green_amber_red_workspace/`, `handoff_protocol/` vs `handoff_workspace/`, and so on. Renaming one side without the other breaks installs — see the `📁` changelog entries for the full lesson.
* Registry/file schemas (`routing.yaml` subset, `state.json` shapes) — CLIs parse a fixed subset; checklists enforce it.

---

## 2. Verify locally (copy-paste battery)

```bash
# Compile all CLIs
python3 -m py_compile green_amber_red_team_protocol/init_teams.py \
  handoff_protocol/handoff.py question_protocol/init_questions.py \
  tier_routing_protocol/resolve_model.py

# Status + validators (all must be green)
python3 green_amber_red_team_protocol/init_teams.py --check
python3 question_protocol/init_questions.py --validate question_protocol/examples/good_example.md
python3 tier_routing_protocol/resolve_model.py --validate
python3 tier_routing_protocol/resolve_model.py --check

# Bootstrap idempotency (second run must print [SKIP]/[OK], never duplicate)
# -- run each --install/--init twice in a /tmp scratch dir, as in §3 below.

# Stale-name sweep (adapt the patterns to your rename)
grep -rn --exclude-dir=.git --exclude=CHANGELOG.md \
  -e 'model_routing_protocol' -e 'green-amber-red-teams' -e 'handoff-protocol' -e 'question-protocol' .
# Expect: no output (CHANGELOG.md history is intentionally untouched).
```

```bash
# 3. Temp-lifecycle pattern (never test bootstraps in this repo)
rm -rf /tmp/opencode/scratch && mkdir -p /tmp/opencode/scratch
cp <protocol>/init_*.py /tmp/opencode/scratch/   # or resolve_model.py
# ... run init → use → archive/remove → --check, all inside scratch ...
rm -rf /tmp/opencode/scratch
```

---

## 3. Stay in sync with upstream

```bash
# Once, in your fork:
git remote add upstream https://github.com/milkboyinchina/agents-boilerplate.git

# Regularly:
git fetch upstream
git merge upstream/main   # or: git rebase upstream/main
```

Keep local adaptations in clearly separated commits (rename vs behavior vs registry data) so upstream fixes merge cleanly. If you change a shared schema, propose it back upstream instead of forking the format.

---

## 4. Conventions (normative sources)

* Folder naming, README benefit sections, runtime gitignore, changelog discipline → [`AGENTS.md`](./AGENTS.md).
* New-protocol requirements (files, CLI parity, verification) → [`NEW_PROTOCOL_CHECKLIST.md`](./NEW_PROTOCOL_CHECKLIST.md).
* User-facing install flow → [`README.md`](./README.md) Quick Start.

---

## 5. What NOT to commit

Runtime state is per-machine and gitignored by each bootstrap CLI. Never force-add:

* `question_workspace/state.json`
* `tier_routing_workspace/heartbeat.json`, `tier_routing_workspace/routing_state.json`
* `green_amber_red_workspace/` workspaces, `handoff_workspace/handoff-*.md` active files
* `green_amber_red_team_protocol/redteam/{inbox,outbox,inbox-archive,outbox-archive}/*` packet contents (both sides)
* `__pycache__/`, `*.pyc`

Reviewable history (`routing_updates/pending-*.md`, archived handoffs/plans) **is** committed — that's the audit trail, not state.
