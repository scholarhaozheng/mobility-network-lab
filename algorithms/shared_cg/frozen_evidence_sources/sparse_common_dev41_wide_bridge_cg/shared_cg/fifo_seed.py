"""Exact source-audited FIFO feasible-column loader for the shared CG core.

The input is a compact constructive route schedule, not an old LP/CG state.
Every original release commodity is expanded into its legitimate fractional
wait-then-travel paths and validated in the original model before Phase II.
"""
from pathlib import Path
import hashlib,math
import numpy as np
from shared_cg.implicit_graph import PathColumn

def load_fifo_seed(model,path,expected_sha256):
 path=Path(path)
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 if h.hexdigest()!=expected_sha256:raise ValueError('FIFO seed SHA256 drift')
 a=np.load(path,allow_pickle=False)
 required={'od_edge_offset','edge_index','entry_offset_steps','od_hourly_pce','od_static_shortest_cost','od_departure_steps'}
 if set(a.files)!=required:raise ValueError('FIFO seed fields changed')
 off=a['od_edge_offset'];edge=a['edge_index'];entry=a['entry_offset_steps'];q=a['od_hourly_pce'];pc=a['od_static_shortest_cost'];lengths=a['od_departure_steps']
 OD=len(model.od);T=model.release_steps
 if len(q)!=OD or len(off)!=OD+1 or len(lengths)!=OD or len(edge)!=len(entry):raise ValueError('FIFO seed shape')
 if int(off[0])!=0 or int(off[-1])!=len(edge) or np.any(np.diff(off)<0):raise ValueError('FIFO seed offsets')
 if np.any(lengths<T) or np.any(lengths>model.H):raise ValueError('FIFO seed departure length outside model')
 columns=[];weights=[];qgot=np.zeros(model.K,dtype=np.float64);loads={};max_arrival=0
 for i in range(OD):
  qi=float(q[i]);o,d,origin,dest,original_q=model.od[i]
  if abs(qi-original_q)>1e-9:raise ValueError('FIFO seed original demand mismatch')
  route=np.asarray(edge[int(off[i]):int(off[i+1])],dtype=np.int32)
  offsets=np.asarray(entry[int(off[i]):int(off[i+1])],dtype=np.int32)
  node=int(origin);time=0;value=0.0
  for j,e0 in enumerate(route):
   e=int(e0)
   if e<0 or e>=len(model.u) or int(model.u[e])!=node or int(offsets[j])!=time:
    raise ValueError('FIFO seed original route mapping')
   value+=float(model.cost[e]);time+=int(model.duration[e]);node=int(model.v[e])
  if node!=int(dest) or abs(value-float(pc[i]))>1e-7:raise ValueError('FIFO seed route terminal or cost')
  L=int(lengths[i])
  if L-1+time>model.H:raise ValueError('FIFO seed late terminal')
  max_arrival=max(max_arrival,L-1+time)
  physical=np.flatnonzero(model.physical_pos[route]>=0)
  base_res=model.physical_pos[route[physical]]*model.H+offsets[physical]
  for r in range(T):
   commodity=i*T+r;first=(r*L)//T;last=((r+1)*L-1)//T
   for s in range(first,last+1):
    mass=max(0,min((r+1)*L,(s+1)*T)-max(r*L,s*T))
    if mass<=0:continue
    if s<r:raise ValueError('FIFO seed pre-release departure')
    flow=qi*mass/(T*L)
    pairs=np.empty(2*(s-r+len(route)),dtype=np.int32)
    for w in range(s-r):pairs[2*w]=-2;pairs[2*w+1]=r+w
    start=2*(s-r)
    for j,e in enumerate(route):pairs[start+2*j]=int(e);pairs[start+2*j+1]=s+int(offsets[j])
    resources=np.asarray(base_res+s,dtype=np.int32)
    raw=value+(s-r)*model.wait_cost
    identity=hashlib.blake2b(pairs.tobytes(),digest_size=16).hexdigest()
    columns.append(PathColumn(commodity,raw,resources,pairs,raw,identity));weights.append(flow)
    qgot[commodity]+=flow
    for resource in resources:
     key=int(resource);loads[key]=loads.get(key,0.0)+flow
 residual=float(np.max(np.abs(qgot-model.q)))
 if residual>1e-8:raise ValueError(f'FIFO seed event conservation {residual}')
 used=np.fromiter(loads.keys(),dtype=np.int64,count=len(loads))
 amount=np.fromiter(loads.values(),dtype=np.float64,count=len(loads))
 cap=model.capacity_for_rows(used)
 excess=float(np.max(amount-cap)) if len(used) else 0.0
 if excess>1e-8:raise ValueError(f'FIFO seed physical capacity excess {excess}')
 return columns,np.asarray(weights,dtype=np.float64),{
  'seed_path':str(path),'seed_sha256':expected_sha256,
  'original_positive_OD':OD,'original_release_events':model.K,
  'seed_path_columns':len(columns),'seed_positive_path_columns':int(np.count_nonzero(np.asarray(weights)>0)),
  'seed_max_event_demand_residual':residual,'seed_max_capacity_excess':max(0.0,excess),
  'seed_used_capacity_rows':len(used),'seed_last_arrival_step':max_arrival,
  'seed_primal_cost':float(sum(x.objective_cost*w for x,w in zip(columns,weights)))}
