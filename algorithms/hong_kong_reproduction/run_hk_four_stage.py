"""Portable execution of the recovered, unchanged Hong Kong R2 four-stage source.

Starts from the two published frozen aggregate input tables. It does not acquire
raw building, GPS, or provider snapshots and does not claim their reconstruction.
"""
import argparse, csv, hashlib, json, math, platform, shutil, subprocess, sys, time
from pathlib import Path

BASE = 'docs/assets/hong_kong/full_stack_r5/r2r4_baseline/phase_b'
INPUTS = ('zone_activity_r2.csv', 'mode_costs_by_od.csv')
OUTPUTS = ('production_attraction_r2.csv','od_person_distribution_r2.csv','mode_probabilities_by_od.csv','mode_demand_by_od.csv','OD_LINEAGE.csv')

def rows(p):
    with p.open(newline='', encoding='utf-8-sig') as f: return list(csv.DictReader(f))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d): p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def compare(a,b):
    if len(a)!=len(b): return {'pass':False,'reason':'row count mismatch'}
    error=0.; mismatch=0
    for x,y in zip(a,b):
        if x.keys()!=y.keys(): mismatch+=1;continue
        for k,v in x.items():
            if v==y[k]: continue
            try:
                u,w=float(v),float(y[k])
                if not(math.isfinite(u) and math.isfinite(w)): mismatch+=1
                else: error=max(error,abs(u-w)/max(1.,abs(w)))
            except ValueError: mismatch+=1
    return {'pass':mismatch==0 and error<=1e-9,'rows':len(a),'max_scaled_numeric_error':error,'text_mismatches':mismatch}
def verify(repo,out):
    b=out/'work/phase_b'; checks=[]
    receipt=json.loads((out/'run.json').read_text())
    checks.append({'name':'immutable_inputs','pass':all(sha(repo/BASE/n)==receipt['input_sha256'][n] and sha(b/n)==receipt['input_sha256'][n] for n in INPUTS)})
    for name in OUTPUTS: checks.append({'name':'accepted_table:'+name,**compare(rows(b/name),rows(repo/BASE/name))})
    pa=rows(b/OUTPUTS[0]); dist=rows(b/OUTPUTS[1]); probs=rows(b/OUTPUTS[2]); demand=rows(b/OUTPUTS[3])
    margins={}; targets={}; maxerr=0.
    for r in pa:
        for tag,field in [('o','interzonal_production_person_trips_am'),('d','interzonal_attraction_person_trips_am')]:targets[r['purpose'],tag,r['zone_id']]=float(r[field])
    for r in dist:
        for tag,field in [('o','o_zone_id'),('d','d_zone_id')]:
            k=(r['purpose'],tag,r[field]);margins[k]=margins.get(k,0.)+float(r['person_trips_am'])
    maxerr=max(abs(v-margins.get(k,0.)) for k,v in targets.items())
    checks.append({'name':'independent_ipf_margins','pass':maxerr<=1e-7,'max_absolute_residual':maxerr})
    pe=max(abs(sum(float(r[m+'_prob_'+v]) for m in ('drive','transit','walk'))-1.) for r in probs for v in ('low_drive','base','high_drive'))
    checks.append({'name':'mode_probabilities_nonnegative_and_sum_one','pass':pe<=1e-12 and all(0<=float(r[m+'_prob_'+v])<=1 for r in probs for m in ('drive','transit','walk') for v in ('low_drive','base','high_drive')),'max_residual':pe})
    de=max(abs(sum(float(r[m+'_person_trips_am']) for m in ('drive','transit','walk'))-float(r['total_trip_opportunities_person_am'])) for r in demand)
    ve=max(abs(float(r['drive_person_trips_am'])/1.5-float(r['loaded_drive_pce_per_one_hour_am'])) for r in demand)
    checks.append({'name':'independent_mode_and_occupancy_conservation','pass':max(de,ve)<=1e-9,'mode_residual':de,'vehicle_conversion_residual':ve})
    checks.append({'name':'finite_nonnegative_output','pass':all(math.isfinite(float(r['person_trips_am'])) and float(r['person_trips_am'])>=0 for r in dist)})
    result={'success':all(c['pass'] for c in checks),'status':'PASS' if all(c['pass'] for c in checks) else 'FAIL','optimizer_calls':0,'checks':checks,'scope':'Frozen 95-zone aggregate inputs to generation, base IPF distribution, three mode probability variants and base one-hour drive demand. Low/high capture are generation totals only; low/high beta are declared sensitivity values, not independently solved distributions.','metrics':{'zones':95,'directed_od_pairs':len(demand),'loaded_drive_pce':sum(float(r['loaded_drive_pce_per_one_hour_am']) for r in demand),'max_ipf_margin_residual':maxerr}}
    save(out/'verification.json',result);return result

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=('run','verify'));ap.add_argument('--repo-root',type=Path,required=True);ap.add_argument('--output',type=Path);ap.add_argument('--run',type=Path);args=ap.parse_args();repo=args.repo_root.resolve();out=(args.output if args.action=='run' else args.run)
    if out is None: ap.error('run requires --output; verify requires --run')
    out=out.resolve()
    if args.action=='run':
        if out.exists() and any(out.iterdir()): raise SystemExit('Output must be empty; existing results are never overwritten.')
        for n in INPUTS:
            if not (repo/BASE/n).is_file(): raise SystemExit('Missing frozen input: '+n)
        work=out/'work';(work/'phase_b').mkdir(parents=True,exist_ok=True)
        source=Path(__file__).with_name('build_four_stage.py');shutil.copyfile(source,work/source.name)
        for n in INPUTS:shutil.copyfile(repo/BASE/n,work/'phase_b'/n)
        start=time.perf_counter();p=subprocess.run([sys.executable,'-B',str(work/source.name)],capture_output=True,text=True)
        (out/'stdout.log').write_text(p.stdout,encoding='utf-8');(out/'stderr.log').write_text(p.stderr,encoding='utf-8')
        import numpy
        save(out/'run.json',{'case_id':'hk-four-stage-r2','source_sha256':sha(source),'input_sha256':{n:sha(repo/BASE/n) for n in INPUTS},'environment':{'python':platform.python_version(),'numpy':numpy.__version__},'returncode':p.returncode,'wall_seconds':time.perf_counter()-start})
        if p.returncode:raise SystemExit(p.returncode)
    result=verify(repo,out);print(json.dumps(result));return 0 if result['success'] else 2
if __name__=='__main__':raise SystemExit(main())
