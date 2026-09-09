# Defect Ledger — live file: `green_amber_red_workspace/defects.md` (runtime, gitignored)

> Single-writer-per-field. Red writes FINDINGS (via defect reports only — never
> this file). Green transcribes findings here at `review-redteam` and owns every
> fix-lifecycle field. Amber's fixes flip linked task rows; Green reconciles.
> Every status transition stamps who + when + packet ref. No stamp = not done.

| ID | Sev | Title | Found by / at | Packet ref | Status | Fixed by / at | Verified by / at | Linked task |
|:---|:---:|:---|:---|:---|:---:|:---|:---|:---|
| `BUG-20260713-001` | P1 | _Example: auth bypass via crafted JWT_ | red-a / 2026-07-13 | `packet_red_20260713_0900` | `OPEN` | — | — | Task 2 |

## Lifecycle

`OPEN` (red-reported) → `ACKED` (green triaged) → `IN_FIX` (amber assigned) →
`FIXED` (amber done, awaiting retest) → `VERIFIED` (red recheck or green review
confirms) → `CLOSED`. Transitions move forward only; reopening a `CLOSED` defect
creates a NEW row referencing the old ID (history is append-only).

## Red-side visibility (no shared file)

Red never reads this ledger directly. Each outbound packet embeds an
open-defects snapshot; `recheck-redteam` diffs inbox findings against it before
reporting, so sequential teams (A→B) never duplicate reports.
