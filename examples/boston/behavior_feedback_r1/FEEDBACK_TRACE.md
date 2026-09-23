# One auditable feedback trace

This is the historical `behavior_feedback_r1` trace. For the corrected selected scenario, use the [current feedback walkthrough](../behavior_feedback_r1_semantic_fix_r1/FEEDBACK_TRACE.md).

Status: **technical propagation demonstrated; empirical validation not established**.

1. GPS observation `gps-stop-pair:mbtav:cccdb505033abedc:s01:5-10` is the pre-qualified MBTA trip `78591067` on route `749`, direction `1`, stop interval `1788→5093`. Its elapsed time is 86 s versus 180 s scheduled.
2. Disabled-by-default parameter `gps_midday_stop_pair_09` carries factor 0.477778; it is a same-sample midday exploratory overlay, not an independently validated AM parameter.
3. For `panel_od_019` at `12:30:00`, the time-dependent GTFS path changes from 28.099 to 27.403 min.
4. Under the explicitly non-empirical `mu_transit=1.0` boundary diagnostic, walk-access-transit probability changes from 0.040990 to 0.046064; corresponding TW person trips change from 0.111465 to 0.125262.
5. Selected-OD auto vehicle trips change from 2.164631 to 2.153178. The same FW solver then changes aggregate panel-only flow on link `16105` from 19.280398 to 19.237405 vehicles (Δ=-0.042993).

Fixed: OD person weight; GMNS network; GTFS feed; TDM23 coefficients/base shares; all non-overlay service; FW solver/capacity.

Changed: only named GPS service overlay, affected GTFS times, nested-pivot demand, derived vehicle OD.

This difference is a model-internal dependency-chain result, not observed causal evidence.
