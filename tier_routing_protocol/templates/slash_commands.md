# Slash command definitions (aliases only — never raw model IDs)

## /hard-fix

Force Tier 3 + strongest reasoning for this resolve. One-shot, unpinned.
Replaces hardcoded model-specific commands, which break on vendor renames.

```bash
python3 tier_routing_protocol/resolve_model.py --tier T3 --tool <name> --task <id> --force-tier T3
```

## /pin-model <alias>

Pin a portable alias to the active task when the tier default keeps failing.
Example: Antigravity's T3 `gemini-flash` high variant fails repeatedly:

```bash
python3 tier_routing_protocol/resolve_model.py pin claude-sonnet --task <id>
```

* Per-task only — auto-releases on `[COMPLETED]`. No session pin exists.
* Unknown alias aborts with the valid list from `routing.yaml`.

## /unpin

Release the active task's pin early (routing defaults apply again):

```bash
python3 tier_routing_protocol/resolve_model.py unpin --task <id>
```
