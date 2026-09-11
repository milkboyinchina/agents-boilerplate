# macOS launchd — manual install (weekly heartbeat)

`--install-cron` attempts this automatically (cron is deprecated on macOS).
If it failed, run verbatim (replace `<workspace>` with the project root):

```bash
# 1. Write the agent plist (copy cron/com.tierrouting.heartbeat.plist template,
#    replacing __SCRIPT__ with <workspace>/tier_routing_protocol/resolve_model.py)
cp <workspace>/tier_routing_protocol/cron/com.tierrouting.heartbeat.plist \
   ~/Library/LaunchAgents/com.tierrouting.heartbeat.plist

# 2. Load it
launchctl load ~/Library/LaunchAgents/com.tierrouting.heartbeat.plist

# 3. Verify
launchctl list | grep tierrouting.heartbeat
python3 <workspace>/tier_routing_protocol/resolve_model.py --check
```

Remove:

```bash
launchctl unload ~/Library/LaunchAgents/com.tierrouting.heartbeat.plist
rm ~/Library/LaunchAgents/com.tierrouting.heartbeat.plist
# or: python3 <workspace>/tier_routing_protocol/resolve_model.py --uninstall-cron
```

The job's sole output is `.protocol/tier_routing_workspace/heartbeat.json` (gitignored).
