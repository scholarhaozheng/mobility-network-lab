"""Exact algebraic base interface for every original uniform-release event.

The cold FIFO seed splits some original OD/release commodities into fragments.
All other commodities remain algebraic AON paths. A fragment key is its FIFO
index; an unsplit key is n_fragments + OD_index * T + release_step. Keys for
FIFO-managed OD are invalid in the latter range, preventing demand duplication.
"""
from collections import Counter, defaultdict
import numpy as np

from .source_uniform_base import UniformQBase


class FullUniformQBase(UniformQBase):
 def __init__(self, model, aon_path, fifo_path):
  super().__init__(model, aon_path, fifo_path)
  self.n_fragments=len(self.fod)
  self.T=int(model.release_steps)
  self.unsplit_od=np.asarray([i for i in range(len(model.od)) if i not in self.byod],dtype=np.int32)
  if np.any(self.fm<=0) or np.any(self.fr<0) or np.any(self.fr>=self.T):
   raise ValueError('FIFO fragment release or mass')
  for i in self.selected:
   idx=self.byod[int(i)]
   mass=np.bincount(self.fr[idx],weights=self.fm[idx],minlength=self.T)
   if len(mass)!=self.T or np.max(np.abs(mass-self.hourly[int(i)]/self.T))>1e-10:
    raise ValueError('FIFO fragments do not partition original OD/releases')

 def unsplit_key(self, od_index, release_step):
  i=int(od_index);r=int(release_step)
  if i<0 or i>=len(self.hourly) or i in self.byod or r<0 or r>=self.T:
   raise ValueError('not an unsplit original event')
  return self.n_fragments+i*self.T+r

 def event(self, key):
  k=int(key)
  if 0<=k<self.n_fragments:
   return int(self.fod[k]),int(self.fr[k]),float(self.fm[k]),float(self.donor_cost[k])
  x=k-self.n_fragments;i,r=divmod(x,self.T)
  if x<0 or i<0 or i>=len(self.hourly) or i in self.byod:
   raise ValueError('invalid or duplicate original event key')
  return i,r,float(self.hourly[i]/self.T),float(self.short[i])

 def event_arrays(self, keys):
  keys=np.asarray(keys,dtype=np.int64)
  fragment=(keys>=0)&(keys<self.n_fragments)
  x=keys-self.n_fragments
  i=np.empty(len(keys),dtype=np.int32);r=np.empty(len(keys),dtype=np.int32)
  m=np.empty(len(keys),dtype=np.float64);c=np.empty(len(keys),dtype=np.float64)
  i[fragment]=self.fod[keys[fragment]];r[fragment]=self.fr[keys[fragment]]
  m[fragment]=self.fm[keys[fragment]];c[fragment]=self.donor_cost[keys[fragment]]
  i[~fragment]=x[~fragment]//self.T;r[~fragment]=x[~fragment]%self.T
  if np.any(keys<0) or np.any(i<0) or np.any(i>=len(self.hourly)) or any(int(v) in self.byod for v in np.unique(i[~fragment])):
   raise ValueError('invalid or duplicate original event keys')
  m[~fragment]=self.hourly[i[~fragment]]/self.T;c[~fragment]=self.short[i[~fragment]]
  return i,r,m,c

 def base_rows(self, key):
  k=int(key)
  if k<self.n_fragments:return super().base_rows(k)
  i,r,_,_=self.event(k)
  out=Counter()
  for e,offset in self.route[i]:
   p=int(self.model.physical_pos[e])
   if p>=0:out[p*self.model.H+r+offset]+=1
  return out

 def base_toll_keys(self, keys, lambda_by_row):
  keys=np.asarray(keys,dtype=np.int64)
  out=np.zeros(len(keys),dtype=np.float64)
  fragment=(keys>=0)&(keys<self.n_fragments)
  if np.any(fragment):out[fragment]=super().base_toll(keys[fragment],lambda_by_row)
  if not np.any(~fragment) or not lambda_by_row:return out
  i,r,_,_=self.event_arrays(keys[~fragment]);where=np.flatnonzero(~fragment)
  byedge=defaultdict(lambda:np.zeros(self.model.H,dtype=np.float64))
  for row,value in lambda_by_row.items():
   if value>0:
    p,t=divmod(int(row),self.model.H)
    byedge[int(self.model.physical_edges[p])][t]=float(value)
  for od in np.unique(i):
   take=np.flatnonzero(i==od);rel=r[take]
   for e,offset in self.route[int(od)]:
    if e in byedge:out[where[take]]+=byedge[e][rel+offset]
  return out
