"""Construct H S2 selective FIFO feasible solutions from frozen original sources.

The route sequence is read from independently checked Q shortest-path files;
all entry offsets, capacities, OD volumes, release events and horizons are
recomputed for each original 30-second H model. This does not certify CG
optimality or alter the accepted H model identity.
"""
from pathlib import Path
from collections import defaultdict
import csv,hashlib,json,math,numpy as np
R=Path(__file__).resolve().parent
PAIRS=(('urbana_S2_H','urbana_S2_Q'),('pittsburgh_S2_H','pittsburgh_S2_Q'))
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def solve(hcase,qcase):
 cfg=json.loads((R/'cases'/f'{hcase}__sparse_common_dev3_exact_fixed.json').read_text(encoding='utf-8'))
 source=Path(cfg['source_dir']);expected=cfg['expected_source_hashes']
 if {n:sha(source/n) for n in expected}!=expected:raise ValueError('source changed')
 qp=R/f'Q_SELECTIVE_FIFO_PATHS_{qcase}.npz'
 qc=json.loads((R/f'Q_SELECTIVE_FIFO_CERTIFICATE_{qcase}.json').read_text(encoding='utf-8'))
 if sha(qp)!=qc['path_sha256'] or expected!=qc['source_hashes']:raise ValueError('source or Q route mismatch')
 a=np.load(qp);off=a['od_edge_offset'];flat=a['edge_index'];q=a['od_hourly_pce'];pathcost=a['od_static_shortest_cost']
 with (source/'network.csv').open(encoding='utf-8-sig',newline='') as f:net=list(csv.DictReader(f))
 dt=float(cfg['dt_seconds']);T=int(cfg['release_steps']);H=int(cfg['horizon_steps']);factor=float(cfg['demand_factor'])
 if abs(T*dt-3600)>1e-8 or abs(factor-qc['demand_factor'])>1e-12:raise ValueError('demand/precision mismatch')
 physical=np.array([r['arc_kind']=='physical' for r in net],dtype=bool)
 cap=np.array([float(r['capacity']) for r in net])
 dur=np.array([max(1,math.ceil(float(r['vdf_fftt'])*60/dt-1e-12)) if physical[e] else 0 for e,r in enumerate(net)],dtype=np.int32)
 edge_total=np.zeros(len(net));users=[set() for _ in net];entry=np.empty(len(flat),dtype=np.int32);maxdur=np.zeros(len(q),dtype=np.int32)
 for i in range(len(q)):
  t=0
  for j in range(int(off[i]),int(off[i+1])):
   e=int(flat[j]);entry[j]=t
   if physical[e]:edge_total[e]+=float(q[i]);users[e].add(i)
   t+=int(dur[e])
  maxdur[i]=t
 over=np.flatnonzero(edge_total>cap*(1+1e-10))
 selected=set().union(*(users[int(e)] for e in over)) if len(over) else set()
 ratio=float(np.max(edge_total[physical]/cap[physical]))
 L=max(T,int(math.ceil(T*ratio*(1+1e-12))))
 lengths=np.full(len(q),T,dtype=np.int32)
 if selected:lengths[list(selected)]=L
 policy='common_stretch_clipped_to_each_OD_horizon'
 if np.any(lengths+maxdur-1>H):
  bad=np.flatnonzero(lengths+maxdur-1>H)
  lengths=np.minimum(lengths,H-maxdur+1)
  test=np.zeros(len(net))
  for i in range(len(q)):
   for j in range(int(off[i]),int(off[i+1])):
    e=int(flat[j])
    if physical[e]:test[e]+=float(q[i])/int(lengths[i])
  rr=test/(cap*dt/3600)
  print(json.dumps({'case':hcase,'status':'CLIPPED_FIFO_HORIZON_SCREEN','H':H,'L':L,'clipped_count':len(bad),'max_duration':int(np.max(maxdur)),'max_capacity_ratio':float(np.max(rr)),'over_edges':int(np.count_nonzero(rr>1+1e-9)),'bad_OD':bad[:20].tolist()}))
  if np.max(rr)>1+1e-9:
   lengths[list(selected)]=(H-maxdur+1)[list(selected)]
   policy='all_bottleneck_OD_depart_at_individual_latest_uniform_horizon'
 conservative=np.zeros(len(net));events=defaultdict(list)
 for i in range(len(q)):
  li=int(lengths[i]);rate=float(q[i])/li
  for j in range(int(off[i]),int(off[i+1])):
   e=int(flat[j])
   if physical[e]:
    conservative[e]+=rate;t=int(entry[j]);events[e].append((t,rate));events[e].append((t+li,-rate))
 used=np.flatnonzero(conservative>0);capstep=cap*dt/3600
 bound=float(np.max(conservative[used]/capstep[used]))
 if bound>1+1e-9:raise ValueError('capacity upper bound')
 actual=0.0;worste=None;worstt=None
 for e,ev in events.items():
  ev.sort();at=0;flow=0.0
  while at<len(ev):
   now=ev[at][0];delta=0
   while at<len(ev) and ev[at][0]==now:delta+=ev[at][1];at+=1
   flow+=delta;rr=flow/capstep[e]
   if rr>actual:actual=rr;worste=net[e]['link_id'];worstt=now
 lower=float(np.dot(q,pathcost));upper=lower+float(np.dot(q,lengths.astype(float)-T))*dt/120
 outpath=R/f'H_S2_SELECTIVE_FIFO_PATHS_{hcase}.npz'
 if outpath.exists():raise FileExistsError(outpath)
 np.savez_compressed(outpath,od_edge_offset=off,edge_index=flat,entry_offset_steps=entry,
  od_hourly_pce=q,od_static_shortest_cost=pathcost,od_departure_steps=lengths)
 cert={'schema':'SHARED_CG_H_S2_SELECTIVE_FIFO_FEASIBLE_R1','case_id':hcase,
  'status':'CONSTRUCTIVE_FEASIBLE_UPPER_BOUND_FULL_ORIGINAL_GRAPH_NOT_OPTIMAL',
  'source_path':str(source),'source_hashes':expected,'demand_factor':factor,
  'original_positive_OD':len(q),'original_release_commodities':len(q)*T,
  'release_steps':T,'dt_seconds':dt,'horizon_steps':H,
  'selected_delayed_OD':len(selected),'departure_policy':policy,'selected_delayed_hourly_pce':float(sum(q[list(selected)])) if selected else 0.0,
  'conservative_original_edge_bottlenecks':len(over),'selected_stretched_departure_steps':L,
  'max_original_arc_path_duration_steps':int(np.max(maxdur)),'max_arrival_step':int(np.max(lengths+maxdur-1)),
  'max_capacity_ratio_conservative_all_time_upper':bound,'max_capacity_ratio_exact_interval_sweep':actual,
  'worst_original_physical_edge_id':worste,'worst_entry_step':worstt,
  'unconstrained_full_graph_lower_bound':lower,'feasible_primal_upper_bound':upper,
  'absolute_open_gap':upper-lower,'relative_open_gap':(upper-lower)/max(1,abs(upper)),
  'path_file':str(outpath),'path_sha256':sha(outpath),
  'flow_kernel':'For each original OD i and release r, flow to departure s is q_i*integer_interval_overlap([r*L_i,(r+1)*L_i),[s*T,(s+1)*T))/(T*L_i); wait s-r at original origin, then follow stored full original edge path.',
  'scientific_limit':'Feasibility proof only, separate from sparse_common_dev3 CG. Does not resolve capacitated optimum or same-build acceptance; prior resource/round-limit receipts remain intact.'}
 out=R/f'H_S2_SELECTIVE_FIFO_CERTIFICATE_{hcase}.json'
 if out.exists():raise FileExistsError(out)
 out.write_text(json.dumps(cert,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 print(json.dumps({k:cert[k] for k in ('case_id','selected_delayed_OD','max_arrival_step','max_capacity_ratio_exact_interval_sweep','unconstrained_full_graph_lower_bound','feasible_primal_upper_bound','relative_open_gap')}))
for h,q in PAIRS:solve(h,q)



