"""Deterministic, demand-aware streaming selection for full-event CG pricing.

Each original OD/window contributes at most its permitted number of negative
reduced-cost events before the global window cap is applied. This preserves
eligible OD diversity that a destination-first top-K truncation can discard.
"""
from dataclasses import dataclass
from collections import defaultdict
import numpy as np


@dataclass(frozen=True)
class SelectedEvent:
 score: float
 key: int
 adjusted_cost: float
 od: int
 release: int
 window: int


class StreamingEventSelector:
 def __init__(self, release_steps, *, window_steps=2048, chosen_windows=4,
              per_window=80, per_od_window=4, total=320, epsilon=1e-6):
  self.release_steps=int(release_steps)
  self.window_steps=int(window_steps)
  self.chosen_windows=int(chosen_windows)
  self.per_window=int(per_window)
  self.per_od_window=int(per_od_window)
  self.total=int(total)
  self.epsilon=float(epsilon)
  if min(self.release_steps,self.window_steps,self.chosen_windows,self.per_window,self.per_od_window,self.total)<=0:
   raise ValueError('selection resource policy')
  self.window_count=(self.release_steps+self.window_steps-1)//self.window_steps
  self.best=np.full(self.window_count,np.inf)
  self.pool=[]
  self.events_priced=0
  self.negative_events=0
  self.minimum_reduced_cost=0.

 def add(self, keys, od, release, mass, adjusted, donor_cost, donor_toll, group_mu):
  keys=np.asarray(keys,dtype=np.int64)
  od=np.asarray(od,dtype=np.int32)
  release=np.asarray(release,dtype=np.int32)
  mass=np.asarray(mass,dtype=np.float64)
  adjusted=np.asarray(adjusted,dtype=np.float64)
  donor_cost=np.asarray(donor_cost,dtype=np.float64)
  donor_toll=np.asarray(donor_toll,dtype=np.float64)
  group_mu=np.asarray(group_mu,dtype=np.float64)
  if not all(len(a)==len(keys) for a in (od,release,mass,adjusted,donor_cost,donor_toll,group_mu)):
   raise ValueError('selection event dimension')
  if np.any(release<0) or np.any(release>=self.release_steps) or np.any(mass<=0):
   raise ValueError('release or mass')
  reduced=adjusted-donor_cost-donor_toll-group_mu
  if not np.all(np.isfinite(reduced)):
   raise ValueError('nonfinite reduced cost')
  score=reduced*mass
  self.events_priced+=len(keys)
  self.minimum_reduced_cost=min(self.minimum_reduced_cost,float(np.min(reduced,initial=0.)))
  negative=reduced<-self.epsilon
  self.negative_events+=int(np.count_nonzero(negative))
  if not np.any(negative):return
  window=release//self.window_steps
  for i in np.unique(od[negative]):
   by_od=np.flatnonzero(negative&(od==i))
   for w in np.unique(window[by_od]):
    pos=by_od[window[by_od]==w]
    order=np.lexsort((keys[pos],score[pos]))[:self.per_od_window]
    take=pos[order]
    self.best[int(w)]=min(self.best[int(w)],float(score[take[0]]))
    self.pool.extend(SelectedEvent(float(score[j]),int(keys[j]),float(adjusted[j]),
                                   int(od[j]),int(release[j]),int(w)) for j in take)

 def select(self):
  windows=set(map(int,np.argsort(self.best,kind='stable')[:self.chosen_windows]))
  candidates=sorted((x for x in self.pool if x.window in windows),
                    key=lambda x:(x.score,x.key))
  selected=[];per_window=defaultdict(int);per_od_window=defaultdict(int)
  for x in candidates:
   if per_window[x.window]>=self.per_window or per_od_window[(x.od,x.window)]>=self.per_od_window:
    continue
   selected.append(x);per_window[x.window]+=1;per_od_window[(x.od,x.window)]+=1
   if len(selected)>=self.total:break
  return selected,sorted(windows)
