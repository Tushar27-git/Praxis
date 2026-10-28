from pathlib import Path
import time
import unittest
from PIL import Image
from coc_advisor.stream import LiveFrame
from coc_advisor.perception import Perception, GeometryGuard

FIXTURES=Path(__file__).parent/'fixtures/perception'


class PerceptionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.reader=Perception()
    def frame(self,name):
        now=time.monotonic(); return LiveFrame('emulator-5554',Image.open(FIXTURES/name).convert('RGB'),1,1,now,now,now,(1600,900))
    def test_real_home_match_army_result_scenes(self):
        for name in ['home','match','army','result']:
            with self.subTest(name=name):self.assertEqual(self.reader.scene(self.frame(name+'.png').image)[0],name)
    def test_current_army_is_read_from_cards(self):
        observation=self.reader.observe(self.frame('army.png'))
        self.assertEqual([(x['name'],x['count'],x['level']) for x in observation.inventory],
                         [('barbarian',20,1),('archer',10,1)])
    def test_matchmaking_cost_is_read_instead_of_assumed(self):
        self.assertEqual(self.reader.observe(self.frame('match.png')).hud.get('match_cost'),10)
    def test_known_victory_requires_result_evidence(self):
        o=self.reader.observe(self.frame('result.png'))
        self.assertEqual((o.result['destruction'],o.result['stars']),(100,3))
        self.assertIsNone(self.reader.observe(self.frame('home.png')).result)
    def test_scout_counts_and_geometry_come_from_current_frame(self):
        o=self.reader.observe(self.frame('scout.png'))
        self.assertEqual(o.scene,'scout'); self.assertEqual(o.hud['remaining'],[20,10])
        self.assertIsNotNone(o.layout['entry'])
    def test_unknown_screen_has_no_actions_or_fake_inventory(self):
        now=time.monotonic(); f=LiveFrame('emulator-5554',Image.new('RGB',(960,540),'purple'),1,1,now,now,now)
        o=self.reader.observe(f)
        self.assertEqual(o.scene,'unknown'); self.assertEqual(o.inventory,[])
    def test_inactivity_modal_is_not_the_home_screen_behind_it(self):
        o=self.reader.observe(self.frame('disconnected.png'))
        self.assertEqual(o.scene,'disconnected')
        self.assertNotIn('home_battle',o.buttons)
    def test_same_scene_camera_shift_invalidates_geometry(self):
        from PIL import ImageChops
        image=self.frame('scout.png').image
        guard=GeometryGuard(image)
        self.assertTrue(guard.matches(image))
        self.assertFalse(guard.matches(ImageChops.offset(image,40,25)))
