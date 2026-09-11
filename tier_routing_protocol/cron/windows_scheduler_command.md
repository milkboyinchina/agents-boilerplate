# Windows Task Scheduler — manual install (weekly heartbeat)

`--install-cron` attempts this automatically. If it failed, run in an
elevated prompt (replace `<workspace>` and `<python>`):

```bat
schtasks /Create /TN "tier-routing-heartbeat" /TR "<python> <workspace>\tier_routing_protocol\resolve_model.py heartbeat --quiet" /SC WEEKLY /D SUN /ST 02:00
```

Verify:

```bat
schtasks /Query /TN "tier-routing-heartbeat"
python <workspace>\tier_routing_protocol\resolve_model.py --check
```

GUI fallback: Task Scheduler → Create Basic Task → Weekly, Sunday 02:00 →
action "Start a program" with the same command line.

Remove:

```bat
schtasks /Delete /TN "tier-routing-heartbeat" /F
```

The job's sole output is `.protocol\tier_routing_workspace\heartbeat.json` (gitignored).
