"""Independent source-CSV replay of fresh dev40 original-Q joint CG output."""
from pathlib import Path
from collections import Counter,defaultdict
import csv,hashlib,json,time
import numpy as np
from scipy import sparse
from verify_dev22_batch_original_paths import replay
R=Path(__file__).resolve().parent
OUT=R/'runs/dev40_bridge_multi_joint_cg_urbana_f'
SEED=R/'runs/dev35_cold_source_seed_urbana_f'
CFG=R/'cases/urbana_F_Q__sparse_common_dev35_cold_seed.json'
DESIGN=R/'DEV40_BRIDGE_MULTI_JOINT_CG_DESIGN.json'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rd(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def csvrows(p):
 with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def main():
 began=time.monotonic();target=OUT/'INDEPENDENT_CERT.json'
 if target.exists():raise FileExistsError(target)
 cfg=rd(CFG);design=rd(DESIGN);result=rd(OUT/'RESULT.json');seed=rd(SEED/'RECEIPT.json')
 if result['design_sha256']!=sha(DESIGN) or result['fresh_seed_receipt_sha256']!=sha(SEED/'RECEIPT.json') or result['initial_columns']!=0:
  raise ValueError('cold source candidate identity')
 source=Path(cfg['source_dir']);hashes={n:sha(source/n) for n in cfg['expected_source_hashes']}
 if hashes!=cfg['expected_source_hashes'] or hashes!=result['source_hashes'] or hashes!=seed['source_hashes']:
  raise ValueError('original source CSV drift')
 if result['final_rmp_sha256']!=sha(OUT/'FINAL_RMP.npz') or result['final_matrix_sha256']!=sha(OUT/'STATE_MATRIX.npz') or result['path_pool_sha256']!=sha(OUT/'RECOVERED_PATH_POOL.npz'):
  raise ValueError('fresh candidate arrays drift')
 cold_cert=rd(SEED/'fifo/INDEPENDENT_ORIGINAL_TIME_CERTIFICATE.json')
 if cold_cert['status']!='PASS_FULL_ORIGINAL_OD_RELEASE_PATH_TIME_CAPACITY_OBJECTIVE' or seed['independent_certificate_sha256']!=sha(SEED/'fifo/INDEPENDENT_ORIGINAL_TIME_CERTIFICATE.json'):
  raise ValueError('fresh full original base not independently certified')
 net=csvrows(source/'network.csv');od=csvrows(source/'assignment_od_pce.csv')
 access={r['zone_id']:r['node_id'] for r in csvrows(source/'access.csv')}
 H=int(cfg['horizon_steps']);T=int(cfg['release_steps']);dt=float(cfg['dt_seconds'])
 physical={e:p for p,e in enumerate(i for i,r in enumerate(net) if r[cfg['physical_field']]==cfg['physical_value'])}
 pedges=np.array(sorted(physical),np.int32)
 cap=np.array([float(net[int(e)]['capacity'])*dt/3600 for e in pedges])
 with np.load(SEED/'aon/UNIFORM_AON_FULL_ORIGINAL_PATHS.npz') as z:
  off=z['od_edge_offset'];ae=z['edge_index'];at=z['entry_offset_steps'];hourly=z['od_hourly_pce'];short=z['od_static_shortest_cost']
 with np.load(SEED/'fifo/FRAGMENTS.npz') as z:
  fod=z['od_index'];fr=z['release_step'];fm=z['mass_pce'];fw=z['wait_steps'];stages=z['stage_original_edge_index'];selected=z['selected_od_index']
 with np.load(OUT/'FINAL_RMP.npz') as z:save={k:z[k].copy() for k in z.files}
 with np.load(OUT/'RECOVERED_PATH_POOL.npz') as z:pool={k:z[k].copy() for k in z.files}
 A=sparse.load_npz(OUT/'STATE_MATRIX.npz').tocsr()
 rows=save['original_rows'];rhs=save['residual_capacity'];cost=save['delta_cost'];group=save['column_group'];mass=save['group_mass'];keys=save['group_key'];signatures=save['column_signature'];flow=save['flow'];mu=save['capacity_mu'];nu=save['group_mu']
 if len(od)!=418 or len(od)*T!=6019200 or len(keys)!=len(mass) or A.shape!=(len(rows),len(cost)) or len(group)!=len(cost) or len(flow)!=len(cost) or len(mu)!=len(rows) or len(nu)!=len(mass) or len(signatures)!=len(cost):
  raise ValueError('full source demand / joint matrix dimensions')
 if np.max(abs(hourly-np.asarray([float(x['volume_pce']) for x in od])))>1e-9:
  raise ValueError('source demand mass')
 nfrag=len(fod);fragment=keys<nfrag
 if np.any(keys<0) or len(np.unique(keys))!=len(keys):
  raise ValueError('duplicate or negative original event key')
 expected=np.empty(len(keys),dtype=np.float64);expected[fragment]=fm[keys[fragment]]
 other=keys[~fragment].astype(np.int64)-nfrag;oi=other//T
 selected_set=set(map(int,selected))
 if np.any(oi<0) or np.any(oi>=len(od)) or any(int(v) in selected_set for v in np.unique(oi)):
  raise ValueError('unsplit key duplicates FIFO-managed OD')
 expected[~fragment]=hourly[oi]/T
 if np.max(abs(mass-expected),initial=0)>1e-12:
  raise ValueError('original full-event demand changed')
 if np.any(group<0) or np.any(group>=len(keys)) or np.any(flow<-1e-8) or np.any(mu>1e-8) or np.any(nu>1e-8):
  raise ValueError('joint variable or dual sign')
 by_group=np.bincount(group,weights=flow,minlength=len(keys))
 if np.max(by_group-mass)>1e-8:raise ValueError('duplicate fragment service')
 if pool['edge_offset'][-1]!=len(pool['original_edge_index']) or len(pool['original_edge_index'])!=len(pool['original_entry_step']):
  raise ValueError('full path pool offsets')
 path_position={str(s):j for j,s in enumerate(pool['signature'])}
 if len(set(map(str,signatures)))!=len(signatures):raise ValueError('duplicate original path column identity')
 stage={int(e):j for j,e in enumerate(stages)}
 rowpos={int(r):j for j,r in enumerate(rows)}
 maxcost=0.;maxflow=0.;positive_new=0;first_wait=0
 for j in range(len(cost)):
  sig=str(signatures[j])
  if sig not in path_position:raise ValueError('column absent from recovered source path pool')
  p=path_position[sig];f=int(pool['source_event_key'][p]);k=int(group[j])
  if f!=int(keys[k]):raise ValueError('recovered path group mapping')
  if f<nfrag:
   i=int(fod[f]);release=int(fr[f]);waitrow=fw[f]
  else:
   i,release=divmod(f-nfrag,T);waitrow=None
   if i<0 or i>=len(od) or i in selected_set:raise ValueError('invalid unsplit path key')
  a=int(pool['edge_offset'][p]);b=int(pool['edge_offset'][p+1])
  edge=pool['original_edge_index'][a:b];entry=pool['original_entry_step'][a:b]
  raw,adjusted,arrival,wait,newrows=replay(net,physical,access[od[i]['o_zone_id']],access[od[i]['d_zone_id']],release,edge,entry,H,dt,{})
  first_wait+=int(len(entry)>0 and int(entry[0])>release)
  donor=[];delay=0
  for x in range(int(off[i]),int(off[i+1])):
   e=int(ae[x])
   if waitrow is not None and e in stage:delay+=int(waitrow[stage[e]])
   if e in physical:donor.append(physical[e]*H+release+int(at[x])+delay)
  oldcost=float(short[i])+(float(np.sum(waitrow))*dt/60. if waitrow is not None else 0.)
  maxcost=max(maxcost,abs(float(cost[j])-(raw-oldcost)))
  if maxcost>1e-7:raise ValueError('original source path cost')
  before=Counter(donor);after=Counter(newrows)
  delta={r:after.get(r,0)-before.get(r,0) for r in after.keys()|before.keys()}
  delta={r:value for r,value in delta.items() if value}
  saved=A[:,j].tocoo();actual={int(rows[r]):float(v) for r,v in zip(saved.row,saved.data)}
  if actual!=delta:raise ValueError('original physical row coefficient')
  if flow[j]>1e-10:positive_new+=1
 # Independently rebuild exact FIFO baseline on all rows touched by the
 # newly generated columns; accepted cold seed cert covers untouched rows.
 byedge=defaultdict(list)
 for j,row in enumerate(rows):
  p,t=divmod(int(row),H)
  if p<0 or p>=len(pedges):raise ValueError('original capacity row outside graph')
  byedge[int(pedges[p])].append((t,j))
 for items in byedge.values():items.sort()
 byod={int(i):np.flatnonzero(fod==i) for i in selected}
 base=np.zeros(len(rows))
 for i in range(len(od)):
  prior=[]
  for x in range(int(off[i]),int(off[i+1])):
   e=int(ae[x])
   if e in stage:prior.append(stage[e])
   if e not in byedge:continue
   times=np.asarray([t for t,j in byedge[e]],np.int32)
   positions=np.asarray([j for t,j in byedge[e]],np.int32)
   if i in byod:
    idx=byod[i];delay=np.sum(fw[idx][:,prior],axis=1,dtype=np.int64) if prior else 0
    when=fr[idx].astype(np.int64)+int(at[x])+delay
    if np.any(when<0) or np.any(when>=H):raise ValueError('cold donor original horizon')
    base[positions]+=np.bincount(when,weights=fm[idx],minlength=H)[times]
   else:base[positions]+=(hourly[i]/T)*((times>=int(at[x]))&(times<int(at[x])+T))
 caprow=cap[rows//H]
 if len(rows) and (np.max(abs(rhs-(caprow-base)))>1e-8 or np.max(base-caprow)>1e-8):
  raise ValueError('original baseline capacity reconstruction')
 after=base+A@flow
 maxexcess=float(np.max(after-caprow,initial=0));minload=float(np.min(after,initial=0))
 if maxexcess>1e-8 or minload<-1e-8:raise ValueError('full original capacity/nonnegative flow')
 increment=float(np.dot(cost,flow))
 upper=float(cold_cert['independent_feasible_primal_upper']+increment)
 if abs(upper-result['candidate_upper_pending_independent_replay'])>1e-6:
  raise ValueError('source true objective')
 reduced=cost-A.T@mu-nu[group]
 if np.min(reduced,initial=0)<-1e-6:raise ValueError('current restricted master dual sign/stationarity')
 dual=float(np.dot(rhs,mu)+np.dot(mass,nu))
 if abs(dual-increment)>1e-5:raise ValueError('current restricted primal dual')
 cert={'schema':'DEV40_FULL_EVENT_JOINT_CG_INDEPENDENT_ORIGINAL_CERT',
  'status':'PASS_FULL_ORIGINAL_PRIMAL_RESTRICTED_DUAL_OPEN_FULL_GRAPH',
  'source_hashes':hashes,'producer_result_sha256':sha(OUT/'RESULT.json'),
  'fresh_seed_certificate_sha256':sha(SEED/'fifo/INDEPENDENT_ORIGINAL_TIME_CERTIFICATE.json'),
  'original_positive_OD':len(od),'original_release_events':len(od)*T,
  'new_source_generated_columns_replayed':len(cost),'positive_generated_columns':positive_new,
  'first_action_wait_paths':first_wait,'max_path_cost_error':maxcost,
  'independent_full_original_feasible_upper':upper,'historical_best_independent_upper':result['historical_best_independent_upper_evaluation_only'],
  'max_original_capacity_excess':max(0.,maxexcess),'min_original_row_flow':minload,
  'restricted_primal_dual_gap':increment-dual,
  'full_graph_pricing_closure':'OPEN_UNLESS_SEPARATE_EXACT_SAME_FINAL_RMP_DUAL_CERT',
  'wall_seconds':time.monotonic()-began,
  'scope':'Fresh source-generated AON/FIFO base and this-run columns; complete original primal and current RMP dual only.'}
 target.write_text(json.dumps(cert,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 print(json.dumps({k:cert[k] for k in ('status','new_source_generated_columns_replayed','positive_generated_columns','independent_full_original_feasible_upper','max_original_capacity_excess','wall_seconds')}),flush=True)
if __name__=='__main__':main()
