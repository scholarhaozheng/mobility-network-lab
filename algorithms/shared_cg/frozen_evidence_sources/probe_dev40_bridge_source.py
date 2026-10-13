"""Source-only audit of the generic queued-bridge prefix column oracle."""
from pathlib import Path
import csv,hashlib,json,sys,time
import numpy as np
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'sparse_common_dev40_bridge_multi_cg'))
from shared_cg.implicit_graph import ImplicitTimeGraph
from shared_cg.source_full_event_base import FullUniformQBase
from shared_cg.source_bridge_candidates import SourceBridgePrefixCandidates
from verify_dev22_batch_original_paths import replay
CFG=R/'cases/urbana_F_Q__sparse_common_dev35_cold_seed.json'
SEED=R/'runs/dev35_cold_source_seed_urbana_f'
OUT=R/'runs/dev40_bridge_source_probe'
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for x in iter(lambda:f.read(1048576),b''):h.update(x)
 return h.hexdigest()
def rows(path):
 with Path(path).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def main():
 began=time.monotonic()
 if (OUT/'RESULT.json').exists():raise FileExistsError('bridge source probe exists')
 cfg=json.loads(CFG.read_text(encoding='utf-8-sig'))
 source=Path(cfg['source_dir'])
 model=ImplicitTimeGraph(source,cfg['dt_seconds'],cfg['horizon_steps'],cfg['release_steps'],cfg['demand_factor'])
 if model.source_hashes!=cfg['expected_source_hashes'] or model.K!=cfg['expected_commodity_events']:
  raise ValueError('frozen original source drift')
 aon=SEED/'aon/UNIFORM_AON_FULL_ORIGINAL_PATHS.npz'
 fifo=SEED/'fifo/FRAGMENTS.npz'
 base=FullUniformQBase(model,aon,fifo)
 oracle=SourceBridgePrefixCandidates(model,base)
 selected,windows=oracle.select(max_events=320,per_od_window=4,window_steps=2048,chosen_windows=4)
 if len(selected)<1 or len(set(map(int,selected)))!=len(selected):
  raise ValueError('source bridge selection empty or duplicate')
 net=rows(source/'network.csv');od=rows(source/'assignment_od_pce.csv')
 access={x['zone_id']:x['node_id'] for x in rows(source/'access.csv')}
 physical={e:p for p,e in enumerate(i for i,x in enumerate(net) if x[cfg['physical_field']]==cfg['physical_value'])}
 maximum=0.;first_wait=0;min_gain=np.inf
 for f in selected:
  f=int(f);i=int(base.fod[f]);release=int(base.fr[f])
  edge,entry,raw=oracle.recover(f)
  source_raw,adjusted,arrival,wait,resources=replay(
   net,physical,access[od[i]['o_zone_id']],access[od[i]['d_zone_id']],
   release,edge,entry,model.H,model.dt,{})
  err=abs(raw-source_raw)
  maximum=max(maximum,err)
  if err>1e-7 or abs(raw-oracle.candidate_unit[f])>1e-7:
   raise ValueError('bridge source path raw cost')
  if base.fm[f]<=0 or arrival>model.H:raise ValueError('source event/path')
  first_wait+=int(len(entry)>0 and int(entry[0])>release)
  min_gain=min(min_gain,float(base.donor_cost[f]-raw))
 if min_gain<=1e-9:raise ValueError('selected bridge path no true saving')
 OUT.mkdir(parents=True,exist_ok=True)
 rec={'schema':'DEV40_SOURCE_ONLY_QUEUED_BRIDGE_PROBE','status':'PASS_SOURCE_ONLY_FULL_ORIGINAL_PATH_REPLAY',
  'source_hashes':model.source_hashes,'original_positive_OD':len(model.od),'original_release_events':model.K,
  'fresh_seed_receipt_sha256':sha(SEED/'RECEIPT.json'),'bridge_edge_original_index':oracle.edge,
  'bridge_selection_rule':'maximum mass-weighted FIFO wait; source edge ID tie break',
  'mass_weighted_wait_steps_PCE':oracle.weighted_wait_steps,'maximum_fixed_service_delay_steps':oracle.max_delay,
  'eligible_source_fragments':len(oracle.eligible),
  'positive_raw_saving_fragments':int(np.count_nonzero(oracle.saving[oracle.eligible]>1e-9)),
  'selected_source_fragments':len(selected),'selected_windows':windows,'selected_first_action_wait_paths':first_wait,
  'minimum_selected_true_unit_saving_minutes':min_gain,'maximum_independent_original_path_cost_error':maximum,
  'source_aon_sha256':sha(aon),'source_fifo_sha256':sha(fifo),
  'wall_seconds':time.monotonic()-began,
  'scope':'Path-generation audit only; no joint capacity feasibility or CG closure claim.'}
 (OUT/'RESULT.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 print(json.dumps(rec,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
