# Hong Kong · evidence, model and reproduction contract

The bounded case is a **reproducible engineering scenario**, not a locally calibrated demand forecast. `OFFICIAL_EXACT` and `OFFICIAL_SEGMENT_TRANSFER` describe posted-limit matching, not observed free-flow speed. Free-speed conversion, lanes, BPR capacities, local capture, building-attraction weights, gravity impedance, mode constants, occupancy and PCE conversion are declared assumptions. The 2022 Travel Characteristics Survey coefficients represent Hong Kong territory-wide and are transferred to this pilot. Storey-weighted building area is neither official gross floor area nor measured employment.

Static FW and Algorithm B solve a BPR/Beckmann model over one-hour vehicle PCE. The finite 10-OD case instead minimizes fixed vehicle-minute costs under time-indexed hard capacities. Its reference LP, CG and Lagrangian feasible primal are comparable **only on that same finite graph and demand**. The independent R5 closure certificate establishes no improving ungenerated path below the −1e-6 threshold for all ten demands; objective agreement alone would not establish that certificate. Frozen ADMM R2 is gated at its first original-unit commodity conservation test and has no accepted objective.

Observation evidence does not close an empirical validation gate: historical station AADT is not a one-hour directed-link count; the detector is a single snapshot; the 2021 UrbanNav SPAN-CPT+IE trace concerns one research vehicle and is not raw GNSS or representative traffic. Complete point-level tables remain private; one narrowly reviewed 12-point projection figure is public. [Historical rights register](../assets/hong_kong/full_stack_r5/r2r4_baseline/HONG_KONG_SOURCE_AND_RIGHTS_REGISTER.csv) · [Figure publication scope](../assets/hong_kong/visual_release_r1/PUBLICATION_SCOPE.txt) · [R5 result matrix](../assets/hong_kong/full_stack_r5/HK_CG_R5_FINAL_RESULT_MATRIX.csv).

## Solver-free reproduction

From a checkout with Python 3.12+, the two published checks audit saved artifacts without calling a scientific solver:

```bash
python -B docs/assets/hong_kong/full_stack_r5/r2r4_baseline/verify_public_bundle.py --root docs/assets/hong_kong/full_stack_r5/r2r4_baseline
python -B docs/assets/hong_kong/full_stack_r5/verify_receiver_r5.py
```

The first verifies 18 historical full-stack figures, source hashes, static acceptance, original-space LP feasibility, Lagrangian recovery and the **historical** R2–R4 CG/ADMM gates. The second verifies the current public R5 package inventory, 26 figure entries and sidecars, frozen model identity, Phase I/II saved results, 10/10 independent pricing closure, and redaction of private route pools and dual arrays. The historical gate is superseded for CG only; ADMM remains gated. [Current case](../cases/hong-kong.md) · [Finite results](../cases/hong-kong-space-time.md).
