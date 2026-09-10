#!/usr/bin/env python3
"""
Tier-routing model resolver + registry maintenance utility.

Tasks declare tiers (T1/T2/T3); this CLI resolves them to per-tool model IDs
at runtime so vendor renames touch only routing.yaml. Zero-dependency Python 3.

Usage:
    python3 resolve_model.py --tier T2 --tool opencode [--task 3]
    python3 resolve_model.py --tier T3 --tool antigravity --force-tier T3
    python3 resolve_model.py pin claude-opus --task 3
    python3 resolve_model.py unpin --task 3
    python3 resolve_model.py heartbeat [--quiet]
    python3 resolve_model.py refresh [--cron] [--dry-run]
    python3 resolve_model.py --install [--dry-run] [--force]
    python3 resolve_model.py --install-cron | --uninstall-cron
    python3 resolve_model.py --check [--json]
    python3 resolve_model.py --validate [--fail-on-stale]
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
from pathlib import Path

__version__ = "1.1.0"

PROTOCOL_DIR = "tier_routing_protocol"
WORKSPACE_DIR = "tier_routing_workspace"
REGISTRY_NAME = "routing.yaml"
STATE_NAME = "routing_state.json"
HEARTBEAT_NAME = "heartbeat.json"
UPDATES_DIR = "routing_updates"  # review trail: stays in SOURCE (committed), only heartbeat/state move out
# Pre-split runtime files (sat directly under tier_routing_protocol/). Frozen:
# detected (with mv hint), never written.
# NOTE: repo-wide renames must EXCLUDE these two lines.
LEGACY_HEARTBEAT_PATH = f"{PROTOCOL_DIR}/{HEARTBEAT_NAME}"
LEGACY_STATE_PATH = f"{PROTOCOL_DIR}/{STATE_NAME}"
STALE_AFTER_DAYS = 30
HEARTBEAT_STALE_DAYS = 10
CRON_MARKER = "tier-routing-heartbeat"

TIERS = ("T1", "T2", "T3")
TIER_FALLBACK = {"T3": "T2", "T2": "T1", "T1": None}

AGENT_DIRECTIVE_FILES = [
    "AGENTS.md",
    "CLAUDE.md",
    ".cursorrules",
    "GEMINI.md",
]

DIRECTIVE_BLOCK = """\n\
### 🎚️ Tier Routing Protocol (`tier_routing_protocol/`)

1. **Tasks declare tiers, never model IDs**: `T1` trivial, `T2` standard, `T3` hard. Green Team stamps Tier per task-row in `plan.md`.
2. **Resolve at runtime**: `python3 tier_routing_protocol/resolve_model.py --tier <T> --tool <name> --task <id>`. Raw IDs live only in `routing.yaml` `aliases:`.
3. **Precedence (later wins, always logged)**: tier default → `--force-tier` → `MODEL_ROUTE_OVERRIDE` → task pin (`/pin-model <alias>`, auto-releases on `[COMPLETED]`, `/unpin` releases early). No session pin exists.
4. **Failover, never hard-fail**: dead IDs fall down `fallbacks:` chains with a loud warning.
5. **Freshness**: weekly dumb cron writes `tier_routing_workspace/heartbeat.json` (sole cron output, gitignored); drift triggers a pending proposal + `Q1-a` approval turn. Stale heartbeat (>10d) = unknown, check live.
""".strip() + "\n"


# ---------------------------------------------------------------------------
# Minimal YAML-subset parser (maps, nested maps, `- item` lists, scalars)
# ---------------------------------------------------------------------------

def _parse_scalar(text: str):
    text = text.strip()
    if text in ("null", "~", ""):
        return None
    if text == "[]":
        return []
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        return text[1:-1]
    if text in ("true", "True"):
        return True
    if text in ("false", "False"):
        return False
    return text


def parse_subset_yaml(text: str) -> dict:
    """Parse the documented subset. Raises ValueError with line number on failure."""
    root: dict = {}
    # Stack frames: {"indent", "container", "owner", "key"} where owner/key
    # locate the container inside its parent (None for root).
    stack: list[dict] = [{"indent": -1, "container": root, "owner": None, "key": None}]
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.split("#", 1)[0] if not raw.lstrip().startswith("#") else ""
        # NOTE: naive `#` strip breaks `#` inside quotes; our registry never uses those.
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        if "\t" in raw[:indent]:
            raise ValueError(f"line {lineno}: tabs not allowed, use 2-space indent")

        while stack and indent <= stack[-1]["indent"]:
            stack.pop()
        if not stack:
            raise ValueError(f"line {lineno}: bad indent")
        frame = stack[-1]
        parent = frame["container"]

        if stripped.startswith("- "):
            if isinstance(parent, list):
                parent.append(_parse_scalar(stripped[2:]))
                continue
            # Fresh `key:` block whose first child is a list item: convert {} -> [].
            if isinstance(parent, dict) and not parent and frame["owner"] is not None:
                new_list: list = []
                frame["owner"][frame["key"]] = new_list
                frame["container"] = new_list
                new_list.append(_parse_scalar(stripped[2:]))
                continue
            raise ValueError(f"line {lineno}: list item outside a list block")

        if ":" not in stripped:
            raise ValueError(f"line {lineno}: expected `key: value`, `- item`, or blank")
        key, _, value = stripped.partition(":")
        key = key.strip()
        value = value.strip()
        if not isinstance(parent, dict):
            raise ValueError(f"line {lineno}: mapping key inside a list block")
        if not key or " " in key:
            raise ValueError(f"line {lineno}: bad key {key!r}")

        if value == "":
            child: object = {}
            parent[key] = child
            stack.append({"indent": indent, "container": child, "owner": parent, "key": key})
        else:
            parent[key] = _parse_scalar(value)
    return root


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _log(message: str, *, quiet: bool = False) -> None:
    if not quiet:
        print(message)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _resolve_proto_dir(root: Path) -> Path:
    # Reference flow first: the copy may live under agents-boilerplate/.
    # Script location always wins (it IS a copy). Falls back to root-level.
    if root.name == PROTOCOL_DIR:
        return root
    for candidate in (root / "agents-boilerplate" / PROTOCOL_DIR,
                      Path(__file__).parent,
                      root / PROTOCOL_DIR):
        if candidate.exists():
            return candidate
    return root / PROTOCOL_DIR


def _dual_presence(root: Path) -> Path | None:
    """A stale same-named local copy coexists with agents-boilerplate/. Returns its path, else None."""
    script_dir = Path(__file__).parent.resolve()
    candidate = (root / script_dir.name).resolve()
    if candidate.exists() and candidate != script_dir:
        return root / script_dir.name
    return None


def _warn_dual_presence(root: Path) -> None:
    # stderr: stdout must stay pure JSON under --check --json.
    dup = _dual_presence(root)
    if dup is not None:
        print(f"[WARN] dual presence: {dup} duplicates the invoked collection copy. "
              "Choose: (a) reference — delete the local copy, keep agents-boilerplate/; "
              "(b) vendor — run the local copy instead. Proceeding with the invoked copy.",
              file=sys.stderr)


def _workspace_dir(root: Path) -> Path:
    return root / WORKSPACE_DIR


def _legacy_file_present(root: Path, rel: str, keys: tuple[str, ...]) -> bool:
    # The boilerplate copy shares legacy paths — only treat as legacy runtime
    # when the file actually holds data (non-empty JSON dict with known keys).
    path = root / rel
    if not path.exists():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    return isinstance(data, dict) and bool(data) and any(k in data for k in keys)


def _legacy_found(root: Path) -> list[str]:
    found = []
    if _legacy_file_present(root, LEGACY_HEARTBEAT_PATH, ("last_check", "tools")):
        found.append(LEGACY_HEARTBEAT_PATH)
    if _legacy_file_present(root, LEGACY_STATE_PATH, ("pins",)):
        found.append(LEGACY_STATE_PATH)
    return found


def _warn_legacy(root: Path) -> None:
    # stderr: stdout must stay pure JSON under --check --json.
    found = _legacy_found(root)
    if found:
        print(f"[WARN] legacy runtime file(s) {', '.join(found)} found (pre-split layout). "
              "Migrate: mkdir -p tier_routing_workspace; "
              "mv <file> tier_routing_workspace/; "
              "swap the .gitignore lines to tier_routing_workspace/.", file=sys.stderr)


def _today() -> datetime.date:
    return datetime.date.today()


def _parse_date(value: object) -> datetime.date | None:
    if value is None:
        return None
    try:
        return datetime.date.fromisoformat(str(value))
    except ValueError:
        return None


def load_registry(root: Path, registry_path: str | None = None) -> tuple[dict, list[str]]:
    """Returns (registry, structural_errors). Staleness is reported separately."""
    path = Path(registry_path) if registry_path else _resolve_proto_dir(root) / REGISTRY_NAME
    if not path.exists():
        return {}, [f"registry not found: {path}"]
    try:
        reg = parse_subset_yaml(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        return {}, [f"registry parse error: {exc}"]
    errors: list[str] = []
    if not isinstance(reg, dict):
        return {}, ["registry root must be a mapping"]
    for section in ("tiers", "aliases", "tools"):
        if section not in reg or not isinstance(reg[section], dict):
            errors.append(f"registry missing mapping `{section}:`")
    if errors:
        return reg, errors
    for tier in TIERS:
        if tier not in reg["tiers"]:
            errors.append(f"tiers: missing {tier}")
    for name, tool in reg["tools"].items():
        if not isinstance(tool, dict):
            errors.append(f"tools.{name}: must be a mapping")
            continue
        models = tool.get("models", {})
        for tier in TIERS:
            alias = models.get(tier) if isinstance(models, dict) else None
            if alias not in reg["aliases"]:
                errors.append(f"tools.{name}.models.{tier}: unknown alias {alias!r}")
        manual = tool.get("manual", False)
        if not manual:
            for alias_name, alias in reg["aliases"].items():
                ids = alias.get("ids", {}) if isinstance(alias, dict) else {}
                ident = ids.get(name) if isinstance(ids, dict) else None
                if ident is None or str(ident).startswith("TODO-"):
                    errors.append(f"aliases.{alias_name}.ids.{name}: placeholder (fill or mark tool manual)")
    return reg, errors


def stale_report(reg: dict, *, stale_after: int) -> list[str]:
    warnings: list[str] = []
    for alias_name, alias in reg.get("aliases", {}).items():
        seen = _parse_date(alias.get("verified"))
        if seen is None or (_today() - seen).days > stale_after:
            warnings.append(f"aliases.{alias_name}: verified {alias.get('verified')} (stale >{stale_after}d)")
    for name, tool in reg.get("tools", {}).items():
        seen = _parse_date(tool.get("verified"))
        if seen is None or (_today() - seen).days > stale_after:
            warnings.append(f"tools.{name}: verified {tool.get('verified')} (stale >{stale_after}d)")
    return warnings


def _is_dead(ident: object) -> bool:
    return ident is None or str(ident).startswith("TODO-")


def _parse_flag(value: str | None) -> bool | None:
    if value is None:
        return None
    v = value.strip().lower()
    if v in ("1", "true", "yes", "on"):
        return True
    if v in ("0", "false", "no", "off"):
        return False
    return None


def enabled_state(reg: dict, tool: str | None = None) -> tuple[bool, str]:
    """Kill-switch evaluation. Precedence: file workspace → file per-tool →
    env workspace → env per-tool. Returns (enabled, source description)."""
    enabled, source = True, "default (enabled)"
    if reg.get("enabled") is False:
        enabled, source = False, "routing.yaml enabled: false"
    if tool is not None:
        entry = (reg.get("tools", {}) or {}).get(tool, {})
        if isinstance(entry, dict) and entry.get("enabled") is False:
            enabled, source = False, f"routing.yaml tools.{tool}.enabled: false"
    env_ws = _parse_flag(os.environ.get("TIER_ROUTING_ENABLED"))
    if env_ws is not None:
        enabled = env_ws
        source = f"TIER_ROUTING_ENABLED={os.environ.get('TIER_ROUTING_ENABLED')}"
    if tool is not None:
        env_tool = _parse_flag(os.environ.get(f"TIER_ROUTING_{tool.upper()}_ENABLED"))
        if env_tool is not None:
            enabled = env_tool
            source = f"TIER_ROUTING_{tool.upper()}_ENABLED={os.environ.get(f'TIER_ROUTING_{tool.upper()}_ENABLED')}"
    return enabled, source


def _state_path(root: Path) -> Path:
    return _workspace_dir(root) / STATE_NAME


def _heartbeat_path(root: Path) -> Path:
    return _workspace_dir(root) / HEARTBEAT_NAME


def _read_state(root: Path) -> dict:
    path = _state_path(root)
    if not path.exists():
        return {"pins": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        data.setdefault("pins", {})
        return data
    except (json.JSONDecodeError, OSError):
        return {"pins": {}, "_corrupt": True}


def _write_state(root: Path, data: dict) -> None:
    _state_path(root).parent.mkdir(parents=True, exist_ok=True)
    _state_path(root).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Resolution
# ---------------------------------------------------------------------------

def resolve_alias_id(reg: dict, alias: str, tool: str, *, _seen: tuple = ()) -> tuple[str | None, list[str]]:
    """Follow alias fallbacks to a live ID. Returns (id, warnings)."""
    warnings: list[str] = []
    if alias in _seen:
        return None, [f"alias cycle: {' -> '.join((*_seen, alias))}"]
    entry = reg.get("aliases", {}).get(alias, {})
    ident = (entry.get("ids", {}) or {}).get(tool)
    if not _is_dead(ident):
        return str(ident), warnings
    warnings.append(f"alias {alias}: id for {tool} is {ident!r} — failing over")
    for fb in entry.get("fallbacks", []) or []:
        ident, w = resolve_alias_id(reg, fb, tool, _seen=(*_seen, alias))
        warnings.extend(w)
        if ident is not None:
            return ident, warnings
    return None, warnings


def resolve(reg: dict, state: dict, *, tier: str, tool: str, task: str | None,
            force_tier: str | None, override: str | None, strict: bool) -> tuple[int, str]:
    """Resolve a tier to a model ID. Returns (exit_code, human-readable output)."""
    out: list[str] = []
    if tool not in reg.get("tools", {}):
        msg = f"unknown tool {tool!r} (no tools.{tool} section — see add-tool workflow)"
        if strict:
            return 1, msg
        out.append(f"warning: {msg} (--lenient: tier descriptors only, no ID)")
        return 0, "\n".join(out)

    on, src = enabled_state(reg, tool)
    if not on:
        return 3, (f"tier routing DISABLED for {tool} ({src}) — "
                   "select model manually (exit 3 = intentional bypass, not an error)")
    layer = f"tier default ({tier})"
    alias = (reg["tools"][tool].get("models", {}) or {}).get(tier)
    if force_tier:
        tier, alias = force_tier, (reg["tools"][tool].get("models", {}) or {}).get(force_tier)
        layer = f"--force-tier ({force_tier})"
    if override:
        ov = override.strip()
        if ov in TIERS:
            tier, alias = ov, (reg["tools"][tool].get("models", {}) or {}).get(ov)
            layer = f"env MODEL_ROUTE_OVERRIDE ({ov})"
        elif ov in reg.get("aliases", {}):
            tier, alias = tier, ov
            layer = f"env MODEL_ROUTE_OVERRIDE (alias {ov})"
        else:
            return 1, f"MODEL_ROUTE_OVERRIDE={ov!r} is neither a tier nor a known alias"
    pin = (state.get("pins", {}) or {}).get(task) if task else None
    if pin and pin.get("alias") in reg.get("aliases", {}):
        alias = pin["alias"]
        layer = f"task pin ({alias}, task {task})"

    if alias not in reg.get("aliases", {}):
        return 1, f"no alias {alias!r} for {tool}/{tier} — registry misconfigured"

    ident, warnings = resolve_alias_id(reg, alias, tool)
    for w in warnings:
        out.append(f"warning: {w}")
    if ident is None:
        # Tier-level fallback before giving up.
        lower = TIER_FALLBACK.get(tier)
        if lower:
            out.append(f"warning: alias chain for {alias} exhausted — falling back {tier} -> {lower}")
            code, sub = resolve(reg, state, tier=lower, tool=tool, task=None,
                                force_tier=None, override=None, strict=strict)
            return code, "\n".join([*out, sub])
        return 1, "\n".join([*out, f"error: no live ID for {tool}/{tier}"])
    out.append(f"{ident}  # via {layer}")
    return 0, "\n".join(out)


# ---------------------------------------------------------------------------
# Heartbeat (dumb cron) + refresh (propose-only)
# ---------------------------------------------------------------------------

def _hash_ids(ids: list[str]) -> str:
    return hashlib.sha256("\n".join(sorted(ids)).encode()).hexdigest()[:12]


def _read_models_file(path: Path) -> list[str] | None:
    """A models file holds a JSON array or newline-separated IDs. None if unreadable."""
    try:
        text = path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    if not text:
        return []
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return [str(x) for x in data]
    except json.JSONDecodeError:
        pass
    return [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("#")]


def run_heartbeat(root: Path, *, quiet: bool, registry_path: str | None = None) -> int:
    reg, errors = load_registry(root, registry_path)
    if errors:
        print("heartbeat aborted: registry invalid:")
        for e in errors:
            print(f"  - {e}")
        return 1
    _workspace_dir(root).mkdir(parents=True, exist_ok=True)
    hb_path = _heartbeat_path(root)
    prev: dict = {}
    try:
        prev = json.loads(hb_path.read_text(encoding="utf-8")) if hb_path.exists() else {}
    except (json.JSONDecodeError, OSError):
        prev = {}
    tools_out: dict = {}
    ok_count, drift = 0, False
    for name, tool in reg.get("tools", {}).items():
        on, src = enabled_state(reg, name)
        if not on:
            tools_out[name] = {"ok": False, "disabled": True, "source": src}
            continue
        mf = (tool.get("discover", {}) or {}).get("models_file")
        if tool.get("manual", False) or not mf:
            tools_out[name] = {"ok": False, "error": "no models_file (manual tool — see TIER_ROUTING.md section 7)"}
            continue
        ids = _read_models_file(root / mf if not str(mf).startswith("/") else Path(str(mf)))
        if ids is None:
            tools_out[name] = {"ok": False, "error": f"unreadable models_file: {mf}"}
            continue
        h = _hash_ids(ids)
        tools_out[name] = {"ok": True, "live_ids_hash": h, "live_ids": sorted(ids)}
        ok_count += 1
        old = ((prev.get("tools", {}) or {}).get(name, {}) or {}).get("live_ids_hash")
        if old is not None and old != h:
            drift = True
    hb = {"last_check": datetime.datetime.now().astimezone().isoformat(),
          "tools": tools_out}
    hb_path.write_text(json.dumps(hb, indent=2) + "\n", encoding="utf-8")
    _log(f"[HEARTBEAT] {hb_path} ({ok_count} tool(s) read)", quiet=quiet)
    if ok_count == 0:
        return 1
    return 2 if drift else 0


def run_refresh(root: Path, *, dry_run: bool, quiet: bool, registry_path: str | None = None) -> int:
    """Compare heartbeat live IDs vs registry; write a pending proposal on drift. Never edits routing.yaml."""
    reg, errors = load_registry(root, registry_path)
    if errors:
        print("refresh aborted: registry invalid:")
        for e in errors:
            print(f"  - {e}")
        return 1
    proto = _resolve_proto_dir(root)
    try:
        hb = json.loads(_heartbeat_path(root).read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        print("refresh: no heartbeat found — run `resolve_model.py heartbeat` (or --install-cron) first.")
        return 1
    last = hb.get("last_check", "")
    try:
        age = (datetime.datetime.now().astimezone()
               - datetime.datetime.fromisoformat(last)).days
    except ValueError:
        age = 10 ** 6
    if age > HEARTBEAT_STALE_DAYS:
        print(f"refresh: heartbeat is {age}d old (>10d) — treated as unknown, check live sources directly.")
        return 1
    drifts: list[str] = []
    for name, snap in (hb.get("tools", {}) or {}).items():
        if snap.get("disabled"):
            continue  # intentionally off — leave alone, re-checked on re-enable
        if not snap.get("ok"):
            drifts.append(f"- {name}: heartbeat error ({snap.get('error')}) — needs the Q13 fallback branch.")
            continue
        live = set(snap.get("live_ids", []))
        reg_ids = {str((a.get("ids", {}) or {}).get(name))
                   for a in reg.get("aliases", {}).values()
                   if not _is_dead((a.get("ids", {}) or {}).get(name))}
        missing = sorted(live - reg_ids)
        gone = sorted(reg_ids - live)
        if missing or gone:
            drifts.append(f"- {name}: live has {missing or 'nothing new'}; registry has {gone or 'nothing stale'}.")
    if not drifts:
        _log("refresh: heartbeat matches registry — nothing to propose.", quiet=quiet)
        return 0
    body = ("# Model routing refresh proposal\n\n"
            f"Heartbeat: {last}\n\n"
            "Drift detected (agent: verify against live sources, then ask the Q9-a approval turn):\n\n"
            + "\n".join(drifts)
            + "\n\nOn approval: edit only the delta lines in routing.yaml, bump `verified:` dates, run `--validate`.\n")
    if dry_run:
        print(body)
        return 2
    upd = proto / UPDATES_DIR
    upd.mkdir(parents=True, exist_ok=True)
    out = upd / datetime.datetime.now().strftime("pending-%Y%m%d-%H%M.md")
    out.write_text(body, encoding="utf-8")
    print(f"refresh: drift found — proposal written (NOT applied): {out}")
    return 2


# ---------------------------------------------------------------------------
# Bootstrap: gitignore, directives, scheduler install
# ---------------------------------------------------------------------------

RUNTIME_GITIGNORE_LINES = [f"{WORKSPACE_DIR}/{HEARTBEAT_NAME}", f"{WORKSPACE_DIR}/{STATE_NAME}"]


def ensure_gitignore(root: Path, *, dry_run: bool, quiet: bool) -> bool:
    gitignore = root / ".gitignore"
    lines = _read_text(gitignore).splitlines()
    wanted = list(RUNTIME_GITIGNORE_LINES)
    if (root / "agents-boilerplate").exists():
        wanted.append("agents-boilerplate/")
    missing = [ln for ln in wanted if ln not in lines]
    if not missing:
        _log("[OK] .gitignore already covers model routing runtime files", quiet=quiet)
        return False
    new_content = _read_text(gitignore).rstrip("\n") + "\n" + "\n".join(missing) + "\n"
    if dry_run:
        for ln in missing:
            _log(f"[DRY-RUN] Would append {ln!r} to {gitignore}", quiet=quiet)
        return True
    gitignore.write_text(new_content, encoding="utf-8")
    _log(f"[UPDATE] {gitignore}", quiet=quiet)
    return True


def detect_agent_files(root: Path) -> list[str]:
    return [n for n in AGENT_DIRECTIVE_FILES if (root / n).exists()]


def _maybe_create_directives(root: Path, *, dry_run: bool, quiet: bool, assume_yes: bool = False) -> bool:
    """Q46-a: no directive file exists — ask (default yes) to create AGENTS.md.
    Non-interactive stdin (piped/CI) never blocks: falls back to INFO + skip,
    unless --yes was passed (scripted installs)."""
    target = root / "AGENTS.md"
    if dry_run:
        _log(f"[DRY-RUN] Would ask to create {target} with the protocol block", quiet=quiet)
        return False
    answer = "a" if assume_yes else "b"
    if not assume_yes and sys.stdin.isatty() and not quiet:
        print("Q1. No directive file found (AGENTS.md/CLAUDE.md/.cursorrules/GEMINI.md). "
              "Create AGENTS.md with the protocol block? (a/yes b/no, I'll copy manually) [a]: ")
        try:
            answer = (input().strip().lower() or "a")
        except EOFError:
            answer = "b"
    if answer not in ("a", "yes", "y"):
        _log("[INFO] Skipped AGENTS.md creation — copy the block manually when ready.", quiet=quiet)
        return False
    target.write_text("# AGENTS.md\n\n" + DIRECTIVE_BLOCK, encoding="utf-8")
    _log(f"[CREATE] {target} (protocol block installed)", quiet=quiet)
    return True


def inject_directives(root: Path, agent_files: list, *, dry_run: bool, quiet: bool, force: bool = False) -> list[str]:
    changed: list[str] = []
    for name in agent_files:
        path = root / name
        existing = _read_text(path)
        if DIRECTIVE_BLOCK.strip() in existing.strip() and not force:
            _log(f"[SKIP] {name} already contains Tier Routing directives", quiet=quiet)
            continue
        if dry_run:
            _log(f"[DRY-RUN] Would append directives to {name}", quiet=quiet)
            changed.append(name)
            continue
        path.write_text(existing.rstrip("\n") + "\n\n" + DIRECTIVE_BLOCK, encoding="utf-8")
        _log(f"[UPDATE] {name}", quiet=quiet)
        changed.append(name)
    return changed


def _cron_command(root: Path) -> str:
    return f"{sys.executable} {_cron_script_path(root)} heartbeat --quiet"


def _cron_script_path(root: Path) -> str:
    # Absolute path the scheduler must invoke (reference-flow aware).
    return str((_resolve_proto_dir(root) / "resolve_model.py").resolve())


def cron_status(root: Path) -> dict:
    """Marker present? Command path valid? A stale entry (marker without a live
    script path) must heal, not report OK."""
    system = platform.system()
    expected = _cron_script_path(root)
    try:
        if system == "Linux":
            out = subprocess.run(["crontab", "-l"], capture_output=True, text=True, timeout=10).stdout
            marker = CRON_MARKER in out
            return {"present": marker, "path_ok": (expected in out) if marker else False}
        if system == "Darwin":
            out = subprocess.run(["launchctl", "list"], capture_output=True, text=True, timeout=10).stdout
            marker = "tierrouting.heartbeat" in out
            dest = Path.home() / "Library" / "LaunchAgents" / "com.tierrouting.heartbeat.plist"
            try:
                path_ok = marker and expected in dest.read_text(encoding="utf-8")
            except OSError:
                path_ok = False
            return {"present": marker, "path_ok": path_ok}
        if system == "Windows":
            out = subprocess.run(["schtasks", "/Query", "/FO", "LIST", "/V"], capture_output=True, text=True, timeout=15).stdout
            marker = CRON_MARKER in out
            return {"present": marker, "path_ok": (expected in out) if marker else False}
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        pass
    return {"present": False, "path_ok": False}


def cron_present(root: Path) -> bool:
    st = cron_status(root)
    return bool(st["present"] and st["path_ok"])


def manual_cron_docs(root: Path) -> dict[str, str]:
    """Exact manual commands per OS (also written to cron/*.md by --install-cron on failure)."""
    cmd = _cron_command(root)
    return {
        "Linux": f"(crontab -l 2>/dev/null; echo '# {CRON_MARKER}'; echo '0 2 * * 0 {cmd}') | crontab -",
        "macOS": f"Write cron/com.tierrouting.heartbeat.plist with ProgramArguments [{sys.executable}, <abs>/resolve_model.py, heartbeat, --quiet], then: launchctl load ~/Library/LaunchAgents/com.tierrouting.heartbeat.plist",
        "Windows": f'schtasks /Create /TN "{CRON_MARKER}" /TR "{cmd}" /SC WEEKLY /D SUN /ST 02:00',
    }


def install_cron(root: Path, *, quiet: bool) -> int:
    system = platform.system()
    cmd = _cron_command(root)
    docs = manual_cron_docs(root)
    try:
        if system == "Linux":
            cur = subprocess.run(["crontab", "-l"], capture_output=True, text=True, timeout=10).stdout
            if CRON_MARKER in cur:
                if _cron_script_path(root) in cur:
                    _log("[OK] cron entry already installed", quiet=quiet)
                    return 0
                print("[WARN] cron marker present but script path is stale — replacing entry.")
                cur = "\n".join(ln for ln in cur.splitlines()
                                if CRON_MARKER not in ln and "resolve_model.py heartbeat" not in ln)
            new = cur + f"# {CRON_MARKER}\n0 2 * * 0 {cmd}\n"
            subprocess.run(["crontab", "-"], input=new, capture_output=True, text=True, timeout=10, check=True)
            _log("[UPDATE] cron entry installed (weekly Sun 02:00)", quiet=quiet)
            return 0
        if system == "Darwin":
            plist = (_resolve_proto_dir(root) / "cron" / "com.tierrouting.heartbeat.plist")
            dest = Path.home() / "Library" / "LaunchAgents" / plist.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(plist.read_text(encoding="utf-8").replace(
                "__SCRIPT__", str((_resolve_proto_dir(root) / "resolve_model.py").resolve())), encoding="utf-8")
            subprocess.run(["launchctl", "load", str(dest)], capture_output=True, text=True, timeout=15, check=True)
            _log("[UPDATE] launchd agent installed (weekly)", quiet=quiet)
            return 0
        if system == "Windows":
            subprocess.run(["schtasks", "/Create", "/TN", CRON_MARKER, "/TR", cmd,
                            "/SC", "WEEKLY", "/D", "SUN", "/ST", "02:00", "/F"],
                           capture_output=True, text=True, timeout=20, check=True)
            _log("[UPDATE] scheduled task installed (weekly Sun 02:00)", quiet=quiet)
            return 0
        raise OSError(f"unsupported OS {system!r}")
    except (subprocess.SubprocessError, FileNotFoundError, OSError) as exc:
        print(f"[WARN] automatic scheduler install failed ({exc}).")
        print(f"Manual command for {system}:\n  {docs.get(system, list(docs.values())[0])}")
        cron_dir = _resolve_proto_dir(root) / "cron"
        print(f"Step-by-step files (already in repo): {cron_dir}/linux_cronjob_command.md, "
              f"macos_launchd_command.md, windows_scheduler_command.md")
        return 2


def uninstall_cron(root: Path, *, quiet: bool) -> int:
    system = platform.system()
    try:
        if system == "Linux":
            cur = subprocess.run(["crontab", "-l"], capture_output=True, text=True, timeout=10).stdout.splitlines()
            kept = [ln for ln in cur if CRON_MARKER not in ln and "resolve_model.py heartbeat" not in ln]
            subprocess.run(["crontab", "-"], input="\n".join(kept) + "\n",
                           capture_output=True, text=True, timeout=10, check=True)
            _log("[REMOVE] cron entry uninstalled", quiet=quiet)
            return 0
        if system == "Darwin":
            dest = Path.home() / "Library" / "LaunchAgents" / "com.tierrouting.heartbeat.plist"
            subprocess.run(["launchctl", "unload", str(dest)], capture_output=True, timeout=15)
            if dest.exists():
                dest.unlink()
            _log("[REMOVE] launchd agent uninstalled", quiet=quiet)
            return 0
        if system == "Windows":
            subprocess.run(["schtasks", "/Delete", "/TN", CRON_MARKER, "/F"],
                           capture_output=True, text=True, timeout=20, check=True)
            _log("[REMOVE] scheduled task uninstalled", quiet=quiet)
            return 0
    except (subprocess.SubprocessError, FileNotFoundError, OSError) as exc:
        print(f"[WARN] automatic uninstall failed ({exc}) — see cron/*.md for manual removal.")
        return 2
    return 0


# ---------------------------------------------------------------------------
# Status check
# ---------------------------------------------------------------------------

def status_check(root: Path, *, json_output: bool, quiet: bool, stale_after: int, registry_path: str | None = None) -> dict:
    _warn_legacy(root)
    reg, errors = load_registry(root, registry_path)
    proto = _resolve_proto_dir(root)
    gi_lines = _read_text(root / ".gitignore").splitlines() if (root / ".gitignore").exists() else []
    ws_on, ws_src = enabled_state(reg)
    per_tool = {name: {"enabled": enabled_state(reg, name)[0],
                       "source": enabled_state(reg, name)[1]}
                for name in reg.get("tools", {}).keys()}
    dup = _dual_presence(root)
    result: dict = {
        "protocol_dir": str(proto),
        "workspace_dir": str(_workspace_dir(root)),
        "dual_presence": str(dup) if dup else None,
        "registry_ok": not errors,
        "registry_errors": errors,
        "enabled": {"workspace": ws_on, "source": ws_src},
        "tools": sorted(reg.get("tools", {}).keys()),
        "tools_enabled": per_tool,
        "alias_count": len(reg.get("aliases", {})),
        "stale_warnings": stale_report(reg, stale_after=stale_after),
        "state_exists": _state_path(root).exists(),
        "heartbeat_exists": _heartbeat_path(root).exists(),
        "legacy_runtime_found": _legacy_found(root),
        "active_pins": _read_state(root).get("pins", {}),
        "gitignore_ok": all(ln in gi_lines for ln in RUNTIME_GITIGNORE_LINES),
        "cron_present": cron_present(root),
        "directives_ok": any(DIRECTIVE_BLOCK.strip() in _read_text(root / f).strip()
                             for f in detect_agent_files(root)),
        "directives_hint": (None if detect_agent_files(root) else
                            "No directive file found — run --install and answer Q1-a to create AGENTS.md."),
    }
    if json_output:
        print(json.dumps(result, indent=2))
    else:
        _log("\n--- Tier Routing Status ---", quiet=quiet)
        for key, value in result.items():
            _log(f"  {key}: {value}", quiet=quiet)
        _log("---------------------------\n", quiet=quiet)
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="resolve_model.py",
        description="Resolve task tiers (T1/T2/T3) to per-tool model IDs; maintain the registry. See root README install profiles (minimal/standard/full).",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--tier", choices=list(TIERS), help="Task tier to resolve.")
    parser.add_argument("--tool", help="Tool name (a tools: section in routing.yaml).")
    parser.add_argument("--task", help="Task ID (for task pins).")
    parser.add_argument("--force-tier", choices=list(TIERS), help="One-shot tier override.")
    parser.add_argument("--prefer", help="Prefer an alias by name (validated against registry).")
    parser.add_argument("--strict", action="store_true", help="Error on unknown tools (default: lenient warn).")
    parser.add_argument("--registry", metavar="PATH", help="Use a candidate registry file (validate/check/resolve before swapping).")
    parser.add_argument("--stale-after", type=int, default=STALE_AFTER_DAYS,
                        help="Days before verified: dates count as stale (default 30).")
    parser.add_argument("--install", action="store_true", help="Bootstrap: gitignore + directives.")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing.")
    parser.add_argument("--force", action="store_true", help="Re-write directive block even if present.")
    parser.add_argument("--quiet", action="store_true", help="Suppress non-essential output.")
    parser.add_argument("--yes", action="store_true", help="Assume yes to prompts (e.g. create AGENTS.md). For scripted installs.")
    parser.add_argument("--json", action="store_true", help="JSON output for --check.")
    parser.add_argument("--check", action="store_true", help="Report workspace status.")
    parser.add_argument("--validate", action="store_true", help="Validate routing.yaml.")
    parser.add_argument("--fail-on-stale", action="store_true", help="Exit 1 on stale entries (for pre-commit).")
    parser.add_argument("--install-cron", action="store_true", help="Install weekly heartbeat scheduler.")
    parser.add_argument("--uninstall-cron", action="store_true", help="Remove weekly heartbeat scheduler.")

    sub = parser.add_subparsers(dest="command")
    pin_p = sub.add_parser("pin", help="Pin an alias to a task (auto-releases on completion).")
    pin_p.add_argument("alias", help="Portable alias from routing.yaml.")
    pin_p.add_argument("--task", required=True, help="Task ID to bind the pin to.")
    pin_p.add_argument("--quiet", action="store_true", help="Suppress non-essential output.")
    unpin_p = sub.add_parser("unpin", help="Release a task pin early.")
    unpin_p.add_argument("--task", required=True, help="Task ID to release.")
    unpin_p.add_argument("--quiet", action="store_true", help="Suppress non-essential output.")
    hb_p = sub.add_parser("heartbeat", help="Write heartbeat.json from models files (dumb cron).")
    hb_p.add_argument("--quiet", action="store_true", help="Suppress non-essential output.")
    ref_p = sub.add_parser("refresh", help="Propose registry updates from heartbeat drift (never applies).")
    ref_p.add_argument("--cron", action="store_true", help="Non-interactive propose-only mode.")
    ref_p.add_argument("--dry-run", action="store_true", help="Print proposal instead of writing it.")
    ref_p.add_argument("--quiet", action="store_true", help="Suppress non-essential output.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path.cwd()
    os_name = platform.system()

    if args.command == "pin":
        reg, errors = load_registry(root, args.registry)
        if errors:
            print("pin aborted: registry invalid:")
            for e in errors:
                print(f"  - {e}")
            return 1
        on, src = enabled_state(reg)
        if not on:
            print(f"pin refused: tier routing DISABLED workspace-wide ({src}) — "
                  "enable it before pinning.")
            return 3
        if args.alias not in reg.get("aliases", {}):
            print(f"pin aborted: unknown alias {args.alias!r} (see routing.yaml aliases:).")
            return 1
        state = _read_state(root)
        state["pins"][args.task] = {"alias": args.alias,
                                    "since": datetime.datetime.now().astimezone().isoformat()}
        if not args.quiet and getattr(args, "dry_run", False):
            print(f"[DRY-RUN] Would pin {args.alias} to task {args.task}")
            return 0
        _write_state(root, state)
        print(f"pinned {args.alias} to task {args.task} (auto-releases on [COMPLETED]; `/unpin --task {args.task}` releases early).")
        return 0

    if args.command == "unpin":
        state = _read_state(root)
        if args.task in state.get("pins", {}):
            del state["pins"][args.task]
            _write_state(root, state)
            print(f"released pin for task {args.task} (routing defaults apply again).")
        else:
            print(f"no pin for task {args.task}.")
        return 0

    if args.command == "heartbeat":
        return run_heartbeat(root, quiet=args.quiet, registry_path=args.registry)

    if args.command == "refresh":
        return run_refresh(root, dry_run=getattr(args, "dry_run", False), quiet=args.quiet, registry_path=args.registry)

    if args.install_cron:
        return install_cron(root, quiet=args.quiet)
    if args.uninstall_cron:
        return uninstall_cron(root, quiet=args.quiet)

    if args.validate:
        reg, errors = load_registry(root, args.registry)
        for e in errors:
            print(f"  - {e}")
        warns = [] if errors else stale_report(reg, stale_after=args.stale_after)
        for w in warns:
            print(f"  ! {w} (stale)")
        if errors:
            print(f"❌ routing.yaml: {len(errors)} structural error(s).")
            return 1
        if warns and args.fail_on_stale:
            print(f"❌ routing.yaml: {len(warns)} stale entrie(s) (--fail-on-stale).")
            return 1
        print(f"✅ routing.yaml valid ({len(reg.get('aliases', {}))} aliases, "
              f"{len(reg.get('tools', {}))} tools{'' if not warns else f', {len(warns)} stale'}{' on ' + os_name}).")
        return 0

    if args.check:
        status_check(root, json_output=args.json, quiet=args.quiet, stale_after=args.stale_after, registry_path=args.registry)
        return 0

    if args.install:
        _warn_dual_presence(root)
        ensure_gitignore(root, dry_run=args.dry_run, quiet=args.quiet)
        if args.dry_run:
            _log(f"[DRY-RUN] Would create directory: {_workspace_dir(root)}", quiet=args.quiet)
        else:
            _workspace_dir(root).mkdir(parents=True, exist_ok=True)
        agent_files = detect_agent_files(root)
        if agent_files:
            inject_directives(root, agent_files, dry_run=args.dry_run, quiet=args.quiet, force=args.force)
        else:
            _maybe_create_directives(root, dry_run=args.dry_run, quiet=args.quiet, assume_yes=args.yes)
        if not args.quiet:
            print("\n✅ Tier routing workspace is ready.")
            print("   Next: fill routing.yaml IDs via the add-tool workflow, then --validate.")
        return 0

    if args.tier and args.tool:
        reg, errors = load_registry(root, args.registry)
        if errors:
            print("resolve aborted: registry invalid:")
            for e in errors:
                print(f"  - {e}")
            return 1
        override = os.environ.get("MODEL_ROUTE_OVERRIDE")
        force_tier = args.force_tier
        if args.prefer:
            if args.prefer not in reg.get("aliases", {}):
                print(f"resolve aborted: --prefer {args.prefer!r} is not a known alias.")
                return 1
            override = args.prefer  # explicit flag beats env
        for w in stale_report(reg, stale_after=args.stale_after):
            print(f"warning: {w}")
        code, out = resolve(reg, _read_state(root), tier=args.tier, tool=args.tool,
                            task=args.task, force_tier=force_tier,
                            override=override, strict=args.strict)
        print(out)
        return code

    print("Nothing to do: pass --tier/--tool to resolve, or --install/--check/--validate, "
          "or pin|unpin|heartbeat|refresh. See --help.")
    return 2


if __name__ == "__main__":
    sys.exit(main())
