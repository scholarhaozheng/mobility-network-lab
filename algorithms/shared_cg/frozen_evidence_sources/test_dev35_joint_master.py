from pathlib import Path
import sys
import numpy as np
from scipy.sparse import csr_matrix
sys.path.insert(0,str(Path(__file__).resolve().parent/'sparse_common_dev35_joint_stabilized_cg'))
from shared_cg.joint_delta_rmp import solve_joint_delta,original_path_reduced_cost

# Full 2-commodity arc-flow optimum by independent enumeration: old 10+1,
# joint new 2+3, bottleneck capacity one.
A=csr_matrix([[1.,1.,-1.]])
result=solve_joint_delta(A,[7],[0.],[-8.,-6.,2.],[0,0,1],[1.,1.])
assert np.allclose(result.y,[1.,0.,1.],atol=1e-8),result.y
assert abs(11.+result.objective_delta-5.)<1e-8
assert abs(result.y[0]+result.y[1]-1.)<1e-8
assert result.max_capacity_excess<=1e-8 and result.max_group_excess<=1e-8
assert np.all(result.reduced_cost>=-1e-8)
price={7:-result.capacity_mu[0]}
for j,(new,base,nrows,brows,g) in enumerate([(2.,10.,[7],[],0),(4.,10.,[7],[],0),(3.,1.,[],[7],1)]):
    rc=original_path_reduced_cost(new,base,nrows,brows,price,result.group_mu[g])
    assert abs(rc-result.reduced_cost[j])<1e-8,(j,rc,result.reduced_cost[j])
# Independent exhaustive vertices for this small LP.
best=1e9
for a in np.linspace(0,1,101):
 for b in np.linspace(0,1-a,round((1-a)*100)+1):
  d=max(0,a+b)
  v=11-8*a-6*b+2*d
  best=min(best,v)
assert abs(best-5.)<1e-8,best
bad=solve_joint_delta(csr_matrix([[1.,1.]]),[7],[0.],[-8.,-6.],[0,0],[1.])
assert np.sum(bad.y)<=1+1e-8
assert bad.max_group_excess<=1e-8
print({'status':'PASS','joint_objective':11+result.objective_delta,'flow':result.y.tolist(),'reduced_cost':result.reduced_cost.tolist(),'independent_enumeration':best,'duplicate_service_rejected':True})
