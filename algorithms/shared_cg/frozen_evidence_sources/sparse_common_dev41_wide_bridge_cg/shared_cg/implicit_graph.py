"""Implicit full-hour finite-time graph for the shared path-CG backend.

This is a source-driven representation: every input travel/turn arc is legal
at every arrival-feasible step; all node-time waits are legal; sink is available
at the original destination at every time through H. Physical entry rows are
shared across all OD releases. The same model can be priced without writing
millions of CSV dictionaries.
"""
from dataclasses import dataclass
from pathlib import Path
import csv,hashlib,heapq,json,math
import numpy as np
from numba import njit

def read_rows(path):
    with Path(path).open(encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))

def file_sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):h.update(b)
    return h.hexdigest()

@njit(cache=True)
def reverse_price(n,H,dest,u,v,duration,base_cost,physical_pos,
                  zero_ptr,zero_edge,reverse_topo,dual,scale,wait_cost):
    dist=np.full((H+1,n),np.inf,dtype=np.float64)
    choice=np.full((H+1,n),-3,dtype=np.int32)
    for t in range(H,-1,-1):
        dist[t,dest]=0.0
        choice[t,dest]=-1
        if t<H:
            for node in range(n):
                w=wait_cost+dist[t+1,node]
                if w<dist[t,node]:
                    dist[t,node]=w
                    choice[t,node]=-2
        for e in range(len(u)):
            step=duration[e]
            if step<=0 or t+step>H:continue
            w=scale*base_cost[e]+dist[t+step,v[e]]
            p=physical_pos[e]
            if p>=0:
                w-=dual[p*H+t]
            if w<dist[t,u[e]]-1e-12:
                dist[t,u[e]]=w
                choice[t,u[e]]=e
        for j in range(len(reverse_topo)):
            node=reverse_topo[j]
            for z in range(zero_ptr[node],zero_ptr[node+1]):
                e=zero_edge[z]
                w=scale*base_cost[e]+dist[t,v[e]]
                if w<dist[t,node]-1e-12:
                    dist[t,node]=w
                    choice[t,node]=e
    return dist,choice

@dataclass
class PathColumn:
    commodity: int
    objective_cost: float
    resources: np.ndarray
    edge_time: np.ndarray
    adjusted_cost: float
    identity: str

class ImplicitTimeGraph:
    def __init__(self,source_dir,dt_seconds,horizon_steps,release_steps,
                 demand_factor=1.0,allow_midroute_wait=True):
        self.source_dir=Path(source_dir)
        self.paths={n:self.source_dir/n for n in ("network.csv","access.csv","assignment_od_pce.csv")}
        self.source_hashes={n:file_sha(p) for n,p in self.paths.items()}
        net=read_rows(self.paths["network.csv"])
        access=read_rows(self.paths["access.csv"])
        od=read_rows(self.paths["assignment_od_pce.csv"])
        if not net or not od or not access:raise ValueError("empty source input")
        if not allow_midroute_wait:
            raise ValueError("shared full-graph backend requires the explicit all-node wait domain")
        self.dt=float(dt_seconds)
        self.H=int(horizon_steps)
        self.release_steps=int(release_steps)
        self.factor=float(demand_factor)
        if self.dt<=0 or self.H<=0 or self.release_steps<=0 or self.factor<=0:
            raise ValueError("invalid time or demand factor")
        if abs(self.release_steps*self.dt-3600)>1e-7:
            raise ValueError("release horizon must cover exactly the original hour")
        self.edge_ids=[r["link_id"] for r in net]
        if len(self.edge_ids)!=len(set(self.edge_ids)):raise ValueError("duplicate source edge")
        self.node_ids=sorted({r["from_node_id"] for r in net}|{r["to_node_id"] for r in net})
        self.node_ix={x:i for i,x in enumerate(self.node_ids)}
        self.n=len(self.node_ids)
        self.u=np.array([self.node_ix[r["from_node_id"]] for r in net],dtype=np.int32)
        self.v=np.array([self.node_ix[r["to_node_id"]] for r in net],dtype=np.int32)
        self.cost=np.array([float(r["vdf_fftt"]) for r in net],dtype=np.float64)
        self.hourly_capacity=np.array([float(r["capacity"]) for r in net],dtype=np.float64)
        self.physical=np.array([r["arc_kind"]=="physical" for r in net],dtype=np.bool_)
        if np.any(~np.isfinite(self.cost)) or np.any(self.cost<0) or np.any(self.hourly_capacity<=0):
            raise ValueError("invalid source cost or capacity")
        self.duration=np.array([max(1,math.ceil(self.cost[e]*60/self.dt-1e-12))
                                if self.physical[e] else 0 for e in range(len(net))],dtype=np.int32)
        self.physical_edges=np.flatnonzero(self.physical).astype(np.int32)
        self.physical_pos=np.full(len(net),-1,dtype=np.int32)
        self.physical_pos[self.physical_edges]=np.arange(len(self.physical_edges),dtype=np.int32)
        self.capacity_per_step=self.hourly_capacity[self.physical_edges]*self.dt/3600
        self.resource_count=len(self.physical_edges)*self.H
        self.graph_kind="implicit"
        zero=[[] for _ in range(self.n)]
        indeg=np.zeros(self.n,dtype=np.int32)
        for e in range(len(net)):
            if self.duration[e]==0:
                zero[int(self.u[e])].append(e)
                indeg[int(self.v[e])]+=1
        for edges in zero:edges.sort(key=lambda e:self.edge_ids[e])
        queue=[i for i in range(self.n) if indeg[i]==0]
        heapq.heapify(queue)
        topo=[]
        while queue:
            node=heapq.heappop(queue)
            topo.append(node)
            for e in zero[node]:
                nxt=int(self.v[e]);indeg[nxt]-=1
                if indeg[nxt]==0:heapq.heappush(queue,nxt)
        if len(topo)!=self.n:
            raise ValueError("zero-duration subgraph has a cycle; use the general same-layer pricing backend")
        self.reverse_topo=np.array(topo[::-1],dtype=np.int32)
        self.zero_ptr=np.zeros(self.n+1,dtype=np.int32)
        self.zero_edge=np.empty(sum(map(len,zero)),dtype=np.int32)
        k=0
        for node,edges in enumerate(zero):
            self.zero_ptr[node]=k
            for e in edges:self.zero_edge[k]=e;k+=1
        self.zero_ptr[self.n]=k
        zone={r["zone_id"]:r["node_id"] for r in access}
        if len(zone)!=len(access) or not set(zone.values())<=set(self.node_ids):
            raise ValueError("zone access missing or duplicate")
        self.od=[]
        seen=set()
        for row in od:
            o,d=row["o_zone_id"],row["d_zone_id"]
            q=float(row["volume_pce"])*self.factor
            if o not in zone or d not in zone or o==d or q<=0 or (o,d) in seen:
                raise ValueError("bad original positive OD")
            seen.add((o,d))
            self.od.append((o,d,self.node_ix[zone[o]],self.node_ix[zone[d]],q))
        self.K=len(self.od)*self.release_steps
        self.q=np.repeat(np.array([x[4]/self.release_steps for x in self.od],dtype=np.float64),
                         self.release_steps)
        self.origin=np.repeat(np.array([x[2] for x in self.od],dtype=np.int32),self.release_steps)
        self.destination=np.repeat(np.array([x[3] for x in self.od],dtype=np.int32),self.release_steps)
        self.release=np.tile(np.arange(self.release_steps,dtype=np.int32),len(self.od))
        self.destinations=np.unique(self.destination)
        self.wait_cost=self.dt/60
        self.model_identity={"schema":"SHARED_CG_IMPLICIT_TIME_MODEL_R1",
            "source_hashes":self.source_hashes,"dt_seconds":self.dt,"horizon_steps":self.H,
            "release_steps":self.release_steps,"demand_factor":self.factor,
            "positive_OD":len(self.od),"commodity_events":self.K,
            "original_hourly_pce":float(sum(x[4] for x in self.od)),
            "source_edges":len(net),"physical_edges":len(self.physical_edges),
            "zero_layer_dag_nodes":self.n,
            "physical_capacity_rows":len(self.physical_edges)*self.H,
            "capacity_rule":"hourly physical edge capacity * dt / 3600 at entry",
            "wait_rule":"all network nodes t->t+1, cost dt/60",
            "sink_rule":"original destination at any t<=H, zero exit cost"}
    def price_destination(self,dest,dual=None,phase="II",epsilon=1e-9):
        if dual is None:
            dual=np.zeros(self.resource_count,dtype=np.float64)
        scale=epsilon if phase=="I" else 1.0
        return reverse_price(self.n,self.H,int(dest),self.u,self.v,self.duration,
                             self.cost,self.physical_pos,self.zero_ptr,self.zero_edge,
                             self.reverse_topo,dual,scale,scale*self.wait_cost)
    def capacity_for_rows(self,rows):
        return self.capacity_per_step[np.asarray(rows,dtype=np.int64)//self.H]
    def path_from_choice(self,k,dist,choice):
        node=int(self.origin[k]); t=int(self.release[k])
        adjusted=float(dist[t,node])
        if not math.isfinite(adjusted):raise ValueError(f"unserved original commodity {k}")
        pairs=[]; resources=[]; raw_cost=0.0
        for _ in range((self.H+1)*(self.n+1)):
            if node==int(self.destination[k]):break
            picked=int(choice[t,node])
            if picked==-2:
                pairs.extend((-2,t));raw_cost+=self.wait_cost;t+=1
            elif picked>=0:
                pairs.extend((picked,t));raw_cost+=float(self.cost[picked])
                p=int(self.physical_pos[picked])
                if p>=0:resources.append(p*self.H+t)
                t+=int(self.duration[picked]);node=int(self.v[picked])
            else:raise ValueError(f"broken priced path {k} at {node},{t}")
            if t>self.H:raise ValueError("priced path passed horizon")
        else:raise ValueError("priced path loop guard")
        edge_time=np.array(pairs,dtype=np.int32)
        identity=hashlib.blake2b(edge_time.tobytes(),digest_size=16).hexdigest()
        return PathColumn(k,raw_cost,np.array(resources,dtype=np.int32),edge_time,adjusted,identity)
