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

The retained implementation in [`algorithms/static_fw/`](../algorithms/static_fw/) uses BPR link costs, the Beckmann integral, all-or-nothing shortest-path loading and line search. The catalog includes a saved approximate Sioux Falls result with separately documented verification.

This model is different from the hard-capacitated, fixed-cost space–time LP. Its numerical objective cannot be compared directly with the CG objective. The static file is an optional library source, not part of `tools/mnl.py run`; see its module documentation before calling it.

## What a verification statement means

Distinguish input consistency, primal feasibility, agreement with a same-model reference, final-RMP optimality information, and independent pricing closure. A reference objective match does not by itself mean a separate missing-column pricing certificate was generated.

Synthetic reference examples protect implementation behavior. Road benchmark records describe previous experiments. Neither category is a calibrated city demand model.

## Method extensions

Origin-based/Bush methods, compressed ALM and coupled primal–dual models are extension directions, not advertised as fully validated methods in this source release. Adapters should declare their mathematical problem and output semantics, retain their own upstream identity, and use an independent evaluator.
