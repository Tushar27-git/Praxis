"""Actual chosen-tactic evidence, never imagined counterfactual rewards."""
from collections import defaultdict
from .prediction import finite


def compare_strategies(rows):
    groups=defaultdict(list)
    for row in rows:
        actual=row.get('actual_destruction')
        if not row.get('verified') or not finite(actual) or not 0<=actual<=100:continue
        if not row.get('chosen') or not row.get('domain'):continue
        groups[row['chosen']].append((row['domain'],actual))
    return {name:dict(count=len(values),mean_destruction=sum(x[1] for x in values)/len(values),
                     domains=sorted({x[0] for x in values}),policy_improvement_proven=False)
            for name,values in groups.items()}
