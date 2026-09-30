# Finite space–time construction and column generation

This page explains the implemented **fixed-cost, hard-capacity finite space–time model branch**. It is not a dynamic traffic simulation, a spillback model, or a complete dynamic user-equilibrium model. Static Frank–Wolfe and Diagnostic L3 solve a separate BPR/Beckmann problem.

## Canonical terms used in this repository

- **finite space–time CG**: the method family;
- **finite time-expanded graph**: the actual node-time graph used by one case;
- **artificial flow**: the Phase-I feasibility device;
- **generated column**: one demand-specific feasible path through the time-expanded graph;
- **final column pool**: the retained generated columns after the accepted solve or certificate continuation;
- **final physical-link movement flow**: time-indexed movement flow aggregated back to physical links;
- **reference-objective agreement**: equality, within the declared tolerance, between CG and the arc-flow LP on the same finite time-expanded graph;
- **independent pricing closure**: an additional certificate that every demand's minimum ungenerated-path reduced cost is nonnegative within the declared tolerance.

Reference-objective agreement and independent pricing closure are separate claims.

## 1. From the physical network to the finite time-expanded graph

A physical network and a declared discrete horizon are converted to node-time states. Movement arcs retain `physical_link_id`, tail/head physical nodes, `from_time`, `to_time`, cost and capacity. A movement starts at departure state `(i,t)` and ends at its modeled arrival `(j,t+travel_time)`. Waiting arcs remain at `i` while advancing one allowed time step. Demand-specific source and arrival-to-sink connectors bind origins, departures and destination support. These computational connectors are distinct from geographic centroid access.

The converter's tables are `dynamic_node.csv`, `dynamic_arc.csv`, `dynamic_demand.csv`, and `dynamic_columns.csv` in the current profile. Verify the active schema and header in the actual instance; filenames alone do not establish a contract. A generated column stores its ordered arc sequence, demand ID, cost and time information. Waiting may appear in `arc_sequence` without appearing as a physical road in the condensed node/link list.

The first representation is the **physical network**, the second is its **finite time-expanded graph**. This construction diagram is not a path selected by column generation and not a final flow map. The three case-specific diagrams are [Boston](../cases/boston-space-time.md#from-the-physical-network-to-the-finite-time-expanded-graph), [Sioux Falls](../cases/sioux-space-time.md#from-the-physical-network-to-the-finite-time-expanded-graph), and [Hong Kong](../cases/hong-kong-space-time.md#from-the-physical-network-to-the-finite-time-expanded-graph).

## A generated column as a time-indexed path

A **generated column** is one feasible demand-specific source-to-sink path through that graph. Its ordered movement, waiting, and source/sink arcs are a third object: neither the whole graph nor the final physical-link movement-flow aggregate. The three case pages show one accepted column each, with source-qualified arc identities. Hong Kong's selected R5 column is a deliberately bounded public excerpt; the full pool and dual arrays are not released.

## 2. Phase I restores feasibility

Artificial variables let the restricted master expose demand that the current real-path column pool cannot yet carry while respecting the configured capacity and conservation constraints. The Phase-I objective prioritizes clearing **artificial flow**. Dual information feeds a pricing oracle; selected improving, nonduplicate generated columns enlarge the real-path pool.

Restricted-master reoptimization can redistribute shared capacity across demands. A column generated for one OD may therefore reduce another OD's artificial flow. Artificial flow is not measured unserved passengers, an observed queue or a road-vehicle count. Candidate generation, candidate selection and positive final column flow are distinct events.

## 3. Shared capacity couples different OD demands

The master couples all demands through shared time-indexed capacities. When a newly generated column moves one demand away from a binding arc, another demand may use the released capacity. This cross-OD effect must be demonstrated from saved before/after master solutions; one selected column is not automatically a unique causal explanation.

Boston and Sioux Falls both retain saved shared-capacity examples, with different demand IDs and network structures. No comparable before/after cross-OD event is demonstrated for Hong Kong R5; its common case section says so explicitly.

## 4. Phase II improves the real-path objective

After Phase I clears artificial flow, Phase II minimizes real path cost on the declared finite time-expanded graph. Pricing uses the current restricted-master duals to seek improving ungenerated columns. A strict objective decrease is not required in every degenerate linear-programming pivot; a valid nonincreasing commit may rotate the optimal basis and dual before a later strict decrease.

A finite candidate cap, partial oracle or reference-objective stopping condition must not be relabeled exhaustive pricing closure. Boston R3 first established reference-objective agreement; Boston R4 then separately established independent pricing closure. Hong Kong R5 likewise establishes both on its unchanged bounded ten-demand graph. The retained Sioux Falls 200/250-OD runs establish reference-objective agreement but not independent pricing closure.

## 5. From time-expanded flows back to final physical-link movement flow

Time-indexed movement arcs are aggregated by `physical_link_id` to obtain final physical-link movement flow. Waiting arcs and demand-specific source/sink connectors are not physical road flow. A complete saved-result audit checks at least:

- demand conservation;
- capacity violations;
- path continuity and time monotonicity;
- reported versus independently recomputed objective;
- model/graph identity between CG and the reference LP;
- physical-link back-projection.

## 6. Independent pricing closure

For each demand, an independent evaluator searches the complete finite time-expanded graph for the minimum-reduced-cost **ungenerated** feasible path under the final restricted-master duals. Closure is established only if every demand satisfies the declared tolerance. Existing-column KKT/stationarity and ungenerated-path pricing closure are different checks.

Boston R4 and Hong Kong R5 each establish closure for 10/10 demands at `1e-6` on **different** finite graphs. The retained Sioux Falls 200/250-OD results do not have an equivalent certificate.

## 7. Executed cases and boundaries

- [Boston bounded pilot](../cases/boston-space-time.md): one real-city GMNS subnetwork, 90 physical nodes, 125 directed links, 10 ODs, 3-second steps, 100-step horizon; Phase I and Phase II completed; reference-objective agreement and independent pricing closure established.
- [Sioux Falls historical selected-OD benchmarks](../cases/sioux-space-time.md): 200-OD and 250-OD finite time-expanded instances; Phase I and Phase II completed; reference-objective agreement established; independent pricing closure not established.
- [Hong Kong bounded R5 case](../cases/hong-kong-space-time.md): unchanged 10-OD, 30-second, 50-step graph; Phase I artificial flow cleared in 12 rounds, Phase II reached the same-graph arc-flow LP objective, and independent full-DAG pricing closure passed 10/10 demands. Its separately frozen ADMM transfer remains gated.

The [current CG orchestration source](../../app/src/gmns_dynamic/run_full_cg_v1.py) remains available for inspecting the implementation; its external-network and conversion modules govern which graph is actually built. The case pages distinguish inspecting saved results from running that source on new inputs.

These case results do not establish citywide dynamic assignment, unique path-flow patterns, general convergence at arbitrary scale, or comparability with static BPR/Beckmann objectives.

<!-- layered-r2-cross-case-cg:start -->
<a id="cg-experiments"></a>
### Executed finite space–time CG experiments

The repository contains **three distinct executed CG case families**. Boston is one bounded real-city pilot on an accepted GMNS subnetwork; Sioux Falls contains two historical selected-OD benchmark instances; Hong Kong R5 is a separately frozen ten-demand Tsim Sha Tsui–Jordan finite case. They share a method family, not a graph, demand, objective value or universal certificate.

<p align="center"><a href="../methods/space-time-cg.md"><img src="../assets/presentation_r5/boston_sioux_cg_parallel_overview.png" width="100%" alt="Six-stage comparison of executed finite space–time CG evidence: one bounded Boston pilot and two historical Sioux Falls selected-OD runs. Both have saved Phase-I, Phase-II, final-flow and reference evidence; independent pricing closure is established only for Boston."></a></p>

| Executed evidence | Boston | Sioux Falls | Hong Kong |
|---|---|---|---|
| **Instance** | 90 physical nodes, 125 links, 10 ODs, 3-second steps, 100-step horizon | Historical 200/250-OD selected subsets | 111 selected physical links, 10 ODs, 30-second steps, 50-step horizon; 24,910 dynamic arcs |
| **Phase I** | Artificial flow **20.5536128974 → 0** in round **90** | Artificial flow reaches zero in rounds **51 / 62** | Artificial flow **4.3502187198 → 0** in **12** rounds |
| **Phase II** | **64.39686151152954** vehicle-min; own-LP agreement | **943,155.589771 / 1,521,090.836620**; each own-LP agreement | **75.03632985794835** vehicle-min; own-LP agreement after three added columns |
| **Pricing certificate** | Independent full-DAG closure **10/10** at `1e-6` | **Not established** for retained historical runs | Independent full-DAG closure **10/10** at `1e-6` |
| **Open the evidence** | [Boston case](../cases/boston-space-time.md) | [Sioux case](../cases/sioux-space-time.md) | [Hong Kong R5 case](../cases/hong-kong-space-time.md) |

*The Boston/Sioux image is an earlier two-city saved overview, retained without being relabeled as a three-city figure. Hong Kong's separate R5 figures appear [on its current case page](../cases/hong-kong-space-time.md). None is a citywide CG or a calibrated forecast. Fixed-cost hard-capacity CG objectives are not numerically comparable with static BPR/Beckmann FW.* [Boston/Sioux overview SVG](../assets/presentation_r5/boston_sioux_cg_parallel_overview.svg) · [Source hashes](../assets/presentation_r5/CG_CASE_SEQUENCE_SOURCES.json) · [Earlier saved overview](../assets/presentation_r4/cg_experiments_overview.png).
<!-- layered-r2-cross-case-cg:end -->
