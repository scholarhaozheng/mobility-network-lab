# Ecosystem and integrations

The separate [interoperability catalog](interoperability.md) records model and exchange standards without treating them as city-level availability evidence. The [open-data evidence catalog](open-data.md) records observed source layers without claiming that each layer is a runnable network.

| Project | Role | Relationship to this repository |
|---|---|---|
| [GMNS](https://github.com/zephyr-data-specs/GMNS) | Network data specification | Vocabulary and explicit identifier conventions |
| [GMNS Plus Dataset](https://github.com/HanZhengIntelliTransport/GMNS_Plus_Dataset) | Standardized network collections and preparation tools | Referenced only; no upstream source or dataset is vendored |
| [TAPLab](https://github.com/asu-trans-ai-lab/TAPLab) | Assignment interfaces, solver adapters, validation and views | External workflow; not bundled into the CG entry point |
| [OSM2GMNS](https://github.com/asu-trans-ai-lab/OSM2GMNS) | OpenStreetMap-to-network conversion | Optional upstream preparation tool |
| [grid2demand](https://github.com/asu-trans-ai-lab/grid2demand) | Zone/activity-based demand generation | Optional upstream demand prior, not an observation or forecasting certificate |
| [TransportationNetworks](https://github.com/bstabler/TransportationNetworks) | Classical road benchmark collection | General benchmark source; exact historical bytes are not inferred |

## Map semantics, not only filenames

A TAPLab field such as `o_zone_id` may correspond to a profile's `origin_zone_id`, but time, capacity, demand units and centroid access must also agree. A settings file for static equilibrium is not a space–time configuration.

## Use upstream tools independently

Follow the selected upstream version's own installation and execution instructions. Record its commit and the input/output conversion. Do not copy an upstream result into a new run directory and call it a local execution.

## Attribution

GMNS, GMNS Plus, TAPLab, OSM2GMNS, grid2demand and TransportationNetworks retain their own authorship and license terms. No source code or raw dataset from those repositories is bundled here. This repository is not an official distribution of those projects and does not imply institutional sponsorship or endorsement. See the repository's [third-party notices](../THIRD_PARTY_NOTICES.md) and [data license boundaries](../DATA_LICENSES.md).
