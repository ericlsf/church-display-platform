# v6.4.0 — Alert Center and Authoritative Media Count

Adds actionable alerts for offline displays, degraded health, sync failures,
missing folders, zero media, available updates, high disk usage, and failed jobs.

All fleet_rows() consumers now receive raw-heartbeat-enriched media counts.
The exact count comes from player.media_count, media.total, or sync.files_synced,
replacing the stale fallback count of one.
