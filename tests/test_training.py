from pathlib import Path
import tempfile
import unittest
from coc_advisor.training import train_candidate, evaluate_candidate, LearningCoordinator
from coc_advisor.prediction import predict


def episodes(n=60):
    return [dict(id=str(i),created=float(i),status='accepted',prediction=None,
        context={'observed_at':float(i),'base_id':str(i),'features':{'x':float(i),'domain':'2:barbarians'}},
        result={'destruction':float(i),'stars':0,'verified':True,'evidence':'fixture'}) for i in range(n)]


class TrainingTests(unittest.TestCase):
    def setUp(self):
        root=Path(__file__).resolve().parents[1]/'tmp'; root.mkdir(exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=root); self.root=Path(self.temp.name)
    def tearDown(self): self.temp.cleanup()
    def test_train_numeric_artifact_and_disjoint_chronological_manifest(self):
        report=train_candidate(episodes(40),self.root)
        self.assertEqual(report['status'],'candidate')
        self.assertFalse(set(report['train_ids'])&set(report['evaluation_ids']))
        self.assertLess(report['train_maxtime'],report['evaluation_mintime'])
        self.assertLess(abs(predict({'x':35,'domain':'2:barbarians'},report['model'])['expected_destruction']-35),2)
    def test_one_battle_repeated_frames_does_not_create_dataset(self):
        data=[episodes(1)[0]]*100
        self.assertEqual(train_candidate(data,self.root)['status'],'insufficient_data')
    def test_repeated_base_is_removed_from_training_if_in_evaluation(self):
        data=episodes(60); data[0]['context']['base_id']=data[-1]['context']['base_id']
        r=train_candidate(data,self.root)
        self.assertNotIn('0',r['train_ids'])
    def test_no_promotion_without_new_prospective_forecasts(self):
        r=train_candidate(episodes(40),self.root)
        self.assertFalse(evaluate_candidate(r,None,episodes(60))['promote'])
    def test_training_is_deferred_while_battle_active(self):
        class Store:
            def episodes(self,*a): raise AssertionError('Must not read/train during battle')
        c=LearningCoordinator(Store(),self.root); c.battle_active=True
        self.assertEqual(c.on_completed_battle('x')['status'],'deferred')
    def test_promotion_cannot_regress_to_prospective_historical_baseline(self):
        model=dict(schema_version=1,model_id='m',feature_names=['x'],mean=[0],scale=[1],weights=[0],intercept=10,domains=['2:basic'])
        incumbent=dict(model,model_id='old',intercept=0)
        candidate=dict(model=model,created=100,mae=0,baseline_mae=40,baseline=50,evaluation_ids=[str(i) for i in range(20)])
        data=[dict(id=str(i),created=i,status='accepted',context={'features':{'x':0,'domain':'2:basic'}},
                   prediction={'model_id':'old','predicted_at':i,'expected_destruction':0,'challengers':{'m':10}},
                   result={'destruction':10 if i<20 else 50}) for i in list(range(20))+list(range(200,220))]
        result=evaluate_candidate(candidate,incumbent,data)
        self.assertFalse(result['promote']); self.assertEqual(result['upper_baseline_delta'],40)
    def test_owned_training_process_is_reaped_on_close(self):
        class Worker:
            def __init__(self):self.terminated=False
            def poll(self):return 0 if self.terminated else None
            def terminate(self):self.terminated=True
            def wait(self,timeout):return 0
        c=LearningCoordinator(None,self.root); w=Worker(); c.worker=w
        c.close(); self.assertTrue(w.terminated)
    def test_every_advertised_domain_requires_prospective_evidence(self):
        model=dict(schema_version=1,model_id='m',feature_names=['x'],mean=[0],scale=[1],weights=[0],intercept=100,domains=['2:basic','3:basic'])
        incumbent=dict(model,model_id='old',intercept=0)
        candidate=dict(model=model,created=100,mae=0,baseline_mae=100,baseline=0,evaluation_ids=[str(i) for i in range(20)])
        rows=[dict(id=str(i),created=i,status='accepted',context={'features':{'x':0,'domain':'2:basic'}},
                   prediction={'model_id':'old','predicted_at':i,'expected_destruction':0,'challengers':{'m':100}},
                   result={'destruction':100}) for i in list(range(20))+list(range(200,220))]
        self.assertFalse(evaluate_candidate(candidate,incumbent,rows)['promote'])
