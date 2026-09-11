---
name: handoff_protocol
description: Captures and resumes project-local AI agent session state using the .protocol/handoff_workspace folder. Use when the user says /handoff-start, /handoff-resume, "pause and capture state", "continue from handoff", or similar session continuity commands.
---

# Handoff Protocol Skill

Use this skill whenever the user says:
- *"/handoff-start"*
- *"/handoff-resume"*
- *"Pause here and capture state."*
- *"Continue from the last handoff."*
- *"Save this context so I can resume later."*

---

## 🎯 Scope

This protocol is **project-local and manual**:
- No global installation.
- No automatic triggers based on quota or checkpoints.
- All files live in `<project-root>/.protocol/handoff_workspace/`.

---

## 📁 Expected Folder Layout

```
<project-root>/
├── .gitignore                              # contains .protocol/ (single line)
└── .protocol/handoff_workspace/
    ├── handoff.py                          # CLI
    ├── README.md
    ├── HANDOFF_PROTOCOL.md
    ├── SKILL.md
    ├── templates/handoff_template.md
    ├── handoff-YYYYMMDD-HHMM.md            # active handoff
    └── archive/
        └── handoff-YYYYMMDD-HHMM.md        # archived handoffs
```

---

## 🛠️ Commands

### /handoff-start

Run:

```bash
python3 handoff_protocol/handoff.py start
```

If an active handoff already exists, ask the user whether to run with `--force`. With no directive file present, `start` asks (Q1-a) to create `AGENTS.md` (`--yes` assumes yes for scripted installs).

The agent MUST:
1. Answer the interactive prompts honestly.
2. Include the current `.protocol/green_amber_red_workspace/plan.md` status if available.
3. Confirm the handoff file path to the user.

### /handoff-resume

Run:

```bash
python3 handoff_protocol/handoff.py resume
```

The agent MUST:
1. Read the printed summary.
2. Read any referenced files.
3. Continue from the **Next Steps** section.

### Task complete

Run:

```bash
python3 handoff_protocol/handoff.py done
```

This moves the active handoff to `.protocol/handoff_workspace/archive/`.

---

## ✅ Completion Criteria

Before responding to the user, verify:
- [ ] `.protocol/handoff_workspace/` exists.
- [ ] `.protocol/handoff_workspace/archive/` exists.
- [ ] `.gitignore` contains the single `.protocol/` line.
- [ ] For `/handoff-start`: a new active handoff file was created.
- [ ] For `/handoff-resume`: the active handoff summary was read and understood.
- [ ] For task completion: the active handoff was archived.
