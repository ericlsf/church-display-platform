# v5.6.0 — Self-Verifying Upgrades

## Authoritative installed version

The display agent now reads its version directly from:

```text
/opt/church-display/display/VERSION
```

`release.json` is retained for additional release metadata.

## Deployment completion

A deployment is now separated into two states:

1. installer completed;
2. heartbeat verified the target version.

A successful job whose next heartbeat still reports the previous version is
shown as `Verification failed`, not fully current.

## Display page

The Software Upgrade section now shows live deployment verification and updates
every 15 seconds.

## Deployment-handler integration

The installer attempts to add `record_installed_release()` to the active
deployment handler before the agent restarts. It prints a warning instead of
blindly modifying the handler when it cannot find a safe integration point.
