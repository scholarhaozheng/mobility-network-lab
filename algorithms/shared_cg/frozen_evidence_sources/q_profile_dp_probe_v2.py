"""Prototype exact destination batch price profile on original time graph."""
from pathlib import Path
from collections import deque
import csv,json,math,time,heapq
import numpy as np
from numba import njit
from q_sparse_time_astar_probe import SparseTimeAStar
R=Path(__file__).resolve().parent
@njit(cache=False)
def sweep(n,H,end,dt,offsets,order,head,cost,duration,price_id,starts,ends,weights,dest,h,query_t,query_o):
 D=int(np.max(duration));ring=np.empty((D+1,n),np.float64);out=np.empty(len(query_t),np.float64);cursor=0
 for k in range(D+1):
  for j in range(n):ring[k,j]=h[j]
 for t in range(end-1,-1,-1):
  slot=t%(D+1);future=(t+1)%(D+1)
  for kk in range(n):
   node=order[kk]
   best=0.0 if node==dest else ring[future,node]+dt/60.0
   for e in range(offsets[node],offsets[node+1]):
    d=duration[e]
    if t+d>H:continue
    nxt=head[e]
    value=ring[slot,nxt] if d==0 else ring[(t+d)%(D+1),nxt]
    candidate=cost[e]+value
    j=price_id[e]
    if j>=0 and starts[j]<=t<ends[j]:candidate+=weights[j]
    if candidate<best:best=candidate
   ring[slot,node]=best
  while cursor<len(query_t) and query_t[cursor]==t:
   out[cursor]=ring[slot,query_o[cursor]];cursor+=1
 if cursor!=len(query_t):raise ValueError('unpriced query')
 return out

def read(p):
 with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def static_h(n,inc,dest):
 h=np.full(n,np.inf);steps=np.full(n,10**9,np.int32);h[dest]=0.;steps[dest]=0;heap=[(0.,0,dest)]
 while heap:
  value,t,node=heapq.heappop(heap)
  if value>h[node]+1e-10 or (abs(value-h[node])<=1e-10 and t>steps[node]):continue
  for prev,c,d in inc[node]:
   new=value+c;nt=t+d
   if new<h[prev]-1e-10 or (abs(new-h[prev])<=1e-10 and nt<steps[prev]):h[prev]=new;steps[prev]=nt;heapq.heappush(heap,(new,nt,prev))
 return h,max(int(x) for x in steps[np.isfinite(h)])
def setup(case,edge_ranges,factor):
 cfg=json.loads((R/'cases'/f'{case}__sparse_common_dev9_delayed_zero_gc.json').read_text(encoding='utf-8'));source=Path(cfg['source_dir']);net=read(source/'network.csv');acc=read(source/'access.csv');od=read(source/'assignment_od_pce.csv');nodes=sorted({x['from_node_id'] for x in net}|{x['to_node_id'] for x in net});ix={x:i for i,x in enumerate(nodes)};access={x['zone_id']:ix[x['node_id']] for x in acc};dt=float(cfg['dt_seconds']);H=int(cfg['horizon_steps']);u=np.array([ix[x['from_node_id']] for x in net],np.int32);v=np.array([ix[x['to_node_id']] for x in net],np.int32);cost=np.array([float(x['vdf_fftt']) for x in net]);physical=np.array([x[cfg['physical_field']]==cfg['physical_value'] for x in net]);dur=np.where(physical,np.maximum(1,np.ceil(cost*60/dt-1e-12).astype(np.int32)),0)
 order_edges=np.argsort(u,kind='stable');u=u[order_edges];v=v[order_edges];cost=cost[order_edges];dur=dur[order_edges];physical=physical[order_edges];inverse=np.empty(len(net),np.int32);inverse[order_edges]=np.arange(len(net));offsets=np.r_[0,np.cumsum(np.bincount(u,minlength=len(nodes)))].astype(np.int32)
 indeg=np.zeros(len(nodes),np.int32)
 for e in range(len(u)):
  if dur[e]==0:indeg[v[e]]+=1
 queue=deque(np.flatnonzero(indeg==0).tolist());topo=[]
 while queue:
  node=queue.popleft();topo.append(node)
  for e in range(offsets[node],offsets[node+1]):
   if dur[e]==0:
    nxt=v[e];indeg[nxt]-=1
    if indeg[nxt]==0:queue.append(int(nxt))
 if len(topo)!=len(nodes):raise ValueError('zero-time cycle')
 reverse=np.asarray(topo[::-1],np.int32);inc=[[] for _ in nodes]
 for e in range(len(u)):inc[v[e]].append((int(u[e]),float(cost[e]),int(dur[e])))
 price_id=np.full(len(net),-1,np.int32);starts=[];ends=[];weights=[];maxlam=max(z[3] for z in edge_ranges)
 for j,(olde,start,end,lam) in enumerate(edge_ranges):
  e=int(inverse[olde]);price_id[e]=j;starts.append(start);ends.append(end);weights.append(factor*dt/60*lam/maxlam)
 return cfg,net,od,nodes,access,u,v,cost,dur,physical,offsets,reverse,inc,price_id,np.asarray(starts,np.int32),np.asarray(ends,np.int32),np.asarray(weights),inverse

def toy():
 n=3;u=np.array([0,0,1],np.int32);v=np.array([1,2,2],np.int32);cost=np.array([1.,4.,1.]);d=np.array([1,2,1],np.int32);offsets=np.array([0,2,3,3],np.int32);order=np.array([2,1,0],np.int32);pid=np.array([0,-1,1],np.int32);s=np.array([1,1],np.int32);e=np.array([2,2],np.int32);w=np.array([10.,10.]);h=np.array([2.,1.,0.]);q=np.array([0],np.int32);o=np.array([0],np.int32);z=sweep(n,4,3,60.,offsets,order,v,cost,d,pid,s,e,w,2,h,q,o)
 if abs(z[0]-3)>1e-9:raise ValueError('toy intermediate wait')
 return float(z[0])
if __name__=='__main__':
 case='urbana_F_Q';base=R/'runs/q_interval_seed_rowgen_dual_r1'/case;du=np.load(base/'CAPACITY_CUT_DUAL.npz');ranges=[(int(e),int(t),int(t)+256,float(lam)) for e,t,lam in zip(du['original_edge_index'],du['original_entry_step'],du['original_time_lambda']) if lam>0];factor=16.;data=setup(case,ranges,factor);cfg,net,od,nodes,access,u,v,cost,dur,physical,offsets,reverse,inc,pid,starts,ends,weights,inverse=data
 dest=access[od[3]['d_zone_id']];orig=access[od[3]['o_zone_id']];h,maxsteps=static_h(len(nodes),inc,dest);terminal=int(max(ends));D=int(max(dur))
 if terminal+D+maxsteps>cfg['horizon_steps']:raise ValueError('terminal static boundary unproved')
 q=np.array([779,907,1034],np.int32);origins=np.full(len(q),orig,np.int32);started=time.monotonic();value=sweep(len(nodes),int(cfg['horizon_steps']),terminal,float(cfg['dt_seconds']),offsets,reverse,v,cost,dur,pid,starts,ends,weights,dest,h,q[::-1],origins[::-1]);secs=time.monotonic()-started
 astar=SparseTimeAStar(len(nodes),np.array([inverse[e] for e in range(len(net))]),np.array([inverse[e] for e in range(len(net))]),cost,dur,physical,float(cfg['dt_seconds']),int(cfg['horizon_steps'])) if False else None
 print(json.dumps({'status':'PROFILE_PROTOTYPE_COMPLETED','toy':toy(),'case':case,'dest':dest,'origin':orig,'max_static_duration':maxsteps,'terminal':terminal,'queries':q[::-1].tolist(),'values':value.tolist(),'seconds':secs}),flush=True)
