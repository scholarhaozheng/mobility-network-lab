# Sioux Falls native Diagnostic L3 saved records

This is the classic **static** 76-link, 528-positive-OD, 2,218-path instance, not the historical selected-link 200OD/250OD time-expanded CG networks. `inputs_snapshot/SiouxFalls/` contains the frozen network, demand, incidence, rank-50 representation and source arrays needed to read the accepted point; no path generation or SVD is needed. `runs/SiouxFalls/A_REG001/` and `B_BECKMANN/` contain the selected outer-04 original path, OD and link flows, native coordinates and original-space checks. Earlier failed or intermediate native iterates and private logs are omitted.

The regularized A profile has gamma=0.01, original Beckmann component F=4325864.946597109 and full-network relative cost gap 8.167461%. The unregularized B profile has gamma=0, F=4289674.484214505 and gap 4.381867%. Both passed recorded numerical feasibility tolerances; neither is a full-network UE certificate. No same-input FW reference pairing is claimed from the separate historical FW record.

Inspect without a native solver:

```bash
python -B tools/mcl_results.py verify-saved --run sioux-native-l3-a-reg001-outer04
python -B tools/mcl_results.py verify-saved --run sioux-native-l3-b-beckmann-outer04
```

The [shared native source and profile adapters](../../../algorithms/path_compression/diagnostic_l3/) describe optional reproduction. All values are model outputs, not GPS-observed city traffic.
