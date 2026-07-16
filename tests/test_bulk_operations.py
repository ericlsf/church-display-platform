import unittest
from unittest.mock import patch

from services.bulk_operations import queue_bulk_jobs


class BulkOperationsTests(unittest.TestCase):
    @patch(
        "services.bulk_operations.create_job",
        side_effect=lambda display_id, job_type, payload: {
            "id": f"{display_id}-{job_type}",
            "display_id": display_id,
            "type": job_type,
            "payload": payload,
        },
    )
    @patch(
        "services.bulk_operations.list_jobs",
        return_value=[],
    )
    @patch(
        "services.bulk_operations.load_config",
        return_value={
            "displays": [
                {"id": "welcome-center"},
                {"id": "lobby"},
            ]
        },
    )
    def test_bulk_sync_queues_each_display(
        self,
        _config,
        _jobs,
        create_job,
    ):
        result = queue_bulk_jobs(
            ["welcome-center", "lobby"],
            "sync_now",
        )

        self.assertEqual(result["queued_count"], 2)
        self.assertEqual(create_job.call_count, 2)

    @patch(
        "services.bulk_operations.load_config",
        return_value={
            "displays": [{"id": "welcome-center"}]
        },
    )
    def test_folder_is_required(self, _config):
        with self.assertRaises(ValueError):
            queue_bulk_jobs(
                ["welcome-center"],
                "assign_folder",
            )


if __name__ == "__main__":
    unittest.main()
