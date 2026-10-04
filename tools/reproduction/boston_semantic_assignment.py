"""Boston S1/S2 assignment-stage replay from the public semantic-fixed GMNS exchange."""
from __future__ import annotations
import argparse,collections,csv,json,subprocess,sys
from pathlib import Path

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def rows(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write_csv(p,fields,records):
 with p.open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(records)
def invoke(root,out,name,args):
 r=subprocess.run([sys.executable,'-B',str(root/'tools/mcl_assignment.py'),*map(str,args)],cwd=root,capture_output=True,text=True,timeout=150)
 if name!='independent-verify':(out/(name+'.log')).write_text(r.stdout+'\n'+r.stderr,encoding='utf-8')
 if r.returncode:raise RuntimeError(name+' failed; see its log')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['run','verify']);p.add_argument('--repo-root',type=Path,required=True);p.add_argument('--scenario',choices=['S1','S2'],required=True);p.add_argument('--output',type=Path);p.add_argument('--run',type=Path);a=p.parse_args()
 root=a.repo_root.resolve();out=(a.output if a.action=='run' else a.run)
 if out is None:p.error('Supply --output for run or --run for verify')
 out=out.resolve();exchange=root/'examples/boston/gmns_exchange_r1/data';s=a.scenario
 if a.action=='run':
  if out.exists() and any(out.iterdir()):raise ValueError('Output must be new or empty')
  inp=out/'inputs';inp.mkdir(parents=True)
  links=rows(exchange/'link.csv');physical=[r for r in links if r['mcl_link_class']=='physical']
  fields=[k[len('mcl_solver_'):] for k in links[0] if k.startswith('mcl_solver_')];fields=[k for k in fields if any(r['mcl_solver_'+k]!='' for r in physical)]
  write_csv(inp/'link.csv',fields,[{k:r['mcl_solver_'+k] for k in fields} for r in physical])
  access={r['export_zone_id']:r['source_physical_access_node_id'] for r in rows(exchange/'id_crosswalk.csv')};q=collections.defaultdict(float);excluded=0
  for r in rows(exchange/('demand_'+s+'.csv')):
   o,d=access[r['o_zone_id']],access[r['d_zone_id']]
   if o==d:excluded+=float(r['volume'])
   else:q[o,d]+=float(r['volume'])
  write_csv(inp/'demand.csv',['o_zone_id','d_zone_id','volume'],[{'o_zone_id':o,'d_zone_id':d,'volume':format(v,'.17g')} for (o,d),v in sorted(q.items())])
  config=read(root/'examples/boston/scalable_tool_r1/assignment_config.json');config['scenario']='Boston semantic-fix '+s+' frozen exchange assignment';config['period']='Declared two-hour effective-capacity midday panel'
  (inp/'config.json').write_text(json.dumps(config,indent=2)+'\n');(out/'preparation.json').write_text(json.dumps({'scenario':s,'physical_links':len(physical),'physical_od':len(q),'vehicle_trips':sum(q.values()),'same_access_excluded':excluded,'scope':'Physical mcl_solver fields and published zone-to-access mapping; no upstream behavior or observation recomputation.'},indent=2)+'\n')
  invoke(root,out,'prepare',['prepare','--input',inp,'--demand',inp/'demand.csv','--config',inp/'config.json','--output',out/'instance'])
  invoke(root,out,'solve',['solve','--instance',out/'instance','--method','fw','--config',inp/'config.json','--output',out/'computed'])
 invoke(root,out,'independent-verify',['verify','--run',out/'computed'])
 v=read(out/'computed/verification.json');g=v['gates'];prep=read(out/'preparation.json')
 actual={r['link_id']:float(r['flow_pce_per_period']) for r in rows(out/'computed/link_flow.csv')}
 expected={r['link_id']:float(r[s.lower()+'_volume']) for r in rows(exchange/'assignment_result_by_scenario.csv')}
 delta=max(abs(actual[k]-expected[k]) for k in actual) if actual.keys()==expected.keys() else float('inf')
 checks={'original_verifier_pass':v['status']=='SOLVED_WITHIN_DECLARED_TOLERANCE','scenario_identity':prep['scenario']==s,'physical_links_5091':v['physical_links']==5091,'physical_od_26':v['od_pairs']==26,'od_balance':v['max_od_residual']<=g['max_od_error_abs'],'od_l1':v['od_residual_l1']<=g['total_od_l1_rel']*max(1,abs(v['demand_pce'])),'nonnegative_path_flow':v['min_path_flow_raw']>=-g['negative_flow_abs'],'nonnegative_link_flow':v['min_link_flow_raw']>=-g['negative_flow_abs'],'link_reconstruction':v['max_link_reconstruction_error']<=g['link_reconstruction_abs'],'full_network_gap':abs(v['full_network_relative_gap'])<=g['full_relative_gap_abs'],'objective_recomputation':abs(v['objective_checked']-v['objective_reported'])<=1e-7,'historical_physical_link_flows':delta<=1e-7}
 metrics={k:v[k] for k in ['od_pairs','physical_links','demand_pce','objective_checked','max_od_residual','max_link_reconstruction_error','full_network_relative_gap']};metrics['historical_max_link_flow_absolute_error']=delta
 report={'success':all(checks.values()),'optimizer_calls':0,'checks':checks,'metrics':metrics,'scope':'Prepared-input '+s+' assignment only. The upstream service-feedback, population, transit/GPS preparation and four-stage chain are not recomputed; this is not the separate conditional absolute-choice recipe.'}
 (out/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));return 0 if report['success'] else 2
if __name__=='__main__':raise SystemExit(main())
