"""Sparse restricted master extension for distinct original OD-release paths.

Every original commodity stays on its algebraic base path unless its bounded
alternative variable is positive. All changed original capacity rows are
explicit, including coefficients of pre-existing family and singleton columns.
"""
from collections import Counter
import numpy as np
from scipy import sparse
from scipy.optimize import linprog
from .two_singleton_phase_ii_rmp import Extension


def extend_batch_events(old_matrix,old_rows,old_rhs,old_cost,old_upper,
                        selected_paths,delays,prior_base_rows,prior_new_rows,
                        physical_pos,physical_edge,baseline,capacity,H,T,
                        batch_base_rows,batch_new_rows,batch_q,batch_cost_increment,
                        time_limit):
 old_matrix=old_matrix.tocsr();old_rows=np.asarray(old_rows,dtype=np.int64)
 old_rhs=np.asarray(old_rhs,dtype=np.float64);old_cost=np.asarray(old_cost,dtype=np.float64);old_upper=np.asarray(old_upper,dtype=np.float64)
 q=np.asarray(batch_q,dtype=np.float64);cost=np.asarray(batch_cost_increment,dtype=np.float64)
 m=len(q);n_family=len(selected_paths)*T
 if old_matrix.shape!=(len(old_rows),len(old_cost)) or len(old_rhs)!=len(old_rows) or len(old_upper)!=len(old_cost):raise ValueError('old exact RMP dimensions')
 if len(old_cost)!=n_family+len(prior_base_rows) or len(prior_base_rows)!=len(prior_new_rows):raise ValueError('old alternative column identities')
 if len(batch_base_rows)!=m or len(batch_new_rows)!=m or len(cost)!=m or np.any(q<=0) or not np.all(np.isfinite(q)) or not np.all(np.isfinite(cost)) or time_limit<=0:raise ValueError('new original event batch dimensions')
 if len(set(map(int,old_rows)))!=len(old_rows) or len(delays)!=len(selected_paths):raise ValueError('retained rows or delay family')
 old_location={int(row):j for j,row in enumerate(old_rows)}
 # Count capacity incidence, preserving repeated uses of a physical resource.
 deltas=[];new_rows=set()
 for base,new in zip(batch_base_rows,batch_new_rows):
  before=Counter(map(int,base));after=Counter(map(int,new))
  delta={r:after.get(r,0)-before.get(r,0) for r in before.keys()|after.keys()}
  delta={r:v for r,v in delta.items() if v}
  for r in delta:
   if r<0 or r//H>=len(physical_edge):raise ValueError('new column resource outside original graph')
   if r not in old_location:new_rows.add(r)
  deltas.append(delta)
 extra=np.array(sorted(new_rows),dtype=np.int64);location={int(r):len(old_rows)+j for j,r in enumerate(extra)}
 location.update(old_location)
 new_rr=[];new_cc=[];new_vv=[]
 for j,delta in enumerate(deltas):
  for row,value in delta.items():
   new_rr.append(location[row]);new_cc.append(j);new_vv.append(float(value))
 new_matrix=sparse.coo_matrix((new_vv,(new_rr,new_cc)),shape=(len(old_rows)+len(extra),m)).tocsr();new_matrix.sum_duplicates()
 extra_rhs=np.empty(len(extra),dtype=np.float64);extra_by_edge={}
 for j,row in enumerate(extra):
  p,t=divmod(int(row),H);edge=int(physical_edge[p])
  extra_rhs[j]=float(capacity[edge])-baseline.load_at(edge,t)
  extra_by_edge.setdefault(p,[]).append((t,j))
 if np.any(extra_rhs<-1e-7):raise ValueError('newly touched original row already overloaded by algebraic base')
 rr=[];cc=[];vv=[]
 for g,path in enumerate(selected_paths):
  delay=int(delays[g])
  for edge,offset in path:
   p=int(physical_pos[int(edge)])
   if p<0:raise ValueError('old delay path nonphysical source edge')
   for t,j in extra_by_edge.get(p,()):
    release=t-int(offset)
    if 0<=release<T:rr.append(j);cc.append(g*T+release);vv.append(-1.)
    release-=delay
    if 0<=release<T:rr.append(j);cc.append(g*T+release);vv.append(1.)
 for k,(base,new) in enumerate(zip(prior_base_rows,prior_new_rows)):
  before=Counter(map(int,base));after=Counter(map(int,new))
  for row,j in zip(extra,range(len(extra))):
   value=after.get(int(row),0)-before.get(int(row),0)
   if value:rr.append(j);cc.append(n_family+k);vv.append(float(value))
 old_extra=sparse.coo_matrix((vv,(rr,cc)),shape=(len(extra),len(old_cost))).tocsr();old_extra.sum_duplicates()
 left=sparse.vstack((old_matrix,old_extra),format='csr')
 A=sparse.hstack((left,new_matrix),format='csr')
 rhs=np.r_[old_rhs,extra_rhs];costs=np.r_[old_cost,cost];upper=np.r_[old_upper,q]
 if not np.all(np.isfinite(rhs)) or np.any(upper<=0):raise ValueError('original capacity/demand invalid')
 sol=linprog(costs,A_ub=A,b_ub=rhs,bounds=np.c_[np.zeros(len(upper)),upper],method='highs',options={'presolve':True,'time_limit':float(time_limit),'primal_feasibility_tolerance':1e-9,'dual_feasibility_tolerance':1e-9})
 if not sol.success:raise RuntimeError(f'batch original Q RMP status={sol.status}: {sol.message}')
 flow=np.asarray(sol.x,dtype=np.float64);excess=float(np.max(A@flow-rhs)) if len(rhs) else float('-inf')
 if excess>1e-6 or np.any(flow<-1e-8) or np.any(flow>upper+1e-8):raise ValueError('exact original capacity or event demand violation')
 mu=np.asarray(sol.ineqlin.marginals,dtype=np.float64);lo=np.asarray(sol.lower.marginals,dtype=np.float64);up=np.asarray(sol.upper.marginals,dtype=np.float64)
 dual=float(np.dot(rhs,mu)+np.dot(upper,up))
 return Extension(A,np.r_[old_rows,extra],rhs,costs,upper,flow,mu,lo,up,float(sol.fun),dual,int(sol.nit),len(extra),excess)
