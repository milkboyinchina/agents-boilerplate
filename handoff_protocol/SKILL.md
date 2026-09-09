---
name: handoff_protocol
description: Captures and resumes project-local AI agent session state using the handoff_protocol folder. Use when the user says /handoff-start, /handoff-resume, "pause and capture state", "continue from handoff", or similar session continuity commands.
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
- All files live in `<project-root>/handoff_protocol/`.

---

## 📁 Expected Folder Layout

```
<project-root>/
├── .gitignore                              # contains handoff_protocol/
└── handoff_protocol/
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

If an active handoff already exists, ask the user whether to run with `--force`.

The agent MUST:
1. Answer the interactive prompts honestly.
2. Include the current `green_amber_red_teams/plan.md` status if available.
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

This moves the active handoff to `handoff_protocol/archive/`.

---

## ✅ Completion Criteria

Before responding to the user, verify:
- [ ] `handoff_protocol/` exists.
- [ ] `handoff_protocol/archive/` exists.
- [ ] `.gitignore` contains `handoff_protocol/`.
- [ ] For `/handoff-start`: a new active handoff file was created.
- [ ] For `/handoff-resume`: the active handoff summary was read and understood.
- [ ] For task completion: the active handoff was archived.
