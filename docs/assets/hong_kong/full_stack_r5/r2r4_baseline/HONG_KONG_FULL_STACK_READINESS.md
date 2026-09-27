# Hong Kong full-stack bounded case — gated transfer

Phase A and B are accepted as a **reproducible technical scenario**. The 95-zone turn-aware network contains 1,239 directed physical links. The four-stage model balances all 8,930 directed interzonal pairs and loads 723.191228 PCE in the 08:00–09:00 one-hour static assignment. Frozen FW and Algorithm B pass independent same-problem verification.

The pre-registered 10-OD finite graph has 11,954 dynamic nodes and 24,910 arcs. Its reference LP is 75.036329858 vehicle-minutes and independently feasible. Frozen Lagrangian R3 passes with a separately recovered feasible primal at 75.036329858 and a 0.7444% independent duality gap.

**First exact blocking gate:** Frozen CG Phase I retains 4.350218720 artificial PCE. Its path enumerator hit the fixed 50,000-state limit for nine of ten ODs; no improving nonduplicate candidate was generated. Phase II and pricing closure were not reached. The selected instance and numerical policy were not replaced or retuned.

Frozen ADMM R2 also gates on its first local commodity QP: 0.082467622 PCE conservation residual exceeds 1e-5, with zero completed outer iterations. Its saved state fails independent primal, capacity and projection checks. No accepted ADMM objective is reported.

This delivery therefore records **accepted data/four-stage/static/LP/Lagrangian core with two gated algorithm transfers**. It does not claim `HONG_KONG_FULL_STACK_BOUNDED_CASE_ACCEPTED` or four-method success. The model is not a full-territory official forecast or locally calibrated production travel model. Free speeds, lane counts, capacities, activity attractions, internal capture, gravity impedance, mode constants and occupancy are explicitly graded engineering assumptions. Annual census counts, one detector snapshot and one research-vehicle reference trace do not establish empirical traffic validation.
