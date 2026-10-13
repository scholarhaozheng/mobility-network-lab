from pathlib import Path
import sys
import numpy as np
from scipy.sparse import csr_matrix
sys.path.insert(0,str(Path(__file__).resolve().parent/'sparse_common_dev35_joint_stabilized_cg'))
from shared_cg.joint_delta_rmp import solve_joint_delta,original_path_reduced_cost
from shared_cg.joint_cg_loop import Candidate,JointState,run_joint_cg
def raises(fn):
 try:fn()
 except (ValueError,RuntimeError):return
 raise AssertionError('semantic negative accepted')
# Independent arc-flow truth: two commodities, single unit bottleneck.
A=csr_matrix([[1.,1.,-1.]])
ok=solve_joint_delta(A,[7],[0.],[-8.,-6.,2.],[0,0,1],[1.,1.])
assert abs(11+ok.objective_delta-5)<1e-8
assert abs(sum(ok.y[:2])-1)<1e-8 and abs(ok.y[2]-1)<1e-8
# An omitted resource or duplicated service must change/reject the result.
raises(lambda:solve_joint_delta(A,[7,7],[0.,0.],[-8.,-6.,2.],[0,0,1],[1.,1.]))
raises(lambda:solve_joint_delta(A,[7],[0.],[-8.,-6.,2.],[0,0,1],[1.,-1.]))
# A tampered capacity to two units produces a different optimum, so this
# fixture actually detects the bottleneck coupling.
loose=solve_joint_delta(A,[7],[1.],[-8.,-6.,2.],[0,0,1],[1.,1.])
assert abs(11+loose.objective_delta-3)<1e-8
price={7:-ok.capacity_mu[0]}
rc=original_path_reduced_cost(2,10,[7],[],price,ok.group_mu[0])
assert abs(rc-ok.reduced_cost[0])<1e-8
wrong=original_path_reduced_cost(2,10,[7],[],{7:ok.capacity_mu[0]},ok.group_mu[0])
assert abs(wrong-rc)>1e-3
# A true negative exact price with only duplicate offers must stay OPEN.
state=JointState(csr_matrix([[-1.]]),[7],[0.],[2.],[1],[1.,1.],['A','B'],['B-detour'],
                 lambda rows:np.zeros(len(rows)))
def price(lam,nu,mode):
 if mode=='partial':return [],{}
 return [Candidate('B',1.,2.,((7,-1.),),'B-detour',(7,'detour'))],{'full_original_lower':0.,'minimum_reduced_cost':-1.}
status,master,hist=run_joint_cg(state,price,max_rounds=2)
assert status=='NEGATIVE_REDUCED_COST_DUPLICATE_OR_MISPRICED_OPEN',status
print({'status':'PASS','joint_objective':5.,'loose_capacity_objective':3.,'false_closure_rejected':True,'dual_sign_detected':True})
