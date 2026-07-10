# Church Display Platform Architecture

## Components

- `hub/`: Flask management application. Owns discovery, jobs, deployments, media browsing, schedules, health, and release views.
- `display/`: Display player, local admin API, sync scripts, and long-running Python agent.
- `shared/`: API contracts and constants shared conceptually across Hub and display.
- `release/`: Reproducible source-package builder, manifest generator, release notes generator, and verifier.
- `scripts/`: Development and repository maintenance commands.

## Runtime ownership

Runtime files must not be committed. The Hub owns files under `hub/config/`, `hub/logs/`, and `hub/static/previews/`. The display owns `display/media/`, `display/status/`, `display/logs/`, and its local configuration.

## Job flow

1. The Hub creates a job in its job store.
2. The display agent polls `/api/v1/jobs/next`.
3. The agent dispatches the job to a typed Python handler.
4. Progress and completion are reported to `/api/v1/jobs/<id>/status`.

## Release flow

1. Commit all source changes.
2. Tag the intended release.
3. Run `./release/build_release.py vX.Y.Z`.
4. Verify with `./release/verify.py ... --manifest ...`.
5. Publish the ZIP, manifest, checksums, and release notes together.

The release builder refuses dirty working trees by default to prevent unreproducible artifacts.
