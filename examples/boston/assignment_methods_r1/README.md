# Boston ABS_PLANNED saved static assignment panel

This public-safe frozen panel has 5,091 physical directed links, 26 endpoint OD pairs, 203.6604786350987 modeled vehicle trips, a fixed 130-path pool, and no background traffic. `inputs_snapshot/link.csv` is the source physical geometry and heterogeneous BPR parameter table; `inputs_snapshot/demand.csv` is the actual ABS_PLANNED demand. Neither is the older semantic S1 GMNS export demand. Physical `link_id` is not an exported GMNS numeric ID without the documented crosswalk.

`reference/fw_solution.csv` is the saved [static FW](../../../algorithms/static_fw/) flow; `reference/full_path_flow.csv` and `reference/link_flow.csv` are the solved [uncompressed finite-path](../../../algorithms/finite_path_reference/) reference; `runs/rank26` and `runs/rank52` contain only the accepted native L3 outer-02 path, OD, link and coordinate records, plus original-space check JSON. The full path-pool membership and sanitized accepted bases are retained. No old failed theta, failed outer-01 iterates or private IPOPT logs are included.

Read a record without solving:

```bash
python -B tools/mcl_results.py show --run boston-abs-planned-l3-rank26-outer02
python -B tools/mcl_results.py verify-saved --run boston-abs-planned-l3-rank26-outer02
```

The five [source-grounded assignment maps](../../../docs/cases/boston-assignment.md) use `FW volume` and accepted `v_from_paths` fields joined one-to-one by original physical `link_id`. Their full-precision 5,091-row plotting table and figure source manifest are in `docs/assets/boston/assignment_methods_r1/`. Re-render using `python -B tools/visuals/render_boston_assignment.py --source-root examples/boston/assignment_methods_r1 --output results/boston_assignment_maps` (saved-data plotting only).

The source network is GMNS Plus 21_Boston, Apache-2.0, commit `116447ab641cca1ed34797d019c8e704063393c3`; modeled results and their limitations are described on the case page. An accepted numerical approximation is not an exact feasible equilibrium or independent traffic validation.
