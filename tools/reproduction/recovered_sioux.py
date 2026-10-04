"""Portable Sioux recovery: fresh computation and explicitly separate saved-state inspection."""
from __future__ import annotations
import argparse,csv,hashlib,heapq,importlib.util,json,math,os,shutil,subprocess,sys,urllib.request,zipfile
from pathlib import Path

BASE=Path('examples/sioux-falls/recovered-r14')

def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,x):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rows(p):
    with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def copy(src,dst):
    dst=Path(dst);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
def module(path,name):
    sys.path.insert(0,str(path.parent));spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

def execute(argv,cwd,out,label,timeout=180,env=None):
    r=subprocess.run(list(map(str,argv)),cwd=cwd,env=env,capture_output=True,text=True,timeout=timeout)
    (out/(label+'.log')).write_text(r.stdout+'\n'+r.stderr,encoding='utf-8')
    if r.returncode:raise RuntimeError(label+' failed with '+str(r.returncode)+'; see '+label+'.log')
    return r

def config(record):
    if record.startswith('sioux-native-'):return 'native','A_REG001' if '-a-' in record else 'B_BECKMANN'
    if record.startswith('sioux-cg-'):return 'cg',record.rsplit('-',1)[-1]
    if record.startswith('sioux-admm-r1-'):return 'r1',record.rsplit('-',1)[-1]
    if record.startswith('sioux-admm-r2s-development-'):return 'r2s',record.rsplit('-',1)[-1]
    if record=='sioux-taplab-official-parity':return 'taplab',None
    raise ValueError('Unknown record: '+record)

def admm(root,out,kind,scale,action):
    folder=root/BASE/('admm-r1' if kind=='r1' else 'admm-r2s')/(scale+'od')
    inputs=root/'examples/sioux-falls/finite-time-r05'/(scale+'od') if kind=='r1' else folder
    arc,demand=inputs/'dynamic_arc.csv',inputs/'dynamic_demand.csv';expected=read(folder/'expected.json')
    code=root/('algorithms/distributed_assignment/admm_r1' if kind=='r1' else 'algorithms/admm_r2')
    plan=root/'algorithms/distributed_assignment/admm_r1/GATES.json' if kind=='r1' else root/'docs/assets/admm_r2/provenance/experiment_plan.json'
    state=out/'computed';case='Sioux_'+scale+'OD'
    if action=='inspect':
        state.mkdir();copy(folder/'saved/state.npz',state/'state.npz');copy(folder/'saved/result.json',state/'result.json')
    elif action=='run':
        solver=code/('admm.py' if kind=='r1' else 'admm_solver.py')
        command=[sys.executable,'-B',solver,'--arc',arc,'--demand',demand,'--output',state,'--gates' if kind=='r1' else '--policy',plan,'--case',case]
        if kind!='r1':command+=['--variant','R2_S']
        execute(command,root,out,'solver',timeout=1900)
    saved=read(state/'result.json')
    if kind=='r1':
        ev=module(code/'evaluate_admm.py','recovered_r1_evaluator').evaluate(arc,demand,state,plan)
        obj=ev['objective_recomputed'];gates={'independent_original_space_gates':ev['status']=='PASS'}
        identity=saved.get('case')==case and saved.get('method')=='full_arc_consensus_admm'
    else:
        ev=module(code/'independent_admm_evaluator.py','recovered_r2_evaluator').evaluate_files(arc,demand,state,read(plan))
        obj=ev['objective'];gates={k:bool(v) for k,v in ev['gates'].items()};gates['independent_original_space_gates']=ev['status']=='PASS'
        identity=saved.get('case')==case and saved.get('variant')=='R2_S' and saved.get('commodity_count')==int(scale)
    gates.update(method_instance_identity=identity,saved_objective_recomputed=abs(obj-expected['objective'])<=1e-5,solver_free_verifier=ev.get('optimizer_calls')==0)
    metrics={k:v for k,v in ev.items() if isinstance(v,(int,float)) and not isinstance(v,bool)}
    metrics.update(od_count=int(scale),objective_absolute_error=abs(obj-expected['objective']),solver_optimizer_calls=saved.get('optimizer_calls'),iterations=saved.get('iterations',saved.get('completed_iterations')))
    write(out/'independent-evaluation.json',ev)
    return gates,metrics,'Exact modeled finite graph and demand; R1 and R2_S remain distinct algorithms. Raw-source construction is outside this replay.'

def native(root,out,cfg,action):
    work=out/'computed';selected=work/'runs/SiouxFalls'/cfg
    if action in ('run','inspect'):
        execute([sys.executable,'-B',root/'tools/prepare_native_run.py','--case','sioux-falls','--output',work],root,out,'prepare-native')
    if action=='inspect':
        copy(root/'examples/sioux-falls/native_l3_r1/runs/SiouxFalls'/cfg/'outer_04_solution.npz',selected/'outer_04_solution.npz')
        copy(root/BASE/'native'/cfg/'outer_04_native.json',selected/'outer_04_native.json');outer=4
    elif action=='run':
        python=Path(os.environ.get('MCL_NATIVE_PYTHON',''));ipopt=Path(os.environ.get('MCL_IPOPT',''))
        if not python.is_file() or not ipopt.is_file():raise ValueError('Set MCL_NATIVE_PYTHON and MCL_IPOPT; see docs/reproduction/recovered-sioux.md')
        expected=read(root/BASE/'native/environment.json')
        if sha(ipopt)!=expected['ipopt_sha256']:raise ValueError('IPOPT executable differs from the retained native environment identity')
        for name in ('checks','configs','tmp'):(work/name).mkdir(exist_ok=True)
        env=os.environ.copy();env['PATH']=os.pathsep.join((str(ipopt.parent),str(python.parent/'Library/bin'),str(python.parent/'Scripts'),env.get('PATH','')))
        env.update(MCL_NATIVE_PYTHON=str(python.resolve()),MCL_IPOPT=str(ipopt.resolve()),TEMP=str(work/'tmp'),TMP=str(work/'tmp'),PYTHONDONTWRITEBYTECODE='1')
        probe='import importlib.metadata as m,json,sys; print(json.dumps({k:m.version(k) for k in ["numpy","scipy","pandas","pyomo"]}))'
        p=execute([python,'-B','-c',probe],work,out,'native-environment',env=env)
        versions=json.loads(p.stdout)
        if versions!=expected['packages']:raise ValueError('Native package versions differ from the recorded environment: '+str(versions))
        # The historical controller retains A-before-B and the original gating sequence.
        execute([python,'-u','-B',work/'runner/controller.py','--execute-native'],work,out,'native-solver',timeout=3700,env=env)
        status=read(selected/'status.json');outer=status.get('accepted_outer')
        if not outer:raise ValueError('Native controller returned no numerically accepted iterate')
    else:
        meta=read(out/'execution.json');outer=meta.get('accepted_outer',4)
    checker=module(work/'runner/check_inner.py','recovered_native_checker');checker.main('SiouxFalls',cfg,outer)
    report=read(selected/('outer_%02d_check.json'%outer))
    expected=read(root/'examples/sioux-falls/native_l3_r1/runs/SiouxFalls'/cfg/'outer_04_check.json')
    gates={k:bool(v) for k,v in report['criteria'].items()}
    gates['historical_objective_agreement']=abs(report['stats']['F_reconstructed_link']-expected['stats']['F_reconstructed_link'])<=1e-4
    metrics=report['stats'];metrics['accepted_outer']=outer;metrics['full_network_relative_gap']=report.get('gap_diagnostics',{}).get('full_network_relative_gap')
    return gates,metrics,'Rank-50 saved or freshly returned native iterate checked in original path/OD/link coordinates; numerical feasibility does not certify full-network user equilibrium.'

def cg(root,out,scale,action):
    folder=root/BASE/'cg'/(scale+'od');inputs=root/'examples/sioux-falls/finite-time-r05'/(scale+'od');state=out/'computed'
    if action=='inspect':shutil.copytree(folder/'saved',state)
    elif action=='run':
        stage=out/'inputs';stage.mkdir()
        for name in ('dynamic_arc.csv','dynamic_demand.csv'):copy(inputs/name,stage/name)
        for name in ('dynamic_node.csv','dynamic_columns.csv'):copy(folder/name,stage/name)
        manifest=read(folder/'frozen_manifest.json');manifest.update(dynamic_data_dir=str(stage),dynamic_arc_file=str(stage/'dynamic_arc.csv'),demand_file=str(stage/'dynamic_demand.csv'),current_candidate_pool_file=str(stage/'dynamic_columns.csv'),output_root=str(state))
        # Use the historical scalar comparison target, never saved optimal flows as solver input.
        manifest.pop('arc_lp_reference_summary_path',None);write(out/'resolved-manifest.json',manifest)
        argv=[sys.executable,'-B',root/'app/src/gmns_dynamic/run_full_cg_v1.py','--input-manifest',out/'resolved-manifest.json','--output-dir',state,'--benchmark-id',manifest['benchmark_id'],'--max-phase-i-rounds',manifest['max_phase_i_rounds'],'--max-phase-ii-rounds',manifest['max_phase_ii_rounds'],'--max-candidates-per-demand',manifest['max_candidates_per_demand_per_round'],'--phase-ii-pricing-mode',manifest['phase_ii_pricing_mode'],'--k-shortest-k',manifest['k_shortest_k'],'--phase-ii-add-policy',manifest['phase_ii_add_policy'],'--max-phase-ii-candidates-per-demand',manifest['max_phase_ii_candidates_per_demand'],'--max-phase-ii-candidates-per-round',manifest['max_phase_ii_candidates_per_round'],'--runtime-cap-seconds',manifest['runtime_cap_seconds'],'--no-mutate-accepted-outputs','--write-review-artifacts','--reference-objective',manifest['arc_lp_reference_objective']]
        execute(argv,root,out,'cg-solver',timeout=manifest['runtime_cap_seconds']+180)
    saved=read(state/'full_cg_v1_run_summary.json');arcs={r['arc_id']:r for r in rows(inputs/'dynamic_arc.csv')};demand={r['demand_id']:r for r in rows(inputs/'dynamic_demand.csv')}
    flow=rows(state/'full_cg_v1_final_capacity_audit.csv');balance=rows(state/'full_cg_v1_final_demand_residual_audit.csv')
    costkey=next(k for k in ('cost','travel_time','arc_cost') if k in next(iter(arcs.values())))
    objective=math.fsum(float(r['flow'])*float(arcs[r['arc_id']][costkey]) for r in flow)
    excess=max([max(0,float(r['flow'])-float(arcs[r['arc_id']]['capacity'])) for r in flow]+[0])
    expected=read(folder/'saved/full_cg_v1_run_summary.json')['phase_ii_final_objective']
    qkey=next(k for k in ('volume','demand','demand_volume') if k in next(iter(demand.values())))
    residual=max([abs(float(r['real_column_flow'])-float(demand[r['demand_id']][qkey])) for r in balance]+[0])
    gates={'saved_run_pass':saved['run_status']=='PASS','complete_arc_ids':len(flow)==len(arcs) and {r['arc_id'] for r in flow}==set(arcs),'complete_demand_ids':len(balance)==len(demand) and {r['demand_id'] for r in balance}==set(demand),'nonnegative_arc_flow':min(float(r['flow']) for r in flow)>=-1e-8,'capacity_feasible':excess<=1e-6,'demand_table_consistent':residual<=1e-6,'saved_objective_recomputed':abs(objective-saved['phase_ii_final_objective'])<=1e-6,'historical_objective':abs(objective-expected)<=1e-6,'phase_i_artificial_cleared':abs(saved['phase_i_artificial_flow_final'])<=1e-6}
    return gates,{'objective':objective,'historical_objective_absolute_error':abs(objective-expected),'max_capacity_excess':excess,'max_demand_residual':residual,'od_count':len(demand),'initial_columns':len(rows(folder/'dynamic_columns.csv'))},'Historical bounded k-shortest CG. Aggregate arc-flow objective/capacity and demand tables are independently checked. No complete commodity-state or independent complete pricing-closure certificate is asserted.'

def taplab(root,out,action):
    folder=root/BASE/'taplab';state=out/'computed';expected=read(folder/'expected.json')
    if action=='inspect':state.mkdir();copy(folder/'link_performance.csv',state/'link_performance.csv')
    elif action=='run':
        acquisition=read(folder/'acquisition.json');archive=Path(os.environ['MCL_TAPLAB_ARCHIVE']) if os.environ.get('MCL_TAPLAB_ARCHIVE') else out/'taplab-source.zip'
        if not archive.exists():
            with urllib.request.urlopen(acquisition['url'],timeout=90) as response:archive.write_bytes(response.read())
        if sha(archive)!=acquisition['sha256']:raise ValueError('Pinned TAPLab source archive hash mismatch')
        unpack=out/'upstream';unpack.mkdir()
        with zipfile.ZipFile(archive) as z:
            for member in z.infolist():
                if not (unpack/member.filename).resolve().is_relative_to(unpack):raise ValueError('Unsafe upstream archive path')
            z.extractall(unpack)
        upstream=unpack/('TAPLab-'+acquisition['commit'])
        if sha(upstream/'taplab/adapters/tapb.py')!=acquisition['required_adapter_sha256']:raise ValueError('Official adapter source identity changed')
        runtime=Path(os.environ.get('MCL_TAPB_RUNTIME',root/'.mcl-runtime/tap-b'));build=read(runtime/'build.json');exe=runtime/build['executable']
        if sha(exe)!=build['executable_sha256'] or build['source_commit']!='040135a20c771fbb84766df6a97cff981fa5df4b':raise ValueError('Build pinned tap-b with tools/reproduction/build_tapb.py first')
        inst=out/'sioux_r21';inst.mkdir()
        for name in ('node.csv','manifest.yml','settings.yml'):copy(folder/name,inst/name)
        for name in ('link.csv','demand.csv'):copy(root/'examples/sioux-falls/native_l3_r1/inputs_snapshot/SiouxFalls'/name,inst/name)
        env=os.environ.copy();env.update(TAPLAB_TAPB_EXE=str(exe.resolve()),PYTHONDONTWRITEBYTECODE='1',TEMP=str(out),TMP=str(out))
        execute([sys.executable,'-B','-m','taplab.cli','run',inst,'--solver','tapb','--algorithm','B','--gap','1e-8','--max-time','1800'],upstream,out,'official-taplab',timeout=1950,env=env)
        produced=upstream/'results/sioux_r21/tapb';shutil.copytree(produced,state)
    inputs=root/'examples/sioux-falls/native_l3_r1/inputs_snapshot/SiouxFalls';link=rows(inputs/'link.csv');flow={r['link_id']:float(r['volume']) for r in rows(state/'link_performance.csv')}
    reference={r['link_id']:float(r.get('volume',r.get('flow'))) for r in rows(root/'algorithms/origin_based_algorithm_b/accepted_results/sioux_physical_link_flow.csv')}
    objective=0.;balance={};adj={};tstt=0.
    for r in link:
        x=flow[r['link_id']];t=float(r['vdf_fftt']);cap=float(r['capacity']);alpha=float(r['vdf_alpha']);beta=float(r['vdf_beta']);c=t*(1+alpha*(x/cap)**beta)
        objective+=t*(x+alpha*x**(beta+1)/((beta+1)*cap**beta));tstt+=x*c
        u,v=int(r['from_node_id']),int(r['to_node_id']);balance[u]=balance.get(u,0)+x;balance[v]=balance.get(v,0)-x;adj.setdefault(u,[]).append((v,c))
    shortest={};sptt=0.
    for q in rows(inputs/'demand.csv'):
        o,d,vol=int(q['o_zone_id']),int(q['d_zone_id']),float(q['volume']);balance[o]-=vol;balance[d]+=vol
        if o not in shortest:
            dist={o:0.};queue=[(0.,o)]
            while queue:
                val,u=heapq.heappop(queue)
                if val!=dist[u]:continue
                for v,c in adj.get(u,[]):
                    if val+c<dist.get(v,float('inf')):dist[v]=val+c;heapq.heappush(queue,(val+c,v))
            shortest[o]=dist
        sptt+=vol*shortest[o][d]
    diff=max(abs(flow[k]-reference[k]) for k in reference);res=max(abs(x) for x in balance.values());gap=(tstt-sptt)/tstt
    gates={'complete_links':set(flow)==set(reference) and len(flow)==76,'nonnegative':min(flow.values())>=-1e-8,'direct_adapter_flow_parity':diff<=1e-7,'objective_parity':abs(objective-expected['objective'])<=1e-6,'aggregate_node_balance':res<=1e-6,'static_relative_gap':gap<=1e-8}
    return gates,{'objective':objective,'max_link_flow_difference':diff,'max_node_residual':res,'relative_gap':gap,'links':len(flow)},'Official pinned TAPLab Algorithm B adapter compared with the accepted direct tap-b solution. Aggregate feasibility is checked; full per-OD path reconstruction is outside this adapter output.'

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=['run','verify','inspect']);ap.add_argument('--repo-root',type=Path,required=True);ap.add_argument('--record',required=True);ap.add_argument('--output',type=Path);ap.add_argument('--run',dest='run_dir',type=Path);ap.add_argument('--ipopt',type=Path,help='Optional native solver path; overrides MCL_IPOPT');a=ap.parse_args()
    if a.ipopt is not None:os.environ['MCL_IPOPT']=str(a.ipopt.resolve())
    root=a.repo_root.resolve();out=(a.run_dir if a.action=='verify' else a.output)
    if out is None:ap.error('Supply --output for run/inspect or --run for verify')
    out=out.resolve();records=read(root/'experiments/recovered/sioux-shared.json')['records'];entry=next(r for r in records if r['id']==a.record)
    pins={x['path']:sha(root/x['path'])==x['sha256'] for x in entry['files']}
    if not all(pins.values()):raise ValueError('Pinned source/input changed: '+str([k for k,v in pins.items() if not v]))
    if a.action!='verify':
        if out.exists() and any(out.iterdir()):raise ValueError('Output must be new or empty')
        out.mkdir(parents=True,exist_ok=True)
        write(out/'execution.json',{'record':a.record,'action':a.action,'fresh_solve':a.action=='run','input_source_hashes':{x['path']:x['sha256'] for x in entry['files']},'python':sys.version.split()[0]})
    else:
        if read(out/'execution.json')['record']!=a.record:raise ValueError('Output belongs to a different record')
    kind,value=config(a.record)
    if kind in ('r1','r2s'):checks,metrics,scope=admm(root,out,kind,value,a.action)
    elif kind=='native':checks,metrics,scope=native(root,out,value,a.action)
    elif kind=='cg':checks,metrics,scope=cg(root,out,value,a.action)
    else:checks,metrics,scope=taplab(root,out,a.action)
    execution=read(out/'execution.json');execution['accepted_outer']=metrics.get('accepted_outer');write(out/'execution.json',execution)
    report={'success':all(checks.values()),'record':a.record,'evidence_basis':'fresh_computation' if execution['fresh_solve'] else 'saved_state_inspection','optimizer_calls':0,'verification_optimizer_calls':0,'checks':checks,'metrics':metrics,'scope':scope,'source_input_hashes_verified':True}
    write(out/'verification.json',report);print(json.dumps(report));return 0 if report['success'] else 2
if __name__=='__main__':raise SystemExit(main())
