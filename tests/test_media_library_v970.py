from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
if not (ROOT/'hub').exists(): ROOT=ROOT/'payload'
class MediaV970Tests(unittest.TestCase):
 def test_guided_workflow(self):
  t=(ROOT/'hub/templates/media.html').read_text();self.assertIn('Choose media',t);self.assertIn('Arrange playback',t);self.assertIn('data-playlist-dropzone',t);self.assertIn('data-add-selected-media',t)
 def test_single_ordering_surface(self):
  t=(ROOT/'hub/templates/media.html').read_text();self.assertNotIn('media-side-column">\n      <section class="media-panel media-playlist-panel">',t);self.assertIn('media-playlist-full',t)
 def test_interactions(self):
  j=(ROOT/'hub/static/media-library-v970.js').read_text();self.assertIn('text/media-path',j);self.assertIn('data-remove-playlist',j);self.assertIn('addCard',j)
 def test_stale_test_fixed(self):
  t=(ROOT/'tests/test_command_center_v920.py').read_text();self.assertIn('data-job-drawer',t);self.assertNotIn('{% if active_jobs %}',t)
if __name__=='__main__':unittest.main()
