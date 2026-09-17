# Mobility Computation Lab

**Open city data → model-ready interfaces → assignment / optimization → verified results**

Mobility Computation Lab connects local mobility-metadata tools and carefully bounded open-data evidence to explicit network inputs, reproducible assignment workflows, and independently checked outputs. It combines selected authorized Open Mobility Data Visibility (OMDV) normalizers and matchers with the working Mobility Network Lab solver, verifier, examples, and benchmark records.

[Open-data evidence](docs/open-data.md) · [Network inputs](docs/data-contract.md) · [Methods](docs/methods.md) · [Benchmark catalog](docs/datasets.md) · [Installation](docs/getting-started.md)

Source repository: [scholarhaozheng/mobility-network-lab](https://github.com/scholarhaozheng/mobility-network-lab) · Configured Pages target (not a deployment claim): [scholarhaozheng.github.io/mobility-network-lab/](https://scholarhaozheng.github.io/mobility-network-lab/)

## What is available now

| Open mobility data | Network computation |
|---|---|
| **Global city frame:** 11,422 GHSL urban centres used as a common analytical denominator | **Static assignment:** retained Frank–Wolfe implementation and a documented Sioux Falls baseline |
| **GTFS static:** 6,951 eligible source records; 4,425 parseable unique-content hashes in the all-retained view; 2,959 cities with inside-polygon stop evidence | **Space–time optimization:** deterministic route initialization, explicit space–time construction, reference LP, and Phase-I/Phase-II column generation |
| **GTFS-Realtime:** 2,465 metadata-level endpoint representatives with separate snapshot city classes | **Verification:** complete final path-pool export plus solver-free demand, capacity, objective, and provenance checks |
| **OSM / shared mobility:** bounded OSM map-feature evidence and a 1,516-row GBFS registry summary, kept separate from transit-feed evidence | **Benchmarks:** verified 200-OD and 250-OD Sioux Falls subset records with approved result figures |

These evidence layers are not additive. An unmatched city is not “data-free”; metadata visibility is not service coverage; a model standard is not proof of city availability. See the [open-data evidence guide](docs/open-data.md) and machine-readable [`catalog/open-data-evidence.json`](catalog/open-data-evidence.json).

## Four-layer architecture

1. **Open-data/evidence layer** — compact accepted summaries, provenance, and claim boundaries.
2. **City/model interface** — explicit node, link, demand, zone-access, unit, and identifier contracts.
3. **Assignment/optimization layer** — static Frank–Wolfe and finite space–time column generation.
4. **Benchmarks/verification layer** — runnable synthetic examples, result records, and independent checks.

The retained numerical implementation remains under `app/src/gmns_dynamic/` for compatibility. New public evidence helpers live under `src/mobilitylab/`. See [architecture](docs/architecture.md).

## Quick start

Python 3.12 is the v2 assembly-test baseline; the retained MNL source was previously checked on Python 3.13. NumPy, SciPy, and PyYAML are required for the network workflow.

```bash
python -m pip install -r requirements.txt
python tools/mnl.py catalog
```

Run the small bundled capacity example:

```bash
python tools/mnl.py run --input app/cases/capacity_zone_probe/input --config app/cases/capacity_zone_probe/case.json --seed-mode auto --seed-k 1 --output results/capacity-demo
python tools/mnl.py verify --run results/capacity-demo
```

The expected solution sends 3 units through the lower-cost route and 7 through the alternative, for objective **27**. Inputs and outputs must be separate, and each run must use a new output directory.

Inspect the evidence catalog without loading raw mobility data:

```bash
python -m unittest tests.test_open_data_evidence -v
python tools/publication_gate.py
```

## Data tools

The executable data workflow normalizes a user-supplied feed-catalog CSV,
standardizes a city CSV, performs transparent exact municipality/country
matching, and writes standardized tables plus a quality report. Install its
optional dependencies in a separate environment:

```bash
python -m venv .venv-data
.venv-data/bin/python -m pip install -r requirements-data-tools.txt
.venv-data/bin/python -B tools/mcl_data.py catalog-city-match --catalog examples/data-tools/feeds_sample.csv --cities examples/data-tools/external_city_universe_sample.csv --output results/data-tools-demo
```

On Windows, use `.venv-data\Scripts\python.exe`. The output includes the
normalized catalog, standardized cities, feed-city matches, city-level
summaries, schema audits, ambiguity records, and `quality_report.json`.

Matching is exact after lowercase/whitespace/hyphen normalization and requires
a valid two-letter country code. Duplicate normalized city keys are reported as
ambiguous rather than guessed; unmatched and missing-field records are
preserved. This is named-entity matching—not GPS map matching, GTFS ZIP parsing,
realtime probing, or city-network compilation. See the complete
[data-tools guide](docs/data-tools.md).

## Use your own network

Declare field mappings and units in `case.json`, then validate and run the current finite profile:

```bash
python tools/mnl.py validate --input /path/to/network/input --config /path/to/network/case.json
python tools/mnl.py run --input /path/to/network/input --config /path/to/network/case.json --seed-mode auto --seed-k 5 --output results/network-run
python tools/mnl.py verify --run results/network-run
```

Current limitations are deliberate: one-minute time steps, positive integer travel times, a common departure time, fixed costs, continuous path flow, declared size limits, and hard shared arc capacities. This is not an unrestricted city-scale DTA, a GPS map matcher, an OD estimator, or a general static user-equilibrium interface. Read the exact [input contract](docs/data-contract.md).

## Verified road benchmarks

[![Final physical-link movement flow for the selected 250-OD Sioux Falls benchmark subset](docs/assets/benchmarks/sioux_250od_final_physical_link_flow.png)](docs/datasets/sioux-250od.md)

*Selected 250-OD Sioux Falls subset. Line width is final movement flow accumulated across modeled time—not static V/C and not observed traffic.*

| Case | Physical nodes | Selected links | OD pairs | Final columns | Objective |
|---|---:|---:|---:|---:|---:|
| **200-OD subset** | 24 | 64 | 200 | 446 | 943,155.589771 |
| **250-OD subset** | 24 | 69 | 250 | 567 | 1,521,090.83662 |

These are different selected-OD instances, so their objectives are not directly comparable. Neither is the full 528-OD static benchmark. See the [200-OD](docs/datasets/sioux-200od.md), [250-OD](docs/datasets/sioux-250od.md), and [static Frank–Wolfe](docs/datasets/sioux-static-fw.md) records.

## Provenance and publication boundary

The OMDV integration contains four selected original implementations, two
bounded example fixtures, a thin MCL adapter, compact aggregate summaries, and
cryptographic provenance. The maintainer explicitly authorized those selected
original files for MIT distribution here; the complete OMDV research
repository has not changed license.

The upload does **not** contain manuscripts, raw GTFS archives, endpoint lists
or payloads, OSM extracts, GBFS registry rows, GHSL geometries, SEDAC material,
review packages, or cached downloads. No OMDV figure was selected because no
candidate completed a file-specific review of underlying-data and basemap
terms.

The root MIT license covers only code that the maintainer has the right to license here. External data, standards, tools, and source repositories keep their own terms. Read [data licenses](DATA_LICENSES.md), [third-party notices](THIRD_PARTY_NOTICES.md), and [OMDV provenance](docs/omdv-provenance.md).

## Roadmap, not shipped functionality

- city compiler and hierarchical zones;
- OD generation and estimation;
- GPS traces and map matching;
- origin-based assignment / Policy Bush;
- coupled primal-dual, Lagrangian, and ADMM methods.

These are future directions, not current capabilities. See the [roadmap](docs/roadmap.md).

## Contributing

Contributions should preserve provenance, data rights, layer boundaries, and executable tests. Start with [CONTRIBUTING.md](CONTRIBUTING.md) and the [network instance guide](docs/add-a-network.md).
