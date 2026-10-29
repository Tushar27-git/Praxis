from types import SimpleNamespace
import unittest
from coc_advisor.runtime import ResultVerifier
from pathlib import Path
import tempfile
from unittest.mock import patch
from coc_advisor.runtime import AttackRuntime
from coc_advisor.stream import LiveFrame
from PIL import Image
import json
import threading
import time


class RuntimeTests(unittest.TestCase):
    def test_pause_evidence_is_bounded_and_skips_unrecognized_screens(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]/'tmp') as tmp, patch('coc_advisor.runtime.ROOT',Path(tmp)):
            runtime=AttackRuntime(None,None)
            now=time.monotonic()
            frame=LiveFrame('emulator-5554',Image.new('RGB',(20,20)),1,100000,now,now,now)
            o=SimpleNamespace(scene='unknown',frame=frame,hud={},unknown=[])
            try:
                runtime.controller.reason='Paused: unreadable screen'
                runtime.record_pause(o)
                self.assertFalse((Path(tmp)/'recordings/diagnostics').exists())
                o.scene='army'
                for i in range(12):
                    runtime.controller.reason=f'Paused: unreadable card {i}'
                    runtime.record_pause(o)
            finally:runtime.run(timeout=0)
            images=list(Path(tmp).glob('recordings/diagnostics/*/*.png'))
            self.assertEqual(len(images),10)
            self.assertEqual(len(list(Path(tmp).glob('recordings/diagnostics/*/*.json'))),10)
    def test_repeated_pause_saves_one_frame_with_observed_state(self):
        stop=threading.Event()
        class Source:
            def __init__(self):self.sequence=0
            def latest(self):
                self.sequence+=1; now=time.monotonic()
                return LiveFrame('emulator-5554',Image.new('RGB',(960,540),'purple'),self.sequence,self.sequence*100000,now,now,now)
        class Reader:
            def __init__(self):self.observations=0
            def canonical(self,image):
                import numpy as np
                return np.array(image)
            def recognize_lines(self,crops):return []
            def observe(self,frame):
                self.observations+=1
                if self.observations==3:stop.set()
                return SimpleNamespace(scene='home',frame=frame,buttons={},inventory=[],unknown=['Unreadable title'],hud={},layout=None,result=None,elapsed_ms=0)
        class Client:
            def tap_latest(self,*args):raise AssertionError('Paused controller must not send inputs')
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]/'tmp') as tmp, patch('coc_advisor.runtime.ROOT',Path(tmp)):
            runtime=AttackRuntime(Client(),Source(),stop=stop); runtime.reader=Reader()
            runtime.run(timeout=2)
            images=list(Path(tmp).glob('recordings/diagnostics/*/*.png'))
            self.assertEqual(len(images),1)
            metadata=json.loads(images[0].with_suffix('.json').read_text(encoding='utf-8'))
            self.assertEqual(metadata['reason'],'Paused: own Town Hall level not verified')
            self.assertEqual(metadata['unknown'],['Unreadable title'])
            self.assertEqual(metadata['source_pts_us'],200000)
            with Image.open(images[0]) as saved:self.assertEqual(saved.size,(960,540))
    def test_zero_input_cap_never_calls_android(self):
        class Source:
            def __init__(self):self.calls=0
            def latest(self):
                self.calls+=1
                return None if self.calls==1 else SimpleNamespace(sequence=1,image=None)
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
            statuses=[]
            r=AttackRuntime(Client(),Source(),max_inputs=0,on_status=statuses.append); r.reader=Reader()
            self.assertIsNone(r.run(timeout=.5)); self.assertEqual(r.actions,0)
            self.assertIn('Input cap reached',statuses[-1])
    def test_missing_video_times_out_without_android_inputs(self):
        class Source:
            def latest(self):return None
        class Client:
            def tap_latest(self,*args):raise AssertionError('No video must mean no input')
        root=Path(__file__).resolve().parents[1]/'tmp'
        with tempfile.TemporaryDirectory(dir=root) as temp, patch('coc_advisor.runtime.ROOT',Path(temp)):
            statuses=[]
            r=AttackRuntime(Client(),Source(),on_status=statuses.append)
            self.assertIsNone(r.run(timeout=.02)); self.assertEqual(r.actions,0)
            self.assertIn('timeout',statuses[-1])
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
    def test_unreadable_frame_breaks_result_confirmation(self):
        v=ResultVerifier(); o=SimpleNamespace(result={'destruction':100,'stars':3},frame=SimpleNamespace(source_pts_us=1))
        v.consider(o)
        o.result=None; o.frame.source_pts_us=100000
        self.assertIsNone(v.consider(o))
        o.result={'destruction':100,'stars':3}; o.frame.source_pts_us=300000
        self.assertIsNone(v.consider(o))
        o.frame.source_pts_us=550000
        self.assertTrue(v.consider(o)['verified'])
    def test_missing_or_reversed_timestamp_breaks_result_confirmation(self):
        for timestamp in (None,500000):
            with self.subTest(timestamp=timestamp):
                v=ResultVerifier(); o=SimpleNamespace(result={'destruction':100,'stars':3},frame=SimpleNamespace(source_pts_us=1000000))
                v.consider(o); o.frame.source_pts_us=timestamp
                self.assertIsNone(v.consider(o))
                o.frame.source_pts_us=1300000
                self.assertIsNone(v.consider(o))
                o.frame.source_pts_us=1550000
                self.assertTrue(v.consider(o)['verified'])
