# Recovered P07 reproduction package

The original preregistered R2 experiment plan has been recovered without changing its bytes (SHA-256 `33709ca3ed3ea0c6d958615032d35b42f29f94bf20f51c7e24f861cd659d541b`). The new adapter calls the five existing public solver/evaluator modules; it does not duplicate or modify their mathematics.

After integrating these files, run from the repository root:

```sh
python -B tools/mcl_reproduce.py run lagrangian-p07-public-C1 --output results/lagrangian-C1
python -B tools/mcl_reproduce.py verify lagrangian-p07-public-C1 --run results/lagrangian-C1
```

The `analytic`, `C0` and `C1` controls freshly reproduce objectives 2, 4 and 8. C1 has 13 iterations and a certified primal/dual gap of 0.727008%; P07 stops at its original 1% threshold. These are task-authored controls, not city reproductions.

To apply the same frozen policy to an independently obtained, compatible finite graph:

```sh
python -B algorithms/distributed_assignment/lagrangian_r2/reproduce.py run --repo-root . --case external --arc inputs/dynamic_arc.csv --demand inputs/dynamic_demand.csv --output results/supplied-P07
python -B algorithms/distributed_assignment/lagrangian_r2/reproduce.py verify --repo-root . --case external --arc inputs/dynamic_arc.csv --demand inputs/dynamic_demand.csv --run results/supplied-P07
```

A successful external-input run is not automatically a reproduction of a historical city. That claim requires matching the exact frozen input hashes and the corresponding numerical reference. City data acquisition is still incomplete: previous artifact-level release decisions excluded the historical dynamic graph/demand and full state arrays. The recovered source/configuration is now concrete, but those excluded inputs have not been copied into this public candidate.

Independent verification recomputes the dual lower bound, recovered path continuity and time monotonicity, commodity conservation, nonnegative flow, shared capacities, physical projection and primal objective without invoking an optimizer. It additionally checks source/input/output hashes and the original 1% certificate gate. A test with a modified path export is rejected.
