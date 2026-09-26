# Distributed assignment / accepted bounded evidence and gates

These methods sit alongside, not in place of, the [static FW and finite space–time CG branches](../methods.md). Lagrangian R2 and ADMM R1 below use fixed-cost, hard-capacity **selected-OD finite time-expanded** Sioux instances. Bush/OBA addresses a different static BPR/Beckmann user-equilibrium problem and has not passed its verification gate. No cross-contract objective ranking is meaningful.

## Lagrangian capacity pricing with separate primal recovery

The dual solver prices shared arc capacities and generates commodity paths. Its best dual value is a lower bound. A **separate restricted-path LP** recovers a feasible primal upper bound; the dual routine did not directly output that flow. The independent evaluator checked the recovered path and physical-link flows, demand conservation, capacities, connectors and objective without optimizer calls. Reference-LP primal paths, flows and duals were not used to generate the algorithm's paths. [Public source, fixtures, histories and exact summary](../../algorithms/distributed_assignment/lagrangian_r2/README.md).

| Selected Sioux instance | Dual lower bound (vehicle-min) | Feasible recovered primal (vehicle-min) | Certified gap | Gate |
|---|---:|---:|---:|---|
| 200 OD | 942,452.403471 | 943,155.589771 | 0.0746% | Accepted regression gate |
| 250 OD | 1,516,258.347432 | 1,521,090.836620 | 0.3177% | Accepted, frozen 1% gate |

<table><tr><td width="50%"><img src="../assets/sioux/distributed_r1/Sioux_200OD_P07.svg" width="100%" alt="Saved Sioux 200-OD Lagrangian dual lower bound and separately recovered feasible upper bound"></td><td width="50%"><img src="../assets/sioux/distributed_r1/Sioux_250OD_P07.svg" width="100%" alt="Saved Sioux 250-OD Lagrangian dual lower bound and separately recovered feasible upper bound"></td></tr></table>

*Accepted saved P07 histories. Each recovered primal matches the arc-flow LP objective on **its own** selected-OD finite graph. The two graphs and demands are different; the gap is not a static UE gap.*

Boston R2 is a **gated transfer**: its separately recovered primal is feasible and matches the accepted same-graph objective, but the certified dual gap is **1.1002%**, exceeding the frozen 1% gate. It is not an accepted Boston Lagrangian result. The older R1 Sioux 250-OD gate failure was superseded by R2; its former dual bound must not be reported as current.

## ADMM local/consensus shared-capacity decomposition

The R1 ADMM implementation uses local commodity arc flows and consensus/capacity variables on the same selected-OD fixed-cost space–time model. The declared primal/dual residual thresholds and independent conservation/capacity checks passed for Sioux 200 and 250 OD. The finite nonzero difference from each same-graph arc-flow LP is **not exact equality**. [Public source, C0 fixture, 200-OD saved history and summary](../../algorithms/distributed_assignment/admm_r1/README.md).

| Selected Sioux instance | ADMM objective (vehicle-min) | Own arc-flow LP (vehicle-min) | LP-relative difference | Outer iterations | Status |
|---|---:|---:|---:|---:|---|
| 200 OD | 943,159.682268 | 943,155.589771 | 0.000434% | 74 | Accepted bounded result |
| 250 OD | 1,521,100.065788 | 1,521,090.836620 | 0.000607% | 94 | Accepted bounded result |

<table><tr><td width="50%"><img src="../assets/sioux/distributed_r1/sioux_200od_objective_difference.svg" width="100%" alt="200-OD accepted ADMM objective above its same-graph LP by 0.000434 percent"></td><td width="50%"><img src="../assets/sioux/distributed_r1/sioux_250od_objective_difference.svg" width="100%" alt="250-OD accepted ADMM objective above its same-graph LP by 0.000607 percent"></td></tr></table>

*Paired scalar saved-result figures, identical axis and layout: the vertical tick is each instance's own LP reference (0%); the dot is the ADMM objective difference. The 250-OD public evidence supplies final metrics, **not an iteration history**, so no 250-OD trajectory was invented. The accepted 200-OD [detailed residual/consensus figure](../assets/sioux/distributed_r1/admm_sioux_200.svg) is supplemental.*

The Boston ADMM transfer failed local commodity conservation (residual **4.18414** under the frozen check) and is **not accepted**. This says nothing about the separate accepted Boston CG or FW results.

## Bush/OBA verification gate

**Bush/OBA research prototype — verification gate not passed; verified upstream baseline work is in progress.** The Sioux static reduced-cost variant's maximum positive-flow root-prefix slack was **6.062 min**, above its **0.05 min** gate. A small aggregate gap alone does not certify the origin-based UE conditions. No accepted Boston Bush transfer or successful Bush card is published.

The accepted Sioux Lagrangian/ADMM selected subsets are not the full 528-OD network and are not a calibrated city forecast. See the [case coverage matrix](../capabilities.md) and [Sioux CG page](../cases/sioux-space-time.md) for the separate column-generation evidence and its certificate limits.
