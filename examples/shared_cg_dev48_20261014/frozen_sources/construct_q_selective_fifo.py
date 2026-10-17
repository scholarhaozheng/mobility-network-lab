"""Construct a selective FIFO Q feasible flow without changing any input.

All OD users of any overloaded shortest-path physical edge are selected before
construction.  Only their original per-release flow is delayed via the exact
integer-overlap kernel.  A conservative sum-of-rates inequality certifies all
physical time-entry rows even when travel offsets differ.
"""
from pathlib import Path
from collections import defaultdict
import csv,hashlib,json,math,numpy as np
R=Path(__file__).resolve().parent
CASES=('urbana_F_Q','urbana_S2_Q','pittsburgh_S2_Q')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def solve(case):
 parent=json.loads((R/f'Q_FIFO_FEASIBLE_CERTIFICATE_{case}.json').read_text(encoding='utf-8'))
 source=Path(parent['source_path']);path=Path(parent['path_file'])
 if sha(path)!=parent['path_sha256']:raise ValueError('parent paths drift')
 with (source/'network.csv').open(encoding='utf-8-sig',newline='') as f:net=list(csv.DictReader(f))
 a=np.load(path);off=a['od_edge_offset'];edge=a['edge_index'];entry=a['entry_offset_steps'];q=a['od_hourly_pce'];cost=a['od_static_shortest_cost']
 cap=np.array([float(r['capacity']) for r in net]);physical=np.array([r['arc_kind']=='physical' for r in net])
 dt=float(parent['dt_seconds']);T=int(parent['release_steps']);H=int(parent['horizon_steps'])
 edge_total=np.zeros(len(net));users=[set() for _ in net];maxdur=np.zeros(len(q),dtype=np.int32)
 duration=np.array([max(1,math.ceil(float(r['vdf_fftt'])*60/dt-1e-12)) if physical[e] else 0 for e,r in enumerate(net)],dtype=np.int32)
 for i in range(len(q)):
  t=0
  for j in range(int(off[i]),int(off[i+1])):
   e=int(edge[j]);
   if int(entry[j])!=t:raise ValueError('parent entry offset drift')
   if physical[e]:edge_total[e]+=float(q[i]);users[e].add(i)
   t+=int(duration[e])
  maxdur[i]=t
 over=np.flatnonzero(edge_total>cap*(1+1e-10))
 selected=set().union(*(users[int(e)] for e in over)) if len(over) else set()
 ratio=float(np.max(edge_total[physical]/cap[physical]))
 L=max(T,int(math.ceil(T*ratio*(1+1e-12))))
 lengths=np.full(len(q),T,dtype=np.int32)
 if selected:lengths[list(selected)]=L
 if np.any(lengths+maxdur-1>H):raise ValueError('horizon overflow')
 conservative_load=np.zeros(len(net))
 events=defaultdict(list)
 for i in range(len(q)):
  li=int(lengths[i]);rate=float(q[i])/li
  for j in range(int(off[i]),int(off[i+1])):
   e=int(edge[j]);
   if physical[e]:
    conservative_load[e]+=rate
    t=int(entry[j]);events[e].append((t,rate));events[e].append((t+li,-rate))
 used=np.flatnonzero(conservative_load>0)
 capstep=cap*dt/3600
 bound_ratio=float(np.max(conservative_load[used]/capstep[used]))
 if bound_ratio>1+1e-9:raise ValueError('conservative all-time capacity bound failed')
 actual=0.0;worste=None;worstt=None
 for e,ev in events.items():
  ev.sort();flow=0;at=0
  while at<len(ev):
   now=ev[at][0];delta=0
   while at<len(ev) and ev[at][0]==now:delta+=ev[at][1];at+=1
   flow+=delta;rr=flow/capstep[e]
   if rr>actual:actual=rr;worste=net[e]['link_id'];worstt=now
 lower=float(np.dot(q,cost))
 wait=float(np.dot(q,lengths.astype(np.float64)-T))*dt/120
 upper=lower+wait
 outpath=R/f'Q_SELECTIVE_FIFO_PATHS_{case}.npz'
 if outpath.exists():raise FileExistsError(outpath)
 np.savez_compressed(outpath,od_edge_offset=off,edge_index=edge,entry_offset_steps=entry,
  od_hourly_pce=q,od_static_shortest_cost=cost,od_departure_steps=lengths)
 cert={'schema':'SHARED_CG_Q_SELECTIVE_FIFO_FEASIBLE_R1','case_id':case,
  'status':'CONSTRUCTIVE_FEASIBLE_UPPER_BOUND_FULL_ORIGINAL_GRAPH_NOT_OPTIMAL',
  'source_path':str(source),'source_hashes':parent['source_hashes'],'demand_factor':parent['demand_factor'],
  'original_positive_OD':len(q),'original_release_commodities':len(q)*T,'release_steps':T,
  'dt_seconds':dt,'horizon_steps':H,'selected_delayed_OD':len(selected),
  'selected_delayed_hourly_pce':float(sum(q[list(selected)])) if selected else 0.0,
  'conservative_original_edge_bottlenecks':len(over),'selected_stretched_departure_steps':L,
  'max_original_arc_path_duration_steps':int(np.max(maxdur)),
  'max_arrival_step':int(np.max(lengths+maxdur-1)),
  'max_capacity_ratio_conservative_all_time_upper':bound_ratio,
  'max_capacity_ratio_exact_interval_sweep':actual,
  'worst_original_physical_edge_id':worste,'worst_entry_step':worstt,
  'unconstrained_full_graph_lower_bound':lower,'feasible_primal_upper_bound':upper,
  'absolute_open_gap':upper-lower,'relative_open_gap':(upper-lower)/max(1,abs(upper)),
  'path_file':str(outpath),'path_sha256':sha(outpath),
  'flow_kernel':'Each original OD i has L_i=T or stretched L. For release r and departure s, flow=q_i*overlap([r*L_i,(r+1)*L_i),[s*T,(s+1)*T))/(T*L_i), waiting s-r at original origin, then stored source path. No original release event omitted.',
  'selection_rule':'Select every OD using any original physical edge whose total source shortest-route hourly demand exceeds its original hourly capacity. Give only selected OD the common L=ceil(T*max_e(edge_total/cap_e)); all other OD retain L_i=T. The conservative per-edge sum q_i/L_i is <= original per-step capacity.',
  'scientific_limit':'Source-driven feasible upper and unconstrained lower only; no capacitated optimum or same CG build pass.'}
 out=R/f'Q_SELECTIVE_FIFO_CERTIFICATE_{case}.json'
 if out.exists():raise FileExistsError(out)
 out.write_text(json.dumps(cert,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 print(json.dumps({k:cert[k] for k in ('case_id','selected_delayed_OD','selected_delayed_hourly_pce','max_capacity_ratio_exact_interval_sweep','unconstrained_full_graph_lower_bound','feasible_primal_upper_bound','relative_open_gap')}))
for case in CASES:solve(case)
