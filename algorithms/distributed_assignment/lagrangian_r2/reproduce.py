"""Reproduce frozen P07 controls or run the same policy on supplied finite inputs.

This adapter calls the existing public solver and independent evaluator. The
historical city graph/state files are not embedded in this package.
"""
import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

BASE = Path('algorithms/distributed_assignment/lagrangian_r2')
PLAN = Path(__file__).resolve().with_name('experiment_plan.json')
EXPECTED = {'analytic': 2.0, 'C0': 4.0, 'C1': 8.0}

def sha(file):
    return hashlib.sha256(Path(file).read_bytes()).hexdigest()

def write(file, data):
    Path(file).write_text(json.dumps(data, indent=2, allow_nan=False) + '\n', encoding='utf-8')

def source_paths(root):
    return list(sorted((root / BASE / 'src').glob('*.py'))) + [PLAN, Path(__file__).resolve()]

def files(root, case, arc=None, demand=None):
    if case == 'external':
        if not arc or not demand:
            raise ValueError('The external case requires --arc and --demand.')
        return Path(arc).resolve(), Path(demand).resolve()
    folder = root / BASE / 'fixtures' / case
    return folder / 'dynamic_arc.csv', folder / 'dynamic_demand.csv'

def digest_inputs(root, case, arc, demand):
    paths = source_paths(root) + [arc, demand]
    return {str(p.resolve()): sha(p) for p in paths}

def evaluate(root, case, folder, arc=None, demand=None):
    record = json.loads((folder / 'reproduction.json').read_text())
    arc, demand = files(root, case, arc, demand)
    checks = [{'name': 'case_identity', 'pass': record['case'] == case},
              {'name': 'source_and_input_hashes', 'pass': digest_inputs(root,case,arc,demand) == record['source_inputs']}]
    for name, digest in record['outputs'].items():
        checks.append({'name': 'output_hash:' + name, 'pass': (folder / name).is_file() and sha(folder/name) == digest})
    if all(item['pass'] for item in checks):
        code = root / BASE / 'src'
        sys.path.insert(0, str(code))
        spec = importlib.util.spec_from_file_location('p07_independent', code/'independent_lagrangian_evaluator.py')
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        ev = mod.evaluate(arc,demand,folder / "state",PLAN)
        checks += [{'name':k, 'pass':bool(v)} for k,v in ev['checks'].items()]
        if case in EXPECTED:
            checks.append({'name':'known_fixture_optimum','pass':abs(ev['objective_recomputed']-EXPECTED[case])<=1e-7})
        checks.append({'name':'one_percent_certificate','pass':ev.get('duality_gap',float('inf'))<=0.01})
        metrics={k:v for k,v in ev.items() if isinstance(v,(int,float)) and not isinstance(v,bool)}
        metrics['optimizer_calls']=0
    else:
        metrics={}
    result={'success':all(c['pass'] for c in checks),'optimizer_calls':0,'checks':checks,'metrics':metrics,
            'scope':'Fresh P07 solve of a task-authored control fixture.' if case!='external' else 'Supplied finite graph; not automatically a reproduction of a historical city.'}
    write(folder/'verification.json',result)
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['run','verify'])
    p.add_argument('--repo-root',type=Path,required=True)
    p.add_argument('--output',type=Path);p.add_argument('--run',type=Path)
    p.add_argument('--case',choices=['analytic','C0','C1','external'],required=True)
    p.add_argument('--arc',type=Path);p.add_argument('--demand',type=Path)
    a=p.parse_args(); root=a.repo_root.resolve(); folder=(a.output if a.action=='run' else a.run)
    if folder is None: p.error('--output (run) or --run (verify) is required')
    folder=folder.resolve();arc,demand=files(root,a.case,a.arc,a.demand)
    if a.action=='run':
        if folder.exists() and any(folder.iterdir()):raise ValueError('Output must be new or empty.')
        folder.mkdir(parents=True,exist_ok=True)
        before=digest_inputs(root,a.case,arc,demand)
        command=[sys.executable,'-B',str(root/BASE/'src/lagrangian_dual_solver.py'),'--arc',str(arc),'--demand',str(demand),'--plan',str(PLAN),'--variant','P07','--case',a.case,'--output',str(folder/'state')]
        done=subprocess.run(command,capture_output=True,text=True)
        (folder/'solver.log').write_text(done.stdout+done.stderr,encoding='utf-8')
        if done.returncode:raise RuntimeError('Solver failed; see solver.log.')
        if before!=digest_inputs(root,a.case,arc,demand):raise RuntimeError('Input or source changed during execution.')
        write(folder/'reproduction.json',{'case':a.case,'variant':'P07','source_inputs':before,'outputs':{p.relative_to(folder).as_posix():sha(p) for p in sorted(folder.rglob('*')) if p.is_file()}})
    result=evaluate(root,a.case,folder,a.arc,a.demand)
    print(json.dumps(result))
    return 0 if result['success'] else 2

if __name__=='__main__':
    raise SystemExit(main())
