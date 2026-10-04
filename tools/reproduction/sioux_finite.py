"""Replay exact Sioux P07 / R2_S city instances with unchanged public solvers."""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,subprocess,sys
from pathlib import Path

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,d):p.write_text(json.dumps(d,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def implementation(root,method):
    if method=='lagrangian':return root/'algorithms/distributed_assignment/lagrangian_r2/src',root/'algorithms/distributed_assignment/lagrangian_r2/experiment_plan.json','lagrangian_dual_solver.py','independent_lagrangian_evaluator.py','P07'
    return root/'algorithms/admm_r2',root/'docs/assets/admm_r2/provenance/experiment_plan.json','admm_solver.py','independent_admm_evaluator.py','R2_S'
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=['run','verify']);ap.add_argument('--repo-root',type=Path,required=True);ap.add_argument('--method',choices=['lagrangian','admm'],required=True);ap.add_argument('--scale',choices=['200','250'],required=True);ap.add_argument('--output',type=Path);ap.add_argument('--run',type=Path)
    a=ap.parse_args();root=a.repo_root.resolve();out=(a.output if a.action=='run' else a.run)
    if out is None:ap.error('Supply --output for run or --run for verify')
    out=out.resolve();folder=root/'examples/sioux-falls/finite-time-r05'/(a.scale+'od');arc=folder/'dynamic_arc.csv';demand=folder/'dynamic_demand.csv'
    code,plan,solver,evaluator,variant=implementation(root,a.method);case='Sioux_'+a.scale+'OD'
    if a.action=='run':
        if out.exists() and any(out.iterdir()):raise ValueError('Output must be new or empty')
        out.mkdir(parents=True,exist_ok=True)
        # No reference objective, flow, path or saved state is provided to the solver.
        command=[sys.executable,'-B',str(code/solver),'--arc',str(arc),'--demand',str(demand),'--plan' if a.method=='lagrangian' else '--policy',str(plan),'--variant',variant,'--case',case,'--output',str(out/'state')]
        r=subprocess.run(command,capture_output=True,text=True,timeout=240)
        (out/'solver.log').write_text(r.stdout+'\n'+r.stderr,encoding='utf-8')
        if r.returncode:raise RuntimeError('Solver returned '+str(r.returncode)+'; see solver.log')
    expected=read(folder/'expected.json');result=read(out/'state/result.json')
    sys.path.insert(0,str(code));spec=importlib.util.spec_from_file_location('sioux_independent_'+a.method,code/evaluator);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    checks={'exact_arc_identity':sha(arc)==expected['arc_sha256'],'exact_demand_identity':sha(demand)==expected['demand_sha256'],'method_instance_identity':result.get('case')==case and result.get('variant')==variant}
    if a.method=='lagrangian':
        ev=mod.evaluate(arc,demand,out/'state',plan)
        checks.update({'original_'+k:bool(v) for k,v in ev['checks'].items()})
        checks.update({'one_percent_gap':ev.get('duality_gap',float('inf'))<=0.01,'historical_primal':abs(ev.get('objective_recomputed',float('inf'))-expected['lagrangian']['primal'])<=1e-7,'historical_dual':abs(ev.get('dual_recomputed',float('inf'))-expected['lagrangian']['dual'])<=1e-7,'historical_iterations':result.get('iterations')==expected['lagrangian']['iterations']})
    else:
        ev=mod.evaluate_files(arc,demand,out/'state',read(plan))
        checks.update({'original_'+k:bool(v) for k,v in ev['gates'].items()})
        checks.update({'original_evaluator_pass':ev.get('status')=='PASS','historical_objective':abs(ev.get('objective',float('inf'))-expected['admm']['objective'])<=1e-7,'historical_iterations':result.get('completed_iterations')==expected['admm']['iterations'],'arc_and_commodity_count':result.get('arc_count')==expected['arc_count'] and result.get('commodity_count')==int(a.scale)})
    checks['independent_solver_free']=ev.get('optimizer_calls')==0
    metrics={k:v for k,v in ev.items() if isinstance(v,(int,float)) and not isinstance(v,bool)}
    metrics['od_count']=int(a.scale);metrics['arc_count']=expected['arc_count'];metrics['historical_objective_absolute_error']=abs((ev.get('objective_recomputed') if a.method=='lagrangian' else ev.get('objective'))-expected[a.method]['primal' if a.method=='lagrangian' else 'objective'])
    report={'success':all(checks.values()),'optimizer_calls':0,'checks':checks,'metrics':metrics,'scope':'Exact frozen Sioux '+a.scale+'-OD '+variant+' computation and independent verification. No raw-source acquisition or historical CG pricing closure is asserted.'}
    write(out/'verification.json',report);print(json.dumps(report));return 0 if report['success'] else 2
if __name__=='__main__':raise SystemExit(main())
