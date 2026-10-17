"""Independent constructive feasible Q flow via exact uniform-release FIFO mass transport.

All original per-release commodities remain distinct. Each release interval
[r*L,(r+1)*L) in mass coordinates is intersected with departure slots
[s*T,(s+1)*T); commodity (i,r) puts q_i*m/(T*L) on path i after waiting
s-r bins at its original origin.  L>=T proves causality.  This is an
actual fractional path-flow construction on the full original time graph.
"""
from pathlib import Path
from collections import defaultdict
import csv,hashlib,heapq,json,math,numpy as np
R=Path(__file__).resolve().parent
CASES=('urbana_F_Q','urbana_S2_Q','pittsburgh_S2_Q')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(path):
 with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def solve(case):
 screen=json.loads((R/f'Q_AON_SCREEN_{case}.json').read_text(encoding='utf-8'))
 source=Path(screen['source_path']);expected=screen['source_hashes']
 if {n:sha(source/n) for n in expected}!=expected:raise ValueError('source hash drift')
 net=read(source/'network.csv');acc=read(source/'access.csv');od=read(source/'assignment_od_pce.csv')
 zone={r['zone_id']:r['node_id'] for r in acc}
 if len(zone)!=len(acc):raise ValueError('duplicate access zone')
 nodes=sorted({r['from_node_id'] for r in net}|{r['to_node_id'] for r in net});ix={x:i for i,x in enumerate(nodes)}
 u=np.array([ix[r['from_node_id']] for r in net],dtype=np.int32)
 v=np.array([ix[r['to_node_id']] for r in net],dtype=np.int32)
 cost=np.array([float(r['vdf_fftt']) for r in net],dtype=np.float64)
 caphour=np.array([float(r['capacity']) for r in net],dtype=np.float64)
 physical=np.array([r['arc_kind']=='physical' for r in net],dtype=bool)
 if np.any(cost<0) or np.any(caphour<=0):raise ValueError('invalid original edge attributes')
 dt=float(screen['dt_seconds']);T=int(screen['release_steps']);H=int(screen['horizon_steps']);factor=float(screen['demand_factor'])
 dur=np.where(physical,np.maximum(1,np.ceil(cost*60/dt-1e-12).astype(np.int32)),0)
 outgoing=[[] for _ in nodes]
 for e in range(len(net)):outgoing[int(u[e])].append(e)
 for es in outgoing:es.sort(key=lambda e:(float(cost[e]),net[e]['link_id']))
 origins=sorted({ix[zone[r['o_zone_id']]] for r in od});trees={}
 for origin in origins:
  dist=np.full(len(nodes),np.inf);pred=np.full(len(nodes),-1,dtype=np.int32)
  dist[origin]=0.0;heap=[(0.0,int(origin))]
  while heap:
   d,node=heapq.heappop(heap)
   if d>dist[node]+1e-12:continue
   for e in outgoing[node]:
    nxt=int(v[e]);cand=d+float(cost[e])
    if cand<dist[nxt]-1e-12:dist[nxt]=cand;pred[nxt]=e;heapq.heappush(heap,(cand,nxt))
  trees[origin]=(dist,pred)
 edge_total=np.zeros(len(net),dtype=np.float64);path_offsets=[0];flat=[];entry=[];q=[];shortest=[];maxduration=0
 for i,row in enumerate(od):
  origin=ix[zone[row['o_zone_id']]];dest=ix[zone[row['d_zone_id']]]
  dist,pred=trees[origin]
  if not math.isfinite(float(dist[dest])):raise ValueError('unreachable positive original OD '+str(i))
  reverse=[];node=dest
  for _ in range(len(nodes)+len(net)):
   if node==origin:break
   e=int(pred[node]);
   if e<0 or int(v[e])!=node:raise ValueError('broken predecessor tree')
   reverse.append(e);node=int(u[e])
  else:raise ValueError('path cycle')
  route=reverse[::-1];node=origin;t=0;value=0.0;amount=float(row['volume_pce'])*factor
  for e in route:
   if int(u[e])!=node:raise ValueError('path continuity')
   flat.append(e);entry.append(t);value+=float(cost[e])
   if physical[e]:edge_total[e]+=amount
   t+=int(dur[e]);node=int(v[e])
  if node!=dest or abs(value-float(dist[dest]))>1e-7:raise ValueError('path cost/terminal mismatch')
  maxduration=max(maxduration,t);q.append(amount);shortest.append(float(dist[dest]));path_offsets.append(len(flat))
 used=np.flatnonzero(edge_total>0)
 max_hourly_ratio=float(np.max(edge_total[used]/caphour[used]))
 L=max(T,int(math.ceil(T*max_hourly_ratio*(1+1e-12))))
 if maxduration+L-1>H:raise ValueError('constructed last arrival beyond frozen horizon')
 all_ratios=edge_total[used]/(L*caphour[used]*dt/3600)
 max_ratio=float(np.max(all_ratios))
 if max_ratio>1+1e-10:raise ValueError('capacity proof failed')
 # Exact integer overlap check for the common release-to-departure kernel.
 # A release interval has length L; a departure slot has length T.
 max_splits=0;last_depart=-1
 for r in range(T):
  lo=r*L;hi=(r+1)*L;s0=lo//T;s1=(hi-1)//T;mass=0
  if s0<r:raise ValueError('early departure')
  for s in range(s0,s1+1):
   overlap=max(0,min(hi,(s+1)*T)-max(lo,s*T))
   mass+=overlap
  if mass!=L:raise ValueError('per-release conservation failure')
  max_splits=max(max_splits,s1-s0+1);last_depart=max(last_depart,s1)
 if last_depart!=L-1:raise ValueError('departure horizon coverage failure')
 # Each service slot has exactly T integer mass units because [0,T*L)
 # is exactly partitioned by release intervals. This implies q_i/L
 # departing on every slot, independent of OD and without rescaling q_i.
 lower=float(np.dot(np.asarray(q),np.asarray(shortest)))
 wait_extra=float(sum(q))*(L-T)*dt/120
 upper=lower+wait_extra
 path=R/f'Q_FIFO_FEASIBLE_PATHS_{case}.npz'
 if path.exists():raise FileExistsError(path)
 np.savez_compressed(path,od_edge_offset=np.asarray(path_offsets,dtype=np.int64),edge_index=np.asarray(flat,dtype=np.int32),
  entry_offset_steps=np.asarray(entry,dtype=np.int32),od_hourly_pce=np.asarray(q,dtype=np.float64),
  od_static_shortest_cost=np.asarray(shortest,dtype=np.float64),release_steps=np.asarray([T],dtype=np.int32),
  stretched_departure_steps=np.asarray([L],dtype=np.int32))
 report={'schema':'SHARED_CG_Q_FIFO_FULL_SOURCE_FEASIBLE_R1','case_id':case,
  'status':'CONSTRUCTIVE_FEASIBLE_UPPER_BOUND_FULL_ORIGINAL_GRAPH_NOT_OPTIMAL',
  'source_hashes':expected,'source_path':str(source),'demand_factor':factor,
  'original_positive_OD':len(od),'exact_release_commodities':len(od)*T,
  'exact_hourly_pce':float(sum(q)),'dt_seconds':dt,'release_steps':T,'horizon_steps':H,
  'full_original_arcs':len(net),'physical_arcs':int(np.count_nonzero(physical)),
  'full_original_physical_entry_capacity_rows':int(np.count_nonzero(physical))*H,
  'stretched_departure_steps':L,'last_departure_step':L-1,'max_release_to_departure_splits':max_splits,
  'last_arrival_step':L-1+maxduration,'maximum_edge_hourly_demand_to_hourly_capacity':max_hourly_ratio,
  'maximum_original_physical_entry_load_to_capacity':max_ratio,
  'unconstrained_full_graph_cost_lower_bound':lower,'constructed_primal_feasible_upper_bound':upper,
  'absolute_open_gap':upper-lower,'relative_open_gap':(upper-lower)/max(1,abs(upper)),
  'path_file':str(path),'path_sha256':sha(path),
  'flow_kernel':'For original OD i, release r and departure s, flow=q_i * overlap([r*L,(r+1)*L),[s*T,(s+1)*T))/(T*L); wait s-r at origin; then use stored original-arc path. Integer overlap gives exact conservation; L>=T gives causality; per-departure flow q_i/L; all physical entry rows bounded by each edge total q/L.',
  'scientific_limit':'This is a feasible upper and independent source-driven unconstrained lower. It is not a capacitated optimum or a dev3 CG solver endpoint; Q cases remain open under the single-CG-build acceptance gate.'}
 out=R/f'Q_FIFO_FEASIBLE_CERTIFICATE_{case}.json'
 if out.exists():raise FileExistsError(out)
 out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 print(json.dumps({k:report[k] for k in ('case_id','status','stretched_departure_steps','maximum_original_physical_entry_load_to_capacity','unconstrained_full_graph_cost_lower_bound','constructed_primal_feasible_upper_bound','relative_open_gap')},ensure_ascii=False))
for case in CASES:solve(case)
