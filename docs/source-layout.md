# Source layout

The v2 public navigation uses four layers. The retained numerical engine stays in its tested compatibility paths.

- src/mobilitylab/data/: compact evidence-catalog loader and guardrails;
- app/src/gmns_dynamic/: city/model input contract and space–time assignment;
- algorithms/static_fw/: static Frank–Wolfe baseline;
- algorithms/origin_based_algorithm_b/: selected task-local TAPLab-compatible lossless adapter, independent static UE evaluator, accepted Sioux/Boston B1 derived results, eight source SVGs and R2.1 official-adapter parity records; no upstream solver binary or source tree;
- algorithms/distributed_assignment/lagrangian_r2/: selected public capacity-pricing, separate feasible-recovery source, fixtures and accepted Sioux 200/250-OD summaries;
- algorithms/distributed_assignment/admm_r1/: selected public local/consensus source, synthetic fixture, saved 200-OD history and accepted 200/250-OD final metrics;
- algorithms/admm_r2/: frozen R2_S source for selected Sioux and bounded Boston finite shared-capacity evidence; authored controls are in examples/admm-r2-fixtures/ and accepted figures/derived Boston table in docs/assets/admm_r2/;
- examples/hong-kong/gmns_pilot_r1/: official-derived bounded GMNS/data tables, attribution, five SVGs and offline validation/trace scripts; assignment is gated;
- launcher/ and tools/: verification, repository checks, and publication gate;
- catalog/: open-data evidence, interoperability, datasets, source hashes, and OMDV provenance.

The numerical code is selected from the known-working GMNS-CG 0.3.0-rc5 distribution. The public external-input runner and solver-free verifier retain their transitive Python dependencies. Some internal helper filenames reflect earlier diagnostics; they are required code, not archived failed runs.

The original `app/src/gmns_dynamic/` relative location is preserved because the engine resolves some internal paths from it. The public entry point is `tools/mnl.py`; it supplies module paths in a separate worker and writes English reports without editing the retained optimizer files.

Compare function contracts and run focused regressions when updating the numerical engine. Keep data preparation, solver logic and result verification independently inspectable.

The distributed method components and Algorithm B are bounded research branches, not substituted into `tools/mnl.py run`. The public Hong Kong example is a data/relationship pilot, not a runnable assignment instance. [Algorithm B adapter scope](integrations/taplab-tapb.md) · [ADMM R2 method and limits](methods/admm-space-time.md) · [Earlier distributed method scope](methods/distributed-assignment.md) · [Hong Kong case](cases/hong-kong-gmns-pilot.md).
