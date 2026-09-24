# Boston HBW-midday scale profile (research candidate)

The 36-zone-pair / 26-physical-node-pair ABS_PLANNED result remains the read-only **Fixed-panel algorithm check**. This profile selects new zonal OD from the saved HBW-midday person-OD asset. It does not regenerate distribution, collect observations, or rescale selected demand.

`scale_500.json`, `scale_2000.json`, and `scale_all.json` are nested scenario configurations. Replace their `PATH_TO_*` input values with exact local files and choose interpreters with the documented routing and solver dependencies. The 500, 2,000 and all labels count **selected source-zone pairs**; the final physical-node OD count and eligible vehicle mass are measured after new planned-service routing and fixed-spec choice. The generic vehicle-OD route is demonstrated separately in `examples/scalable_vehicle_fixture/`.

From repository root:

```sh
python3 -B tools/mcl_assignment.py scale --profile examples/boston/scalable_tool_r1/scale_500.json --output results/boston-hbw-midday-r1
python3 -B tools/mcl_assignment.py scale --profile examples/boston/scalable_tool_r1/scale_2000.json --output results/boston-hbw-midday-r1
python3 -B tools/mcl_assignment.py scale --profile examples/boston/scalable_tool_r1/scale_all.json --output results/boston-hbw-midday-r1
```

The same commands use `python` on Windows. The scale runner executes one stage process group at a time, checks completed source/skim chunks, and stops with a nonzero partial status at the stated skim/heavy limits. It does not advertise an unfinished tier as solved. It first computes scheduled drive/TW attributes with the accepted semantic adapter; `mcl_person_choice.py` then applies the fixed DA/S2/S3/TW absolute-attribute model. The same `mcl_assignment.py` FW route solves the resulting physical-node vehicle demand. Full-path and native L3 are separately configurable method attempts on the exact prepared instance.

In this measured handoff, all three new FW tiers passed the independent numerical gate. The all-interzonal run used 30,790 selected source-zone OD and yielded 17,522 eligible physical-node OD; its choice result is a conditional engineering-cohort sensitivity. Full-path/native comparisons were resource-gated after actual 500 and 2,000 path-pool work, and the all-tier path pool was gated before allocation. The private local time extension used for this research run is not encoded in the public example profiles.

The local Boston routing sources required by the profile are the accepted directed road graph, H3 zone centroids/access, bounded OSM walk graph, MBTA GTFS feed and transit text tables. Their acquisition and licenses must be handled separately; these files are not embedded in this candidate. The source-to-solver `id_crosswalk.csv` preserves H3 zone and physical access identities. Nonphysical GMNS centroid connectors are excluded from route cost and link-flow maps.

See `docs/RUN_YOUR_OWN_GMNS.md` for input contracts, numerical gates and method limits, and `docs/BOSTON_SCALE_RESULTS.md` for actual measured outcomes from this bounded execution.
