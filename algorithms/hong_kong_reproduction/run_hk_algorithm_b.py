"""Reproduce exact Hong Kong Phase A/B Algorithm B instances from a pinned source build."""
import argparse,csv,json,os,platform,subprocess,sys,time
from pathlib import Path
from run_hk_static_fw import demand,rows,sha,save,B
CORE='algorithms/origin_based_algorithm_b/code'
CONFIG='examples/hong-kong/static_assignment_r2/cases.json'
COMMIT='040135a20c771fbb84766df6a97cff981fa5df4b'
ARCHIVE_SHA='5163b43051457c5c72cfc53253db4fc3668524cd3a5190169c99d2606fc430a5'
def invoke(argv,out,label):
    p=subprocess.run([sys.executable,'-B',*map(str,argv)],capture_output=True,text=True,timeout=1950)
    (out/(label+'.stdout.log')).write_text(p.stdout,encoding='utf-8');(out/(label+'.stderr.log')).write_text(p.stderr,encoding='utf-8')
    if p.returncode:raise RuntimeError(label+' failed; inspect '+str(out/(label+'.stderr.log')))
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=('run','verify'));ap.add_argument('--repo-root',required=True,type=Path);ap.add_argument('--case',required=True);ap.add_argument('--runtime',type=Path);ap.add_argument('--output',type=Path);ap.add_argument('--run',type=Path);a=ap.parse_args();repo=a.repo_root.resolve();case=json.loads((repo/CONFIG).read_text())['cases'][a.case];out=a.output if a.action=='run' else a.run
    if out is None:ap.error('run requires --output; verify requires --run')
    out=out.resolve();link=repo/B/'phase_a/static_input/turn_expanded_links.csv'
    if a.action=='run':
        if out.exists() and any(out.iterdir()):raise ValueError('Output must be empty; existing results are preserved.')
        runtime=(a.runtime or Path(os.environ.get('MCL_TAPB_RUNTIME',str(repo/'.mcl-runtime/tap-b')))).resolve();build=json.loads((runtime/'build.json').read_text());exe=runtime/build['executable']
        if build['exit_code']!=0 or build['source_commit']!=COMMIT or build['archive_sha256']!=ARCHIVE_SHA or sha(exe)!=build['executable_sha256']:raise ValueError('Pinned source-build provenance failed')
        out.mkdir(parents=True,exist_ok=True);save(out/'runtime-provenance.json',build)
        if case['demand_file']:
            (out/'demand.csv').write_bytes((repo/case['demand_file']).read_bytes())
        else:
            od=demand(repo,case['tier'])
            with (out/'demand.csv').open('w',newline='',encoding='utf-8') as f:
                w=csv.DictWriter(f,fieldnames=list(od[0]));w.writeheader();w.writerows(od)
        start=time.perf_counter();invoke([repo/CORE/'taplab_bush_solver_adapter.py','run','--exe',exe,'--link',link,'--demand',out/'demand.csv','--out',out/'computed'],out,'solve')
        save(out/'run.json',{'case_id':'hk-'+a.case+'-algorithm-b','environment':{'python':platform.python_version()},'wall_seconds':time.perf_counter()-start,'link_sha256':sha(link),'demand_sha256':sha(out/'demand.csv'),'built_executable_sha256':sha(exe),'scope':case['claim_boundary']})
    build=json.loads((out/'runtime-provenance.json').read_text());invoke([repo/CORE/'independent_static_ue_evaluator.py','--link',link,'--demand',out/'demand.csv','--run',out/'computed','--expected-exe-sha',build['executable_sha256']],out,'independent-verify')
    ev=json.loads((out/'computed/evaluation.json').read_text());ref=case['reference'];receipt=json.loads((out/'run.json').read_text());delta=abs(ev['objective']-ref['objective']);checks=[{'name':'independent_path_origin_and_full_graph_gates','pass':ev['status']=='ACCEPTED'},{'name':'frozen_input_hashes','pass':sha(link)==receipt['link_sha256'] and sha(out/'demand.csv')==receipt['demand_sha256']},{'name':'accepted_objective','pass':delta<=1e-7,'absolute_difference':delta},{'name':'accepted_od_count','pass':ev['positive_od']==ref['positive_od']},{'name':'accepted_demand','pass':abs(ev['total_demand']-ref['total_demand'])<=1e-8}]
    hist={k:sha(out/'computed'/(k+'_flow.csv'))==v for k,v in case['historical_output_sha256'].items()}
    report={'success':all(x['pass'] for x in checks),'status':'PASS' if all(x['pass'] for x in checks) else 'FAIL','optimizer_calls':0,'checks':checks,'metrics':{k:ev[k] for k in ('objective','relative_gap','positive_od','total_demand','max_od_residual','max_origin_node_residual','max_link_mismatch')},'historical_output_bytes_match':hist,'scope':case['claim_boundary']};save(out/'verification.json',report);print(json.dumps(report));return 0 if report['success'] else 2
if __name__=='__main__':raise SystemExit(main())
