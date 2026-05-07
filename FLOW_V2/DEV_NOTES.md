1. Bug: Stats returning 0 despite DB having data

Problem:
API /stats/today returned all zeros even though database had activity logs.

Root Cause:
Data existed, but not for the current date.
Query filtered using:

timestamp >= today_start

All records were from an older date → query returned empty.

Debugging Process:

Removed SQL filter → confirmed DB had data
Printed dataframe → saw timestamps (2025-11-04)
Compared with current date → mismatch

Fix:

No code change needed
Generated fresh data OR adjusted query logic

Learning:

Always verify data assumptions before blaming logic
Time-based filters are common failure points