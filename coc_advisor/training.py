"""Offline regression, disjoint evaluation and between-battle activation."""
import hashlib
import json
from pathlib import Path
import threading
import time
import uuid
import subprocess
import sys
from .prediction import finite,load_model,predict,validate_model


def atomic_json(path,value):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix('.tmp'); temp.write_text(json.dumps(value,allow_nan=False,indent=2),encoding='utf-8'); temp.replace(path)


def train_candidate(accepted_episodes,destination):
    import numpy as np
    from sklearn.linear_model import Ridge
    from sklearn.preprocessing import StandardScaler
    rows={r['id']:r for r in accepted_episodes if r.get('status')=='accepted'
          and r.get('result',{}).get('verified') is True}
    rows=sorted(rows.values(),key=lambda r:(r['created'],r['id']))
    if len(rows)<40:return {'status':'insufficient_data','accepted_battles':len(rows),'required':40}
    evaluation=rows[-20:]; training=rows[:-20]
    eval_bases={r['context'].get('base_id') for r in evaluation}-{None}
    training=[r for r in training if r['context'].get('base_id') not in eval_bases]
    if len(training)<20:return {'status':'insufficient_data','accepted_battles':len(rows),'reason':'Grouped split needs more independent battles'}
    features=training[0]['context'].get('features',{})
    names=sorted(k for k,v in features.items() if finite(v))
    if not names:return {'status':'insufficient_data','reason':'No observed numeric features'}
    usable=lambda r: all(finite(r['context'].get('features',{}).get(k)) for k in names)
    training=[r for r in training if usable(r)]; evaluation=[r for r in evaluation if usable(r)]
    if len(training)<20 or len(evaluation)<20:return {'status':'insufficient_data','reason':'Incomplete feature observations'}
    domains=sorted({r['context']['features'].get('domain') for r in training if r['context']['features'].get('domain')})
    if not domains:return {'status':'insufficient_data','reason':'Unknown TH/army domain'}
    x=np.array([[r['context']['features'][k] for k in names] for r in training]); y=np.array([r['result']['destruction'] for r in training])
    scaler=StandardScaler(); xx=scaler.fit_transform(x); reg=Ridge(alpha=1.).fit(xx,y)
    model=validate_model(dict(schema_version=1,model_id=uuid.uuid4().hex,feature_names=names,
        mean=scaler.mean_.tolist(),scale=scaler.scale_.tolist(),weights=reg.coef_.tolist(),
        intercept=float(reg.intercept_),domains=domains))
    errors=[]; baseline=[]; slices={}
    for row in evaluation:
        pred=predict(row['context']['features'],model)['expected_destruction']
        if pred is None:return {'status':'insufficient_data','reason':'Unseen evaluation domain'}
        error=abs(pred-row['result']['destruction']); errors.append(error)
        baseline.append(abs(float(y.mean())-row['result']['destruction']))
        slices.setdefault(row['context']['features']['domain'],[]).append(error)
    report=dict(status='candidate',model=model,created=time.time(),
        train_ids=[r['id'] for r in training],evaluation_ids=[r['id'] for r in evaluation],
        train_maxtime=max(r['created'] for r in training),evaluation_mintime=min(r['created'] for r in evaluation),
        mae=float(np.mean(errors)),baseline_mae=float(np.mean(baseline)),baseline=float(y.mean()),
        slice_mae={k:float(np.mean(v)) for k,v in slices.items()},
        data_digest=hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest())
    atomic_json(Path(destination)/'candidate.json',report)
    return report


def evaluate_candidate(candidate,incumbent,evaluation_ids):
    import numpy as np
    rows=evaluation_ids; model=candidate['model']; model_id=model['model_id']; paired=[]; baseline_pairs=[]; slices={}
    evaluation=[r for r in rows if r['id'] in candidate.get('evaluation_ids',[])]
    if len(evaluation)<20:return {'promote':False,'reason':'Missing held-out evaluation evidence'}
    if incumbent:
        deltas=[]
        for r in evaluation:
            features=r['context'].get('features',{}); a=predict(features,model)['expected_destruction']; b=predict(features,incumbent)['expected_destruction']
            if a is None or b is None:return {'promote':False,'reason':'Incumbent comparison unsupported'}
            deltas.append(abs(a-r['result']['destruction'])-abs(b-r['result']['destruction']))
        if np.mean(deltas)>=0:return {'promote':False,'reason':'Evaluation incumbent was not beaten'}
    for row in rows:
        if row['created']<=candidate['created']:continue
        if row['id'] in set(candidate.get('train_ids',[])+candidate.get('evaluation_ids',[])):continue
        prediction=row.get('prediction') or {}; shadow=prediction.get('challengers',{}).get(model_id)
        if not finite(shadow) or prediction.get('predicted_at') is None:continue
        if row['status']!='accepted':continue
        actual=row['result']['destruction']
        if incumbent:
            if prediction.get('model_id')!=incumbent['model_id']:continue
            champion=prediction.get('expected_destruction')
            if not finite(champion):continue
        else:champion=candidate['baseline']
        diff=abs(shadow-actual)-abs(champion-actual); paired.append(diff)
        baseline_pairs.append(abs(shadow-actual)-abs(candidate['baseline']-actual))
        domain=row['context'].get('features',{}).get('domain'); slices.setdefault(domain,[]).append(diff)
    if len(paired)<20:return {'promote':False,'reason':'Need 20 new prospective paired forecasts','count':len(paired)}
    if candidate['mae']>=candidate['baseline_mae']:return {'promote':False,'reason':'Candidate did not beat evaluation baseline'}
    # Resample whole battles, never frames. This does not certify a 98% win rate.
    rng=np.random.default_rng(17); a=np.asarray(paired)
    upper=float(np.quantile(a[rng.integers(0,len(a),(2000,len(a)))].mean(axis=1),.95))
    baseline_array=np.asarray(baseline_pairs)
    baseline_upper=float(np.quantile(baseline_array[rng.integers(0,len(a),(2000,len(a)))].mean(axis=1),.95))
    enough=set(slices)==set(model['domains']) and all(len(v)>=20 and np.mean(v)<0 for v in slices.values())
    return dict(promote=bool(upper<0 and baseline_upper<0 and enough),reason='paired prospective MAE gate',upper_mae_delta=upper,upper_baseline_delta=baseline_upper,count=len(paired))


class LearningCoordinator:
    def __init__(self,store,root):
        self.store=store; self.root=Path(root); self.root.mkdir(parents=True,exist_ok=True)
        self.battle_active=False; self.lock=threading.Lock(); self.worker=None; self.status={'status':'waiting_for_data'}

    def snapshot(self): return load_model(self.root/'active.json')

    def shadow(self,features):
        path=self.root/'candidate.json'
        if not path.exists():return {}
        candidate=json.loads(path.read_text(encoding='utf-8')); m=candidate['model']
        value=predict(features,m)['expected_destruction']
        return {m['model_id']:value} if value is not None else {}

    def on_completed_battle(self,battle_id):
        if self.battle_active:return {'status':'deferred'}
        rows=self.store.episodes('accepted'); path=self.root/'candidate.json'
        if not path.exists():
            result=train_candidate(rows,self.root)
        else:
            candidate=json.loads(path.read_text(encoding='utf-8')); decision=evaluate_candidate(candidate,self.snapshot(),rows)
            result={'status':'evaluating','decision':decision}
            with self.lock:
                if decision['promote'] and not self.battle_active:
                    active=self.snapshot()
                    if active:atomic_json(self.root/'previous.json',active)
                    atomic_json(self.root/'active.json',candidate['model'])
                    atomic_json(self.root/'promotion.json',decision)
                    path.rename(self.root/f"evaluated-{candidate['model']['model_id']}.json")
                    result={'status':'promoted','model_id':candidate['model']['model_id']}
        self.status=result; return result

    def schedule(self,battle_id):
        if self.battle_active or (self.worker and self.worker.poll() is None):return
        self.store.flush()
        with (self.root/'training.log').open('ab') as log:
            self.worker=subprocess.Popen([sys.executable,'-m','coc_advisor.training',
                '--data',str(self.store.path.parent),'--models',str(self.root)],
                stdout=log,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        self.status={'status':'training_worker_started'}

    def set_battle_active(self,active):
        with self.lock:self.battle_active=active
        if active and self.worker and self.worker.poll() is None:
            self.worker.terminate()
            try:self.worker.wait(timeout=1)
            except subprocess.TimeoutExpired:self.worker.kill(); self.worker.wait(timeout=1)
            self.status={'status':'training_preempted_for_gameplay'}

    def rollback(self):
        with self.lock:
            if self.battle_active:raise RuntimeError('Cannot swap a model during battle')
            model=load_model(self.root/'previous.json')
            if model is None:raise RuntimeError('No previous validated model')
            atomic_json(self.root/'active.json',model)

    def close(self,wait=0):
        if not self.worker or self.worker.poll() is not None:return
        if wait:
            try:self.worker.wait(timeout=wait); return
            except subprocess.TimeoutExpired:pass
        self.worker.terminate()
        try:self.worker.wait(timeout=1)
        except subprocess.TimeoutExpired:self.worker.kill();self.worker.wait(timeout=1)


if __name__=='__main__':
    import argparse
    from .experience import ExperienceStore
    from threadpoolctl import threadpool_limits
    parser=argparse.ArgumentParser(); parser.add_argument('--data',required=True); parser.add_argument('--models',required=True)
    args=parser.parse_args(); store=ExperienceStore(args.data)
    try:
        with threadpool_limits(limits=1):print(json.dumps(LearningCoordinator(store,args.models).on_completed_battle(None)),flush=True)
    finally:store.close()
