# v4.3.3 — Immutable display release artifacts

## Fixed

Display deployments no longer rebuild a package when the Pi downloads it.

When a deployment job is queued, the Hub now:

1. builds the package once;
2. writes the exact bytes to `hub/data/display-releases/<sha256>.tar.gz`;
3. verifies the stored file against the checksum;
4. places that checksum and checksum-addressed URL in the job;
5. serves the same immutable file to the display.

This removes package-generation differences, process differences, timing
differences, and request-time rebuilds from checksum verification.

## Required action

Cancel or resolve every deployment job created before this update. Old jobs
reference old URLs/checksums. Queue a completely new dry-run deployment after
the Hub restarts.
