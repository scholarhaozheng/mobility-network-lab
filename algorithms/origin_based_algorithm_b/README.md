# TAPLab + tap-b Algorithm B: accepted static UE evidence

This directory contains selected public R2 candidate code, accepted derived results and the eight accepted SVG figures, plus selected R2.1 adapter-parity records. The mathematical solver is the official [`spartalab/tap-b`](https://github.com/spartalab/tap-b) Algorithm B at commit `040135a20c771fbb84766df6a97cff981fa5df4b`. The TAPLab integration audit used [`TAPLab`](https://github.com/asu-trans-ai-lab/TAPLab) commit `081e44a0dd451c549d6903933516bccb4166bbd0`.

The Sioux Falls official registered TAPLab `tapb` adapter passed CLI, direct-callable and `taplab verify` parity. Boston B0/B1 were solved with the same official tap-b executable through the **task-local TAPLab-compatible lossless adapter** in `code/`; the stock TAPLab converter was stopped before Boston solving because it does not preserve the frozen input contract. [Method](../../docs/methods/origin-based-algorithm-b.md) · [Integration audit](../../docs/integrations/taplab-tapb.md).

## Contents and scope

- `code/static_ue_problem_contract.py` validates physical directed links and OD and exports 17-significant-digit TNTP with `FIRST THRU NODE=1`.
- `code/taplab_bush_solver_adapter.py` is the task-local preparation/process adapter. It is not TAPLab's registered adapter.
- `code/independent_static_ue_evaluator.py` rechecks saved link/path results against BPR/Beckmann and original-space conservation and cost gates.
- `accepted_results/` contains the two public accepted R2 evaluations and full aggregate physical-link flows for classic Sioux and Boston B1. B0 is an accepted interface control documented on the Boston case page; its detailed flow is not a public candidate.
- `figures/` contains the eight accepted SVGs. Selected-origin flows are reconstructed from exported OD paths; they are not a dump of native internal Bush state.
- `parity/` contains R2.1 official-adapter status, entry-point and output-contract records.

The accepted source-file SHA-256 inventory is in [the delivery figure audit](../../docs/assets/algorithm_b_r21/SOURCE_SVG_SHA256.csv). The cross-city overview is a display composition of these eight SVGs, not a scientific rerun.

## Reproduction boundary

The published files permit contract preparation and independent evaluation **when the user supplies licensed original inputs and a locally built solver output**. They do not include the frozen raw Boston OD tables, native executable, original paths, private logs, or upstream source tree; hence these files alone cannot recreate the accepted numerical runs. Build the pinned tap-b source under its own MIT terms. The accepted task-local binary used two text-output precision changes (link-flow and OD-path formatting from `%f` to `%.17g`); the patch itself was not in the rights-cleared public candidate set, so this release describes the change rather than linking a missing patch. Do not alter the BPR values or OD demand to make a converter pass.

For a newly supplied compatible link/demand pair, preparation is solver-free:

```text
python algorithms/origin_based_algorithm_b/code/taplab_bush_solver_adapter.py prepare --link LINKS.csv --demand DEMAND.csv --out RUN_DIR
```

`run` additionally needs `--exe /path/to/locally-built/tap-b` and invokes the external solver; it was **not** executed during this publication update. The independent evaluator needs `--link`, `--demand`, and `--run` pointing to a completed run. [Official Sioux CLI route and Boston route](../../docs/integrations/taplab-tapb.md) are deliberately distinct.

## Rights

The selected task-local code is project MIT code; [LICENSE](LICENSE) retains its notice. TAPLab and tap-b are external MIT projects and are linked, not vendored. Boston network lineage is GMNS Plus `21_Boston`, Apache-2.0, commit `116447ab641cca1ed34797d019c8e704063393c3`; the full source dataset is not redistributed here. See [third-party notices](../../THIRD_PARTY_NOTICES.md) and [data licenses](../../DATA_LICENSES.md).
