# Native Diagnostic L3: saved Boston and Sioux Falls profiles

This is the corrected native Pyomo/IPOPT reduced-coordinate method used for the selected saved results, not the older unconstrained ordinary-v4 approximation. The [isolated mathematical builder](source/build_alm_model_levels.py) has the **same function AST** as `run_diagnostic_levels.py` (original SHA-256 `0a054ab078d46a8b74fa257336a65275564c38cc3e60e5c4d8cb9c412a87a22a`; isolated AST SHA-256 `8109299162b031a96f857c14eea58587ff0f78611067408df6fede9b78429b4b`). Its inactive historical driver, private output path, plots and unrelated levels are not imported or shipped. The public isolated file SHA-256 is `27644472699b1c93f9795b6a7940928c4935e43a2a062c96a6f7a682df8208b5`.

The effective method is builder **plus** profile adapters. Both profiles set every explicit link-flow lower bound to zero after construction and retain the hard reconstructed minor-path nonnegativity constraints and original ALM updates. Boston's adapter additionally replaces the builder's fixed beta-four BPR integral with the actual linkwise `beta=2` integral `t0*v + t0*alpha/(beta+1)*v*(v/capacity)**beta`; it does not change the effective frozen capacity or floor the 37 small `vdf_fftt` values. Sioux retains its frozen rank-50 representation and separate gamma=0.01 regularized and gamma=0 Beckmann profiles. Solver options and recorded stopping logic remain in the attributed adapters.

The selected [Boston outer-02 records](../../../examples/boston/assignment_methods_r1/README.md) and [Sioux outer-04 records](../../../examples/sioux-falls/native_l3_r1/README.md) can be inspected without Pyomo/IPOPT:

```bash
python -B tools/mcl_results.py list --case boston
python -B tools/mcl_results.py verify-saved --run boston-abs-planned-l3-rank26-outer02
python -B tools/mcl_results.py verify-saved --run sioux-native-l3-b-beckmann-outer04
```

An optional new native run needs a separately prepared **Windows** Python environment with NumPy, SciPy, Pyomo, native IPOPT with MUMPS, and enough memory. Stage frozen inputs and code into a **new** output directory using `python -B tools/prepare_native_run.py --case boston --output results/new-boston-l3` (or `--case sioux-falls`). That command only copies reviewed public files; it does not solve. Set `MCL_NATIVE_PYTHON` to the chosen interpreter and `MCL_IPOPT` to the native executable. The staged controller requires an explicit `--execute-native` flag; `--help` and the standard saved-result inspector do not start a solve. The Sioux public controller runs Sioux A then B only; the prior Anaheim A/B records are supplemental and are not silently run by this profile. After reviewing the staged source, an **optional** new solve command is:

```powershell
$env:MCL_NATIVE_PYTHON = '<native Python executable>'
$env:MCL_IPOPT = '<IPOPT executable with MUMPS>'
Set-Location results/new-boston-l3
& $env:MCL_NATIVE_PYTHON -B checks/preflight.py
& $env:MCL_NATIVE_PYTHON -B adapters/controller.py --execute-native
# For a separately staged Sioux directory, use runner/controller.py --execute-native instead.
```

Use a new output directory and do not execute these commands just to inspect the saved records. This publication task did not retest native portability or execute a solver.

Boston's very small negative signed gaps reflect tolerated OD deficits, not exact feasibility or improvement below the feasible optimum. Sioux's gamma=0 full-network cost gap remains 4.381867%, so numerical acceptance is **not** a full-network UE certificate. Neither profile establishes cold-start acceleration, peak IPOPT memory, two-city matched performance, or independent empirical validation.
