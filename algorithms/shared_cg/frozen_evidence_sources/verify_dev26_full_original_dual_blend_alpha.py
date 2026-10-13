"""Independent original CSV Bellman audit of one frozen cross-method Q dual blend."""
from pathlib import Path
from hashlib import sha256
from collections import deque
import argparse,csv,json,math,numpy as np
from verify_dev21_third_rmp_dual_price import independent_values
R=Path(__file__).resolve().parent;D=R/'DEV26_FULL_ORIGINAL_DUAL_BLEND_GRID_DESIGN.json';SUP=R/'runs/dev26_dual_blend_support_urbana_f';OUT=R/'runs/dev26_full_original_dual_blend_grid_urbana_f'
CFG=R/'cases/urbana_F_Q__sparse_common_dev20_rolling_path_recovery.json';SEED=R/'runs/sparse_common_dev20_rolling_path_recovery/urbana_F_Q/solver/UNIFORM_AON_FULL_ORIGINAL_PATHS.npz'
def sha(p):
 h=sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def csvrows(p):
 with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--alpha-index',type=int,required=True);args=ap.parse_args()
 d=json.loads(D.read_text(encoding='utf-8-sig'));cfg=json.loads(CFG.read_text(encoding='utf-8-sig'))
 if not 0<=args.alpha_index<len(d['alpha_grid']):raise ValueError('not a frozen original dual alpha')
 for key,p in [('support_result_sha256',SUP/'RESULT.json'),('support_npz_sha256',SUP/'DUAL_ROW_AND_AFFECTED_EVENT_SUPPORT.npz'),('base_independent_cert_sha256',R/'runs/dev25_two_subgradient_bundle_grid_urbana_f/INDEPENDENT_FULL_ORIGINAL_DUAL_CERT.json'),('RMP_independent_cert_sha256',R/'runs/dev22_batch_event_rmp_urbana_f/INDEPENDENT_CERT.json')]:
  if sha(p)!=d[key]:raise ValueError('source-certified blend parent drift '+key)
 alpha_dir=OUT/f'ALPHA_{args.alpha_index:03d}';rp=alpha_dir/'RESULT.json';target=alpha_dir/'INDEPENDENT_DUAL_CERT.json'
 if target.exists():raise FileExistsError(target)
 result=json.loads(rp.read_text(encoding='utf-8-sig'))
 if result['design_sha256']!=sha(D) or result['alpha_index']!=args.alpha_index or abs(result['alpha']-d['alpha_grid'][args.alpha_index])>1e-12:raise ValueError('producer frozen alpha')
 source=Path(cfg['source_dir']);hashes={n:sha(source/n) for n in cfg['expected_source_hashes']}
 if hashes!=cfg['expected_source_hashes'] or hashes!=result['source_hashes']:raise ValueError('original source CSV changed')
 net=csvrows(source/'network.csv');access=csvrows(source/'access.csv');od=csvrows(source/'assignment_od_pce.csv')
 nodes=sorted({r['from_node_id'] for r in net}|{r['to_node_id'] for r in net});ix={v:i for i,v in enumerate(nodes)};zone={r['zone_id']:ix[r['node_id']] for r in access}
 H=int(cfg['horizon_steps']);T=int(cfg['release_steps']);dt=float(cfg['dt_seconds'])
 physical_edges=[];positive=[];zero=[[] for _ in nodes];indeg=np.zeros(len(nodes),dtype=np.int32)
 for e,arc in enumerate(net):
  u=ix[arc['from_node_id']];v=ix[arc['to_node_id']];c=float(arc['vdf_fftt'])
  if arc['arc_kind']=='physical':
   duration=max(1,math.ceil(c*60/dt-1e-12));positive.append((u,v,c,duration,e));physical_edges.append(e)
  else:zero[u].append((v,c));indeg[v]+=1
 queue=deque(int(i) for i in np.flatnonzero(indeg==0));topo=[]
 while queue:
  node=queue.popleft();topo.append(node)
  for v,c in zero[node]:
   indeg[v]-=1
   if indeg[v]==0:queue.append(v)
 if len(topo)!=len(nodes):raise ValueError('original zero-time DAG cycle')
 zp=np.r_[0,np.cumsum([len(v) for v in zero])].astype(np.int32);zh=np.array([v for group in zero for v,c in group],np.int32);zc=np.array([c for group in zero for v,c in group],np.float64)
 with np.load(SEED) as z:off=z['od_edge_offset'];edge=z['edge_index'];entry=z['entry_offset_steps'];hourly=z['od_hourly_pce'];short=z['od_static_shortest_cost']
 if len(od)!=len(hourly) or len(od)*T!=d['all_original_release_events'] or np.max(abs(hourly-np.array([float(x['volume_pce']) for x in od])))>1e-9:raise ValueError('all original hourly source demand')
 with np.load(SUP/'DUAL_ROW_AND_AFFECTED_EVENT_SUPPORT.npz') as z:rows=z['original_resource_rows'];base=z['base_capacity_lambda'];other=z['RMP_capacity_lambda'];ai=z['affected_original_OD_index'];ar=z['affected_release_step'];adest=z['affected_destination_node_index'];astatic=z['affected_static_cost']
 if len(ai)!=d['affected_original_events'] or len(od)*T-len(ai)!=d['unaffected_original_events_proven_static'] or np.max(abs(astatic-short[ai]))>1e-10:raise ValueError('source affected dimensions')
 # Reconstruct the exact source AON touched set without using the producer mask.
 phys=np.array(physical_edges,np.int32);ppos=np.full(len(net),-1,np.int32);ppos[phys]=np.arange(len(phys),dtype=np.int32)
 marked=np.zeros((len(od),T),bool);times_by_p={}
 for row in rows:times_by_p.setdefault(int(row//H),[]).append(int(row%H))
 for p in times_by_p:times_by_p[p]=np.asarray(times_by_p[p],np.int32)
 for i in range(len(od)):
  for j in range(int(off[i]),int(off[i+1])):
   p=int(ppos[int(edge[j])]);times=times_by_p.get(p)
   if times is None:continue
   rel=times-int(entry[j]);rel=rel[(rel>=0)&(rel<T)];marked[i,rel]=True
 check_i,check_r=np.nonzero(marked)
 if not np.array_equal(ai,check_i) or not np.array_equal(ar,check_r):raise ValueError('hidden original OD-release or bad source AON price support')
 true_dest=np.array([zone[od[int(i)]['d_zone_id']] for i in ai],np.int32)
 if not np.array_equal(true_dest,adest):raise ValueError('bad original destination mapping')
 alpha=float(d['alpha_grid'][args.alpha_index]);full_lambda=(1-alpha)*base+alpha*other;active=full_lambda>0;priced_rows=rows[active];lam=full_lambda[active]
 priced_physical=np.unique(priced_rows//H);priced_edge=[physical_edges[int(p)] for p in priced_physical];pmap={e:j for j,e in enumerate(priced_edge)}
 toll=np.zeros((len(priced_edge),H),np.float64)
 for row,value in zip(priced_rows,lam):
  e=physical_edges[int(row//H)];t=int(row%H);toll[pmap[e],t]=float(value)
 pu=np.array([x[0] for x in positive],np.int32);pv=np.array([x[1] for x in positive],np.int32);pc=np.array([x[2] for x in positive],np.float64);pdur=np.array([x[3] for x in positive],np.int32);pid=np.array([pmap.get(x[4],-1) for x in positive],np.int32)
 with np.load(alpha_dir/'ALL_AFFECTED_ORIGINAL_PRICE_VALUES.npz') as z:producer=z['minimum_adjusted_price']
 if len(producer)!=len(ai) or sha(alpha_dir/'ALL_AFFECTED_ORIGINAL_PRICE_VALUES.npz')!=result['profile_sha256']:raise ValueError('saved producer price profile drift')
 receipt=json.loads((alpha_dir/'DESTINATION_STAGE_RECEIPT.json').read_text(encoding='utf-8-sig'))
 if len(receipt['completed_destinations'])!=len(d['affected_destination_node_indices']) or sha(alpha_dir/'DESTINATION_STAGE_RECEIPT.json')!=result['stage_receipt_sha256']:raise ValueError('destination price stages incomplete')
 full=np.empty(len(ai),np.float64);maximum=0.;max_unaffected=0.;checked_events=0;stages=[]
 for k,dest in enumerate(d['affected_destination_node_indices']):
  ids=np.array([i for i,r in enumerate(od) if zone[r['d_zone_id']]==dest],np.int32)
  origins=np.array([zone[od[int(i)]['o_zone_id']] for i in ids],np.int32)
  values=independent_values(len(nodes),H,T,dt,int(dest),origins,pu,pv,pc,pdur,pid,toll,zp,zh,zc,np.asarray(topo[::-1],np.int32))
  if not np.all(np.isfinite(values)):raise ValueError('unreachable original event in independent full graph')
  mapping=np.full(len(od),-1,np.int32);mapping[ids]=np.arange(len(ids),dtype=np.int32)
  positions=np.flatnonzero(adest==dest);got=values[mapping[ai[positions]],ar[positions]];full[positions]=got
  file=alpha_dir/f'DESTINATION_{dest:05d}_PRICE.npz';stage=receipt['completed_destinations'][k]
  if stage['destination_node_index']!=dest or stage['sha256']!=sha(file):raise ValueError('destination artifact identity')
  with np.load(file) as z:producer_pos=z['selection_position'];producer_values=z['minimum_adjusted_price']
  if not np.array_equal(positions,producer_pos) or np.max(abs(got-producer_values))>1e-7:raise ValueError('independent original graph destination price')
  diff=float(np.max(abs(got-producer[positions])));maximum=max(maximum,diff)
  untouched=~marked[ids]
  if np.any(untouched):max_unaffected=max(max_unaffected,float(np.max(abs(values[untouched]-np.broadcast_to(short[ids,None],values.shape)[untouched]))))
  checked_events+=values.size;stages.append({'destination_node_index':int(dest),'original_events_independently_priced':int(values.size),'affected_events':len(positions),'maximum_producer_price_error':diff})
  print(json.dumps({'independent_alpha':alpha,'completed_destinations':k+1,'of':len(d['affected_destination_node_indices']),'destination':dest,'max_difference':diff}),flush=True)
 if maximum>1e-7 or max_unaffected>1e-7:raise ValueError('complete original affected/unaffected price mismatch')
 cap=np.array([float(net[int(e)]['capacity'])*dt/3600 for e in phys],np.float64)
 weighted=float(np.dot(hourly,short)+np.dot(hourly[ai]/T,full-astatic));term=float(np.dot(cap[priced_rows//H],lam));lower=weighted-term
 if abs(lower-result['exact_full_original_graph_dual_lower'])>1e-5 or abs(term-result['original_capacity_price_term'])>1e-5 or lower>result['accepted_source_feasible_upper']+1e-6:raise ValueError('independent source full original dual bound')
 profile=alpha_dir/'INDEPENDENT_ALL_AFFECTED_PRICE_VALUES.npz';np.savez_compressed(profile,minimum_adjusted_price=full)
 cert={'schema':'SHARED_CG_DEV26_INDEPENDENT_FULL_ORIGINAL_DUAL_BLEND_ALPHA_R1','status':'PASS_ALL_ORIGINAL_EVENTS_VALID_DUAL_OPEN_CG_GAP','alpha_index':args.alpha_index,'alpha':alpha,'producer_result_sha256':sha(rp),'source_hashes':hashes,'original_OD_count':len(od),'original_release_events':len(od)*T,'original_events_independently_priced_in_affected_destinations':checked_events,'original_events_static_proven_from_unpriced_AON':len(od)*T-len(ai),'affected_original_events_with_independent_price':len(ai),'affected_destinations':len(stages),'maximum_producer_price_difference':maximum,'maximum_unaffected_static_price_difference':max_unaffected,'independent_source_dual_lower':lower,'accepted_source_feasible_upper':result['accepted_source_feasible_upper'],'relative_open_gap':(result['accepted_source_feasible_upper']-lower)/result['accepted_source_feasible_upper'],'independent_profile_sha256':sha(profile),'stages':stages,'scope':'full original graph Bellman prices for all potentially affected source events and exact static proof for every omitted event; no CG optimum'}
 target.write_text(json.dumps(cert,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:cert[k] for k in ('status','alpha','independent_source_dual_lower','maximum_producer_price_difference','relative_open_gap')}),flush=True)
if __name__=='__main__':main()
