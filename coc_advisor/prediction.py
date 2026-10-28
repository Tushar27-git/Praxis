"""Numeric-only model artifacts; absent/unsupported evidence means unknown."""
import json
import math
from pathlib import Path


def finite(value): return type(value) in (int,float) and math.isfinite(value)


def validate_model(model):
    if model.get('schema_version')!=1 or not isinstance(model.get('model_id'),str):
        raise ValueError('Unsupported prediction schema.')
    names=model.get('feature_names',[]); n=len(names)
    if not n or len(set(names))!=n or not all(isinstance(x,str) for x in names): raise ValueError('Invalid features.')
    for key in ('mean','scale','weights'):
        values=model.get(key,[])
        if len(values)!=n or not all(finite(x) for x in values): raise ValueError('Invalid model parameters.')
    if any(x<=0 for x in model['scale']) or not finite(model.get('intercept')): raise ValueError('Invalid scaling.')
    if not model.get('domains') or not all(isinstance(x,str) for x in model['domains']): raise ValueError('No supported domains.')
    return model


def load_model(path):
    path=Path(path)
    if not path.is_file(): return None
    return validate_model(json.loads(path.read_text(encoding='utf-8')))


def predict(features, model_snapshot):
    result={'expected_destruction':None,'model_id':None,'schema_version':1,'reason':'No validated model'}
    if model_snapshot is None:return result
    model=validate_model(model_snapshot); result['model_id']=model['model_id']
    if features.get('domain') not in model['domains']:
        result['reason']='Unsupported TH/army domain'; return result
    values=[features.get(name) for name in model['feature_names']]
    if not all(finite(v) for v in values):
        result['reason']='Missing or non-finite observation'; return result
    value=model['intercept']+sum(w*(x-m)/s for x,m,s,w in zip(values,model['mean'],model['scale'],model['weights']))
    result.update(expected_destruction=max(0.,min(100.,value)),reason='Expected destruction; not success probability')
    return result
