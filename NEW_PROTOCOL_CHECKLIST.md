# New Protocol Authoring Checklist

Follow this checklist when adding a boilerplate to this collection. It encodes the workspace rules so future protocols stay consistent without re-reading history.

---

## 1. Naming

- [ ] Folder name: spaces become `_`, always append `_protocol` (e.g. `tier_routing_protocol/`).
- [ ] Never kebab-case, never a bare name without the `_protocol` suffix.
- [ ] Runtime state dir (if any) unmistakably distinct from the source folder — never one letter apart.
- [ ] CLI entry point lives at `<folder>/<verb>_<noun>.py` (e.g. `resolve_model.py`).

## 2. Required files

- [ ] `README.md` — quick start, folder layout, CLI reference, lifecycle, relations, `## 💡 Why use this?` benefit section (see §3).
- [ ] Full spec `<NAME>.md` — numbered rules, edge cases, verification checklist.
- [ ] `SKILL.md` — trigger phrases, autonomous steps, completion criteria.
- [ ] Zero-dependency Python 3 CLI with `--dry-run`, `--check`, `--json`, `--quiet` (plus `--validate` where a file format exists).
- [ ] `templates/` — copy-paste artifacts agents actually use.
- [ ] `examples/` — at least one passing and one failing fixture where validation applies.

## 3. README benefit section (mandatory shape)

- [ ] `## 💡 Why use this?` placed right after the intro, before Quick Start.
- [ ] One paragraph: the concrete pain without the protocol.
- [ ] A `Without this protocol | With this protocol` table, 3–4 rows, each row a concrete pain → concrete gain.

## 4. Runtime hygiene

- [ ] Runtime lives under `.protocol/` (single gitignore line, ensured + stale-pruned at init, idempotent); source stays committed.
- [ ] Exchange/packet contents (diffs, binaries, reports) are gitignored per-directory-contents (`<dir>/*`), never whole-folder when the folder also holds tracked templates/config.
- [ ] `--check` reports gitignore status; cron/scheduler presence where applicable.
- [ ] No raw secrets, no model IDs, no machine-specific paths in committed files.

## 5. Docs & log

- [ ] Root `README.md`: table row + `##` section with usage block.
- [ ] `CHANGELOG.md`: new reverse-chronological entry (scope, affected files, verification results). Never rewrite history.
- [ ] `AGENTS.md`: inject the protocol directive block if agents should follow it here.

## 6. Verification before first commit

- [ ] `python3 -m py_compile` passes on all CLIs.
- [ ] `--help`, `--dry-run`, `--check`, `--check --json` behave correctly.
- [ ] Validator passes good fixture, fails bad fixture with line numbers.
- [ ] Bootstrap is idempotent (second run = `[SKIP]`/`[OK]`).
- [ ] Temp-workspace lifecycle test (init → use → archive/remove) passes.
- [ ] Repo-wide grep: no stale names, no TODO placeholders left behind.
