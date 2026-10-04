"""Run seven bounded public fixtures through unchanged computational CLIs.

These controls validate reusable tools. They do not reproduce a city pipeline,
empirical behaviour, or the historical Victoria GTFS ZIP.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math, subprocess, sys, zipfile
from collections import defaultdict
from pathlib import Path

def load(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def rows(p):
    with Path(p).open(encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))
def write(p,v): Path(p).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def invoke(root,out,name,*args):
    command=[sys.executable,'-B','-X','utf8',*[str(a) for a in args]]
    p=subprocess.run(command,cwd=root,capture_output=True,text=True,timeout=120)
    if not name.startswith('verify-'): (out/(name+'.log')).write_text(p.stdout+p.stderr,encoding='utf-8')
    if p.returncode: raise RuntimeError(name+' failed; see '+name+'.log')

def compute(root,out,mode):
    out.mkdir(parents=True,exist_ok=True)
    if mode in ('fw','finite-path'):
        base=root/'examples/scalable_vehicle_fixture'
        invoke(root,out,'prepare',root/'tools/mcl_assignment.py','prepare','--input',base/'network','--demand',base/'vehicle.csv','--config',base/'config.json','--output',out/'prepared')
        argv=[root/'tools/mcl_assignment.py','solve','--instance',out/'prepared','--method','fw' if mode=='fw' else 'full-path','--output',out/'computed']
        if mode=='finite-path':
            write(out/'full-path-config.json',{'k':5,'max_iterations':200}); argv+=['--config',out/'full-path-config.json']
        invoke(root,out,'solve',*argv)
    elif mode=='person-choice':
        base=root/'examples/scalable_person_fixture'
        invoke(root,out,'choice',root/'tools/mcl_person_choice.py','--person-od',base/'person.csv','--skims',base/'skims.csv','--spec',root/'examples/boston/scalable_tool_r1/choice_spec.json','--config',base/'choice_config.json','--output',out/'computed')
    elif mode in ('cg-capacity','cg-auto'):
        base=root/'app/cases'/('capacity_zone_probe' if mode=='cg-capacity' else 'external_auto_4node')
        invoke(root,out,'solve',root/'tools/mnl.py','run','--input',base/'input','--config',base/'case.json','--seed-mode','auto','--seed-k','1','--output',out/'computed','--timeout','110')
    elif mode=='catalog-match':
        base=root/'examples/data-tools'
        invoke(root,out,'catalog',root/'tools/mcl_data.py','catalog-city-match','--catalog',base/'feeds_sample.csv','--cities',base/'external_city_universe_sample.csv','--output',out/'computed')
    elif mode=='gtfs-parser':
        members=load(root/'experiments/public-controls/synthetic-gtfs-members.json')
        with zipfile.ZipFile(out/'synthetic-fixture.zip','w',compression=zipfile.ZIP_STORED) as z:
            for name,value in members.items(): z.writestr(zipfile.ZipInfo(name,(2026,1,1,0,0,0)),value)
        invoke(root,out,'parser',root/'tools/mcl_data.py','process-gtfs','--zip',out/'synthetic-fixture.zip','--output',out/'computed')

def verify(root,out,mode):
    computed=out/'computed'; metrics={}; checks={}
    if mode in ('fw','finite-path'):
        invoke(root,out,'verify-static',root/'tools/mcl_assignment.py','verify','--run',computed)
        v=load(computed/'verification.json'); metrics=v
        checks={'public_independent_verifier':v['status']=='SOLVED_WITHIN_DECLARED_TOLERANCE',
                'fixture_identity':v.get('od_pairs',v.get('node_od'))==2 and v['physical_links']==5 and abs(v.get('demand_pce',v.get('demand_total'))-14)<1e-12,
                'expected_objective':abs(v['objective_checked']-38.0056431104)<=1e-8,
                'od_conservation':v['max_od_residual']<=1e-8,
                'link_reconstruction':v['max_link_reconstruction_error']<=1e-8,
                'full_network_gap':abs(v.get('full_network_relative_gap',v.get('full_relative_gap')))<=1e-8}
        if mode=='finite-path': checks['generated_pool_size']=v['path_count']==4
    elif mode=='person-choice':
        p=rows(computed/'probabilities.csv'); v=rows(computed/'person_to_vehicle.csv'); d=rows(computed/'vehicle_demand.csv'); s=load(computed/'summary.json')
        groups=defaultdict(list)
        for r in p: groups[(r['od_id'],r['departure_time'])].append(r)
        ps=max(abs(sum(float(r['probability']) for r in g)-1) for g in groups.values())
        mass=max(abs(float(r['conditional_person_trips'])-float(r['probability'])*float(r['person_mass'])) for r in p)
        occ=max(abs(float(r['vehicle_trips'])*float(r['occupancy'])-float(r['person_trips'])) for r in v)
        loaded=sum(float(r['volume']) for r in d)
        counts={k:len(g) for k,g in groups.items()}
        metrics={'probability_rows':len(p),'choice_groups':len(groups),'max_probability_sum_error':ps,'max_person_mass_error':mass,'max_occupancy_conversion_error':occ,'loaded_vehicle_trips':loaded,'evaluated_person_mass':s['evaluated_person_mass']}
        checks={'fixture_scope':len(p)==8 and len(groups)==2 and set(counts.values())=={4} and s['evaluated_person_mass']==14 and s['non_evaluated_person_mass']==0,
                'probability_bounds':all(math.isfinite(float(r['probability'])) and 0<=float(r['probability'])<=1 for r in p),
                'probability_sums':ps<=1e-12,'person_mass':mass<=1e-12,'occupancy_conversion':occ<=1e-12,
                'vehicle_conservation':abs(loaded-sum(float(r['vehicle_trips']) for r in v if r['road_status']=='eligible'))<=1e-12,
                'expected_loaded_vehicles':abs(loaded-11.153540248879068)<=1e-10}
    elif mode in ('cg-capacity','cg-auto'):
        invoke(root,out,'verify-cg',root/'tools/mnl.py','verify','--run',computed)
        v=load(computed/'offline_verification.json'); metrics=v; expected=27 if mode=='cg-capacity' else 10
        checks={'public_solver_free_verifier':v['status']=='PASS' and v['optimization_invocations_during_verify']==0,
                'expected_objective':abs(v['recomputed_objective']-expected)<=1e-8,
                'same_graph_lp':v['recomputed_objective_matches_reference'] is True,
                'primal_export':v['final_rmp_primal_and_export_checks'] is True,
                'pricing_boundary_retained':v['pricing_closure_proven'] is False and v['independent_pricing_certificate_present'] is False}
    elif mode=='catalog-match':
        m=rows(computed/'feed_city_matches.csv'); q=load(computed/'quality_report.json')
        expected={'mdb-001':'sample-ext-london','mdb-002':'sample-ext-london','mdb-003':'sample-ext-new-york','mdb-004':'sample-ext-new-york','mdb-005':''}
        actual={r['feed_id']:r['city_id'] for r in m}
        metrics={'catalog_rows':len(m),'matched_feed_records':sum(bool(r['city_id']) for r in m),'unmatched_records':sum(not r['city_id'] for r in m),'matched_city_ids':len({r['city_id'] for r in m if r['city_id']})}
        checks={'all_rows_preserved':len(m)==5 and len(actual)==5,'exact_fixture_matches':actual==expected,
                'unmatched_preserved':next(r for r in m if r['feed_id']=='mdb-005')['match_status']=='unmatched_other',
                'input_hashes':q['inputs']['catalog']['sha256']==sha(root/'examples/data-tools/feeds_sample.csv') and q['inputs']['cities']['sha256']==sha(root/'examples/data-tools/external_city_universe_sample.csv'),
                'output_checksums':all(sha(computed/e['path'])==e['sha256'] for e in q['outputs'].values())}
    elif mode=='gtfs-parser':
        v=load(computed/'metrics.json'); r=load(computed/'report.json'); metrics=v
        with zipfile.ZipFile(out/'synthetic-fixture.zip') as z: members={n:z.read(n).decode() for n in z.namelist()}
        checks={'synthetic_input_identity':members==load(root/'experiments/public-controls/synthetic-gtfs-members.json'),
                'content_sha256':v['content_sha256']==sha(out/'synthetic-fixture.zip'),
                'parsed':v['parse_status']=='parsed','one_stop_time':v['stop_time_row_count']==1,
                'valid_stop_references':v['invalid_stop_references']==0,
                'no_network_or_extraction':r['network_used'] is False and r['input_modified_or_extracted'] is False and not (out/'stops.txt').exists()}
    report={'status':'PASS' if all(checks.values()) else 'FAIL','success':bool(checks) and all(checks.values()),'optimizer_calls':0,'checks':checks,'metrics':metrics,'scope':'Bounded public fixture only; no city source-to-result or historical Victoria GTFS claim.'}
    write(out/'verification.json',report); return report

def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('action',choices=['run','verify']); p.add_argument('--repo-root',required=True,type=Path); p.add_argument('--output',type=Path); p.add_argument('--run',type=Path); p.add_argument('--mode',required=True,choices=['fw','finite-path','person-choice','cg-capacity','cg-auto','catalog-match','gtfs-parser'])
    a=p.parse_args(); root=a.repo_root.resolve(); target=a.output if a.action=='run' else a.run
    if target is None: p.error('Output/run directory required')
    out=target.resolve()
    if a.action=='run':
        if out.exists() and any(out.iterdir()): raise ValueError('Output must be new or empty')
        if out==root or root.is_relative_to(out): raise ValueError('Output overlaps source root')
        compute(root,out,a.mode)
    report=verify(root,out,a.mode); print(json.dumps(report,indent=2)); return 0 if report['success'] else 2
if __name__=='__main__': raise SystemExit(main())
