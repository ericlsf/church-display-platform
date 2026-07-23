# v5.6.3 — Version API Compatibility

The display updated successfully and VERSION reported 5.6.2, but the agent exited
because update.py still imports get_version_info(), which had been removed.

This release restores get_version_info() while preserving VERSION-file authority.
