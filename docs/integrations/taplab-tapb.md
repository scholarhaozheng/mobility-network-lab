# TAPLab registered `tapb` adapter and task-local Algorithm B route

The accepted mathematical solver is official [`spartalab/tap-b`](https://github.com/spartalab/tap-b) **Algorithm B**, frozen at commit `040135a20c771fbb84766df6a97cff981fa5df4b`. The official adapter audit used [`TAPLab`](https://github.com/asu-trans-ai-lab/TAPLab) commit `081e44a0dd451c549d6903933516bccb4166bbd0`. TAPLab is the CLI/registered-adapter and verification environment here, not a separate mathematical solver. Both upstream projects retain their MIT terms; neither upstream source tree nor native binary is redistributed.

| Case | Official TAPLab registered adapter | Accepted numerical result |
|---|---|---|
| Classic Sioux Falls | CLI + direct callable parity passed; standard `taplab verify` certified | Official TAPLab adapter result and independent R2 checks |
| Boston B0 interface | Stock converter contract blocked **before** solve | Official tap-b Algorithm B via task-local TAPLab-compatible lossless adapter |
| Boston B1 frozen holdout | Stock converter contract blocked **before** solve | Official tap-b Algorithm B via task-local TAPLab-compatible lossless adapter |

The [R2.1 parity matrix](../../algorithms/origin_based_algorithm_b/parity/TAPLAB_ADAPTER_PARITY_MATRIX.csv), [entry-point record](../../algorithms/origin_based_algorithm_b/parity/TAPLAB_PUBLIC_ENTRYPOINT_RECORD.json), and [standard-output audit](../../algorithms/origin_based_algorithm_b/parity/STANDARD_OUTPUT_CONTRACT_AUDIT.csv) identify which route was actually exercised. They do not imply that a Boston official-adapter solve failed: none was invoked.

## Official Sioux Falls route

Obtain the pinned TAPLab source and the pinned tap-b source from their official repositories under their MIT notices; build tap-b locally and prepare a licensed classic Sioux instance that preserves the frozen 24-node/76-link/528-positive-OD contract. Use a task-local Python environment and task-local temporary directory. Set `TAPLAB_TAPB_EXE` to the locally built executable. From the pinned TAPLab source root, the accepted R2.1 CLI route was:

```powershell
$env:TAPLAB_TAPB_EXE = '<absolute path to your locally built tap-b executable>'
$inst = '<absolute path to your classic Sioux TAPLab instance>'
python -m taplab.cli validate $inst
python -m taplab.cli run $inst --solver tapb --algorithm B --gap 1e-8 --max-time 1800
python -m taplab.cli verify $inst --solver tapb --gap-target 1e-4
```

For the frozen audit, validation, run and verification returned zero; the registered adapter and `taplab.adapters.tapb.solve` direct call had zero physical-link-flow difference from accepted R2. `taplab verify` certified the standard output. The adapter did not expose R2's explicit 10,000-iteration cap or OD-path export, and did not itself inspect the native subprocess return code; the frozen parity run stopped at 18 iterations, so the cap was nonbinding. The independent R2 [evaluation record](../../algorithms/origin_based_algorithm_b/accepted_results/sioux_evaluation.json) supplies path-level verification. This release does not claim byte-identical parameter settings across the two routes.

## Boston task-local lossless route

The pinned stock converter's pre-solve dry-run wrote `FIRST THRU NODE=13` for B0 and `132` for B1 instead of the required `1`, and rounded **26/26** and **453/453** OD values respectively to four decimals. Three positive B1 OD values became zero. B1 also lacked the stock converter's required `length` field; the dry-run supplied a placeholder **only for converter inspection**, while the authoritative BPR `vdf_fftt` was preserved. None of these converted inputs was passed to a Boston official-adapter solve.

To reproduce a *new* compatible Boston-style run, supply your own lawful physical-link/OD CSVs with the original precision, build the pinned official tap-b executable, and use the selected [task-local contract/adapter code](../../algorithms/origin_based_algorithm_b/README.md):

```text
python algorithms/origin_based_algorithm_b/code/taplab_bush_solver_adapter.py prepare --link LINKS.csv --demand DEMAND.csv --out RUN_DIR
python algorithms/origin_based_algorithm_b/code/taplab_bush_solver_adapter.py run --exe TAP_B_EXECUTABLE --link LINKS.csv --demand DEMAND.csv --out RUN_DIR
python algorithms/origin_based_algorithm_b/code/independent_static_ue_evaluator.py --link LINKS.csv --demand DEMAND.csv --run RUN_DIR
```

The `run` line invokes the external solver and is **documentation only** for this publication task. The accepted R2 task-local executable had link-flow and OD-path text outputs widened from `%f` to `%.17g`; the source patch was not in the rights-cleared public candidate directory. See the [code README](../../algorithms/origin_based_algorithm_b/README.md) for what is and is not supplied. Public accepted B1 aggregate flows and evaluations are inspection artifacts, not a replacement for the original input or path-flow run directory.

## Claim boundary

The Boston B1 result is a conditional HBW-midday, two-hour modeled cohort, not observed traffic, an all-day citywide result, or empirical validation. Exported OD paths allow reconstructed origin-link flow; they do not disclose native Policy Bush internal merge/label/restriction-update state. Same-problem FW agreement in this low-congestion holdout is a numerical check, not a generalized Algorithm B speed or quality advantage. [Sioux case](../cases/sioux-algorithm-b.md) · [Boston case](../cases/boston-algorithm-b.md).
