# v4.13.2 — Live Backup Verification

## Fixed

The production gate compared restored files against live files that continued
changing during the test. Active SQLite databases and audit logs could therefore
report false checksum mismatches.

The verifier now:

- creates a point-in-time staging snapshot first;
- uses SQLite's backup API for `.db`, `.sqlite`, and `.sqlite3` files;
- excludes SQLite WAL and SHM sidecar files;
- archives only the stable snapshot;
- compares restored files against that exact snapshot;
- uses safe tar extraction semantics;
- avoids the Python 3.14 tar extraction deprecation warning.
