"""Small policy contract for the wider source candidate stream."""
from pathlib import Path
from types import SimpleNamespace
import sys
import numpy as np

R = Path(__file__).resolve().parent
sys.path.insert(0, str(R / 'sparse_common_dev41_wide_bridge_cg'))
from shared_cg.source_bridge_candidates import SourceBridgePrefixCandidates


def main():
    obj = SourceBridgePrefixCandidates.__new__(SourceBridgePrefixCandidates)
    obj.eligible = np.arange(8, dtype=np.int32)
    obj.saving = np.array([8., 7., 6., 5., 4., 3., 2., 1.])
    obj.base = SimpleNamespace(
        fm=np.ones(8),
        fod=np.array([0, 1, 0, 1, 0, 1, 0, 1], dtype=np.int32),
        fr=np.array([0, 0, 1, 1, 2, 2, 3, 3], dtype=np.int32),
    )
    obj.origin_od = np.array([0, 1], dtype=np.int32)
    selected, windows = obj.select(max_events=4, per_od_window=2,
                                   window_steps=2, chosen_windows=2,
                                   max_per_window=1)
    assert selected.tolist() == [0, 4], selected
    assert windows == [0, 1], windows
    print('PASS wide source selection OD/window capacity contract')


if __name__ == '__main__':
    main()
