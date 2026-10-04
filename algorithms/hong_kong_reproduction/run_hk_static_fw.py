"""Reproduce historical Hong Kong Phase B FW tiers from published frozen inputs.

Demand selection and FW settings match the recovered run_phase_b_static.py.
Independent verification recomputes network conservation, BPR costs, Beckmann
objective, and shortest-path gap. No solver is called during verification.
"""
import argparse,csv,hashlib,heapq,json,math,os,platform,shutil,subprocess,sys,time
from collections import defaultdict
from pathlib import Path
B='docs/assets/hong_kong/full_stack_r5/r2r4_baseline'
S='algorithms/static_fw/tap_frank_wolfe.py'
COUNTS={'smoke':10,'medium':1000,'full':8930}
def rows(p):
    with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')
def demand(repo,tier):
    costs={(r['o_zone_id'],r['d_zone_id']):r for r in rows(repo/B/'phase_b/mode_costs_by_od.csv')}
    allrows=[]
    for r in rows(repo/B/'phase_b/mode_demand_by_od.csv'):
        c=costs[r['o_zone_id'],r['d_zone_id']]
        allrows.append({'o_zone_id':c['o_access_node_id'],'d_zone_id':c['d_access_node_id'],'volume':float(r['loaded_drive_pce_per_one_hour_am']),'source_o_zone_id':int(r['o_zone_id']),'source_d_zone_id':int(r['d_zone_id']),'scenario_tier':'four_stage_full'})
    return sorted(allrows,key=lambda r:(-r['volume'],r['source_o_zone_id'],r['source_d_zone_id']))[:COUNTS[tier]]
def verify(repo,out,tier):
    checks=[];link=rows(repo/B/'phase_a/static_input/turn_expanded_links.csv');sol=rows(out/(tier+'_solution.csv'));od=demand(repo,tier);byid={r['link_id']:r for r in sol};balance=defaultdict(float);target=defaultdict(float);adj=defaultdict(list);obj=0.;tt=0.;negative=0.;err=0.;finite=True
    for r in link:
        v=float(byid[r['link_id']]['volume']);t=float(r['vdf_fftt']);cap=max(1.,float(r['capacity']));a=float(r['vdf_alpha']);b=float(r['vdf_beta']);c=t*(1+a*(max(0.,v)/cap)**b)
        finite=finite and math.isfinite(v);negative=max(negative,-v);obj+=t*v*(1+a*(max(0.,v)/cap)**b/(b+1));tt+=c*v;err=max(err,abs(c-float(byid[r['link_id']]['travel_time'])));u=r['from_node_id'];z=r['to_node_id'];balance[u]+=v;balance[z]-=v;adj[u].append((z,c))
    grouped=defaultdict(list)
    for r in od:
        q=r['volume'];u=r['o_zone_id'];v=r['d_zone_id'];target[u]+=q;target[v]-=q;grouped[u].append((v,q))
    residual=max(abs(balance[n]-target[n]) for n in set(balance)|set(target));spcost=0.
    for origin,ds in grouped.items():
        dist={origin:0.};heap=[(0.,origin)]
        while heap:
            du,u=heapq.heappop(heap)
            if du!=dist[u]:continue
            for v,c in adj[u]:
                nd=du+c
                if nd<dist.get(v,math.inf):dist[v]=nd;heapq.heappush(heap,(nd,v))
        spcost+=sum(q*dist.get(v,math.inf) for v,q in ds)
    gap=(tt-spcost)/max(1.,abs(obj));expected=json.loads((repo/B/'phase_b/STATIC_ASSIGNMENT_COMPARISON.json').read_text())[tier]
    checks.extend([{'name':'complete_unique_link_identity','pass':len(sol)==len(link)==len(byid) and set(byid)=={r['link_id'] for r in link}}, {'name':'finite_nonnegative_flow','pass':finite and negative<=1e-10,'negative_flow':negative},{'name':'network_node_conservation','pass':residual<=1e-7,'max_residual':residual},{'name':'recomputed_bpr_cost','pass':err<=1e-9,'max_cost_difference':err},{'name':'full_graph_shortest_path_gap','pass':math.isfinite(gap) and abs(gap)<=1e-4,'relative_gap':gap},{'name':'accepted_objective','pass':abs(obj-expected['fw_beckmann_objective'])<=1e-7,'actual':obj,'expected':expected['fw_beckmann_objective']},{'name':'accepted_demand_identity','pass':len(od)==expected['positive_od'] and abs(sum(r['volume'] for r in od)-expected['total_drive_pce'])<=1e-8}])
    result={'success':all(c['pass'] for c in checks),'status':'PASS' if all(c['pass'] for c in checks) else 'FAIL','optimizer_calls':0,'checks':checks,'metrics':{'objective':obj,'relative_gap':gap,'od_count':len(od),'total_demand_pce':sum(r['volume'] for r in od),'max_node_balance':residual},'scope':'Historical Phase B '+tier+' FW on the accepted turn-expanded static graph. Frozen modeled one-hour PCE demand; not measured OD or the H1 finite-path instance.'};save(out/'verification.json',result);return result

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=('run','verify'));ap.add_argument('--repo-root',type=Path,required=True);ap.add_argument('--tier',choices=tuple(COUNTS),required=True);ap.add_argument('--output',type=Path);ap.add_argument('--run',type=Path);a=ap.parse_args();repo=a.repo_root.resolve();out=a.output if a.action=='run' else a.run
    if out is None:ap.error('run requires --output; verify requires --run')
    out=out.resolve()
    if a.action=='run':
        if out.exists() and any(out.iterdir()):raise SystemExit('Output must be empty; existing results are never overwritten.')
        od=demand(repo,a.tier);out.mkdir(parents=True,exist_ok=True);shutil.copyfile(repo/B/'phase_a/static_input/turn_expanded_links.csv',out/'link.csv')
        with (out/'demand.csv').open('w',newline='',encoding='utf-8') as f:
            writer=csv.DictWriter(f,fieldnames=list(od[0]));writer.writeheader();writer.writerows(od)
        code='import sys;sys.path.insert(0,sys.argv[1]);from tap_frank_wolfe import solve_fw_refined;solve_fw_refined(".",run_name=sys.argv[2],max_iter=100,cap_scale=1.0)'
        start=time.perf_counter();p=subprocess.run([sys.executable,'-B','-c',code,str((repo/S).parent),a.tier],cwd=out,capture_output=True,text=True);(out/'stdout.log').write_text(p.stdout,encoding='utf-8');(out/'stderr.log').write_text(p.stderr,encoding='utf-8')
        import numpy,pandas,scipy
        save(out/'run.json',{'case_id':'hk-static-b-'+a.tier+'-fw','source_sha256':sha(repo/S),'demand_sha256':sha(out/'demand.csv'),'link_sha256':sha(out/'link.csv'),'parameters':{'max_iter':100,'cap_scale':1.0,'selection':'descending modeled base drive PCE, source origin ID, source destination ID'},'environment':{'python':platform.python_version(),'numpy':numpy.__version__,'pandas':pandas.__version__,'scipy':scipy.__version__},'returncode':p.returncode,'wall_seconds':time.perf_counter()-start})
        if p.returncode:raise SystemExit(p.returncode)
    result=verify(repo,out,a.tier);print(json.dumps(result));return 0 if result['success'] else 2
if __name__=='__main__':raise SystemExit(main())
