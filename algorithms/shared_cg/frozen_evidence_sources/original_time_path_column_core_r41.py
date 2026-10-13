"""Reusable original time-path column: complete path validation and physical capacity row incidence."""
from collections import defaultdict
import heapq,math
import numpy as np
def network_arrays(rows,dt,physical_field="arc_kind",physical_value="physical"):
 u=[x["from_node_id"] for x in rows];v=[x["to_node_id"] for x in rows]
 c=np.array([float(x["vdf_fftt"]) for x in rows],np.float64)
 physical=np.array([x[physical_field]==physical_value for x in rows],np.bool_)
 duration=np.where(physical,np.maximum(1,np.ceil(c*60./dt-1e-12).astype(np.int32)),0)
 return u,v,c,physical,duration
def static_suffix(rows,origin,destination,start_step,dt,horizon,physical_field="arc_kind",physical_value="physical"):
 """Return original edge IDs and entry steps of min-cost, shortest-duration static suffix."""
 u,v,c,physical,dur=network_arrays(rows,dt,physical_field,physical_value);incoming=defaultdict(list)
 for e,node in enumerate(v):incoming[node].append(e)
 best={destination:(0.,0)};nxt={};heap=[(0.,0,destination)]
 while heap:
  val,steps,node=heapq.heappop(heap)
  old=best.get(node,(math.inf,2**62))
  if val>old[0]+1e-10 or (abs(val-old[0])<=1e-10 and steps>old[1]):continue
  for e in incoming[node]:
   prev=u[e];cand=(val+float(c[e]),steps+int(dur[e]));prior=best.get(prev,(math.inf,2**62))
   if cand[0]<prior[0]-1e-10 or (abs(cand[0]-prior[0])<=1e-10 and cand[1]<prior[1]):
    best[prev]=cand;nxt[prev]=e;heapq.heappush(heap,(cand[0],cand[1],prev))
 if origin not in best:raise ValueError("static tail unreachable")
 edge=[];entry=[];node=origin;t=int(start_step)
 while node!=destination:
  if node not in nxt:raise ValueError("static tail incomplete")
  e=nxt[node];edge.append(e);entry.append(t);t+=int(dur[e]);node=v[e]
  if len(edge)>len(rows):raise ValueError("static tail cycle")
 if t>horizon:raise ValueError("static tail exceeds horizon")
 return np.asarray(edge,np.int32),np.asarray(entry,np.int32),float(best[origin][0]),t
def replay_column(rows,edge_index,entry_step,origin,destination,release_step,dt,horizon,price=None,physical_field="arc_kind",physical_value="physical"):
 """Validate one original time-expanded path and return a sparse physical resource column."""
 u,v,c,physical,dur=network_arrays(rows,dt,physical_field,physical_value)
 if len(edge_index)!=len(entry_step):raise ValueError("arc/entry length")
 node=origin;t=int(release_step);base=0.;priced=0.;resource={};physical_actions=0
 for ee,tt in zip(edge_index,entry_step):
  e=int(ee);entry=int(tt)
  if e<0 or e>=len(rows) or entry<t or entry>=horizon or u[e]!=node:raise ValueError("original arc continuity or time")
  waiting=(entry-t)*dt/60.;base+=waiting+float(c[e]);priced+=waiting+float(c[e])
  if price is not None:priced+=float(price(e,entry))
  if physical[e]:
   key=int(e)*int(horizon)+entry;resource[key]=resource.get(key,0)+1;physical_actions+=1
  node=v[e];t=entry+int(dur[e])
 if node!=destination or t>horizon:raise ValueError("original destination or horizon")
 keys=np.array(sorted(resource),np.int64);counts=np.array([resource[int(k)] for k in keys],np.int32)
 return {"base_cost_minutes":base,"adjusted_cost_minutes":priced,"arrival_step":t,"physical_actions":physical_actions,"capacity_row_key":keys,"capacity_row_coefficient":counts,"capacity_row_count":len(keys),"max_same_time_resource_coefficient":int(max(counts)) if len(counts) else 0}