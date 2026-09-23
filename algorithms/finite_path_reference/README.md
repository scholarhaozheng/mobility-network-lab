# Finite-path Boston reference

The frozen Boston ABS_PLANNED comparison used the original 5,091-link network, 26 physical endpoint OD pairs, 203.6604786350987 modeled vehicle trips, and a fixed 130-path pool. [`adapters/solve_full_path.py`](adapters/solve_full_path.py) is the actual SLSQP implementation: nonnegative path variables, exact OD equality constraints, heterogeneous BPR Beckmann objective, and recorded `ftol=1e-10`, `maxiter=500`. Its direct helper and original experiment configuration are retained here. This is a finite-pool reference, not a new path-pool generator or a global UE certificate.

The saved path/link flows and [solver record](../../examples/boston/assignment_methods_r1/reference/full_path_solver_result.json) are directly browsable. Inspect them without solving with `python -B tools/mcl_results.py verify-saved --run boston-abs-planned-full-path`. The original full-path run reported F=707.0579230712882 vehicle-minutes, zero maximum OD residual, and 0.1028839 seconds total recorded wall time; those are frozen-run measurements, not new publication timings.

Optional rerun, in an environment with NumPy and SciPy, from the repository root (do **not** run to inspect saved results):

```bash
python -B algorithms/finite_path_reference/adapters/solve_full_path.py --inputs examples/boston/assignment_methods_r1/inputs_snapshot --pool examples/boston/assignment_methods_r1/inputs_snapshot/path_pool --config algorithms/finite_path_reference/config/experiment.json --out results/new-boston-full-path
```

Choose a new output directory. This publication task did not execute the optional command. The frozen helper guards small negative link values during objective evaluation; raw OD/path feasibility is evaluated separately.
