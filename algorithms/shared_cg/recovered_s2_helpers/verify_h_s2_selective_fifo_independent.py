"""Independent original-network verifier for selective FIFO time-flow.

Runs no producer function or shared-CG code. Uses original CSV hashes, reverse
Dijkstra, full route reconstruction, per-release integer transport checks,
and exact interval load sweeps on original physical entry resources.
"""
from pathlib import Path
from collections import defaultdict
import csv,hashlib,heapq,json,math,numpy as np
R=Path(__file__).resolve().parent
CASES=('urbana_S2_H',)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def check_kernel(T,L):
 if L<T:raise ValueError('early service duration')
 for r in range(T):
  lo=r*L;hi=(r+1)*L;got=0
  for s in range(lo//T,(hi-1)//T+1):
   m=max(0,min(hi,(s+1)*T)-max(lo,s*T))
   if m and s<r:raise ValueError('pre-release departure')
   got+=m
  if got!=L:raise ValueError('hidden released demand')
 for s in range(L):
  lo=s*T;hi=(s+1)*T;got=0
  for r in range(lo//L,(hi-1)//L+1):got+=max(0,min(hi,(r+1)*L)-max(lo,r*L))
  if got!=T:raise ValueError('departure service mass')
def verify(case):
 producer=json.loads((R/f'H_S2_SELECTIVE_FIFO_CERTIFICATE_{case}.json').read_text(encoding='utf-8'))
 source=Path(producer['source_path']);expected=producer['source_hashes']
 if {n:sha(source/n) for n in expected}!=expected:raise ValueError('source hash drift')
 path=Path(producer['path_file'])
 if sha(path)!=producer['path_sha256']:raise ValueError('path SHA drift')
 a=np.load(path);off=a['od_edge_offset'];flat=a['edge_index'];entry=a['entry_offset_steps'];pq=a['od_hourly_pce'];pc=a['od_static_shortest_cost'];li=a['od_departure_steps']
 net=read(source/'network.csv');acc=read(source/'access.csv');od=read(source/'assignment_od_pce.csv')
 zone={r['zone_id']:r['node_id'] for r in acc}
 if len(zone)!=len(acc) or len(od)!=len(pq) or len(off)!=len(od)+1:raise ValueError('OD/access mapping')
 T=int(producer['release_steps']);H=int(producer['horizon_steps']);dt=float(producer['dt_seconds']);factor=float(producer['demand_factor'])
 if T<=0 or abs(T*dt-3600)>1e-8:raise ValueError('time precision')
 lengths=sorted({int(x) for x in li})
 for L in lengths:check_kernel(T,L)
 nodes=sorted({r['from_node_id'] for r in net}|{r['to_node_id'] for r in net});ix={n:i for i,n in enumerate(nodes)}
 u=np.array([ix[r['from_node_id']] for r in net],dtype=np.int32);v=np.array([ix[r['to_node_id']] for r in net],dtype=np.int32)
 cost=np.array([float(r['vdf_fftt']) for r in net]);cap=np.array([float(r['capacity']) for r in net]);physical=np.array([r['arc_kind']=='physical' for r in net],dtype=bool)
 if np.any(cost<0) or np.any(cap<=0):raise ValueError('original arc attributes')
 dur=np.where(physical,np.maximum(1,np.ceil(cost*60/dt-1e-12).astype(np.int32)),0)
 incoming=[[] for _ in nodes]
 for e in range(len(net)):incoming[int(v[e])].append(e)
 dests=sorted({ix[zone[r['d_zone_id']]] for r in od});trees={}
 for dest in dests:
  dist=np.full(len(nodes),np.inf);dist[dest]=0.0;h=[(0.0,dest)]
  while h:
   d,node=heapq.heappop(h)
   if d>dist[node]+1e-12:continue
   for e in incoming[node]:
    prev=int(u[e]);cand=d+float(cost[e])
    if cand<dist[prev]-1e-12:dist[prev]=cand;heapq.heappush(h,(cand,prev))
  trees[dest]=dist
 events=defaultdict(list);totalq=0.0;lower=0.0;wait=0.0;latest=0;delayed=0;delayedq=0.0
 for i,row in enumerate(od):
  q=float(row['volume_pce'])*factor;L=int(li[i]);origin=ix[zone[row['o_zone_id']]];dest=ix[zone[row['d_zone_id']]]
  if q<=0 or abs(q-float(pq[i]))>1e-9:raise ValueError('per-original-OD hourly q mismatch')
  if L>T:delayed+=1;delayedq+=q
  node=origin;t=0;value=0.0
  if int(off[i])<0 or int(off[i+1])<int(off[i]) or int(off[i+1])>len(flat):raise ValueError('path offset')
  for j in range(int(off[i]),int(off[i+1])):
   e=int(flat[j])
   if e<0 or e>=len(net) or int(u[e])!=node or int(entry[j])!=t:raise ValueError('original arc or time mapping')
   value+=float(cost[e]);node=int(v[e])
   if physical[e]:
    events[e].append((t,q/L));events[e].append((t+L,-q/L))
   t+=int(dur[e])
  if node!=dest or t+L-1>H:raise ValueError('unserved or late original commodity')
  d=float(trees[dest][origin])
  if not math.isfinite(d) or abs(d-value)>1e-7 or abs(d-float(pc[i]))>1e-7:raise ValueError('full-network shortest path')
  latest=max(latest,t+L-1);totalq+=q;lower+=q*d;wait+=q*(L-T)*dt/120
 worst=0.0;worst_e=None;worst_t=None;used=0
 for e,ev in events.items():
  ev.sort(key=lambda x:x[0]);flow=0.0;at=0;used+=len(ev)//2
  while at<len(ev):
   now=ev[at][0];delta=0.0
   while at<len(ev) and ev[at][0]==now:delta+=ev[at][1];at+=1
   flow+=delta;ratio=flow/(cap[e]*dt/3600)
   if ratio>worst:worst=ratio;worst_e=net[e]['link_id'];worst_t=now
 if worst>1+1e-9:raise ValueError('original physical time capacity excess')
 upper=lower+wait
 if abs(lower-producer['unconstrained_full_graph_lower_bound'])>1e-6 or abs(upper-producer['feasible_primal_upper_bound'])>1e-6 or latest!=producer['max_arrival_step']:
  raise ValueError('independent objective or arrival mismatch')
 result={'schema':'SHARED_CG_H_INDEPENDENT_SELECTIVE_FIFO_CERT_R1','case_id':case,
  'status':'PASS_FULL_ORIGINAL_GRAPH_FEASIBLE_UPPER_ONLY',
  'source_hashes':expected,'path_sha256':producer['path_sha256'],
  'proof_methods':['original CSV reverse Dijkstra by destination','every OD full original arc path, cost, release and terminal check','integer flow-kernel release and departure conservation for each distinct departure length','exact interval sweep of each used original physical time-entry resource'],
  'original_positive_OD':len(od),'original_release_commodities':len(od)*T,'original_network_arcs':len(net),
  'original_physical_arcs':int(np.count_nonzero(physical)),'all_original_physical_entry_rows':int(np.count_nonzero(physical))*H,
  'original_total_hourly_pce':totalq,'release_steps':T,'departure_lengths_checked':lengths,
  'selected_delayed_OD':delayed,'selected_delayed_hourly_pce':delayedq,'horizon_steps':H,'dt_seconds':dt,
  'used_physical_edge_interval_contributions':used,'max_original_capacity_ratio':worst,
  'worst_original_physical_edge_id':worst_e,'worst_entry_step':worst_t,'last_arrival_step':latest,
  'independent_full_graph_unconstrained_lower_bound':lower,'independent_feasible_primal_upper_bound':upper,
  'absolute_open_gap':upper-lower,'relative_open_gap':(upper-lower)/max(1,abs(upper)),
  'conclusion':'Constructive path-flow solves the full original demand feasibility problem, with a nonzero open optimality gap. It is not a same-build shared CG optimum.'}
 out=R/f'H_S2_SELECTIVE_FIFO_INDEPENDENT_CERTIFICATE_{case}.json'
 if out.exists():raise FileExistsError(out)
 out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 print(json.dumps({k:result[k] for k in ('case_id','status','selected_delayed_OD','max_original_capacity_ratio','independent_full_graph_unconstrained_lower_bound','independent_feasible_primal_upper_bound','relative_open_gap')},ensure_ascii=False))
for case in CASES:verify(case)

