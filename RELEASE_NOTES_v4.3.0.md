# v4.3.0 — Hub-managed display software deployment

## Changed

Display software updates no longer require Git on the Raspberry Pi.

## Deployment process

1. Hub builds a display-only package from the selected Git tag.
2. Hub computes and sends its SHA-256 checksum.
3. Agent downloads the package from the Hub over LAN.
4. Agent verifies the checksum and package version.
5. Agent extracts to a temporary staging directory.
6. Agent compiles staged Python source.
7. Agent backs up the currently installed display source.
8. Agent installs the new application, agent, scripts, and requirements.
9. Agent updates Python dependencies.
10. Agent restarts and verifies the player.
11. Agent reports success and restarts itself.
12. On failure, the prior display source is restored automatically.

Runtime media, configuration, status, logs, and the existing virtual
environment are preserved.

## Operator workflow

Use the existing Deployments page:

- choose a tagged version;
- select one or more displays;
- run a dry run first;
- deploy to a canary display;
- deploy to groups/sites after verification.

The bootstrap installer remains only for first installation or disaster recovery.
