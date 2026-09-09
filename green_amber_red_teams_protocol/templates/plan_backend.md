# [Backend Feature / Fix]
> **Lifecycle Status**: `📋 PLANNED`
> **Planner (Green Team)**: <Agent Name> (Timestamp)
> **Executor (Amber Team)**: Pending
> **Active Task**: None

## 1. Problem Context & Architectural Scope
[API contract, schema changes, business logic]

## 2. Execution Sequence

| # | Task | Status | Who | Affected / Edited Files | Effort | Notes |
|:--|:---|:---:|:---:|:---|:---:|:---|
| 1 | Database / Schema Migration | `[PLANNED]` | Amber Team | • `apps/<app>/models.py`<br>• `apps/<app>/migrations/` | ~15m | |
| 2 | Backend API Implementation | `[PLANNED]` | Amber Team | • `apps/<app>/views.py`<br>• `apps/<app>/serializers.py`<br>• `urls.py` | ~30m | |
| 3 | Service / Business Logic | `[PLANNED]` | Amber Team | • `apps/<app>/services.py` | ~20m | |
| 4 | Tests & Verification | `[PLANNED]` | Amber Team | • `tests/test_*.py` | ~15m | |

## 3. Verification Plan
```bash
python3 -m py_compile src/**/*.py
pytest
python manage.py migrate --check
```
