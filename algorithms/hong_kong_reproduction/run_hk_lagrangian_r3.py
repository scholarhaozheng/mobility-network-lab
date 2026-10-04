"""Exact Hong Kong HK10 R3 continuation from the published frozen finite graph."""
import argparse,json,platform,sys,time
from pathlib import Path

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=('run','verify'));ap.add_argument('--repo-root',type=Path,required=True);ap.add_argument('--output',type=Path);ap.add_argument('--run',type=Path);a=ap.parse_args();repo=a.repo_root.resolve();out=a.output if a.action=='run' else a.run
    if out is None:ap.error('run requires --output; verify requires --run')
    out=out.resolve();source=repo/'algorithms/distributed_assignment/r3';sys.path.insert(0,str(source))
    from instance_adapter import load_case
    from independent_evaluator import evaluate
    case=repo/'docs/assets/hong_kong/full_stack_r5/r2r4_baseline/phase_c/case/case.json';base=case.parent.parent;planpath=source/'LAGRANGIAN_R3_EXPERIMENT_PLAN.json';plan=json.loads(planpath.read_text());variant=next(v for v in plan['variants'] if v['id']=='R3_CONTINUATION');problem,manifest,metadata=load_case(case)
    if a.action=='run':
        if out.exists() and any(out.iterdir()):raise ValueError('Output must be empty; original results are never overwritten.')
        out.mkdir(parents=True,exist_ok=True)
        from lagrangian_dual_solver import run_case
        from restricted_primal_recovery import recover_saved_pool
        start=time.perf_counter();result=run_case(problem,metadata,variant,plan['common'],planpath,out/'computed');recovery=recover_saved_pool(problem,out/'computed/pool_paths.csv',out/'recovery')
        import numpy,scipy
        (out/'run.json').write_text(json.dumps({'case_id':'hk10-lagrangian-r3-continuation','environment':{'python':platform.python_version(),'numpy':numpy.__version__,'scipy':scipy.__version__},'wall_seconds':time.perf_counter()-start,'result':result,'recovery':recovery},indent=2)+'\n')
    ev=evaluate(case.parent/'dynamic_arc.csv',case.parent/'dynamic_demand.csv',out/'computed',planpath,base/'ARC_FLOW_REFERENCE_SUMMARY.json',out/'recovery',case)
    historical=json.loads((base/'lagrangian_run/result.json').read_text());result=json.loads((out/'computed/result.json').read_text());checks=[{'name':k,'pass':v} for k,v in ev['checks'].items()];checks.extend([{'name':'independent_evaluator','pass':ev['status']=='PASS'},{'name':'historical_primal','pass':abs(ev['objective_recomputed']-historical['best_primal'])<=1e-7},{'name':'historical_dual','pass':abs(ev['dual_recomputed']-historical['best_dual'])<=1e-7},{'name':'historical_iteration_count','pass':result['iterations']==historical['iterations']},{'name':'certified_gap','pass':ev['duality_gap']<=plan['common']['target_gap']}])
    report={'success':all(x['pass'] for x in checks),'status':'PASS' if all(x['pass'] for x in checks) else 'FAIL','checks':checks,'optimizer_calls':0,'metrics':{k:ev[k] for k in ('objective_recomputed','dual_recomputed','duality_gap','max_balance_residual','max_capacity_violation','physical_projection_error')},'iterations':result['iterations'],'scope':'HK10 finite time-expanded fixed-cost shared-capacity R3 continuation, independent restricted-primal recovery. This is not the HK4 ADMM instance, R2 P07 algorithm, static UE or full-city assignment.'}
    (out/'independent-evaluation.json').write_text(json.dumps(ev,indent=2)+'\n');(out/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));return 0 if report['success'] else 2
if __name__=='__main__':raise SystemExit(main())
