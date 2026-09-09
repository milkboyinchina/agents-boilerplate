# Linux cron — manual install (weekly heartbeat)

`--install-cron` attempts this automatically. If it failed, run verbatim
(replace `<workspace>` with the project root):

```bash
# 1. Inspect current crontab
crontab -l

# 2. Install (idempotent marker: tier-routing-heartbeat)
(crontab -l 2>/dev/null; echo '# tier-routing-heartbeat'; echo '0 2 * * 0 /usr/bin/python3 <workspace>/tier_routing_protocol/resolve_model.py heartbeat --quiet') | crontab -

# 3. Verify
crontab -l | grep tier-routing-heartbeat
python3 <workspace>/tier_routing_protocol/resolve_model.py --check
```

Remove:

```bash
crontab -l | grep -v 'tier-routing-heartbeat' | grep -v 'resolve_model.py heartbeat' | crontab -
# or: python3 <workspace>/tier_routing_protocol/resolve_model.py --uninstall-cron
```

The job's sole output is `tier_routing_protocol/heartbeat.json` (gitignored).
Exit `2` = model drift detected (notifiers may fire); exit `1` = all tools failed.
