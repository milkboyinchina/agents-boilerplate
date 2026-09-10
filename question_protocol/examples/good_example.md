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

Resolved: Q1-a, Q2-custom(120s), Q3-open.

Next turn (delta + importance):

**Open:**
- Q3. Theme? → shown last turn, reply SHOW Q3 for full text

**New:**
- Q4. Retry policy? (A/backoff b/fixed-3)
- Q5! Deploy to prod tonight? (a/yes b/no)

User reply:

Q3-B, Q4-a+c, Q5: skip

Agent resolution:

Resolved: Q3-B, Q4-a+c, Q5!-open.
