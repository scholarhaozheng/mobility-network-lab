<p align="center"><img src="docs/assets/hero.png" width="100%" alt="Mobility Network Lab — GMNS-compatible data and reproducible network optimization"></p>

<p align="center">
  <a href="#quick-start">Quick start</a> ·
  <a href="docs/datasets.md">Data catalog</a> ·
  <a href="docs/methods.md">Methods</a> ·
  <a href="docs/data-contract.md">Input specification</a> ·
  <a href="CONTRIBUTING.md">Contribute</a>
</p>

# Mobility Network Lab

**GMNS-compatible network data, reproducible assignment workflows, and inspectable optimization results.**

Repository: [github.com/scholarhaozheng/mobility-network-lab](https://github.com/scholarhaozheng/mobility-network-lab)

Mobility Network Lab connects road networks and origin–destination demand to route initialization, network optimization, and independently checked outputs. A shared codebase supports configurable instances, with explicit data provenance and model-specific input profiles.

Use the repository to run a finite space–time path-flow model, inspect benchmark results, or add a network without rewriting the optimization engine. The current runnable workflow includes automatic or supplied initial routes, two-phase column generation, a same-model reference LP, and complete final path-flow exports.

## What you can use

| Component | Purpose | Entry point |
|---|---|---|
| **Network inputs** | Preserve node, link and zone identifiers; declare units and field mappings | [Input specification](docs/data-contract.md) |
| **Route initialization** | Generate deterministic initial paths or validate supplied routes | [Route initialization](docs/routes.md) |
| **Space–time optimization** | Allocate continuous path flows under fixed costs and shared arc capacities | [Model and solver](docs/methods.md) |
| **Result verification** | Recompute flow, path, capacity and objective checks from saved files | [Outputs and verification](docs/outputs.md) |
| **Benchmark catalog** | Inspect documented road-network experiments and reference examples | [Available records](docs/datasets.md) |
| **Instance extensions** | Add data, provenance and a matching input profile | [Add a network](docs/add-a-network.md) |

## Data catalog

Road benchmarks and synthetic reference examples are listed separately. A results record does not imply that its source data are redistributed in this repository.

| Road benchmark | Physical nodes | Physical links | OD pairs | Record |
|---|---:|---:|---:|---|
| **Sioux Falls · 200 OD** | 24 | 64 | 200 | [Space–time CG results](docs/datasets/sioux-200od.md) |
| **Sioux Falls · 250 OD** | 24 | 69 | 250 | [Space–time CG results](docs/datasets/sioux-250od.md) |
| **Sioux Falls · static assignment** | 24 | 76 | 528 | [Frank–Wolfe approximate baseline](docs/datasets/sioux-static-fw.md) |

The bundled [reference examples](docs/examples.md) exercise route initialization, zone access and capacity-constrained flow allocation. They are synthetic tests, not city datasets. Machine-readable records are available in [`catalog/datasets.json`](catalog/datasets.json).

## Quick start

Use an existing Python environment or create a project-local one. Python **3.13** is the source-testing baseline; NumPy, SciPy and PyYAML are required. No commercial solver is needed for the CG workflow.

```bash
python -m pip install -r requirements.txt
python tools/mnl.py catalog
```

Run the bundled capacity example from raw network and demand tables:

```bash
python tools/mnl.py run --input app/cases/capacity_zone_probe/input --config app/cases/capacity_zone_probe/case.json --seed-mode auto --seed-k 1 --output results/capacity-demo
python tools/mnl.py verify --run results/capacity-demo
```

Open `results/capacity-demo/report.html` to inspect the results. The expected solution sends 3 units through the lower-cost route and 7 through the alternative, for an objective of **27**. This expectation is specific to the bundled example.

Choose a new output directory for each run. Inputs and outputs must be separate. See [installation and execution](docs/getting-started.md) for virtual environments, the portable Windows option, and supplied-route mode.

## Bring your own network

Start with the [input profile](docs/data-contract.md), declare your field mappings and units in `case.json`, then use the same entry point:

```bash
python tools/mnl.py validate --input /path/to/network/input --config /path/to/network/case.json
python tools/mnl.py run --input /path/to/network/input --config /path/to/network/case.json --seed-mode auto --seed-k 5 --output results/network-run
python tools/mnl.py verify --run results/network-run
```

The current profile is deliberately finite: a one-minute time step, positive integer travel times, a common departure time, fixed costs and declared size limits. This is not an unrestricted city-scale DTA or static user-equilibrium interface. [Profile constraints →](docs/data-contract.md#model-profile)

## From inputs to results

```text
Network + demand + configuration
              │
       Input normalization
              │
     Initial route generation
              │
    Explicit space–time network
              │
    Reference LP + Phase-I/II CG
              │
Final path pool · path flows · duals
              │
  Independent result verification
```

The allowed network is defined independently of the initial routes. The final export contains every column in the last successfully solved pool, including zero-flow columns. Reference agreement and independent pricing closure are reported as different forms of evidence.

## Project layout

```text
app/src/gmns_dynamic/   Selected numerical engine and input workflow
app/cases/             Self-contained reference inputs
launcher/              Solver-free result verification
algorithms/static_fw/  Retained static FW implementation
catalog/               Dataset records and source provenance
schemas/               Catalog and instance metadata schemas
docs/                  User documentation and static project website
tools/                 Public entry point and repository checks
```

## Ecosystem and interoperability

The project follows the network vocabulary of [GMNS](https://github.com/zephyr-data-specs/GMNS) and references [GMNS Plus Dataset](https://github.com/HanZhengIntelliTransport/GMNS_Plus_Dataset) and [TAPLab](https://github.com/asu-trans-ai-lab/TAPLab). These are distinct upstream projects; their data preparation, algorithms and licenses remain attributed to their authors.

[Integration guide](docs/integrations.md) explains how to map compatible inputs without conflating different demand, capacity or time conventions. Network acquisition, GPS matching, transit and new city collections are tracked in the [roadmap](docs/roadmap.md); they are not advertised as shipped capabilities.

## Contributing and data access

Contributions are welcome as reproducible instances, focused solver adapters, verification improvements and documentation. Follow the [contribution guide](CONTRIBUTING.md), include provenance, and separate observed data from estimated or synthetic inputs.

Data access and licensing are component-specific. Consult [data access and notices](docs/data-access.md) before redistributing upstream files. Cite the version and dataset record used; see [citation guidance](docs/citation.md).

## License and rights

Original project code is available under the [MIT License](LICENSE). The root license does not relicense external projects, third-party dependencies or upstream datasets. See [third-party notices](THIRD_PARTY_NOTICES.md) and [data licenses and publication boundaries](DATA_LICENSES.md).
