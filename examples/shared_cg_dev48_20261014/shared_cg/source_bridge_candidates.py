"""Construct legal fixed-bridge prefix alternatives from the current source seed.

The bridge is selected by mass-weighted FIFO wait, with source edge ID only as
a deterministic tie break. No historical candidate path or solved flow enters.
This is a partial column oracle; full-graph pricing remains mandatory.
"""
from collections import defaultdict
import numpy as np

from .bridge_prefix import exact_fixed_target_prefix,recover_fixed_prefix


class SourceBridgePrefixCandidates:
 def __init__(self,model,base):
  self.model=model;self.base=base
  if len(base.stages)==0 or base.fw.shape[1]!=len(base.stages):
   raise ValueError('no source FIFO stage')
  work=np.sum(base.fw*base.fm[:,None],axis=0,dtype=np.float64)
  order=sorted(range(len(work)),key=lambda j:(-float(work[j]),int(base.stages[j])))
  self.stage_index=int(order[0]);self.edge=int(base.stages[self.stage_index])
  self.weighted_wait_steps=float(work[self.stage_index])
  if self.weighted_wait_steps<=0 or model.physical_pos[self.edge]<0:
   raise ValueError('no positive physical queued bridge')
  self.tail=int(model.u[self.edge])
  self.od_route={}
  self.excluded_repeated_bridge_OD=[]
  for i in sorted(base.byod):
   route=base.route[i]
   positions=[k for k,(e,off) in enumerate(route) if e==self.edge]
   if len(positions)>1:
    self.excluded_repeated_bridge_OD.append(int(i));continue
   if not positions:continue
   b=positions[0]
   prefix_stage=[base.stage[e] for e,off in route[:b+1] if e in base.stage]
   after_stage=[base.stage[e] for e,off in route[b+1:] if e in base.stage]
   suffix_raw=sum(float(model.cost[e]) for e,off in route[b:])
   self.od_route[int(i)]=(b,int(route[b][1]),tuple(prefix_stage),
                          tuple(after_stage),float(suffix_raw))
  if not self.od_route:raise ValueError('queued bridge absent from source AON paths')
  eligible=np.flatnonzero(np.isin(base.fod,np.asarray(sorted(self.od_route),np.int32))).astype(np.int32)
  self.eligible=eligible
  self.delay=np.full(len(base.fod),-1,dtype=np.int32)
  self.candidate_unit=np.full(len(base.fod),np.inf,dtype=np.float64)
  self.origin_od=np.asarray(sorted(self.od_route),dtype=np.int32)
  origins=np.asarray([model.od[int(i)][2] for i in self.origin_od],dtype=np.int32)
  self.origin_column={int(i):j for j,i in enumerate(self.origin_od)}
  for i in self.origin_od:
   idx=eligible[base.fod[eligible]==i]
   b,offset,prior,after,suffix=self.od_route[int(i)]
   wait=np.sum(base.fw[idx][:,prior],axis=1,dtype=np.int64) if prior else 0
   self.delay[idx]=offset+wait
  if np.any(self.delay[eligible]<0):raise ValueError('bridge delay mapping')
  self.max_delay=int(np.max(self.delay[eligible]))
  self.action,self.profile=exact_fixed_target_prefix(model,self.tail,self.edge,
                                                      self.max_delay,origins)
  for i in self.origin_od:
   idx=eligible[base.fod[eligible]==i]
   b,offset,prior,after,suffix=self.od_route[int(i)]
   downstream=np.sum(base.fw[idx][:,after],axis=1,dtype=np.int64) if after else 0
   self.candidate_unit[idx]=(self.profile[self.delay[idx],self.origin_column[int(i)]]+
                             suffix+downstream*model.dt/60.)
  if np.any(~np.isfinite(self.candidate_unit[eligible])):
   raise ValueError('original queued bridge prefix unreachable')
  self.saving=base.donor_cost-self.candidate_unit

 def select(self,*,max_events=320,per_od_window=4,window_steps=2048,
            chosen_windows=4,max_per_window=80,min_saving=1e-9):
  if min(max_events,per_od_window,window_steps,chosen_windows,max_per_window)<=0:
   raise ValueError('bridge selection policy')
  score=self.saving*self.base.fm
  candidates=[];best=defaultdict(lambda:-np.inf)
  good=self.eligible[self.saving[self.eligible]>min_saving]
  for i in self.origin_od:
   idx=good[self.base.fod[good]==i]
   if not len(idx):continue
   windows=self.base.fr[idx]//window_steps
   for w in np.unique(windows):
    loc=idx[windows==w]
    ranked=loc[np.lexsort((loc,-score[loc]))[:per_od_window]]
    best[int(w)]=max(best[int(w)],float(score[ranked[0]]))
    candidates.extend((float(score[f]),int(f),int(i),int(w)) for f in ranked)
  windows=set(w for w,value in sorted(best.items(),key=lambda pair:(-pair[1],pair[0]))[:chosen_windows])
  candidates.sort(key=lambda item:(-item[0],item[1]))
  selected=[];used=defaultdict(int)
  for score,f,i,w in candidates:
   if w not in windows or used[w]>=max_per_window:continue
   selected.append(f);used[w]+=1
   if len(selected)>=max_events:break
  return np.asarray(selected,dtype=np.int32),sorted(windows)

 def recover(self,fragment):
  f=int(fragment)
  if f<0 or f>=len(self.base.fod) or self.delay[f]<0:
   raise ValueError('fragment not in source bridge domain')
  i=int(self.base.fod[f]);release=int(self.base.fr[f])
  prefix=recover_fixed_prefix(self.model,self.action,int(self.model.od[i][2]),
                              release,int(self.delay[f]),self.tail)
  b,offset,prior,after,suffix=self.od_route[i]
  edges=list(map(int,prefix.original_edges));entry=list(map(int,prefix.original_entry_steps))
  wait=0
  for k,(e,off) in enumerate(self.base.route[i]):
   if e in self.base.stage:wait+=int(self.base.fw[f,self.base.stage[e]])
   if k>=b:
    edges.append(int(e));entry.append(release+int(off)+wait)
  if entry[len(prefix.original_entry_steps)]!=release+int(self.delay[f]):
   raise ValueError('bridge service time drift')
  raw=float(prefix.prefix_raw_cost+suffix+
            (np.sum(self.base.fw[f,list(after)]) if after else 0)*self.model.dt/60.)
  if abs(raw-self.candidate_unit[f])>1e-7:
   raise ValueError('bridge DP and recovered path cost mismatch')
  if entry and max(entry)>self.model.H:
   raise ValueError('candidate beyond original horizon')
  return np.asarray(edges,dtype=np.int32),np.asarray(entry,dtype=np.int32),raw
