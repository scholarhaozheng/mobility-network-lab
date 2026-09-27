# Hong Kong · bounded Tsim Sha Tsui–Jordan case

This is an **accepted bounded technical case**, not an empirically calibrated Hong Kong forecast. It extends the retained [R1 GMNS/data pilot](hong-kong-gmns-pilot.md) without rewriting that historical checkpoint. The R2–R4 public bundle adds an assignment-ready, turn-aware network, a four-stage engineering scenario, static Frank–Wolfe and Algorithm B, and a preregistered finite space–time reference LP. R5 completes current two-phase column generation (CG) and independent pricing closure on the **unchanged ten-demand finite case**. Hong Kong ADMM remains gated.

| Layer | Saved result | Scope |
|---|---|---|
| City graph and hierarchy | 780 physical nodes, 1,239 directed physical links, 95 fine SSG zones, 10 STPUG parents | Source IDs, nonphysical access, turn and grade-separation checks retained |
| Four-stage scenario | 8,930 reachable directed interzonal OD pairs; 723.191 PCE modeled one-hour road load | Transferred rates, proxy activity, sensitivity mode choice; not observed demand |
| Static assignment | Turn-aware FW and official `tap-b` Algorithm B agree under the accepted task-local lossless TAPLab-compatible adapter | Stock official-adapter parity is **not** claimed for Hong Kong |
| Finite space–time LP / CG | 10 ODs, 111 selected physical links, 11,954 dynamic nodes, 24,910 arcs; CG and LP agree at 75.036329857948 vehicle-minutes | Independent full-DAG pricing closure passes 10/10 demands at 1e-6 |
| Lagrangian / ADMM | Feasible Lagrangian primal with 0.7444% certified gap; ADMM R2 gated before accepted outer iterations | No accepted Hong Kong ADMM objective |

![Hong Kong bounded physical network with modeled static flow](../assets/hong_kong/full_stack_r5/r2r4_baseline/figures/hk_full_stack_overview.png)

*Official-derived physical roads and **modeled** one-hour static PCE, not an observed traffic map.* [SVG](../assets/hong_kong/full_stack_r5/r2r4_baseline/figures/hk_full_stack_overview.svg) · [Source record](../assets/hong_kong/full_stack_r5/r2r4_baseline/figures/hk_full_stack_overview.source.json).

## Read the evidence in model order

1. [GMNS objects, source register and rights boundary](../datasets/hong-kong-gmns.md) distinguish physical links, turn states, centroids, connectors and the two zone levels.
2. [Four-stage scenario](hong-kong-four-stage.md) gives the population/household/activity preparation, transferred trip rates, distribution, mode costs and observation grades.
3. [Static assignment](hong-kong-static-assignment.md) gives FW, Algorithm B, independent conservation and turn checks under one BPR objective.
4. [Finite space–time CG, reference LP, Lagrangian and ADMM gate](hong-kong-space-time.md) separates each mathematical certificate.
5. [Evidence contract](../methods/hong-kong-evidence-contract.md) names the assumptions, source rights and supported reproduction.

The [R5 public bundle](../assets/hong_kong/full_stack_r5/PUBLIC_CANDIDATE_README.md) preserves the accepted R2–R4 public candidate under `r2r4_baseline/` and adds only approved aggregate CG evidence. Its old gated CG text is **historical R2–R4 evidence, superseded by R5**; it is not the current Hong Kong CG status. The original R1 pilot remains a separately dated data checkpoint, not the assignment gate for this later case.
