from pathlib import Path
import sys
import numpy as np
from scipy.sparse import csr_matrix
sys.path.insert(0,str(Path(__file__).resolve().parent/'sparse_common_dev35_joint_stabilized_cg'))
from shared_cg.joint_cg_loop import Candidate,JointState,run_joint_cg
state=JointState(csr_matrix([[-1.]]),[7],[0.],[2.],[1],[1.,1.],['A','B'],['B-detour'],
                 lambda rows:np.zeros(len(rows)))
def pricing(lam,nu,mode):
 if mode=='partial':
  return [Candidate('A',1.,-8.,((7,1.),),'A-bottleneck',(7,'use'))],{}
 return [],{'full_original_lower':5.,'minimum_reduced_cost':0.}
status,master,history=run_joint_cg(state,pricing,max_rounds=5,max_new_per_round=2)
assert status=='FULL_PRICE_NO_NEGATIVE_PENDING_INDEPENDENT_CERT',status
assert abs(11+master.objective_delta-5)<1e-8,(master.objective_delta,history)
assert len(history)==2 and history[0]['added']==1 and history[1]['added']==0,history
assert np.max(np.bincount(state.group,weights=master.y,minlength=2)-state.mass)<1e-8
print({'status':'PASS','objective':11+master.objective_delta,'rounds':len(history),'columns':state.A.shape[1]})
