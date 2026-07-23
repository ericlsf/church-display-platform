# v3.4.1 — Repository cleanup

## Changed

- Active source validation now skips virtual environments, bytecode caches, and archived migration helpers.
- Historical one-time `apply-vX.Y.Z` scripts are moved under `tools/migrations/`.
- The obsolete broken `apply-deployments-page` helper is removed.
- Validation now compiles only maintained Python source, parses all Hub templates, runs tests, and invokes the repository audit.

## Notes

This release does not change application behavior.
