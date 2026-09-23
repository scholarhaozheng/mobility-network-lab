# Sioux Falls case · static assignment and historical space–time CG

Sioux Falls is a classical benchmark entry in the same network-computation framework, **not** a new present-day real-city GPS/four-stage dataset. Its static native Diagnostic L3 instance has 24 nodes, 76 directed links, 528 positive OD records, 2,218 paths and rank 50. The historical 200OD and 250OD time-expanded CG cases are separate selected-link/horizon instances. [Return to the project homepage](../index.md).

## Instance & GMNS Structure

The classic 76-link topology and OD table are [frozen with the native representation](../../examples/sioux-falls/native_l3_r1/README.md). Their IDs and path/OD/link records are explicit; no Boston H3 zones, GTFS, GPS traces or present-day physical street tiles are imputed to this benchmark. The two CG diagrams below are schematic flows of their different selected-link instances.

## Trip Generation

OD demand is **provided exogenously** for the classic benchmark. Trip-production rates were not estimated in this case.

## Trip Distribution

The static 528-record OD table is a supplied input, not a gravity/IPF result. Historical 200OD and 250OD CG instances select different demand subsets and links.

## Mode Choice

No traveller mode-choice model was estimated for the classic Sioux assignment benchmark. Its fixed vehicle demand should not be confused with Boston's conditional DA/S2/S3/TW study.

## Traffic Assignment

The [historical static FW result](../datasets/sioux-static-fw.md) is actually executed: saved approximate Beckmann objective **4,236,715.140437842**, 24 nodes, 76 links, 528 OD records and a reported 0.236154949% fixed-flow gap under its own denominator. Its runtime OD-file hash and path disaggregation were not retained; therefore it is **not** asserted to be an exact matching reference for the native frozen input.

The corrected [native Diagnostic L3 method](../../algorithms/path_compression/diagnostic_l3/README.md) has accepted outer-04 results on the static 76-link instance. It keeps the rank-50 basis, 535 major and 1,683 minor paths, 585 reduced path coordinates and **661 total native variables**, including the explicit link flows.

| Native configuration | Gamma | Original Beckmann component F | Max OD residual | Full-network relative cost gap | Meaning |
|---|---:|---:|---:|---:|---|
| [A_REG001 · outer 04](../../examples/sioux-falls/native_l3_r1/runs/SiouxFalls/A_REG001/outer_04_check.json) | 0.01 | 4,325,864.946597109 | 5.548833712509804e-7 | 8.167461% | Regularized diagnostic, numerically accepted |
| [B_BECKMANN · outer 04](../../examples/sioux-falls/native_l3_r1/runs/SiouxFalls/B_BECKMANN/outer_04_check.json) | 0 | 4,289,674.484214505 | 6.957361051718181e-7 | 4.381867% | Unregularized numerical candidate, **not** full-network UE |

Both have zero negative path-flow mass and passed recorded original-space numerical tests. Their nonzero full-network gaps remain visible; a passing numerical-feasibility gate is not an equilibrium or empirical-validation certificate. Gamma=0.01 adds a reference-centred term, so the two F values are not a shared-objective leaderboard. The source and effective zero-link-bound adapter are released, but native portability has not been retested in this publication task.

The historical **finite space–time CG** results solve a different fixed-cost, hard-capacity linear formulation with a reference LP. They belong inside this case, not in the static native comparison:

| Historical CG experiment | Selected links | OD pairs | Final columns | Objective | Evidence |
|---|---:|---:|---:|---:|---|
| [200OD](../datasets/sioux-200od.md) | 64 | 200 | 446 | 943,155.589771 | Saved final flow and Phase-I/II figures |
| [250OD](../datasets/sioux-250od.md) | 69 | 250 | 567 | 1,521,090.836620 | Saved final flow and Phase-I/II figures |

![Historical Sioux Falls 200OD schematic physical-link movement flow](../assets/benchmarks/sioux_200od_final_physical_link_flow.png)

![Historical Sioux Falls 250OD schematic physical-link movement flow](../assets/benchmarks/sioux_250od_final_physical_link_flow.png)

## Observations & Feedback

No real-city GPS/GTFS observations or Boston-style service-feedback workflow are included in the classic Sioux instance. The benchmark is algorithmic, not an observed urban traffic panel.

## Experiments & Reproduction

```bash
python -B tools/mcl_results.py list --case sioux-falls
python -B tools/mcl_results.py verify-saved --run sioux-native-l3-a-reg001-outer04
python -B tools/mcl_results.py verify-saved --run sioux-native-l3-b-beckmann-outer04
```

The saved inspector reconstructs path-to-OD/link flows and the original Beckmann component without solving. [Selected frozen data and checks](../../examples/sioux-falls/native_l3_r1/README.md) and [optional native staging instructions](../../algorithms/path_compression/diagnostic_l3/README.md) are separate from the historical [CG implementation](../../app/src/gmns_dynamic/run_full_cg_v1.py). No new Sioux run was made for this publication.
