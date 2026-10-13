"""One additional legal time-DAG path from a priced shortest-path tree.

This is a column-generation acceleration, not a restricted pricing certificate:
the caller still prices every original commodity on the complete graph first.
"""
import hashlib,math
import numpy as np
from shared_cg.implicit_graph import PathColumn

def _outgoing(model):
 out=getattr(model,'_sidetrack_outgoing',None)
 if out is None:
  out=[[] for _ in range(model.n)]
  for e,node in enumerate(model.u):out[int(node)].append(e)
  for edges in out:edges.sort(key=lambda e:model.edge_ids[e])
  model._sidetrack_outgoing=out
 return out

def _advance(model,node,t,action):
 if action==-2:
  if t>=model.H:raise ValueError('wait beyond horizon')
  return node,t+1
 if action<0 or int(model.u[action])!=node or t+int(model.duration[action])>model.H:
  raise ValueError('invalid sidetrack arc')
 return int(model.v[action]),t+int(model.duration[action])

def _column(model,k,actions,dual):
 raw=0.0;adjusted=0.0;resources=[];pairs=[]
 node=int(model.origin[k]);t=int(model.release[k])
 for action,at in actions:
  if at!=t:raise ValueError('sidetrack time discontinuity')
  pairs.extend((int(action),int(t)))
  if action==-2:
   raw+=model.wait_cost;adjusted+=model.wait_cost
  else:
   raw+=float(model.cost[action]);adjusted+=float(model.cost[action])
   p=int(model.physical_pos[action])
   if p>=0:
    row=p*model.H+t;resources.append(row);adjusted-=float(dual[row])
  node,t=_advance(model,node,t,action)
 if node!=int(model.destination[k]):raise ValueError('sidetrack terminal mismatch')
 encoded=np.asarray(pairs,dtype=np.int32)
 identity=hashlib.blake2b(encoded.tobytes(),digest_size=16).hexdigest()
 return PathColumn(int(k),raw,np.asarray(resources,dtype=np.int32),encoded,adjusted,identity)

def one_novel_sidetrack(model,k,dist,choice,dual,excluded,equality_dual):
 """Find the cheapest unseen single-deviation path with negative reduced cost."""
 if model.graph_kind!='implicit':raise ValueError('implicit time graph required')
 out=_outgoing(model);dest=int(model.destination[k])
 node=int(model.origin[k]);t=int(model.release[k])
 first=float(dist[t,node])
 if not math.isfinite(first):raise ValueError('unreachable original commodity')
 actions=[];states=[]
 for _ in range((model.H+1)*(model.n+1)):
  if node==dest:break
  act=int(choice[t,node])
  if act<-2:raise ValueError('broken full-graph choice')
  states.append((node,t,act))
  actions.append((act,t))
  node,t=_advance(model,node,t,act)
 else:raise ValueError('shortest path loop')
 options=[]
 for i,(node,t,chosen) in enumerate(states):
  at=float(dist[t,node])
  if t<model.H and chosen!=-2:
   suffix=float(dist[t+1,node])
   if math.isfinite(suffix):
    score=model.wait_cost+suffix
    if score-at>=-1e-8 and first+score-at-equality_dual<-1e-6:
     options.append((first+score-at,i,-2,t))
  for e in out[node]:
   if e==chosen:continue
   dur=int(model.duration[e]);next_t=t+dur
   if next_t>model.H:continue
   suffix=float(dist[next_t,int(model.v[e])])
   if not math.isfinite(suffix):continue
   score=float(model.cost[e])+suffix
   p=int(model.physical_pos[e])
   if p>=0:score-=float(dual[p*model.H+t])
   if score-at>=-1e-8 and first+score-at-equality_dual<-1e-6:
    options.append((first+score-at,i,e,t))
 options.sort(key=lambda x:(x[0],x[1],x[2]))
 for _,i,alternate,at in options:
  pair=actions[:i]+[(alternate,at)]
  node,t=_advance(model,states[i][0],at,alternate)
  for _ in range((model.H+1)*(model.n+1)):
   if node==dest:break
   act=int(choice[t,node])
   if act<-2:raise ValueError('broken sidetrack suffix choice')
   pair.append((act,t))
   node,t=_advance(model,node,t,act)
  else:raise ValueError('sidetrack suffix loop')
  col=_column(model,k,pair,dual)
  if col.identity not in excluded and col.adjusted_cost-equality_dual<-1e-6:
   return col
 return None
