"""Frozen two-lane event selection for a coupled, full-event CG experiment.

The receiver lane searches negative adjusted-cost events.  The release lane
searches events whose certified base path carries a high current capacity
price.  Both lanes cover every release window before path recovery; the
common RMP subsequently checks actual resource release and accurate duals.
"""
from dataclasses import dataclass
from collections import defaultdict
import numpy as np


@dataclass(frozen=True)
class SelectedEvent:
    key: int
    adjusted_cost: float
    od: int
    release: int
    window: int
    lane: str
    score: float


class BalancedEventSelector:
    def __init__(self, release_steps, *, window_steps=2048,
                 per_window_per_lane=20, per_od_window_per_lane=2,
                 per_lane_total=160, epsilon=1e-6):
        self.release_steps = int(release_steps)
        self.window_steps = int(window_steps)
        self.per_window = int(per_window_per_lane)
        self.per_od_window = int(per_od_window_per_lane)
        self.per_lane_total = int(per_lane_total)
        self.epsilon = float(epsilon)
        if min(self.release_steps, self.window_steps, self.per_window,
               self.per_od_window, self.per_lane_total) <= 0:
            raise ValueError('balanced selection policy')
        self.window_count = (self.release_steps + self.window_steps - 1) // self.window_steps
        self.pool = []
        self.events_priced = 0
        self.negative_events = 0
        self.positive_donor_toll_events = 0
        self.minimum_reduced_cost = 0.

    def add(self, keys, od, release, mass, adjusted, donor_cost, donor_toll, group_mu):
        keys = np.asarray(keys, np.int64)
        od = np.asarray(od, np.int32)
        release = np.asarray(release, np.int32)
        mass = np.asarray(mass, np.float64)
        adjusted = np.asarray(adjusted, np.float64)
        donor_cost = np.asarray(donor_cost, np.float64)
        donor_toll = np.asarray(donor_toll, np.float64)
        group_mu = np.asarray(group_mu, np.float64)
        if not all(len(a) == len(keys) for a in
                   (od, release, mass, adjusted, donor_cost, donor_toll, group_mu)):
            raise ValueError('balanced event dimensions')
        if np.any(release < 0) or np.any(release >= self.release_steps) or np.any(mass <= 0):
            raise ValueError('balanced release or mass')
        reduced = adjusted - donor_cost - donor_toll - group_mu
        if not np.all(np.isfinite(reduced + mass)):
            raise ValueError('balanced nonfinite event')
        self.events_priced += len(keys)
        self.minimum_reduced_cost = min(self.minimum_reduced_cost,
                                        float(np.min(reduced, initial=0.)))
        negative = reduced < -self.epsilon
        releasing = donor_toll > self.epsilon
        self.negative_events += int(np.count_nonzero(negative))
        self.positive_donor_toll_events += int(np.count_nonzero(releasing))
        window = release // self.window_steps
        for mask, lane, score in ((negative, 'negative_rc', reduced * mass),
                                  (releasing, 'capacity_release', -donor_toll * mass)):
            if not np.any(mask):
                continue
            for i in np.unique(od[mask]):
                by_od = np.flatnonzero(mask & (od == i))
                for w in np.unique(window[by_od]):
                    pos = by_od[window[by_od] == w]
                    order = np.lexsort((keys[pos], score[pos]))[:self.per_od_window]
                    for j in pos[order]:
                        self.pool.append(SelectedEvent(int(keys[j]), float(adjusted[j]),
                                                       int(od[j]), int(release[j]), int(w),
                                                       lane, float(score[j])))

    def select(self):
        selected = []
        per_window = defaultdict(int)
        per_od_window = defaultdict(int)
        for lane in ('negative_rc', 'capacity_release'):
            candidates = sorted((x for x in self.pool if x.lane == lane),
                                key=lambda x: (x.score, x.key))
            lane_count = 0
            # First pass gives every original time window its quota.
            for w in range(self.window_count):
                for x in candidates:
                    if x.window != w or per_window[(lane, w)] >= self.per_window:
                        continue
                    key = (lane, x.od, w)
                    if per_od_window[key] >= self.per_od_window:
                        continue
                    selected.append(x)
                    per_window[(lane, w)] += 1
                    per_od_window[key] += 1
                    lane_count += 1
                    if lane_count >= self.per_lane_total:
                        break
                if lane_count >= self.per_lane_total:
                    break
        return selected, list(range(self.window_count))
