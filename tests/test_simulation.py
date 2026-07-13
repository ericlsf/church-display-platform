import unittest
from datetime import datetime
from unittest.mock import patch
from services.simulation import resolve_simulation

class SimulationTests(unittest.TestCase):
    @patch('services.simulation.load_resilience', return_value={'maintenance': {'enabled': False, 'message': ''}})
    @patch('services.simulation.get_playlist_entry', return_value={'published_order': ['a.jpg','b.mp4']})
    @patch('services.simulation.load_schedules')
    @patch('services.simulation.load_config', return_value={'displays':[{'id':'lobby','name':'Lobby'}]})
    def test_resolves_latest_schedule(self, _cfg, schedules, _playlist, _resilience):
        schedules.return_value={'schedules':[{'id':'1','display_id':'lobby','job_type':'set_sync_folder','run_at':'2026-07-10T08:00','recurrence':'once','enabled':True,'payload':{'remote':'gdrive','folder':'Weekly'}},{'id':'2','display_id':'lobby','job_type':'set_sync_folder','run_at':'2026-07-10T09:00','recurrence':'once','enabled':True,'payload':{'remote':'gdrive','folder':'Missions'}}]}
        result=resolve_simulation('lobby', datetime.fromisoformat('2026-07-10T10:00'))
        self.assertEqual(result['folder'],'Missions')
        self.assertEqual(result['first_media'],'a.jpg')

if __name__=='__main__': unittest.main()
