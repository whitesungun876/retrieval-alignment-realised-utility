"""Prospectively frozen target-level P-C analysis; no automatic file discovery."""

from __future__ import annotations

from collections import defaultdict
import math
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
from scipy import stats


ALPHA = .05
MARGIN = .05
RESAMPLES = 10_000
SEED = 202608120904


def target_condition_means(rows: Iterable[Mapping[str, Any]]) -> dict[str, dict[str, float]]:
    grouped: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        if bool(row.get("technical_failure")):
            continue
        grouped[str(row["target_id"])][str(row["condition"])].append(float(bool(row["terminal_success"])))
    return {target:{condition:float(np.mean(values)) for condition,values in conditions.items() if values} for target,conditions in grouped.items()}


def paired_differences(means: Mapping[str, Mapping[str,float]]) -> tuple[list[str], np.ndarray]:
    targets=sorted(target for target,value in means.items() if "P" in value and "C" in value)
    return targets,np.asarray([means[target]["P"]-means[target]["C"] for target in targets],dtype=float)


def bootstrap_ci(values: Sequence[float], quantiles: tuple[float,float]=(.025,.975),resamples:int=RESAMPLES,seed:int=SEED)->tuple[float,float]:
    x=np.asarray(values,dtype=float);rng=np.random.default_rng(seed);estimates=np.empty(resamples)
    for start in range(0,resamples,1000):
        batch=min(1000,resamples-start);indices=rng.integers(0,len(x),size=(batch,len(x)));estimates[start:start+batch]=x[indices].mean(axis=1)
    low,high=np.quantile(estimates,quantiles);return float(low),float(high)


def sign_flip_pvalue(values:Sequence[float],resamples:int=RESAMPLES,seed:int=SEED+1)->float:
    x=np.asarray(values,dtype=float);observed=abs(float(x.mean()));rng=np.random.default_rng(seed);extreme=0
    for start in range(0,resamples,1000):
        batch=min(1000,resamples-start);statistics=np.abs((rng.choice((-1.,1.),size=(batch,len(x)))*x).mean(axis=1));extreme+=int(np.sum(statistics>=observed-1e-15))
    return (extreme+1)/(resamples+1)


def tost(values:Sequence[float],margin:float=MARGIN,alpha:float=ALPHA)->dict[str,Any]:
    x=np.asarray(values,dtype=float);n=len(x);mean=float(x.mean());sd=float(x.std(ddof=1));se=sd/math.sqrt(n)
    if se==0:lower=0. if mean>-margin else 1.;upper=0. if mean<margin else 1.;low=high=mean
    else:
        lower=float(stats.t.sf((mean+margin)/se,n-1));upper=float(stats.t.cdf((mean-margin)/se,n-1));critical=float(stats.t.ppf(1-alpha,n-1));low,high=mean-critical*se,mean+critical*se
    return {"n":n,"mean":mean,"sd":sd,"standard_error":se,"margin":margin,"alpha_one_sided":alpha,"lower_p_one_sided":lower,"upper_p_one_sided":upper,"ci_90":[low,high],"equivalent":lower<alpha and upper<alpha}


def analyze(rows:Sequence[Mapping[str,Any]])->dict[str,Any]:
    means=target_condition_means(rows);targets,differences=paired_differences(means);low,high=bootstrap_ci(differences);effect=float(differences.mean())
    difference_p=sign_flip_pvalue(differences);equivalence=tost(differences)
    different=difference_p<ALPHA;equivalent=bool(equivalence["equivalent"])
    conclusion=("both_different_and_equivalent" if different and equivalent else "superior_or_inferior_only" if different else "equivalent_only" if equivalent else "inconclusive")
    return {"schema_version":"protocol_control_pc_analysis_v1","independent_unit":"target","targets":len(targets),"contrast":"P-C","risk_difference":effect,"risk_difference_percentage_points":effect*100,"paired_target_bootstrap_95_ci":[low,high],"paired_target_bootstrap_95_ci_percentage_points":[low*100,high*100],"sign_flip_p_two_sided":difference_p,"sign_flip_role":"paired symmetry sensitivity, not claimed as exact design-based randomization inference","tost":equivalence,"decision_category":conclusion,"missing_rule":"Available valid repetitions are averaged within target-condition; a target is omitted only if either condition has no valid repetition.","claim_boundary":"Concrete coherent replay-verified trajectory relative to an abstract format/length/phase-matched scaffold; not a pure experience or replay-verification effect."}


__all__=["analyze","bootstrap_ci","paired_differences","sign_flip_pvalue","target_condition_means","tost"]

