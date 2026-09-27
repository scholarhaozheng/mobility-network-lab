# Preregistered finite space-time transfer

Case selection used positive Phase B demand, a shared static bottleneck, alternate routes, directed reachability and a declared size gate before any Hong Kong dynamic solver result. The 10-OD selected core contains 111 physical links, 11,954 dynamic nodes and 24,910 arcs at 30-second steps over 25 minutes. Physical movement capacity is hourly PCE multiplied by 30/3600. Turns and zone access are zero-time nonphysical arcs; waiting consumes time. The 15/30-second rounding and route-order audit is saved.

The full finite arc-flow LP reference objective is 75.0363298579 vehicle-minutes; independent balance, capacity and physical mapping checks pass. The frozen Lagrangian R3 dual bound is 74.4777450849. Separate restricted-path recovery is feasible at the LP reference objective and has an independently certified 0.7444% gap.

The frozen CG run is **gated**: Phase I retained 4.3502187198 artificial PCE after the path enumerator reached its fixed 50,000-state limit for nine ODs. Phase II and independent pricing closure were not reached. Frozen ADMM R2 is **gated**: its first local QP had 0.082467622 PCE conservation residual against 1e-5, and the independent saved-state evaluator failed. Neither gated method has an accepted objective. The selected case and frozen policies were not changed after these results.

Static Beckmann objectives and finite LP vehicle-minute objectives represent different mathematical models and are not compared numerically.
