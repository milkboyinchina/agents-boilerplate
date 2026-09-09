# 🎚️ Tier Routing Protocol

A portable, zero-dependency router that maps task tiers (`T1/T2/T3`) to per-tool model IDs at runtime — so vendor renames touch one registry file, never your tasks, plans, or slash commands.

Built for workspaces shared by several agentic tools (opencode, antigravity, codex, devin) whose catalogs churn:

- **Tiers, not IDs**: tasks declare `T1` trivial / `T2` standard / `T3` hard.
- **One ID home**: raw model IDs live only in `routing.yaml` `aliases:` (portable names like `claude-opus` everywhere else).
- **Sticky task pins**: `/pin-model claude-sonnet` when the T3 default fails — per-task, auto-releases on completion. No session pin exists.
- **Failover, never hard-fail**: dead IDs fall down chains with loud warnings.
- **Session-free freshness**: weekly dumb cron writes `heartbeat.json` (its sole output); drift triggers a pending proposal + one `Q1-a` approval.

---

## 💡 Why use this?

Without tier routing, model IDs get hardcoded where they rot: a `/hard-fix-sonnet` breaks on deprecation, every tool needs its own mapping, and a failing T3 default leaves you hand-switching models mid-task.

| Without this protocol | With this protocol |
|:---|:---|
| Model ID baked into commands/plans — renames break everything | Tasks declare `T1/T2/T3`; IDs live only in `routing.yaml` |
| One mapping per tool, maintained by hand in chat | Open `tools:` map + per-tool resolve; adding codex = one block |
| T3 default failing → manually re-brief another model | `/pin-model claude-sonnet` pins per-task till completion |
| Stale mappings discovered only when tasks fail | Weekly heartbeat + drift proposals + pre-commit stale gate |

---

## ⚡ Quick Start

```bash
# 1. Copy this folder into your project
cp -r /path/to/agents-boilerplate/tier_routing_protocol ./

# 2. Bootstrap (gitignore runtime files + directives)
python3 tier_routing_protocol/resolve_model.py --install

# 3. Fill IDs via the add-tool workflow, then validate
python3 tier_routing_protocol/resolve_model.py --validate

# 4. Resolve before executing a task
python3 tier_routing_protocol/resolve_model.py --tier T2 --tool opencode --task 3

# 5. Weekly freshness signal (OS-aware install, manual fallback in cron/)
python3 tier_routing_protocol/resolve_model.py --install-cron
```

Or tell your agent:

> *"Read `tier_routing_protocol/TIER_ROUTING.md` — resolve tiers via `resolve_model.py`, never hardcode model IDs."*

---

## 📁 Folder Layout

```
<project-root>/
├── .gitignore                              # += heartbeat.json + routing_state.json (init-managed)
└── tier_routing_protocol/
    ├── resolve_model.py                    # resolver + registry maintenance CLI
    ├── routing.yaml                        # THE registry (only raw IDs live here)
    ├── README.md / TIER_ROUTING.md / SKILL.md
    ├── routing_state.json                  # task pins (gitignored, runtime)
    ├── heartbeat.json                      # weekly cron output (gitignored, runtime)
    ├── routing_updates/pending-*.md        # refresh proposals (committed, review trail)
    ├── templates/
    │   ├── plan_tier_row.md                # Tier column snippet for plan.md
    │   └── slash_commands.md               # /hard-fix, /pin-model, /unpin defs
    ├── examples/
    │   ├── registry_four_tools.yaml        # filled example (4 tools)
    │   └── stale_registry.yaml             # --fail-on-stale demo fixture
    └── cron/
        ├── linux_cronjob_command.md
        ├── macos_launchd_command.md
        ├── windows_scheduler_command.md
        └── com.tierrouting.heartbeat.plist  # macOS launchd template
```

---

## 🛠️ CLI Reference

| Command | Description |
|:---|:---|
| `--tier T --tool NAME [--task ID]` | Resolve a tier to a model ID (prints `id  # via <layer>`). |
| `--force-tier T` / `--prefer ALIAS` | One-shot overrides (validated, logged). |
| `pin ALIAS --task ID` / `unpin --task ID` | Per-task sticky pin / early release. |
| `heartbeat` | Dumb-cron snapshot → `heartbeat.json` (exit 2 on drift). |
| `refresh [--cron] [--dry-run]` | Propose registry updates from drift (never applies). |
| `--install [--dry-run] [--force]` | Bootstrap: gitignore + directives. |
| `--install-cron` / `--uninstall-cron` | OS-aware weekly scheduler setup/removal. |
| `--check [--json]` | Registry, pins, gitignore, cron, directives status. |
| `--validate [--fail-on-stale]` | Structure + placeholder + staleness gate. |

Env: `MODEL_ROUTE_OVERRIDE` (`T1/T2/T3` or alias) sits between flags and pins. Kill switches: `TIER_ROUTING_ENABLED=0/1`, `TIER_ROUTING_<TOOL>_ENABLED=0/1` (disabled scope exits `3` = select manually).

---

## 🔄 Resolve Lifecycle

```
[Green: plan.md task-row gets Tier]
        │
        ▼
[Amber: resolve --tier T --tool X --task N → id # via <layer>]
        │
        ▼
[T3 default failing? → pin claude-sonnet --task N (sticky till COMPLETED)]
        │
        ▼
[Weekly cron → heartbeat.json → drift? → pending proposal → Q1-a → apply]
```

---

## 🔗 Relationship to Other Boilerplates

* `green_amber_red_teams`: Tier column in `plan.md` task table; Amber resolves pre-execution.
* `handoff_protocol`: record tier + resolved ID + active pin for resume recovery.
* `question_protocol`: refresh approvals + no-models-file branches are `Q1/Q1-a` turns.

---

## 📚 Full Specification

See [`TIER_ROUTING.md`](./TIER_ROUTING.md).
