"""Small exact fixed-service prefix truth and recovery checks."""
from pathlib import Path
import sys
import numpy as np
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'sparse_common_dev40_bridge_multi_cg'))
from shared_cg.bridge_prefix import exact_fixed_target_prefix,recover_fixed_prefix

class M:
 n=4
 dt=60.
 H=10
 u=np.array([0,1,0,2],dtype=np.int32)
 v=np.array([1,2,2,3],dtype=np.int32)
 cost=np.array([1.,0.,2.,1.])
 duration=np.array([1,0,2,1],dtype=np.int32)
 reverse_topo=np.array([3,2,1,0],dtype=np.int32)

def main():
 model=M()
 action,val=exact_fixed_target_prefix(model,2,3,3,np.array([0,1],np.int32))
 assert np.allclose(val[:3,0],[np.inf,1.,2.],equal_nan=True)
 assert np.allclose(val[:3,1],[0.,1.,2.])
 for delta in (1,2,3):
  p=recover_fixed_prefix(model,action,0,5,delta,2)
  assert abs(p.prefix_raw_cost-val[delta,0])<1e-12
  assert 3 not in p.original_edges
  assert len(p.original_edges)==len(p.original_entry_steps)
 assert int(action[0,1])==1
 try:recover_fixed_prefix(model,action,0,0,0,2)
 except ValueError:pass
 else:raise AssertionError('unreachable service accepted')
 print('PASS_FIXED_BRIDGE_PREFIX_COST_ZERO_ARC_WAIT_RECOVERY_NEGATIVE')
if __name__=='__main__':main()
