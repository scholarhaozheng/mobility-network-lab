"""Generic original-time destination price profile for triangular and flat physical-row dual prices."""
import numpy as np
from numba import njit
@njit(cache=False)
def price_profile(n,H,end,dt,offsets,order,head,cost,duration,triangle_edge,triangle_first,triangle_price,flat_toll,dest,h,release,origin):
 D=int(np.max(duration));ring=np.empty((D+1,n),np.float64);out=np.empty(len(release),np.float64);cursor=0
 for j in range(D+1):
  for node in range(n):ring[j,node]=h[node]
 for t in range(end-1,-1,-1):
  slot=t%(D+1);future=(t+1)%(D+1)
  for k in range(n):
   node=order[k];best=0. if node==dest else ring[future,node]+dt/60.
   for e in range(offsets[node],offsets[node+1]):
    d=duration[e]
    if t+d>H:continue
    nxt=head[e];cand=cost[e]+(ring[slot,nxt] if d==0 else ring[(t+d)%(D+1),nxt])+flat_toll[e]
    if e==triangle_edge and t>=triangle_first:cand+=triangle_price[t-triangle_first]
    if cand<best:best=cand
   ring[slot,node]=best
  while cursor<len(release) and release[cursor]==t:out[cursor]=ring[slot,origin[cursor]];cursor+=1
 if cursor!=len(release):raise ValueError('unpriced original release')
 return out
