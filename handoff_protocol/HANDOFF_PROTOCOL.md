# 🔄 Handoff Protocol Specification

> **Quick Start**: In any project, copy the `handoff_protocol/` folder and run:
> ```bash
> python3 handoff_protocol/handoff.py start --no-prompt
> ```
> Then tell your agent: *"Use `/handoff-start` and `/handoff-resume` for session continuity."*

This document defines a **project-local, manual session handoff protocol** for AI coding assistants.

---

## 1. Purpose

Agent sessions can be interrupted by:
- User stopping the session.
- Switching to a different agent or model.
- Closing the IDE or terminal.
- Needing to pause a complex task and resume later.

This protocol captures the **minimum viable context** needed for a new or resumed agent session to continue without losing state.

---

## 2. Triggers

This protocol is **manual only**:

| Command | User Says | Action |
|---|---|---|
| `/handoff-start` | *"Pause here and capture state."* | Agent runs `handoff.py start`. |
| `/handoff-resume` | *"Continue from the last handoff."* | Agent runs `handoff.py resume` and reads the active handoff file. |

There are **no automatic triggers** based on quota, checkpoints, or time.

---

## 3. Output Location

All handoff artifacts are stored inside the project workspace:

```
<project-root>/
└── handoff_workspace/
    ├── handoff-YYYYMMDD-HHMM.md       # active handoff
    └── archive/
        └── handoff-YYYYMMDD-HHMM.md   # completed handoffs
```

The `handoff_workspace/` folder is automatically added to `.gitignore` so handoff files never leak into version control.

---

## 4. Lifecycle

```
/handoff-start
    │
    ▼
handoff.py start
    │
    ▼
handoff_workspace/handoff-YYYYMMDD-HHMM.md   (active)
    │
    ▼
/handoff-resume
    │
    ▼
handoff.py resume
    │
    ▼
agent continues work
    │
    ▼
handoff.py done
    │
    ▼
handoff_workspace/archive/handoff-YYYYMMDD-HHMM.md   (archived)
```

### Rules
- Only **one active handoff** is allowed at a time.
- To create a new active handoff while one exists, use `handoff.py start --force` (the old one is archived first).
- `handoff.py done` archives the active handoff when work is complete.

---

## 5. 9-Field Handoff Template

Every handoff file MUST contain these 9 sections:

### 1. Session Metadata
- Date and time of handoff.
- Agent/model identifier (optional).
- Trigger (`/handoff-start`).
- Session identifier (optional).

### 2. Active Task / Plan Status
- Current task name and phase.
- `green_amber_red_workspace/plan.md` status if present.
- Risk level if applicable.

### 3. Files Changed
- `git status --short` output.
- Backup paths for any modified files.

### 4. Recent Changes Summary
- Narrative summary of what changed since the last handoff.
- Reference to relevant changelog entries if available.

### 5. Verification Results
- Commands run and their results.
- Test outcomes, lint results, build status.

### 6. Rollback Plan
- Exact steps to revert changes if needed.
- Backup file paths or revert commands.

### 7. Blockers / Risks
- Open questions.
- External dependencies.
- Things that could go wrong.

### 8. Next Steps
- Exact actions the resuming agent should take first.
- Files to read or commands to run.

### 9. Additional Notes
- Free-form context, links, references.
- Anything else the next agent should know.

---

## 6. Agent Instructions

### On `/handoff-start`

1. Run `python3 handoff_protocol/handoff.py start`.
2. If an active handoff already exists, warn the user and ask whether to use `--force`.
3. Answer the prompts (or accept placeholders with `--no-prompt`).
4. Confirm the handoff file was created.

### On `/handoff-resume`

1. Run `python3 handoff_protocol/handoff.py resume`.
2. Read the printed summary.
3. Read any files referenced in the handoff.
4. Continue from the **Next Steps** section.

### On task completion

1. Run `python3 handoff_protocol/handoff.py done`.
2. The active handoff is moved to `handoff_workspace/archive/`.

---

## 7. Coexistence with Other Protocols

This handoff protocol is **complementary** to:

- **Green-Amber-Red Teams**: structures planning, execution, and auditing. Handoff auto-detects `green_amber_red_workspace/plan.md` status.
- **Global agent rules** such as `~/.config/opencode/rules/handoff.md`: global rules may still apply for cross-session continuity; this protocol adds project-local state capture.

---

## 8. Verification Checklist

- [ ] `handoff_workspace/` exists in project root.
- [ ] `handoff_workspace/archive/` exists.
- [ ] `.gitignore` contains `handoff_workspace/`.
- [ ] `handoff.py start` creates a handoff file.
- [ ] `handoff.py resume` reads the active handoff.
- [ ] `handoff.py done` moves the active handoff to archive.
