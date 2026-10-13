"""Prepare exact source-affected support for a certified original-Q dual blend."""
from pathlib import Path
from hashlib import sha256
import csv,json,numpy as np
R=Path(__file__).resolve().parent;OUT=R/'runs/dev26_dual_blend_support_urbana_f'
BASE=R/'runs/dev25_two_subgradient_bundle_grid_urbana_f';RMP=R/'runs/dev22_batch_event_rmp_urbana_f'
CFG=R/'cases/urbana_F_Q__sparse_common_dev20_rolling_path_recovery.json';SEED=R/'runs/sparse_common_dev20_rolling_path_recovery/urbana_F_Q/solver/UNIFORM_AON_FULL_ORIGINAL_PATHS.npz'
def sha(p):return sha256(Path(p).read_bytes()).hexdigest()
def csvrows(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def main():
 if OUT.exists() and any(OUT.iterdir()):raise FileExistsError(OUT)
 cfg=json.loads(CFG.read_text(encoding='utf-8-sig'));source=Path(cfg['source_dir']);hashes={n:sha(source/n) for n in cfg['expected_source_hashes']}
 bcert=json.loads((BASE/'INDEPENDENT_FULL_ORIGINAL_DUAL_CERT.json').read_text(encoding='utf-8-sig'))
 rcert=json.loads((RMP/'INDEPENDENT_CERT.json').read_text(encoding='utf-8-sig'))
 if hashes!=cfg['expected_source_hashes'] or bcert['status']!='PASS_EXACT_FULL_ORIGINAL_GRAPH_DUAL_IMPROVED_OPEN_OPTIMALITY' or rcert['status']!='PASS_ALL_ORIGINAL_DEMAND_PHYSICAL_ROWS_RESTRICTED_PRIMAL_DUAL':raise ValueError('independent full original parent identities')
 net=csvrows(source/'network.csv');od=csvrows(source/'assignment_od_pce.csv');access=csvrows(source/'access.csv')
 H=int(cfg['horizon_steps']);T=int(cfg['release_steps']);dt=float(cfg['dt_seconds'])
 physical=np.array([r['arc_kind']=='physical' for r in net],bool);phys=np.flatnonzero(physical);pos=np.full(len(net),-1,np.int32);pos[phys]=np.arange(len(phys),dtype=np.int32)
 with np.load(SEED) as z:off=z['od_edge_offset'];edge=z['edge_index'];entry=z['entry_offset_steps'];hourly=z['od_hourly_pce'];short=z['od_static_shortest_cost']
 with np.load(BASE/'BEST_PRICE_PROFILE.npz') as z:ids=z['original_OD_index'];release=z['original_release_step'];price=z['adjusted_shortest_cost'];bridge_lambda=z['bridge_price_per_step'];loops=z['flat_original_loop_edges'];flat=float(z['flat_loop_toll_minutes'][0])
 with np.load(RMP/'NEW_RESTRICTED_RMP_ROWS_AND_DUAL.npz') as z:rrows=z['original_resource_rows'];rmu=z['capacity_dual']
 if len(od)!=len(hourly) or len(od)*T!=cfg['expected_commodity_events'] or len(bridge_lambda)!=18024-557 or len(ids)!=bcert['affected_original_events_independently_repriced']:raise ValueError('full original demand/time/price profile')
 if np.max(abs(hourly-np.array([float(x['volume_pce']) for x in od])))>1e-9:raise ValueError('source hourly demand')
 brow=[np.arange(int(pos[447])*H+557,int(pos[447])*H+18024,dtype=np.int64)];blam=[bridge_lambda]
 for e in loops:
  brow.append(np.arange(int(pos[int(e)])*H,int(pos[int(e)])*H+18024,dtype=np.int64));blam.append(np.full(18024,flat,np.float64))
 brow=np.concatenate(brow);blam=np.concatenate(blam)
 if len(np.unique(brow))!=len(brow):raise ValueError('accepted base resource duplication')
 positive=rmu<-1e-12;rrows=rrows[positive];rlam=-rmu[positive]
 rows=np.unique(np.r_[brow,rrows]);base=np.zeros(len(rows),np.float64);other=np.zeros(len(rows),np.float64)
 base[np.searchsorted(rows,brow)]=blam;other[np.searchsorted(rows,rrows)]=rlam
 cap=np.array([float(net[int(e)]['capacity'])*dt/3600 for e in phys],np.float64)
 baseline=float(np.dot(hourly,short));weighted=baseline+float(np.dot(hourly[ids]/T,price-short[ids]));term=float(np.dot(cap[rows//H],base));lower=weighted-term
 if abs(lower-bcert['independent_new_lower'])>1e-6:raise ValueError('accepted base capacity row support/lower cannot be reproduced')
 priced={}
 for row in rows:priced.setdefault(int(row//H),[]).append(int(row%H))
 priced={p:np.asarray(v,dtype=np.int32) for p,v in priced.items()}
 affected=np.zeros((len(od),T),bool)
 for i in range(len(od)):
  for j in range(int(off[i]),int(off[i+1])):
   p=int(pos[int(edge[j])]);times=priced.get(p)
   if times is None:continue
   r=times-int(entry[j]);r=r[(r>=0)&(r<T)];affected[i,r]=True
 ai,ar=np.nonzero(affected);ai=ai.astype(np.int32);ar=ar.astype(np.int32)
 node_ids=sorted({x['from_node_id'] for x in net}|{x['to_node_id'] for x in net});nodeix={x:j for j,x in enumerate(node_ids)};zone={x['zone_id']:nodeix[x['node_id']] for x in access}
 dest=np.array([zone[od[int(i)]['d_zone_id']] for i in ai],np.int32)
 OUT.mkdir(parents=True,exist_ok=False);arr=OUT/'DUAL_ROW_AND_AFFECTED_EVENT_SUPPORT.npz'
 np.savez_compressed(arr,original_resource_rows=rows,base_capacity_lambda=base,RMP_capacity_lambda=other,affected_original_OD_index=ai,affected_release_step=ar,affected_destination_node_index=dest,affected_static_cost=short[ai])
 result={'schema':'SHARED_CG_DEV26_DUAL_BLEND_SOURCE_SUPPORT_R1','status':'SOURCE_AON_AFFECTED_SUPPORT_AND_ACCEPTED_BASE_DUAL_REPRODUCED','source_hashes':hashes,'original_OD_count':len(od),'original_release_events':len(od)*T,'original_physical_rows':len(phys)*H,'priced_source_physical_edges':len(priced),'union_priced_original_rows':len(rows),'affected_original_OD':int(np.count_nonzero(affected.any(axis=1))),'affected_original_events':len(ai),'unaffected_original_events_proven_static':len(od)*T-len(ai),'affected_destinations':int(len(np.unique(dest))),'base_independent_dual_lower_reconstructed':lower,'base_independent_dual_lower_certified':bcert['independent_new_lower'],'base_cert_sha256':sha(BASE/'INDEPENDENT_FULL_ORIGINAL_DUAL_CERT.json'),'RMP_cert_sha256':sha(RMP/'INDEPENDENT_CERT.json'),'support_npz_sha256':sha(arr),'proof':'For any original OD-release whose source AON path touches no positive row in either nonnegative capacity-price support, its adjusted AON cost remains static shortest cost; no other path can cost less after nonnegative tolls. Thus all omitted events have their exact full original graph minimum at static cost.','scope':'source support only; no new dual endpoint solved'}
 (OUT/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result),flush=True)
if __name__=='__main__':main()
