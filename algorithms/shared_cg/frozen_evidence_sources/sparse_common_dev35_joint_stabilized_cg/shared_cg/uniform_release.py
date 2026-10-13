"""Generic exact compressed uniform-release shortcut for nonbinding Q models.

This is part of the one shared solver build. It proves optimum only if a
source-shortest path construction satisfies every original physical time-entry
capacity. If any row overloads, it exits OPEN and does not claim a CG solve.
The unrestricted path CG remains the shared fallback for other graph types.
"""
from pathlib import Path
from collections import defaultdict
import csv,hashlib,heapq,json,math,numpy as np

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(path):
 with Path(path).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def run_uniform_release(config_path,cfg,output):
 source=Path(cfg['source_dir']);names=('network.csv','access.csv','assignment_od_pce.csv')
 hashes={n:sha(source/n) for n in names}
 if hashes!=cfg['expected_source_hashes']:raise ValueError('Q source SHA drift')
 net=read(source/'network.csv');acc=read(source/'access.csv');od=read(source/'assignment_od_pce.csv')
 if not net or not od or not acc:raise ValueError('empty original Q source')
 zone={r['zone_id']:r['node_id'] for r in acc}
 if len(zone)!=len(acc):raise ValueError('duplicate Q access zone')
 node_ids=sorted({r['from_node_id'] for r in net}|{r['to_node_id'] for r in net});ix={n:i for i,n in enumerate(node_ids)}
 if not set(zone.values())<=set(ix):raise ValueError('Q zone access node missing')
 ids=[r['link_id'] for r in net]
 if len(ids)!=len(set(ids)):raise ValueError('duplicate Q edge ID')
 u=np.array([ix[r['from_node_id']] for r in net],dtype=np.int32)
 v=np.array([ix[r['to_node_id']] for r in net],dtype=np.int32)
 cost=np.array([float(r['vdf_fftt']) for r in net],dtype=np.float64)
 caphour=np.array([float(r['capacity']) for r in net],dtype=np.float64)
 field=cfg['physical_field'];value=cfg['physical_value']
 physical=np.array([r[field]==value for r in net],dtype=bool)
 if not np.all(np.isfinite(cost)) or np.any(cost<0) or not np.all(np.isfinite(caphour)) or np.any(caphour<=0):
  raise ValueError('invalid original Q edge cost/capacity')
 dt=float(cfg['dt_seconds']);T=int(cfg['release_steps']);H=int(cfg['horizon_steps']);factor=float(cfg['demand_factor'])
 if dt<=0 or T<=0 or H<T or factor<=0 or abs(T*dt-3600)>1e-7:
  raise ValueError('Q release/time model identity')
 if len(od)*T!=int(cfg['expected_commodity_events']):raise ValueError('hidden original Q OD')
 dur=np.where(physical,np.maximum(1,np.ceil(cost*60/dt-1e-12).astype(np.int32)),0)
 # The zero-time subgraph is a DAG, matching the full time graph contract.
 zero=[[] for _ in node_ids];indeg=np.zeros(len(node_ids),dtype=np.int32)
 for e in range(len(net)):
  if dur[e]==0:zero[int(u[e])].append(e);indeg[int(v[e])]+=1
 queue=[i for i in range(len(node_ids)) if indeg[i]==0];heapq.heapify(queue);count=0
 while queue:
  n=heapq.heappop(queue);count+=1
  for e in zero[n]:
   nxt=int(v[e]);indeg[nxt]-=1
   if indeg[nxt]==0:heapq.heappush(queue,nxt)
 if count!=len(node_ids):raise ValueError('zero-time original Q subgraph cycle')
 incoming=[[] for _ in node_ids]
 for e in range(len(net)):incoming[int(v[e])].append(e)
 for es in incoming:es.sort(key=lambda e:ids[e])
 dests=sorted({ix[zone[r['d_zone_id']]] for r in od})
 trees={}
 for dest in dests:
  dist=np.full(len(node_ids),np.inf);pick=np.full(len(node_ids),-1,dtype=np.int32)
  dist[dest]=0.0;heap=[(0.0,int(dest))]
  while heap:
   d,n=heapq.heappop(heap)
   if d>dist[n]+1e-12:continue
   for e in incoming[n]:
    prev=int(u[e]);cand=d+float(cost[e])
    if cand<dist[prev]-1e-12:
     dist[prev]=cand;pick[prev]=e;heapq.heappush(heap,(cand,prev))
  trees[dest]=(dist,pick)
 events=defaultdict(list);off=[0];flat=[];entry=[];vol=[];short=[];maxarrival=0;seen_od=set()
 for i,row in enumerate(od):
  oz=row['o_zone_id'];dz=row['d_zone_id'];qi=float(row['volume_pce'])*factor
  if oz not in zone or dz not in zone or oz==dz or qi<=0 or (oz,dz) in seen_od:
   raise ValueError('bad original positive Q OD')
  seen_od.add((oz,dz));origin=ix[zone[oz]];dest=ix[zone[dz]];dist,pick=trees[dest]
  if not math.isfinite(float(dist[origin])):raise ValueError('unreachable original Q OD')
  node=origin;t=0;actual=0.0
  for _ in range(len(node_ids)+len(net)):
   if node==dest:break
   e=int(pick[node])
   if e<0 or int(u[e])!=node:raise ValueError('broken original Q shortest tree')
   flat.append(e);entry.append(t);actual+=float(cost[e])
   if physical[e]:
    amount=qi/T;events[e].append((t,amount));events[e].append((t+T,-amount))
   t+=int(dur[e]);node=int(v[e])
  else:raise ValueError('Q shortest path cycle')
  if t+T-1>H or abs(actual-float(dist[origin]))>1e-7:raise ValueError('Q arrival or shortest path')
  maxarrival=max(maxarrival,t+T-1);off.append(len(flat));vol.append(qi);short.append(float(dist[origin]))
 worst=0.0;worste=None;worstt=None;worstload=0.0;over=0
 for e,ev in events.items():
  ev.sort(key=lambda z:z[0]);at=0;load=0.0;top=0.0;top_t=0
  while at<len(ev):
   now=ev[at][0];delta=0.0
   while at<len(ev) and ev[at][0]==now:delta+=ev[at][1];at+=1
   load+=delta
   if load>top:top=load;top_t=now
  ratio=top/(caphour[e]*dt/3600)
  if ratio>1+1e-9:over+=1
  if ratio>worst:worst=ratio;worste=ids[e];worstt=top_t;worstload=top
 path=output/'UNIFORM_AON_FULL_ORIGINAL_PATHS.npz'
 np.savez_compressed(path,od_edge_offset=np.asarray(off,dtype=np.int64),edge_index=np.asarray(flat,dtype=np.int32),
  entry_offset_steps=np.asarray(entry,dtype=np.int32),od_hourly_pce=np.asarray(vol,dtype=np.float64),
  od_static_shortest_cost=np.asarray(short,dtype=np.float64))
 objective=float(np.dot(np.asarray(vol),np.asarray(short)))
 model={'schema':'SHARED_CG_COMPRESSED_UNIFORM_RELEASE_Q_MODEL_R1','case_id':cfg['case_id'],'source_hashes':hashes,
  'dt_seconds':dt,'release_steps':T,'horizon_steps':H,'demand_factor':factor,'positive_original_OD':len(od),
  'positive_original_commodity_events':len(od)*T,'original_edges':len(net),
  'original_physical_edges':int(np.count_nonzero(physical)),
  'original_physical_entry_rows':int(np.count_nonzero(physical))*H,
  'capacity_rule':'original hourly physical edge capacity * dt / 3600 at entry',
  'wait_rule':'all node-time waits cost dt / 60 minutes','sink_rule':'original destination any arrival step <= H'}
 (output/'MODEL_IDENTITY.json').write_text(json.dumps(model,indent=2)+'\n',encoding='utf-8')
 status='SOLVER_PRIMAL_DUAL_CLOSED' if over==0 else 'AON_CAPACITY_OVERLOAD_NEEDS_GENERIC_CG'
 result={'schema':'SHARED_CG_COMPRESSED_UNIFORM_AON_R1','status':status,'case_id':cfg['case_id'],'build_id':cfg['build_id'],
  'graph_type':'uniform_release_implicit','config_path':str(config_path),'config_sha256':sha(config_path),
  'source_hashes':hashes,'model':model,'path_file':str(path),'path_sha256':sha(path),
  'full_graph_unconstrained_shortest_lower_bound':objective,
  'phase_II_objective':objective if over==0 else None,
  'full_graph_lower_bound':objective if over==0 else None,
  'relative_gap_raw':0.0 if over==0 else None,
  'AON_capacity_overloaded_original_edges':over,'AON_maximum_original_capacity_ratio':worst,
  'AON_worst_original_physical_edge_id':worste,'AON_worst_entry_step':worstt,
  'AON_worst_step_load_pce':worstload,'max_release_plus_path_arrival_step':maxarrival,
  'proof_scope':'Exact optimum only when original full-graph nonnegative-cost shortest construction is feasible on every original physical time-entry resource; otherwise AON is a screen, not a solver certificate.'}
 (output/'RESULT.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 print(json.dumps({k:result[k] for k in ('case_id','status','phase_II_objective','AON_maximum_original_capacity_ratio','AON_capacity_overloaded_original_edges')},ensure_ascii=False),flush=True)
 return 0 if over==0 else 2
