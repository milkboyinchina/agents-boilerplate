# Good example — passes `init_questions.py --validate`

**New:**
- Q1. Deploy now?
  - Q1-a) Yes, deploy
  - Q1-b) No, wait
- Q2. Cache TTL?
  - Q2-a) 60s
  - Q2-b) 300s
- Q3. Theme?
  - Q3-a) Dark
  - Q3-b) Light

User reply:

Q1-a, Q2: 120s custom, not in the list. Q3: skip

Agent resolution:

Resolved: Q1-a (= Yes, deploy), Q2: custom TTL 120s, Q3 skipped (still open).

Next turn (late answer + carryover):

**Open:**
- Q3. Theme?
  - Q3-a) Dark
  - Q3-b) Light

**New:**
- Q4. Retry policy?
  - Q4-A) Exponential backoff
  - Q4-b) Fixed 3 retries

User reply:

Q3-B, Q4-a+c
