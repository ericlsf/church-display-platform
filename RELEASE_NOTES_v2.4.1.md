# v2.4.1 — Stabilization cycle

## Added

- End-to-end platform smoke test.
- Release validation command that combines repository audit, tests, compilation, smoke checks, package build, and package verification.
- Post-deployment health verification command.
- Repeatable release and rollback checklist.

## Changed

- Release cadence is now explicitly test → tag → deploy → verify.
- Stabilization checks cover Hub pages, agent status, content manifests, sync status, and release artifacts.

## Notes

This release is additive and does not replace application code or alter content behavior.
