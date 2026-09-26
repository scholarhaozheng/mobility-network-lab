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

## 1. From the physical network to time-indexed columns

A physical network and a declared discrete horizon are converted to node-time states. Movement arcs retain `physical_link_id`, tail/head physical nodes, `from_time`, `to_time`, cost and capacity. A movement starts at departure state `(i,t)` and ends at its modeled arrival `(j,t+travel_time)`. Waiting arcs remain at `i` while advancing one allowed time step. Demand-specific source and arrival-to-sink connectors bind origins, departures and destination support. These computational connectors are distinct from geographic centroid access.

The converter's tables are `dynamic_node.csv`, `dynamic_arc.csv`, `dynamic_demand.csv`, and `dynamic_columns.csv` in the current profile. Verify the active schema and header in the actual instance; filenames alone do not establish a contract. A generated column stores its ordered arc sequence, demand ID, cost and time information. Waiting may appear in `arc_sequence` without appearing as a physical road in the condensed node/link list.

## 2. Phase I restores feasibility

Artificial variables let the restricted master expose demand that the current real-path column pool cannot yet carry while respecting the configured capacity and conservation constraints. The Phase-I objective prioritizes clearing **artificial flow**. Dual information feeds a pricing oracle; selected improving, nonduplicate generated columns enlarge the real-path pool.

Restricted-master reoptimization can redistribute shared capacity across demands. A column generated for one OD may therefore reduce another OD's artificial flow. Artificial flow is not measured unserved passengers, an observed queue or a road-vehicle count. Candidate generation, candidate selection and positive final column flow are distinct events.

## 3. A new path can help a different OD

The master couples all demands through shared time-indexed capacities. When a newly generated column moves one demand away from a binding arc, another demand may use the released capacity. This cross-OD effect must be demonstrated from saved before/after master solutions; one selected column is not automatically a unique causal explanation.

Boston and Sioux Falls both retain saved shared-capacity examples, with different demand IDs and network structures. Their case pages use the same section title and evidence language.

## 4. Phase II improves the real-path objective

After Phase I clears artificial flow, Phase II minimizes real path cost on the declared finite time-expanded graph. Pricing uses the current restricted-master duals to seek improving ungenerated columns. A strict objective decrease is not required in every degenerate linear-programming pivot; a valid nonincreasing commit may rotate the optimal basis and dual before a later strict decrease.

A finite candidate cap, partial oracle or reference-objective stopping condition must not be relabeled exhaustive pricing closure. Boston R3 first established reference-objective agreement; Boston R4 then separately established independent pricing closure. The retained Sioux Falls 200/250-OD runs establish reference-objective agreement but not independent pricing closure.

## 5. Final physical-link movement flow and validation

Time-indexed movement arcs are aggregated by `physical_link_id` to obtain final physical-link movement flow. Waiting arcs and demand-specific source/sink connectors are not physical road flow. A complete saved-result audit checks at least:

- demand conservation;
- capacity violations;
- path continuity and time monotonicity;
- reported versus independently recomputed objective;
- model/graph identity between CG and the reference LP;
- physical-link back-projection.

## 6. Independent pricing closure

For each demand, an independent evaluator searches the complete finite time-expanded graph for the minimum-reduced-cost **ungenerated** feasible path under the final restricted-master duals. Closure is established only if every demand satisfies the declared tolerance. Existing-column KKT/stationarity and ungenerated-path pricing closure are different checks.

Boston R4 establishes closure for 10/10 demands at `1e-6`. The retained Sioux Falls 200/250-OD results do not yet have an equivalent certificate.

## 7. Executed cases and boundaries

- [Boston bounded pilot](../cases/boston-space-time.md): one real-city GMNS subnetwork, 90 physical nodes, 125 directed links, 10 ODs, 3-second steps, 100-step horizon; Phase I and Phase II completed; reference-objective agreement and independent pricing closure established.
- [Sioux Falls historical selected-OD benchmarks](../cases/sioux-space-time.md): 200-OD and 250-OD finite time-expanded instances; Phase I and Phase II completed; reference-objective agreement established; independent pricing closure not established.

The [current CG orchestration source](../../app/src/gmns_dynamic/run_full_cg_v1.py) remains available for inspecting the implementation; its external-network and conversion modules govern which graph is actually built. The case pages distinguish inspecting saved results from running that source on new inputs.

These case results do not establish citywide dynamic assignment, unique path-flow patterns, general convergence at arbitrary scale, or comparability with static BPR/Beckmann objectives.
