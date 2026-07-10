# Development workflow

## Branches

- `main` is always deployable and contains tagged releases.
- `develop` is the integration branch for completed work awaiting the next release.
- Feature and fix branches start from `develop` and merge back through pull requests.

Suggested names:

- `feature/content-calendar`
- `fix/manifest-ordering`
- `chore/release-validation`

Do not develop directly on a deployed tag or use `git reset --hard <tag>` on the development checkout. Displays may deploy tagged packages, but the canonical working repository should remain on a branch.

## Standard change flow

```bash
git switch develop
git pull --ff-only origin develop
git switch -c feature/short-description

# Make and test changes.
./scripts/repo-audit.sh
./scripts/run-tests.sh

git add <specific-files>
git commit -m "Describe the change"
git push -u origin feature/short-description
```

Open a pull request into `develop`. Before a release, open a pull request from `develop` into `main`.

## Releases

After `develop` is merged into `main` and CI passes:

```bash
git switch main
git pull --ff-only origin main
git tag -a vX.Y.Z -m "Release summary"
git push origin vX.Y.Z
```

The tag workflow runs tests, builds the source package, verifies its checksum and structure, uploads artifacts, and publishes the GitHub Release.

## Hotfixes

Create hotfix branches from `main`, merge the fix into `main`, tag a patch release, and then merge the same fix back into `develop`.

## Runtime data

Google Drive content, Hub cache, manifests generated at runtime, previews, logs, SQLite databases, status files, media caches, backups, secrets, and virtual environments do not belong in Git.
