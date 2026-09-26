# Models and methods

## Finite space–time path-flow optimization

The executable workflow allocates continuous path flows with fixed generalized costs, OD demand conservation and shared capacities on time-indexed arcs. In compact form,

```text
minimize    c^T f
subject to  A f = q,  B f <= u,  f >= 0
```

Paths are columns. The implementation constructs an explicit allowed graph, initializes a route pool, uses Phase-I for restricted-pool feasibility, and uses Phase-II pricing to add improving candidates. It exports the exact last successfully solved pool and corresponding primal and dual records.

The workflow computes a reference arc-flow LP on the same finite graph. This makes the current interface useful for bounded experiments; the reference model can be the scaling bottleneck. Do not infer large-city or full-DTA support from the small reference examples.

## Static Frank–Wolfe reference implementation

The retained implementation in [`algorithms/static_fw/`](../algorithms/static_fw/) uses BPR link costs, the Beckmann integral, all-or-nothing shortest-path loading and line search. The catalog includes saved Boston conditional ABS runs and a separately documented historical approximate Sioux Falls result.

This model is different from the hard-capacitated, fixed-cost space–time LP. Its numerical objective cannot be compared directly with the CG objective. The static file is an optional library source, not part of `tools/mnl.py run`; see its module documentation before calling it.

## What a verification statement means

Distinguish input consistency, primal feasibility, agreement with a same-model reference, final-RMP optimality information, and independent pricing closure. A reference objective match does not by itself mean a separate missing-column pricing certificate was generated.

Synthetic reference examples protect implementation behavior. Road benchmark records describe previous experiments. Neither category is a calibrated city demand model.

## Solved finite-path reference and native Diagnostic L3

On the [frozen Boston ABS_PLANNED instance](cases/boston-assignment.md), the [actual uncompressed SLSQP solver](../algorithms/finite_path_reference/README.md) minimizes the original Beckmann objective over 130 nonnegative path variables with exact 26 OD equalities. Its saved F is 707.0579230712882 vehicle-minutes; it is a **finite-pool** reference, not a new full-network method.

The corrected [native Diagnostic L3 implementation](../algorithms/path_compression/diagnostic_l3/README.md) uses one AST-isolated mathematical builder with distinct effective adapters for Boston and Sioux Falls. Boston's accepted rank-26 and rank-52 outer-02 saved results pass their numerical gate on the same ABS_PLANNED network/demand/pool, but small negative signed gaps reflect tolerated OD deficits. Sioux's accepted outer-04 gamma=0.01 and gamma=0 records have remaining full-network cost gaps of 8.167461% and 4.381867%, respectively; neither is a UE certificate. The older unconstrained ordinary-v4 attempt is not the active method.

| Method | Mathematical role | Actual public implementation | Existing case evidence |
|---|---|---|---|
| Static FW | BPR/Beckmann link assignment | [Existing source](../algorithms/static_fw/tap_frank_wolfe.py) | [Boston ABS and semantic branches](cases/boston.md); [historical Sioux FW](cases/sioux-falls.md) |
| Uncompressed finite path | Exact OD equalities on one finite pool | [SLSQP source/config](../algorithms/finite_path_reference/README.md) | [Boston 26OD/130-path reference](cases/boston-assignment.md) |
| Native Diagnostic L3 | Reduced path coordinates plus explicit links, original-space checks | [Builder and two profiles](../algorithms/path_compression/diagnostic_l3/README.md) | [Boston ranks 26/52](cases/boston-assignment.md); [Sioux A/B](cases/sioux-falls.md) |
| Finite time-expanded CG | Fixed-cost hard-capacity linear space–time path flow | [Existing CG source](../app/src/gmns_dynamic/run_full_cg_v1.py) | [Sioux 200OD/250OD history](cases/sioux-falls.md) |
| Lagrangian R2 | Shared-capacity dual lower bound plus separate restricted-path feasible recovery | [Public source and fixtures](../algorithms/distributed_assignment/lagrangian_r2/README.md) | [Accepted Sioux 200/250 OD; Boston transfer gated](methods/distributed-assignment.md) |
| ADMM R1 | Local/consensus decomposition of fixed-cost shared-capacity space–time flow | [Public source and saved evidence](../algorithms/distributed_assignment/admm_r1/README.md) | [Accepted Sioux 200/250 OD; Boston transfer gated](methods/distributed-assignment.md) |

Inspect selected saved records without any solver: `python -B tools/mcl_results.py list --case boston`, then `python -B tools/mcl_results.py verify-saved --run boston-abs-planned-l3-rank26-outer02`. The optional native rerun requires a separately prepared Pyomo/IPOPT/MUMPS environment and explicit output directory; the publication integration did not execute it. These existing records are not a strict paired Boston/Sioux performance experiment, cold-start speedup result, or empirical validation.

## Other method extensions

The [distributed assignment page](methods/distributed-assignment.md) distinguishes accepted bounded Sioux Lagrangian/ADMM evidence from gated Boston transfers. Origin-based/Bush remains a research prototype with a failed used-arc verification condition, not an accepted UE solve. Coupled primal–dual work, model fitting and fair cross-case repetition are future work, not part of this publication.
