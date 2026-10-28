from types import SimpleNamespace
import unittest
from coc_advisor.runtime import ResultVerifier
from pathlib import Path
import tempfile
from unittest.mock import patch
from coc_advisor.runtime import AttackRuntime


class RuntimeTests(unittest.TestCase):
    def test_zero_input_cap_never_calls_android(self):
        class Source:
            def latest(self):return SimpleNamespace(sequence=1,image=None)
        class Reader:
            def canonical(self,image):
                import numpy as np
                return np.zeros((540,960,3),dtype='uint8')
            def recognize_lines(self,crops):return []
            def observe(self,frame):return SimpleNamespace(scene='home',frame=frame,buttons={'home_battle':(.06,.89)},inventory=[],unknown=[],hud={'own_th':2},layout=None,result=None,elapsed_ms=0)
        class Client:
            def tap_latest(self,*args):raise AssertionError('Input cap failed')
        root=Path(__file__).resolve().parents[1]/'tmp'
        with tempfile.TemporaryDirectory(dir=root) as temp, patch('coc_advisor.runtime.ROOT',Path(temp)):
            r=AttackRuntime(Client(),Source(),max_inputs=0); r.reader=Reader()
            self.assertIsNone(r.run(timeout=.5)); self.assertEqual(r.actions,0)
    def test_result_needs_distinct_spaced_source_frames(self):
        v=ResultVerifier()
        o=SimpleNamespace(result={'destruction':100,'stars':3,'method':'validated-template'},frame=SimpleNamespace(source_pts_us=1000000))
        self.assertIsNone(v.consider(o)); self.assertIsNone(v.consider(o))
        o.frame.source_pts_us=1250000
        self.assertTrue(v.consider(o)['verified'])
    def test_conflicting_result_restarts_verification(self):
        v=ResultVerifier(); o=SimpleNamespace(result={'destruction':100,'stars':3},frame=SimpleNamespace(source_pts_us=1))
        v.consider(o); o.result={'destruction':50,'stars':1}; o.frame.source_pts_us=300000
        self.assertIsNone(v.consider(o))
