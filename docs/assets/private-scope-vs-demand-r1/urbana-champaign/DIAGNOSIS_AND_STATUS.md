# C02 Urbana–Champaign: scope versus demand diagnosis (R1)

## Conclusion

The accepted original T4 is a nonbinding-capacity model for four OD pairs in the first five-minute bin of a 19.303 km2 central Champaign–Urbana city subarea. The short optimization traces follow from the selected demand and time-bin rule: the four hash-ranked pairs total only 0.05162314826794134 PCE in the loaded bin, while the smallest physical time-arc capacity is 3.75 PCE. The original LR and ADMM each met their frozen certificate or residual stop in one iteration; there is no evidence that an iteration cap artificially ended a capacity-active calculation. A compatible outer-network G control has not been run. Thus geography's causal effect on the same OD paths, cost, or capacity competition remains NOT_TESTED.

All previous S72, Native9, B, 418-OD four-stage, original T4 and new CUMTD bus→choice→FW accepted outcomes are read-only. The new transit-revision vehicle total of 1667.0899464425695 PCE/h belongs to a different demand identity and is never used to explain old T4.

## Identity and accounting

The original T4 model signature is bd634a94e6dfa1435fdb087bc78fc87959198537b314d44cedd953465c71d8b. Frozen Stage3 OD SHA256 is 34b6ff081d51ad326871769c8231abf88a5a58b2904c3e160e500a5dfdadc4b6; original static turn-expanded network SHA256 is f451468b31e51dce09e62760768e5bd762437dc8c16ba3f43abfcfe68c340df0; T4 time arc SHA256 is 76db0032a865d56a8823c17d4a049491d037799a323bbba7bc30e3d809689764. The separate CUMTD vehicle OD SHA256 is f2b7b270f8b4686a73082604e74d46461ff6e9542f64d71d0b44190f54b20789.

OD_LEDGER.csv lists all 418 Stage3 pairs, frozen SHA256 rank, source hourly PCE, selected/excluded reason, original zone-access nodes and GMNS links, first-bin amount, remaining eleven-bin amount, and unselected hourly amount. Every rank and hash key (network SHA | origin | destination) matched the accepted source. Four selected hourly OD volumes are 0.008379147452691818, 0.02373560946215502, 0.2824469184690113, and 0.3049161038314379 PCE/h. Stage3 already expresses vehicle PCE/h. Each selected pair is divided by twelve exactly once; there is no second persons-to-vehicles conversion.

| Item | Frozen value | Evidence status |
|---|---:|---|
| Geographic Stage3 background | 19.303 km2 city subarea, 21 zones | known |
| Original physical/turn solver arcs | 11,365 / 15,237 (26,602 total) | known |
| T4 retained time graph | 1,429,496 arcs; 668,725 nodes; 334,794 timed physical arcs | known; not geographic area |
| Full hour Stage3 | 418 OD; 1963.64831271256 PCE/h | independently checked |
| Selected full hour | 4 OD; 0.6194777792152961 PCE/h | independently checked |
| Selected first five minutes | 0.05162314826794134 PCE | independently checked |
| Selected other eleven bins excluded | 0.5678546309473548 PCE | independently checked |
| Other 414 OD whole hour excluded | 1963.02883493334 PCE/h | independently checked |
| Time rule | 30 s arcs, departure step 5 at 08:02:30, H160 at 09:20 | frozen model |
| Capacity resource | one row per physical time arc, hourly effective PCE divided by 120; min 3.75 | frozen model and source-row audit |
| Original objective lower and upper | 0.375983665133529 PCE-minute; gap about 5.6e-16 | accepted independent LP/dual certificate |
| Original AON | maximum timed physical arc utilization 0.677591%; zero OD-shared timed physical arcs | extracted accepted positive flow |
| Actual old iterations | DAG LP direct certificate; CG one round per phase; LR one; ADMM one plus cold-start confirmation | accepted receipts |
| New D candidate | design frozen; input screen, build, solve not executed | resource gated |
| G geographic control | no compatible frozen outer turn-expanded graph demonstrated | GEOGRAPHIC_CAUSALITY_NOT_TESTED |

Q_T times twelve equals 0.6194777792152961, approximately 0.03155% of the full 418-OD hourly total. This is a bookkeeping relation for a deliberately selected four-pair cohort, not an empirical sampling rate or measured travel behavior. Time-bin loading cuts the selected hour quantity by exactly another factor of twelve.

The accepted four path lengths are 135, 115, 189, and 311 time arcs, containing 67, 57, 94, and 155 physical arcs. All have zero wait arcs. They exit through zero-cost accounting sink connectors at 08:36, 08:31, 08:50, and 09:20 respectively. The last arrival touches H, so the horizon can restrict alternatives, but the terminal connector does not model a physical queue or DNL waiting. Across all positive paths, 373 timed physical arcs are used. Twenty-eight source physical road links are shared by different OD across different times; zero timed physical arcs are shared by different OD.

## Why the original capacity proof is valid, and its limit

The frozen capacity row represents one timed physical arc, never an aggregate of several arcs or bins. The old complete time graph is a DAG, and each commodity enters through its own single source connector. For nonnegative path flows with no cycles or extra source, a unit path consumes at most one unit of any one timed-arc resource. Thus the maximum flow on any row is at most the total Q=0.05162314826794134 PCE, strictly below the minimum physical row capacity 3.75 PCE. The old capacity inequalities are redundant. The accepted independent LP check reports zero capacity rows after this proof, zero balance residual, zero capacity violation, and matching primal/dual objective. An aggregate capacity row would require its own path-resource coefficient bound. The proof cannot be transferred to any new possibly binding model.

Original LR stopped with CERTIFIED_GAP after one iteration. Original ADMM reached its frozen primal/dual residual tests after one iteration; objective differs from LP by 8.44e-12 PCE-minute, and an independent cold run reproduced its state. The short traces are consistent with this genuinely easy nonbinding instance.

## Controls, geography, and resources

CONTROLLED_DESIGN.json was saved before any new candidate solver endpoint. D holds the original physical network, road capacity/cost, direction, turn, 30-second step, H160, original four OD and first-bin rule fixed. It adds at most one original Stage3 OD selected by descending hourly PCE, with origin/destination IDs breaking ties. At most the top two are checked for directed rounded shortest duration no more than 145 steps; the first eligible is used, or no candidate. Candidate quantity is original hourly PCE divided by twelve once. There is at most one solver-ready graph and one CG full-graph reference attempt. No capacity decrease, arbitrary demand multiplier, post-failure OD shrinkage, time-horizon change, or new CUMTD demand is allowed. Because a new OD changes the reachability-pruned retained graph, D is conservatively DESCRIPTIVE_ONLY even though the original physical road source stays fixed. The first two source-ranked inputs are 67.1893424332 and 67.0443556836 PCE/h; neither is yet a selected or solved new case.

The existing underlying GMNS/OSM source is broader than the accepted 26,602-arc clipped solver graph. It is not itself a same-source, same-direction, cost/capacity/access-compatible compiled outer-ring control with proven original-graph embedding. No new outer-ring network is compiled in this task. Internal 418-OD closure omits unmeasured external/through trips; their magnitude cannot be inferred from this absence. Clipped legal alternatives may change costs, and added roads could reduce costs. Hence G remains GEOGRAPHIC_CAUSALITY_NOT_TESTED.

SEMANTIC_NEGATIVE_TESTS.json records a passing positive control and four rejected cases: duplicate 5-minute hourly load, mixing new CUMTD with old T4 identity, hiding one unserved OD, and a bad access mapping. FIG01 and FIG02 show only real old demand and capacity use. There is no new convergence line or new physical back-projection.

The original shared guard was attempted with zero wait. The preserved RESOURCE_RECEIPTS report LOCK_TIMEOUT for the heavy audit and input-only screen. C06 ADMM and C01 choice→FW have priority; no timer or lock polling is active. The guarded new topology/memory screen, T_candidate, new AON, reference CG, new full-graph certificate, and new-model cleanroom replays are pending. Two read-only PrivateFull light-package replays in Chinese-space paths passed and are recorded under validation. No CAPACITY_ACTIVE claim is made. The safe next command is recorded in REPRODUCE.md; it must run only when the shared lock is free. A prior direct heavy audit attempt was rejected by automatic approval review because it bypassed the mandated shared lock; it was not repeated outside the guard. Existing accepted frozen certificates remain the authoritative full-graph checks.

No commit, push, deploy, cross-thread message, public release, or change to old sources was made. Public scope for each asset, especially GTFS/GPS/private GIS, requires separate S0 review.

