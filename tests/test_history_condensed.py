import unittest
from services.history import summarize_events

class HistoryCondensedTests(unittest.TestCase):
    def test_summarize_events_groups_categories(self):
        result=summarize_events([
            {"category":"sync","created_at":"2026-01-01T10:00:00","message":"a"},
            {"category":"sync","created_at":"2026-01-02T10:00:00","message":"b"},
            {"category":"deploy","created_at":"2026-01-01T09:00:00","message":"c"},
        ])
        by={item["category"]:item for item in result}
        self.assertEqual(by["sync"]["count"],2)
        self.assertEqual(by["sync"]["latest_message"],"b")

if __name__ == "__main__": unittest.main()
