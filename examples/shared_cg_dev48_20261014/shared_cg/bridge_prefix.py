"""Source-driven exact prefix paths at a fixed service time of one queued edge.

This is a candidate oracle. Final CG pricing must still cover the full graph.
No previously solved route, flow, or dual is consumed.
"""
from dataclasses import dataclass
import numpy as np
from numba import njit


@njit(cache=False)
def _fixed_target_dp(n,max_delta,dt,ptr,edge_order,head,cost,duration,
                     reverse_zero_topo,target,blocked,origins):
 D=int(np.max(duration))
 ring=np.full((D+1,n),np.inf,dtype=np.float64)
 action=np.full((max_delta+1,n),-3,dtype=np.int32)
 values=np.full((max_delta+1,len(origins)),np.inf,dtype=np.float64)
 for delta in range(max_delta+1):
  slot=delta%(D+1)
  for kk in range(n):
   node=int(reverse_zero_topo[kk])
   if delta==0:
    best=0. if node==target else np.inf
    chosen=-1 if node==target else -3
   else:
    best=ring[(delta-1)%(D+1),node]+dt/60.
    chosen=-2
   for pos in range(ptr[node],ptr[node+1]):
    e=int(edge_order[pos])
    if e==blocked:continue
    steps=int(duration[e])
    if steps>delta:continue
    if steps==0:next_value=ring[slot,int(head[e])]
    else:next_value=ring[(delta-steps)%(D+1),int(head[e])]
    cand=cost[e]+next_value
    if cand<best-1e-12:
     best=cand;chosen=e
   ring[slot,node]=best;action[delta,node]=chosen
  for j in range(len(origins)):
   values[delta,j]=ring[slot,int(origins[j])]
 return action,values


def exact_fixed_target_prefix(model,target,blocked,max_delta,origins):
 """Return action[remaining,node] and exact raw minimum prefix costs."""
 target=int(target);blocked=int(blocked);max_delta=int(max_delta)
 origins=np.asarray(origins,dtype=np.int32)
 if target<0 or target>=model.n or blocked<0 or blocked>=len(model.u) or max_delta<0:
  raise ValueError('fixed target/blocked edge/delay')
 if np.any(origins<0) or np.any(origins>=model.n):
  raise ValueError('prefix origin')
 order=np.lexsort((np.arange(len(model.u),dtype=np.int32),model.u))
 counts=np.bincount(model.u,minlength=model.n)
 ptr=np.r_[0,np.cumsum(counts)].astype(np.int32)
 return _fixed_target_dp(model.n,max_delta,model.dt,ptr,order.astype(np.int32),
                         model.v,model.cost,model.duration,model.reverse_topo,
                         target,blocked,origins)


@dataclass(frozen=True)
class PrefixPath:
 original_edges: np.ndarray
 original_entry_steps: np.ndarray
 prefix_raw_cost: float


def recover_fixed_prefix(model,action,origin,release,delta,target):
 """Recover one legal full-prefix edge/time sequence from the DP policy."""
 node=int(origin);t=int(release);left=int(delta);target=int(target)
 if left<0 or left>=action.shape[0] or node<0 or node>=model.n:
  raise ValueError('prefix recovery domain')
 edges=[];entry=[];raw=0.;guard=0
 while left>0 or node!=target:
  chosen=int(action[left,node])
  if chosen==-2:
   t+=1;left-=1;raw+=model.dt/60.
  elif chosen>=0:
   if int(model.u[chosen])!=node:raise ValueError('broken prefix tail')
   edges.append(chosen);entry.append(t)
   t+=int(model.duration[chosen]);left-=int(model.duration[chosen])
   raw+=float(model.cost[chosen]);node=int(model.v[chosen])
  else:raise ValueError('unreachable prefix policy')
  guard+=1
  if guard>action.shape[0]*(model.n+1) or left<0:
   raise ValueError('prefix path loop/underflow')
 if t!=int(release)+int(delta):raise ValueError('fixed prefix service time')
 return PrefixPath(np.asarray(edges,dtype=np.int32),
                   np.asarray(entry,dtype=np.int32),raw)
