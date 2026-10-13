"""Compact explicit finite-time graph adapter for the one sparse path-CG loop.

Every dynamic_arc.csv row is retained as a shared capacity resource. Demand
source and sink connector mapping is from original demand IDs. All-graph DAG
pricing handles adjusted arc costs, including negative RMP reduced weights.
"""
from pathlib import Path
import csv,hashlib,heapq,json,math
import numpy as np
from numba import njit
from shared_cg.implicit_graph import PathColumn,file_sha

@njit(cache=True)
def reverse_dag_price(n,reverse_topo,ptr,out_edge,u,v,cost,dual,scale,dest):
    dist=np.full(n,np.inf,dtype=np.float64)
    choice=np.full(n,-1,dtype=np.int32)
    dist[dest]=0.0
    for j in range(len(reverse_topo)):
        node=reverse_topo[j]
        if node==dest:continue
        for z in range(ptr[node],ptr[node+1]):
            e=out_edge[z]
            w=scale*cost[e]-dual[e]+dist[v[e]]
            if w<dist[node]-1e-12:
                dist[node]=w
                choice[node]=e
    return dist,choice

class ExplicitTimeGraph:
    def __init__(self,manifest_path):
        manifest_path=Path(manifest_path)
        manifest=json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        arc_path=Path(manifest["dynamic_arc_file"])
        demand_path=Path(manifest["demand_file"])
        self.source_hashes={"dynamic_arc.csv":file_sha(arc_path),
                            "dynamic_demand.csv":file_sha(demand_path)}
        with arc_path.open(encoding="utf-8-sig",newline="") as f:
            arcs=list(csv.DictReader(f))
        with demand_path.open(encoding="utf-8-sig",newline="") as f:
            demands=list(csv.DictReader(f))
        if not arcs or not demands:raise ValueError("empty explicit graph/demand")
        self.arc_ids=[r["arc_id"] for r in arcs]
        if len(set(self.arc_ids))!=len(self.arc_ids):
            raise ValueError("duplicate original explicit arc ID")
        node_ids=sorted({r["from_node_time_id"] for r in arcs}|
                        {r["to_node_time_id"] for r in arcs})
        node_ix={x:i for i,x in enumerate(node_ids)}
        self.node_ids=node_ids
        self.n=len(node_ids)
        self.u=np.array([node_ix[r["from_node_time_id"]] for r in arcs],dtype=np.int32)
        self.v=np.array([node_ix[r["to_node_time_id"]] for r in arcs],dtype=np.int32)
        self.cost=np.array([float(r["cost"]) for r in arcs],dtype=np.float64)
        self.capacity=np.array([float(r["capacity"]) for r in arcs],dtype=np.float64)
        self.from_time=np.array([int(r["from_time"]) for r in arcs],dtype=np.int32)
        self.to_time=np.array([int(r["to_time"]) for r in arcs],dtype=np.int32)
        if np.any(~np.isfinite(self.cost)) or np.any(self.cost<0) or np.any(~np.isfinite(self.capacity)) or np.any(self.capacity<=0):
            raise ValueError("invalid original cost/capacity")
        if np.any(self.to_time<self.from_time):
            raise ValueError("backward explicit time arc")
        self.resource_count=len(arcs)
        self.graph_kind="explicit"
        self.H=int(np.max(self.to_time))
        out=[[] for _ in range(self.n)]
        indeg=np.zeros(self.n,dtype=np.int32)
        for e in range(len(arcs)):
            out[int(self.u[e])].append(e)
            indeg[int(self.v[e])]+=1
        q=[i for i in range(self.n) if indeg[i]==0]
        heapq.heapify(q)
        topo=[]
        while q:
            node=heapq.heappop(q);topo.append(node)
            for e in out[node]:
                nxt=int(self.v[e]);indeg[nxt]-=1
                if indeg[nxt]==0:heapq.heappush(q,nxt)
        if len(topo)!=self.n:
            raise ValueError("explicit allowed network has a directed cycle; DAG adapter cannot price it")
        self.reverse_topo=np.array(topo[::-1],dtype=np.int32)
        self.ptr=np.zeros(self.n+1,dtype=np.int32)
        self.out_edge=np.empty(len(arcs),dtype=np.int32)
        at=0
        for node,edges in enumerate(out):
            self.ptr[node]=at
            for e in edges:self.out_edge[at]=e;at+=1
        self.ptr[self.n]=at
        by_arc={r["arc_id"]:r for r in arcs}
        dids=[r["demand_id"] for r in demands]
        if len(set(dids))!=len(dids):raise ValueError("duplicate demand ID")
        origin=[];destination=[];volume=[];release=[]
        for d in demands:
            did=d["demand_id"]
            source=by_arc.get("source_"+did)
            if source is None or source["arc_type"]!="source_connector":
                raise ValueError(f"missing exact source connector for {did}")
            sink_targets={r["to_node_time_id"] for r in arcs
                          if r["arc_type"]=="sink_connector" and
                          r["arc_id"].startswith("sink_"+did+"_")}
            if len(sink_targets)!=1:
                raise ValueError(f"need one original sink target for {did}; got {len(sink_targets)}")
            start=source["from_node_time_id"]
            target=next(iter(sink_targets))
            if start not in node_ix or target not in node_ix:
                raise ValueError("bad original source/sink node")
            origin.append(node_ix[start]);destination.append(node_ix[target])
            volume.append(float(d["volume"]))
            release.append(int(d["departure_time"]))
        self.origin=np.array(origin,dtype=np.int32)
        self.destination=np.array(destination,dtype=np.int32)
        self.q=np.array(volume,dtype=np.float64)
        self.release=np.array(release,dtype=np.int32)
        if np.any(~np.isfinite(self.q)) or np.any(self.q<=0):
            raise ValueError("bad positive explicit demand")
        self.K=len(demands)
        self.destinations=np.unique(self.destination)
        self.model_identity={"schema":"SHARED_CG_EXPLICIT_TIME_MODEL_R1",
          "manifest":str(manifest_path.resolve()),"manifest_sha256":file_sha(manifest_path),
          "source_hashes":self.source_hashes,"original_arc_count":len(arcs),
          "original_time_node_count":self.n,"original_positive_demands":self.K,
          "all_original_arc_capacity_rows":self.resource_count,
          "capacity_rule":"every original dynamic_arc.csv row, one shared resource",
          "connector_rule":"exact source_<demand_id> and sink_<demand_id>_* original arc IDs"}
    def capacity_for_rows(self,rows):
        return self.capacity[np.asarray(rows,dtype=np.int64)]
    def price_destination(self,dest,dual=None,phase="II",epsilon=1e-9):
        if dual is None:dual=np.zeros(self.resource_count,dtype=np.float64)
        scale=epsilon if phase=="I" else 1.0
        return reverse_dag_price(self.n,self.reverse_topo,self.ptr,self.out_edge,
                                 self.u,self.v,self.cost,dual,scale,int(dest))
    def path_from_choice(self,k,dist,choice):
        node=int(self.origin[k]);dest=int(self.destination[k])
        adjusted=float(dist[node])
        if not math.isfinite(adjusted):raise ValueError(f"unserved original explicit demand {k}")
        pairs=[];resources=[];raw_cost=0.0
        for _ in range(self.n+1):
            if node==dest:break
            e=int(choice[node])
            if e<0 or self.u[e]!=node:raise ValueError(f"broken original explicit path {k}")
            pairs.extend((e,int(self.from_time[e])))
            resources.append(e)
            raw_cost+=float(self.cost[e])
            node=int(self.v[e])
        else:raise ValueError("explicit path loop guard")
        edge_time=np.array(pairs,dtype=np.int32)
        identity=hashlib.blake2b(edge_time.tobytes(),digest_size=16).hexdigest()
        return PathColumn(k,raw_cost,np.array(resources,dtype=np.int32),
                          edge_time,adjusted,identity)
