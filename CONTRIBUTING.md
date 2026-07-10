# Contributing

Use `develop` for integration and keep `main` deployable. All non-emergency changes should use a short-lived feature or fix branch and a pull request.

Before committing:

```bash
./scripts/repo-audit.sh
./scripts/run-tests.sh
```

Keep commits focused. Do not commit media, credentials, runtime state, generated previews, virtual environments, logs, databases, release output, or local configuration containing secrets.

Changes to deployment, content manifests, playlist ordering, sync deletion behavior, or rollback logic must include tests or a written manual validation procedure in the pull request.

See `docs/DEVELOPMENT_WORKFLOW.md` for branching and release instructions.
