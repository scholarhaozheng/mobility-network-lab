# Source layout

The v2 public navigation uses four layers. The retained numerical engine stays in its tested compatibility paths.

- src/mobilitylab/data/: compact evidence-catalog loader and guardrails;
- app/src/gmns_dynamic/: city/model input contract and space–time assignment;
- algorithms/static_fw/: static Frank–Wolfe baseline;
- launcher/ and tools/: verification, repository checks, and publication gate;
- catalog/: open-data evidence, interoperability, datasets, source hashes, and OMDV provenance.

The numerical code is selected from the known-working GMNS-CG 0.3.0-rc5 distribution. The public external-input runner and solver-free verifier retain their transitive Python dependencies. Some internal helper filenames reflect earlier diagnostics; they are required code, not archived failed runs.

The original `app/src/gmns_dynamic/` relative location is preserved because the engine resolves some internal paths from it. The public entry point is `tools/mnl.py`; it supplies module paths in a separate worker and writes English reports without editing the retained optimizer files.

Compare function contracts and run focused regressions when updating the numerical engine. Keep data preparation, solver logic and result verification independently inspectable.
