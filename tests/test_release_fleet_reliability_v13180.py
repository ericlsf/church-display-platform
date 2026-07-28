import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import services.display_release_catalog as catalog
import services.jobs as jobs


def test_release_readiness_requires_aligned_versions_and_reachable_tag():
    with tempfile.TemporaryDirectory() as temp_dir:
        hub_version = Path(temp_dir) / "hub-version"
        display_version = Path(temp_dir) / "display-version"
        hub_version.write_text("v13.18.0\n", encoding="utf-8")
        display_version.write_text("13.18.0\n", encoding="utf-8")

        with (
            patch.object(catalog, "HUB_VERSION_FILE", hub_version),
            patch.object(catalog, "DISPLAY_VERSION_FILE", display_version),
            patch.object(catalog, "latest_display_tag", return_value="v13.18.0"),
            patch.object(catalog, "_git", return_value=""),
            patch.object(catalog, "_git_ok", return_value=True),
        ):
            readiness = catalog.release_readiness()

    assert readiness["ready"] is True
    assert readiness["hub_version"] == "v13.18.0"
    assert readiness["display_version"] == "v13.18.0"
    assert readiness["expected_tag_reachable"] is True


def test_queued_job_expires_with_actionable_message():
    with tempfile.TemporaryDirectory() as temp_dir:
        jobs_file = Path(temp_dir) / "jobs.json"
        jobs_file.write_text(
            json.dumps(
                {
                    "jobs": [
                    {
                        "id": "queued-too-long",
                        "status": "queued",
                        "created_at": (
                            datetime.now() - timedelta(minutes=10)
                        ).isoformat(),
                        "queue_timeout_seconds": 300,
                    }
                    ]
                }
            ),
            encoding="utf-8",
        )

        with patch.object(jobs, "JOBS_FILE", jobs_file):
            result = jobs.list_jobs()

    assert result[0]["status"] == "timed_out"
    assert "Confirm the device is online" in result[0]["message"]


def test_waiting_job_is_labeled_before_expiration():
    waiting_job = {
        "status": "queued",
        "created_at": (datetime.now() - timedelta(minutes=6)).isoformat(),
        "queue_timeout_seconds": 86400,
    }

    assert jobs.job_waiting_state(waiting_job) == "waiting"
