# Historical migration helpers

These scripts were used to apply earlier one-time release migrations.

They are retained for historical reference and disaster recovery, but they are
not active application code and are excluded from normal source validation.

New releases should update the current source tree directly and use the release
pipeline rather than adding another permanent `apply-vX.Y.Z` helper.
