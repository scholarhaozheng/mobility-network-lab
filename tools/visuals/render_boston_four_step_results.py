#!/usr/bin/env python3
"""Render three saved-result figures. This script does not run a traffic model.

Inputs are the published display CSVs and their provenance file. Stage 1 sums
were prepared from saved productions. Stage 2 contains saved HBW midday OD.
Stage 3 contains one fixed case from the accepted mode-response table.
"""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np

ROOT = Path(__file__).resolve().parents[2]

def read_csv(path: Path) -> list[dict[str,str]]:
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def save(fig, out: Path, stem: str) -> None:
    fig.savefig(out / (stem+'.png'), dpi=160)
    fig.savefig(out / (stem+'.svg'))
    plt.close(fig)

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir',type=Path,default=ROOT/'docs/assets/boston/four_step_results_r1/data')
    parser.add_argument('--output',type=Path,default=ROOT/'docs/assets/boston/four_step_results_r1')
    a=parser.parse_args(); d=a.data_dir; out=a.output
    meta=json.loads((d/'PROVENANCE.json').read_text(encoding='utf-8'))
    gen=read_csv(d/'generation_by_purpose.csv')
    values=np.array([float(r['person_trips_per_modeled_workday']) for r in gen])
    if not np.isfinite(values).all() or np.any(values<0): raise ValueError('Invalid saved production values')
    if not math.isclose(math.fsum(values),meta['generation']['total'],rel_tol=1e-12):raise ValueError('Production total mismatch')
    out.mkdir(parents=True,exist_ok=True)
    fig,ax=plt.subplots(figsize=(10,7.2));fig.subplots_adjust(left=.15,right=.94,bottom=.19,top=.75)
    fig.suptitle('01  |  Trip generation',x=.06,y=.97,ha='left',fontsize=25,weight='bold')
    fig.text(.06,.89,'Households × transferred regional rates',fontsize=16)
    fig.text(.06,.84,f"{meta['generation']['total']:,.2f} modeled person trips per workday",fontsize=13)
    bars=ax.barh([r['purpose'] for r in gen], values, height=.65)
    ax.invert_yaxis();ax.set_xlim(0,values.max()*1.24)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v,_:f'{v/1000:.0f}k'))
    ax.set_xlabel('Modeled person trips / average workday',fontsize=12)
    ax.tick_params(axis='both',labelsize=12)
    ax.spines[['top','right']].set_visible(False)
    for bar,v in zip(bars,values):ax.text(v+values.max()*.018,bar.get_y()+bar.get_height()/2,f'{v:,.0f}',va='center',fontsize=12)
    fig.text(.06,.045,'Six purpose codes retained. Source: saved ACS-household / TDM23-rate productions.\nModeled workday person trips, not observed counts or the amount assigned to roads.',fontsize=10)
    save(fig,out,'step1_generation')
    matrix_rows=read_csv(d/'hbw_midday_matrix.csv'); zone_order=read_csv(d/'zone_order.csv')
    zones=[r['zone_id'] for r in zone_order]
    if [r['origin_zone_id'] for r in matrix_rows]!=zones:raise ValueError('Zone order mismatch')
    matrix=np.array([[float(r[z]) if r[z] else np.nan for z in zones] for r in matrix_rows])
    if np.any(matrix[np.isfinite(matrix)]<0):raise ValueError('Negative OD')
    if not math.isclose(float(np.nansum(matrix)),meta['distribution']['total_midday'],rel_tol=1e-12):raise ValueError('OD total mismatch')
    fig,ax=plt.subplots(figsize=(10,7.2));fig.subplots_adjust(left=.12,right=.91,bottom=.18,top=.76)
    fig.suptitle('02  |  Trip distribution',x=.06,y=.97,ha='left',fontsize=25,weight='bold')
    fig.text(.06,.89,'Where do modeled home–work trips go?',fontsize=16)
    fig.text(.06,.84,f"HBW midday OD · {len(zones)} × {len(zones)} zones · {meta['distribution']['total_midday']:,.2f} person trips",fontsize=13)
    im=ax.imshow(np.ma.masked_invalid(np.log1p(matrix)),aspect='auto',interpolation='nearest')
    ax.set_xlabel('Destination H3 index (stable ID order)',fontsize=12);ax.set_ylabel('Origin H3 index',fontsize=12)
    ax.set_xticks([0,44,88,132,176]);ax.set_yticks([0,44,88,132,176]);ax.tick_params(labelsize=11)
    cb=fig.colorbar(im,ax=ax,fraction=.045,pad=.035)
    ticks=[x for x in [0,.1,1,5,10,20] if x<=np.nanmax(matrix)]
    cb.set_ticks(np.log1p(ticks));cb.set_ticklabels([str(x) for x in ticks]);cb.set_label('Person trips · log(1+x) color',fontsize=11)
    fig.text(.06,.045,'Full saved HBW midday OD; blank = no exported record. Stable H3 order is provided.\nModeled demand, not GPS-inferred trips; downstream assignment uses a selected panel.',fontsize=10)
    save(fig,out,'step2_distribution')
    response=read_csv(d/'selected_mode_response.csv')
    s1=np.array([float(r['S1_probability']) for r in response]);s2=np.array([float(r['S2_probability']) for r in response]);delta=(s2-s1)*100
    if not (abs(s1.sum()-1)<1e-10 and abs(s2.sum()-1)<1e-10):raise ValueError('Probability total mismatch')
    labels={'DA':'Drive alone · DA','S2':'2-person auto · S2','S3':'3+ person auto · S3','WK':'Walk · WK','BK':'Bike · BK','TW':'Walk-access transit · TW','TA':'Auto-access transit · TA','SB':'School bus · SB','RS':'Ride service · RS'}
    fig,ax=plt.subplots(figsize=(10,7.2));fig.subplots_adjust(left=.30,right=.91,bottom=.23,top=.76)
    fig.suptitle('03  |  Mode-share response',x=.06,y=.97,ha='left',fontsize=25,weight='bold')
    fig.text(.06,.89,'The service change reaches the choice calculation',fontsize=16)
    fig.text(.06,.84,'panel_od_019 · 12:30 · μ_transit = 1 · S2 minus S1',fontsize=13)
    y=np.arange(len(response));ax.barh(y,delta,height=.64)
    ax.set_yticks(y,[labels[r['mode']] for r in response]);ax.invert_yaxis()
    lim=max(abs(delta.min()),abs(delta.max()))*1.35;ax.set_xlim(-lim,lim)
    ax.set_xlabel('Change in probability (percentage points)',fontsize=12);ax.tick_params(labelsize=11);ax.spines[['top','right']].set_visible(False)
    ax.axvline(0,linewidth=.8,alpha=.5)
    for i,v in enumerate(delta):ax.text(v+(lim*.04 if v>=0 else -lim*.04),i,f'{v:+.4f}',va='center',ha='left' if v>=0 else 'right',fontsize=10)
    fig.text(.06,.14,'Walk-access transit: 4.0990% → 4.2246%  (+0.1256 percentage points).',fontsize=11,weight='bold')
    fig.text(.06,.085,'All nine source model leaves are retained. S1 uses shared regional base shares;\nS2 applies a nested pivot. This is not an estimated absolute baseline-choice model.',fontsize=10)
    fig.text(.06,.03,'TA access legs are not assigned. RS represents occupied trips; empty repositioning is unknown.\nSource: saved mode probabilities; exploratory model response, not observed behavior.',fontsize=10)
    save(fig,out,'step3_mode_response')
    print(json.dumps({'status':'rendered_saved_data','figures':3,'model_runs':0,'generation_total':float(values.sum()),'hbw_midday_total':float(np.nansum(matrix))},indent=2))
    return 0
if __name__=='__main__':raise SystemExit(main())
