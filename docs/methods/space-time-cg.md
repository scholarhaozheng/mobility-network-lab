# Finite space–time construction and column generation

This page explains the **implemented finite fixed-cost, capacitated model branch**. It does not claim a dynamic traffic simulation, spillback model or a complete dynamic user equilibrium. Static FW and Diagnostic L3 solve a separate BPR/Beckmann model.

## Build the representation before solving

A physical network and a declared discrete horizon are converted to node-time states. Movement arcs retain `physical_link_id`, tail/head physical nodes, `from_time`, `to_time`, cost and capacity. A movement starts at departure state `(i,t)` and ends at its modeled arrival `(j,t+travel_time)`. Waiting arcs remain at `i` but advance one allowed time step. Demand-specific source and arrival-to-sink connectors bind origins, departures and destination support. These computational connectors are distinct from geographic centroid access.

The converter's tables are `dynamic_node.csv`, `dynamic_arc.csv`, `dynamic_demand.csv`, and `dynamic_columns.csv` in the existing profile. Verify the active schema/header in the actual instance; filenames alone do not establish a contract. A path column stores its ordered arc sequence, demand ID, cost and time information. Waiting may appear in `arc_sequence` without appearing as a physical road in the condensed node/link list.

## Phase I: find feasible real-path capacity use

Artificial demand variables allow the restricted master to expose uncovered demand while respecting its configured constraints. The Phase-I objective prioritizes clearing artificial mass under its declared formulation. Dual information feeds a path-pricing oracle; selected improving, nonduplicate paths enlarge the real pool. Reoptimizing the master can redistribute shared capacity across demands, so a path priced for one OD may reduce another OD's artificial mass.

Artificial flow is not measured unserved passengers, an observed queue or a road vehicle count. Candidate generation, candidate selection and positive final flow are distinct events.

## Phase II: optimize real path cost

Once the recorded real-path initialization is feasible, the cost restricted master and pricing loop continue on the declared time network. The project can compare the final objective with a same-instance arc-flow LP. A finite candidate cap, partial oracle or reference-objective stopping condition must not be relabeled exhaustive reduced-cost closure. The saved 200/250-OD runs explicitly do not claim global convergence.

## Inspect the actual example

[Sioux Falls construction and mechanism](../cases/sioux-space-time.md) provides actual IDs, phase traces, reference agreement and boundaries. [Current CG source](../../app/src/gmns_dynamic/run_full_cg_v1.py) implements the orchestration; the external-network and conversion modules govern which graph is actually available.

Boston's static expansion does not implicitly execute this branch. A Boston CG experiment would separately need a time/horizon/capacity model, demand support and resource plan. There is no case-specific Boston CG execution in the supplied release evidence.
