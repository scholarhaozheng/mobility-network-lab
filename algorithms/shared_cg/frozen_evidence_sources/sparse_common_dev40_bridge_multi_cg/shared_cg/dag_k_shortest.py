"""Exact K shortest paths on an audited finite-time DAG, negative weights safe.

Path labels share predecessor nodes, so full paths are only materialized for
the final K terminal labels. This is a generic network algorithm, independent
of city names and specific arc IDs.
"""
from collections import defaultdict
import heapq,math

def k_shortest_dag(arcs,start,target_nodes,k,weight_by_id):
 if k<1:raise ValueError("k must be positive")
 outgoing=defaultdict(list)
 indeg=defaultdict(int)
 ids=set()
 for arc in arcs:
  aid=arc["arc_id"];u=arc["from_node_time_id"];v=arc["to_node_time_id"]
  if not aid or not u or not v or aid in ids:
   raise ValueError("invalid or duplicate original dynamic arc")
  ids.add(aid)
  w=float(weight_by_id[aid])
  if not math.isfinite(w):raise ValueError("nonfinite adjusted cost")
  outgoing[u].append((v,aid,w))
  indeg.setdefault(u,0);indeg[v]+=1
 if start not in indeg:raise ValueError("unknown source node")
 targets=set(target_nodes)
 if not targets<=set(indeg):raise ValueError("unknown terminal node")
 for values in outgoing.values():values.sort(key=lambda x:(x[1],x[0]))
 ready=[node for node,count in indeg.items() if count==0]
 heapq.heapify(ready)
 topo=[]
 while ready:
  node=heapq.heappop(ready)
  topo.append(node)
  for v,_,_ in outgoing.get(node,()):
   indeg[v]-=1
   if indeg[v]==0:heapq.heappush(ready,v)
 if len(topo)!=len(indeg):
  raise ValueError("full original time graph is cyclic; use general pricing fallback")
 proposals={start:[(0.0,-1,"")]}
 labels=[]
 finals=[]
 for node in topo:
  options=proposals.pop(node,())
  if not options:continue
  # Negative arc weights are allowed because topological order is exact.
  selected=heapq.nsmallest(k,options,key=lambda x:(x[0],x[2],x[1]))
  for score,previous,aid in selected:
   ix=len(labels)
   labels.append((score,previous,aid))
   if node in targets:
    finals.append(ix)
    continue
   for v,edge_id,w in outgoing.get(node,()):
    proposals.setdefault(v,[]).append((score+w,ix,edge_id))
 finals=heapq.nsmallest(k,finals,key=lambda ix:(labels[ix][0],ix))
 answer=[]
 for ix in finals:
  score=labels[ix][0]
  edges=[]
  while ix>=0:
   _,previous,aid=labels[ix]
   if aid:edges.append(aid)
   ix=previous
  edges.reverse()
  answer.append((score,edges))
 return answer,{"dag_node_count":len(topo),"dag_arc_count":len(arcs),
                "label_count":len(labels),"negative_adjusted_arc_count":sum(float(weight_by_id[a["arc_id"]])<0 for a in arcs)}
