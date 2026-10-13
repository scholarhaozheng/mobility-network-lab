"""Independent source-seed bridge candidate truth on a small legal graph."""
from pathlib import Path
import tempfile,sys
import numpy as np
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'sparse_common_dev40_bridge_multi_cg'))
from shared_cg.source_full_event_base import FullUniformQBase
from shared_cg.source_bridge_candidates import SourceBridgePrefixCandidates

class M:
 n=4;dt=60.;H=10;release_steps=2
 u=np.array([0,0,1,2],dtype=np.int32)
 v=np.array([2,1,2,3],dtype=np.int32)
 cost=np.array([2.,2.5,0.,1.])
 duration=np.array([2,3,0,1],dtype=np.int32)
 reverse_topo=np.array([3,2,1,0],dtype=np.int32)
 physical_pos=np.array([0,1,-1,2],dtype=np.int32)
 physical_edges=np.array([0,1,3],dtype=np.int32)
 capacity_per_step=np.array([2.,2.,2.])
 od=[('o','d',0,3,2.)]

def main():
 with tempfile.TemporaryDirectory() as root:
  p=Path(root)
  np.savez(p/'a.npz',od_edge_offset=np.array([0,2]),edge_index=np.array([0,3]),
           entry_offset_steps=np.array([0,2]),od_hourly_pce=np.array([2.]),
           od_static_shortest_cost=np.array([3.]))
  np.savez(p/'f.npz',od_index=np.array([0,0]),release_step=np.array([0,1]),
           mass_pce=np.array([1.,1.]),wait_steps=np.array([[1],[0]],dtype=np.int32),
           stage_original_edge_index=np.array([3]),selected_od_index=np.array([0]))
  model=M();base=FullUniformQBase(model,p/'a.npz',p/'f.npz')
  oracle=SourceBridgePrefixCandidates(model,base)
  assert oracle.edge==3 and oracle.max_delay==3 and oracle.weighted_wait_steps==1.
  assert abs(oracle.candidate_unit[0]-3.5)<1e-12
  assert abs(oracle.saving[0]-.5)<1e-12 and abs(oracle.saving[1])<1e-12
  selected,windows=oracle.select(max_events=2)
  assert selected.tolist()==[0] and windows==[0]
  e,t,c=oracle.recover(0)
  assert e.tolist()==[1,2,3] and t.tolist()==[0,3,3] and abs(c-3.5)<1e-12
  try:oracle.recover(2)
  except ValueError:pass
  else:raise AssertionError('missing fragment accepted')
  print('PASS_SOURCE_BRIDGE_SELECTION_PREFIX_ROUTE_COST_NEGATIVE')
if __name__=='__main__':main()
