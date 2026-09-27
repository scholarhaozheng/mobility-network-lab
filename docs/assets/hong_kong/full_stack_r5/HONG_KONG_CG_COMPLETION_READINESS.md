# Hong Kong current-CG completion R5

**Status: `ACCEPTED_BOUNDED_HONG_KONG_CG_WITH_INDEPENDENT_PRICING_CLOSURE`.** This accepts the bounded finite current-CG transfer only. The R2–R4 city/four-stage/static/LP/Lagrangian technical core remains accepted; frozen ADMM R2 remains gated.

The unchanged `HK_TST_JORDAN_10OD_30S_50STEPS_R2_R4` case has 11,954 dynamic nodes, 24,910 arcs, ten demands, 30-second steps, 50 steps, and the exact original K=1 seed signature `663f62669debfac29eb130194e4a4f5e9f2b0576c8c41aaeb3b053bec61a2481`. Its model signature is `552877e54d71851891a8dc23a4d08fd14d1e6719ff60267713200912f0ef4847`.

Accepted current source cleared Phase I artificial flow from 4.350218720 to zero in 12 rounds. Phase II added 3 columns in 2 attempted rounds. The final RMP has 25 columns and objective 75.036329857948 vehicle-minutes.

The independent complete-DAG m+1 pricing check covers all ten demands. Its minimum ungenerated reduced cost is 0, above the fixed −1e−6 closure threshold. No closure continuation column was needed. Independently reconstructed primal objective is 75.036329857948 vehicle-minutes versus 75.036329857948 for the unchanged same-graph arc-flow LP. Demand and capacity residuals are zero within 1e−6; the separate saved-result path, cost and physical-flow audit passed.

All six focused current-stack regressions passed. Five required accepted source hashes and model/seed identities matched. No accepted source was repaired; the R5 scripts only adapt paths, render saved results and package evidence. The legacy 50,000-state Phase-I enumerator was not active. R1 and R2–R4 protected hashes were unchanged.

The public candidate contains the previously approved R2–R4 public boundary and R5 aggregate results/figures. The receiver handoff retains the detailed final columns, flows and duals for solver-free checking. No Git operation or publication occurred.

**Claim boundary.** This is a bounded 10-OD technical case, not a citywide dynamic assignment, empirical calibration, proof of general CG convergence, or accepted ADMM result. Hong Kong input free speeds, capacities, activity and demand remain graded engineering assumptions. Static Beckmann and finite fixed-cost objectives are not compared numerically.
