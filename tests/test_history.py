import unittest
from services.history import summarize_health
class HistoryTests(unittest.TestCase):
    def test_summary(self):
        rows=[{'display_id':'a','online':1,'display_app_running':1,'cpu_temp':50.0,'memory_percent':20.0,'disk_percent':30.0,'sync_state':'success'},{'display_id':'a','online':1,'display_app_running':0,'cpu_temp':70.0,'memory_percent':40.0,'disk_percent':30.0,'sync_state':'error'}]
        result=summarize_health(rows)[0]
        self.assertEqual(result['uptime_percent'],100.0)
        self.assertEqual(result['app_uptime_percent'],50.0)
        self.assertEqual(result['sync_errors'],1)
if __name__=='__main__': unittest.main()
