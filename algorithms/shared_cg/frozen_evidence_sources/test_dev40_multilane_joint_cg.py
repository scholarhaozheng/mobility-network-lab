"""Verify common true-dual lane reservation keeps a bottleneck-release column."""
from pathlib import Path
import sys
import numpy as np
from scipy import sparse
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'sparse_common_dev40_bridge_multi_cg'))
from shared_cg.joint_cg_loop import Candidate,JointState,run_joint_cg

def main():
 state=JointState(sparse.csr_matrix((0,0)),[],[],[],[],[],[],[],lambda rows:np.zeros(len(rows)))
 cols=[
  Candidate('a',1.,-10.,tuple(),'full_a',('a',),'full_graph'),
  Candidate('b',1.,-9.,tuple(),'full_b',('b',),'full_graph'),
  Candidate('c',1.,-1.,tuple(),'bridge_c',('c',),'bridge_prefix'),
 ]
 def price(lam,nu,mode):
  assert mode=='partial'
  return cols,{'minimum_reduced_cost':-10.}
 status,master,hist=run_joint_cg(state,price,max_rounds=1,max_new_per_round=2,
  lane_minimums={'bridge_prefix':1},checkpoint=None)
 assert status=='ROUND_LIMIT_OPEN'
 assert state.A.shape==(0,2)
 assert set(state.column_signatures)=={'full_a','bridge_c'}
 assert hist[0]['added']==2
 print('PASS_TRUE_DUAL_MULTILANE_RESERVATION_WITH_SHARED_RMP')
if __name__=='__main__':main()
