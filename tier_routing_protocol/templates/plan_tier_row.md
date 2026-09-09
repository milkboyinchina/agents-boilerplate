# Tier column snippet for green_amber_red_teams/plan.md task tables

Add a `Tier` column (stamped by Green Team) and a `Model (resolved)` column
(filled by Amber Team after running resolve_model.py):

| # | Task | Status | Tier | Model (resolved) | Who | Affected / Edited Files | Effort |
|:--|:---|:---:|:---:|:---|:---:|:---|:---:|
| 1 | Add retry policy | `[PLANNED]` | T2 | `… # via tier default (T2)` | Amber Team | • `src/retry.py` | ~20m |
| 2 | Redesign auth flow | `[PLANNED]` | T3 | `… # via task pin (claude-opus, task 2)` | Amber Team | • `src/auth/*` | ~60m |

Resolve before executing:

```bash
python3 tier_routing_protocol/resolve_model.py --tier T2 --tool opencode --task 1
```
