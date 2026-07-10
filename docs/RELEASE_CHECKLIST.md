# Release checklist

## Before tagging

1. Work from `main`.
2. Pull the latest remote changes with `git pull --ff-only origin main`.
3. Confirm the working tree is clean.
4. Run:

   ```bash
   ./scripts/validate-release.sh vX.Y.Z
   ```

5. Review the generated manifest, checksum, and release notes.

## Tag and publish

```bash
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin vX.Y.Z
```

GitHub Actions should run tests, build the package, verify it, and publish the release artifact.

## Deployment test order

1. Deploy to one test display using **Dry Run**.
2. Deploy the same version using **Real Deploy**.
3. Run:

   ```bash
   ./scripts/post-deploy-check.sh vX.Y.Z
   ```

4. Confirm:
   - agent is active;
   - Hub health page responds;
   - display heartbeat resumes;
   - preview upload resumes;
   - content sync source is `hub`;
   - current playlist and revision match;
   - rollback marker exists;
   - no repository files are dirty.

## Content-cache behavior

Test these Google Drive changes:

1. Add a new file: it should appear at the front under `newest_first`.
2. Modify an existing file: it should move to the front.
3. Delete a file: it should disappear from the manifest and display cache.
4. Reorder manually: unchanged files should retain the saved relative order.
5. Disconnect Drive temporarily: displays should continue using Hub-cached content.
6. Disconnect Hub temporarily: the display should keep playing its local cache.

## Rollback exercise

At least once per minor release:

1. Deploy an older known-good tag to the test display.
2. Confirm the repository stays on `main`.
3. Deploy the current release again.
4. Verify agent, Hub, content sync, and playback.
5. Record the result in the release notes or issue tracker.
