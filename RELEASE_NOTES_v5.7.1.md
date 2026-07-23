# v5.7.1 — Dispatcher Integration Fix

The original v5.7.0 installer expected one exact formatting style for the
`deploy_update` branch in `display/agent/dispatcher.py`.

This correction:

- finds the `agent.jobs` import regardless of module order;
- adds `rollback` without duplicating imports;
- identifies `deploy_update` regardless of quote style or whitespace;
- inserts `rollback_update` using the dispatcher’s existing indentation;
- remains idempotent when rerun.
