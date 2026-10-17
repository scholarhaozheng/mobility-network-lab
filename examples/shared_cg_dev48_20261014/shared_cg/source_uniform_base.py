"""Source-driven algebraic base and exact residual rows for uniform Q CG."""
from collections import Counter,defaultdict
from pathlib import Path
import hashlib
import numpy as np

def file_sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()

class UniformQBase:
 def __init__(self,model,aon_path,fifo_path):
  self.model=model;self.aon_path=Path(aon_path);self.fifo_path=Path(fifo_path)
  with np.load(aon_path,allow_pickle=False) as z:
   self.off=z['od_edge_offset'].copy();self.edge=z['edge_index'].copy()
   self.entry=z['entry_offset_steps'].copy();self.hourly=z['od_hourly_pce'].copy()
   self.short=z['od_static_shortest_cost'].copy()
  with np.load(fifo_path,allow_pickle=False) as z:
   self.fod=z['od_index'].copy();self.fr=z['release_step'].copy()
   self.fm=z['mass_pce'].copy();self.fw=z['wait_steps'].copy()
   self.stages=z['stage_original_edge_index'].copy();self.selected=z['selected_od_index'].copy()
  if len(self.hourly)!=len(model.od) or len(self.fod)!=len(self.fr) or len(self.fod)!=len(self.fm) or len(self.fod)!=len(self.fw):
   raise ValueError('source Q base dimensions')
  if np.max(abs(self.hourly-np.array([x[4] for x in model.od])))>1e-9:
   raise ValueError('original hourly demand drift')
  self.stage={int(e):j for j,e in enumerate(self.stages)}
  self.byod={int(i):np.flatnonzero(self.fod==i) for i in self.selected}
  self.user_by_edge=defaultdict(list)
  self.route=[]
  for i in range(len(model.od)):
   preceding=[];path=[]
   for k in range(int(self.off[i]),int(self.off[i+1])):
    e=int(self.edge[k]);offset=int(self.entry[k])
    if e in self.stage:preceding.append(self.stage[e])
    if model.physical_pos[e]>=0:self.user_by_edge[e].append((i,offset,tuple(preceding)))
    path.append((e,offset))
   self.route.append(path)
  self.hist={}
  self.donor_cost=self.short[self.fod]+np.sum(self.fw,axis=1,dtype=np.int64)*model.dt/60.
  self._base_rows={}
 def base_rows(self,fragment):
  f=int(fragment)
  if f in self._base_rows:return self._base_rows[f]
  i=int(self.fod[f]);r=int(self.fr[f]);wait=0;resource=[]
  for e,offset in self.route[i]:
   if e in self.stage:wait+=int(self.fw[f,self.stage[e]])
   p=int(self.model.physical_pos[e])
   if p>=0:resource.append(p*self.model.H+r+offset+wait)
  if len(self._base_rows)>20000:self._base_rows.clear()
  out=Counter(resource);self._base_rows[f]=out
  return out
 def base_toll(self,fragments,lambda_by_row):
  fragments=np.asarray(fragments,dtype=np.int64);out=np.zeros(len(fragments))
  byedge=defaultdict(dict);H=self.model.H
  for row,value in lambda_by_row.items():
   if value>0:
    p,t=divmod(int(row),H);e=int(self.model.physical_edges[p])
    byedge[e][t]=float(value)
  if not byedge:return out
  byod=defaultdict(list)
  for j,f in enumerate(fragments):byod[int(self.fod[f])].append(j)
  for i,index in byod.items():
   pos=np.asarray(index,dtype=np.int32);ff=fragments[pos]
   before=[]
   for e,offset in self.route[i]:
    if e in self.stage:before.append(self.stage[e])
    if e not in byedge:continue
    delay=np.sum(self.fw[ff][:,before],axis=1,dtype=np.int64) if before else np.zeros(len(ff),np.int64)
    times=self.fr[ff].astype(np.int64)+offset+delay
    toll=byedge[e]
    out[pos]+=np.fromiter((toll.get(int(t),0.) for t in times),dtype=np.float64,count=len(times))
  return out
 def _history(self,i,prefix):
  key=(int(i),tuple(prefix))
  if key not in self.hist:
   part=self.byod[i];delay=np.sum(self.fw[part][:,prefix],axis=1,dtype=np.int64) if prefix else 0
   times=self.fr[part].astype(np.int64)+delay
   if np.any(times<0) or np.any(times>=self.model.H):raise ValueError('original donor horizon')
   self.hist[key]=np.bincount(times,weights=self.fm[part],minlength=self.model.H)
  return self.hist[key]
 def residual_capacity(self,newrows):
  newrows=np.asarray(newrows,dtype=np.int64);out=np.empty(len(newrows))
  grouped=defaultdict(list);H=self.model.H
  for j,row in enumerate(newrows):
   p,t=divmod(int(row),H)
   if p<0 or p>=len(self.model.physical_edges):raise ValueError('original physical row outside model')
   grouped[int(self.model.physical_edges[p])].append((t,j))
  for e,parts in grouped.items():
   times=np.array([t for t,j in parts],np.int32);positions=np.array([j for t,j in parts],np.int32)
   load=np.zeros(len(times))
   for i,offset,prefix in self.user_by_edge[e]:
    if i in self.byod:
     hist=self._history(i,prefix)
     valid=(times>=offset)&(times-offset<H)
     load[valid]+=hist[times[valid]-offset]
    else:load+=(self.hourly[i]/self.model.release_steps)*((times>=offset)&(times<offset+self.model.release_steps))
   out[positions]=self.model.capacity_per_step[int(self.model.physical_pos[e])]-load
  if len(out) and np.min(out)<-1e-7:raise ValueError('independently feasible donor overloaded')
  return out
