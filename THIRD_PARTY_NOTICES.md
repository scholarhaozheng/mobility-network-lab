# Third-party notices

## Scope of the root license

The root [MIT License](LICENSE) applies only to original project code for which the copyright holder has the right to grant that license. It does not relicense third-party code, third-party data, external tools or upstream projects. Any third-party material added in the future must retain its own copyright, license and attribution notices.

The publication review found no copied source code from the external projects listed below in this upload set. They are referenced for interoperability, data vocabulary or optional upstream preparation only.

## Runtime dependencies not vendored

| Dependency | Use | Distribution status |
|---|---|---|
| [NumPy](https://numpy.org/) | Numerical arrays | Installed separately; no package source or binary is included |
| [SciPy](https://scipy.org/) | Linear programming and sparse algorithms | Installed separately; no package source or binary is included |
| [PyYAML](https://pyyaml.org/) | Configuration parsing | Installed separately; no package source or binary is included |
| [pandas](https://pandas.pydata.org/) | Optional static Frank–Wolfe input handling | Installed separately; no package source or binary is included |
| [markdown-it-py](https://github.com/executablebooks/markdown-it-py) | Documentation generation | Installed separately; no package source or binary is included |

Each dependency remains governed by the terms supplied by its own maintainers and distributors.

## Referenced upstream projects not bundled

| Project | Relationship to Mobility Network Lab |
|---|---|
| [GMNS](https://github.com/zephyr-data-specs/GMNS) | Referenced network vocabulary and specification; no GMNS repository source is copied here |
| [GMNS Plus Dataset](https://github.com/HanZhengIntelliTransport/GMNS_Plus_Dataset) | Referenced external data ecosystem; no GMNS Plus source dataset is copied here |
| [TAPLab](https://github.com/asu-trans-ai-lab/TAPLab) | Referenced external assignment and validation ecosystem; no TAPLab source or benchmark data is copied here |
| [OSM2GMNS](https://github.com/asu-trans-ai-lab/OSM2GMNS) | Referenced optional upstream preparation tool; no OSM2GMNS source is copied here |
| [grid2demand](https://github.com/asu-trans-ai-lab/grid2demand) | Referenced optional upstream demand tool; no grid2demand source is copied here |
| [TransportationNetworks](https://github.com/bstabler/TransportationNetworks) | Referenced benchmark collection; no raw TransportationNetworks dataset is copied here |

Follow the license and attribution terms published by the exact upstream version you obtain. A link or compatibility statement in this repository is not a license grant for an upstream project.

## Retained project source

The selected numerical engine, public input workflow, verification modules and static Frank–Wolfe source are recorded in [`catalog/source-files.json`](catalog/source-files.json). Their hashes are checked by `tools/check_repository.py`. The maintainer confirmed the right to publish the original project code under the root MIT License on 2026-09-17.
