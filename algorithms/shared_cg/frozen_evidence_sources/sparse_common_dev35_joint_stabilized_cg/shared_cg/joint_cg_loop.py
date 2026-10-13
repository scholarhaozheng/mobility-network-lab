"""Common coupled sparse column-generation loop.

A pricing adapter supplies legal original paths; all columns, including
different paths of one OD/release group, enter one shared master. Partial
pricing advances the pool. Exact full-graph pricing is required for closure.
"""
from dataclasses import dataclass
from collections import Counter
import numpy as np
from scipy import sparse
from .joint_delta_rmp import solve_joint_delta,JointResult

@dataclass(frozen=True)
class Candidate:
    group_key: object
    group_mass: float
    delta_cost: float
    delta_resources: tuple
    path_signature: str
    diversity_key: object

class JointState:
    def __init__(self, matrix, rows, residual_capacity, delta_cost, column_group,
                 group_mass, group_keys, signatures, residual_lookup):
        self.A=sparse.csr_matrix(matrix,dtype=np.float64)
        self.rows=list(map(int,rows))
        self.rhs=list(map(float,residual_capacity))
        self.cost=list(map(float,delta_cost))
        self.group=list(map(int,column_group))
        self.mass=list(map(float,group_mass))
        self.keys=list(group_keys)
        self.column_signatures=list(signatures)
        self.signatures=set(signatures)
        self.residual_lookup=residual_lookup
        if self.A.shape!=(len(self.rows),len(self.cost)) or len(self.group)!=len(self.cost) or len(self.mass)!=len(self.keys) or len(self.column_signatures)!=len(self.cost):
            raise ValueError('joint CG initial dimensions')
        if len(set(self.rows))!=len(self.rows) or len(set(self.keys))!=len(self.keys):
            raise ValueError('duplicate initial resource/group')
        self.key_index={key:j for j,key in enumerate(self.keys)}
        self.row_index={row:j for j,row in enumerate(self.rows)}
    def add(self,candidates):
        fresh=[]
        for col in candidates:
            if col.path_signature in self.signatures:continue
            if col.group_mass<=0 or not np.isfinite(col.group_mass) or not np.isfinite(col.delta_cost):
                raise ValueError('new column mass/cost')
            delta=Counter(dict(col.delta_resources))
            delta={int(r):float(v) for r,v in delta.items() if abs(v)>1e-14}
            if not delta and abs(col.delta_cost)<=1e-14:continue
            fresh.append((col,delta))
            self.signatures.add(col.path_signature)
        if not fresh:return 0
        extra=sorted({r for _,delta in fresh for r in delta if r not in self.row_index})
        if extra:
            newrhs=np.asarray(self.residual_lookup(np.asarray(extra,dtype=np.int64)),dtype=np.float64)
            if newrhs.shape!=(len(extra),) or not np.all(np.isfinite(newrhs)):
                raise ValueError('original new-row baseline missing')
            oldcols=self.A.shape[1]
            self.A=sparse.vstack((self.A,sparse.csr_matrix((len(extra),oldcols))),format='csr')
            for r,b in zip(extra,newrhs):
                self.row_index[r]=len(self.rows);self.rows.append(r);self.rhs.append(float(b))
        rr=[];cc=[];vv=[]
        for j,(col,delta) in enumerate(fresh):
            if col.group_key in self.key_index:
                k=self.key_index[col.group_key]
                if abs(self.mass[k]-col.group_mass)>max(1e-12,1e-9*self.mass[k]):
                    raise ValueError('original commodity mass changed')
            else:
                k=len(self.keys);self.key_index[col.group_key]=k
                self.keys.append(col.group_key);self.mass.append(float(col.group_mass))
            self.group.append(k);self.cost.append(float(col.delta_cost));self.column_signatures.append(col.path_signature)
            for r,value in delta.items():
                rr.append(self.row_index[r]);cc.append(j);vv.append(value)
        B=sparse.coo_matrix((vv,(rr,cc)),shape=(len(self.rows),len(fresh))).tocsr()
        B.sum_duplicates()
        self.A=sparse.hstack((self.A,B),format='csr')
        return len(fresh)
    def solve(self,time_limit=1800.):
        if not self.cost:
            if self.rows and min(self.rhs)<-1e-8:
                raise ValueError('zero-column algebraic base infeasible')
            return JointResult(np.empty(0),0.0,0.0,np.zeros(len(self.rows)),
                               np.zeros(len(self.mass)),np.empty(0),0,0,0,0.0,0.0)
        return solve_joint_delta(self.A,self.rows,self.rhs,self.cost,self.group,self.mass,time_limit=time_limit)
    def reduced_cost(self,column,dual):
        k=self.key_index.get(column.group_key)
        nu=float(dual.group_mu[k]) if k is not None else 0.
        loc=self.row_index
        mu=dual.capacity_mu
        toll=0.
        for row,value in column.delta_resources:
            j=loc.get(int(row))
            if j is not None:toll-=mu[j]*float(value)
        return float(column.delta_cost+toll-nu)

def run_joint_cg(state,pricing,*,max_rounds=20,max_new_per_round=200,
                 max_per_group=3,epsilon=1e-7,rmp_seconds=1800,
                 stabilization_alpha=0.7,checkpoint=None):
    """Run RMP -> stabilized partial price -> accurate selection -> exact fallback.

    pricing(lambda_by_original_row, group_mu_by_key, mode) returns Candidate
    objects and an optional full-original lower certificate in exact mode.
    The same-run center updates after each new solved RMP. The pricing
    callback must cover the full legal graph in exact mode.
    """
    if not 0<stabilization_alpha<=1 or max_rounds<=0 or max_new_per_round<=0:
        raise ValueError('common CG policy')
    history=[];center=None;center_groups=None;alpha=float(stabilization_alpha)
    for round_no in range(1,max_rounds+1):
        master=state.solve(rmp_seconds)
        lam=-master.capacity_mu
        groups={key:float(master.group_mu[i]) for i,key in enumerate(state.keys)}
        if center is None:
            center={r:float(x) for r,x in zip(state.rows,lam)}
            center_groups=groups.copy()
        stable={r:alpha*float(x)+(1-alpha)*center.get(r,0.) for r,x in zip(state.rows,lam)}
        stable_groups={k:alpha*v+(1-alpha)*center_groups.get(k,0.) for k,v in groups.items()}
        proposed,screen=pricing(stable,stable_groups,'partial')
        full_called=False;full_lower=None
        def choose(items):
            ranked=[]
            for col in items:
                if col.path_signature in state.signatures:continue
                rc=state.reduced_cost(col,master)
                if rc<-epsilon or abs(rc)<=epsilon:
                    ranked.append((rc*col.group_mass,rc,col))
            ranked.sort(key=lambda a:(a[0],a[1],a[2].path_signature))
            picked=[];pergroup={};diverse=set()
            for _,_,col in ranked:
                if pergroup.get(col.group_key,0)>=max_per_group:continue
                key=(col.group_key,col.diversity_key)
                if key in diverse:continue
                picked.append(col);diverse.add(key)
                pergroup[col.group_key]=pergroup.get(col.group_key,0)+1
                if len(picked)>=max_new_per_round:break
            return picked,len(ranked)
        picked,novel=choose(proposed)
        if not picked:
            proposed,screen=pricing({r:float(x) for r,x in zip(state.rows,lam)},groups,'exact')
            full_called=True;full_lower=screen.get('full_original_lower')
            picked,novel=choose(proposed)
            alpha=min(1.,alpha+0.15)
        row={'round':round_no,'restricted_delta':master.objective_delta,
             'positive_columns':int(np.count_nonzero(master.y>1e-10)),
             'columns_before':state.A.shape[1],'pricing_mode':'exact' if full_called else 'partial',
             'novel_nonpositive_current_rc':novel,'full_original_lower':full_lower,
             'max_capacity_excess':master.max_capacity_excess,'RMP_iterations':master.iterations}
        if picked:
            added=state.add(picked);row['added']=added;history.append(row)
            if checkpoint is not None:checkpoint(state,history)
            center={r:0.5*center.get(r,0.)+0.5*float(x) for r,x in zip(state.rows,[-master.capacity_mu[state.row_index[r]] if r in state.row_index and state.row_index[r]<len(master.capacity_mu) else 0. for r in state.rows])}
            center_groups={k:0.5*center_groups.get(k,0.)+0.5*v for k,v in groups.items()}
            continue
        row['added']=0;history.append(row)
        if not full_called:
            status='PARTIAL_PRICE_STALLED'
        elif screen.get('minimum_reduced_cost',-np.inf)<-epsilon:
            status='NEGATIVE_REDUCED_COST_DUPLICATE_OR_MISPRICED_OPEN'
        elif full_lower is None:
            status='EXACT_PRICE_WITHOUT_VALID_FULL_LOWER_OPEN'
        else:
            status='FULL_PRICE_NO_NEGATIVE_PENDING_INDEPENDENT_CERT'
        return status,master,history
    return 'ROUND_LIMIT_OPEN',master,history

