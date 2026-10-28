from pathlib import Path
import tempfile
import unittest
from coc_advisor.experience import ExperienceStore


class ExperienceTests(unittest.TestCase):
    def setUp(self):
        root=Path(__file__).resolve().parents[1]/'tmp'; root.mkdir(exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=root)
        self.store=ExperienceStore(Path(self.temp.name))
    def tearDown(self): self.store.close(); self.temp.cleanup()
    def test_prediction_result_join_and_idempotence(self):
        b=self.store.begin_battle({'features':{'own_th':2},'observed_at':1})
        self.store.record_prediction(b,{'predicted_at':2,'expected_destruction':70,'model_id':'m1'})
        r={'destruction':100,'stars':3,'verified':True,'evidence':'result.png'}
        self.store.finish_battle(b,r); self.store.finish_battle(b,r)
        rows=self.store.episodes('accepted')
        self.assertEqual(len(rows),1); self.assertEqual(rows[0]['prediction']['model_id'],'m1')
        self.assertEqual(rows[0]['result']['destruction'],100)
    def test_uncertain_and_invalid_results_quarantined(self):
        for r in [{'destruction':100,'stars':3,'verified':False},
                  {'destruction':101,'stars':3,'verified':True,'evidence':'x'},
                  {'destruction':100,'stars':0,'verified':True,'evidence':'x'}]:
            b=self.store.begin_battle({}); self.store.finish_battle(b,r)
        self.assertEqual(len(self.store.episodes('quarantined')),3)
        self.assertEqual(self.store.episodes('accepted'),[])
    def test_interrupted_battle_not_training_label(self):
        self.store.begin_battle({'skipped':True})
        self.assertEqual(len(self.store.episodes('incomplete')),1)
        self.assertEqual(self.store.episodes('accepted'),[])
    def test_conflicting_later_result_quarantines_previous_label(self):
        b=self.store.begin_battle({})
        self.store.finish_battle(b,{'destruction':100,'stars':3,'verified':True,'evidence':'a'})
        self.store.finish_battle(b,{'destruction':50,'stars':1,'verified':True,'evidence':'b'})
        self.assertEqual(self.store.episodes('accepted'),[])
        self.assertEqual(len(self.store.episodes('quarantined')),1)
    def test_future_features_rejected(self):
        b=self.store.begin_battle({'observed_at':5})
        with self.assertRaises(ValueError): self.store.record_prediction(b,{'predicted_at':2})
