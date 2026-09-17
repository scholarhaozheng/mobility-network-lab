# City network workflow

A city instance connects a study area, road network, zones, demand and mobility evidence to a defined assignment or optimization model. The same identifiers, time conventions and validation rules should carry through the pipeline. This is the organizing direction of Mobility Computation Lab, not a claim that a raw-city compiler is already shipped.

## The shared modelling sequence

```text
City / study area and data provenance
                 ↓
Road network and mode-specific links
                 ↓
Zones, spatial levels, centroids and network access
                 ↓
OD demand with explicit volume, time and source
                 ↓
Assignment / optimization → paths, flows, costs and checks
                 ↑
Supporting evidence: GPS, counts, speeds and transit services
```

Observation layers can inform model preparation or later calibration. They must not silently become demand or capacity merely because they are spatially nearby.

## Start with what is executable

The current network route begins with **prepared node, link, demand and optional zone-access tables**. Follow the [input contract](data-contract.md), [route initialization guide](routes.md) and [quick start](getting-started.md). The public metadata route separately accepts local catalog and city tables; see [data tools](data-tools.md).

| City component | What the current release does | What an extension must add |
|---|---|---|
| Study area | Record provenance in the instance data card | Acquire/validate the actual boundary and document subarea treatment |
| Road network | Read explicit directed-node/link tables and check the finite model profile | An actual OSM2GMNS or other preparation step with a recorded input/output mapping |
| Zones / hierarchy | Use supplied zone-to-node access mappings | Zone geometry, parent/child spatial levels, centroid connectors and boundary gateways |
| OD demand | Read supplied demand with explicit time and volume | A separately documented generation, estimation or prediction model |
| Mobility evidence | Normalize and match city/catalog metadata; preserve source summaries | Actual GPS/count/speed/transit records mapped to this network and time support |
| Computation | Run finite space–time CG; retain a separate static FW baseline | Additional model-compatible adapters; origin-based / Policy Bush extensions |
| Results | Export complete solved columns and verify stored outputs; show road benchmark figures | New city-specific results produced by the new instance, with its own checks |

## Reuse upstream tools rather than duplicate them

[GMNS Plus](https://github.com/HanZhengIntelliTransport/GMNS_Plus_Dataset) provides reference network organization. [OSM2GMNS](https://github.com/asu-trans-ai-lab/OSM2GMNS) and [grid2demand](https://github.com/asu-trans-ai-lab/grid2demand) are candidate upstream preparation tools. [TAPLab](https://github.com/asu-trans-ai-lab/TAPLab) provides separate assignment implementations and experiment conventions. Follow [interoperability](interoperability.md) and the actual source licenses; these links do not mean all tools are bundled or already run by this release.

The OMDV modules prepare metadata and support source discovery. Exact city-name matching is **not GPS map matching**. A GTFS service schedule is not passenger OD demand, and the evidence catalog is not a collection of assignment-ready city models.

## A complete city contribution

A contribution should identify its geographic scope; provide lawful inputs or acquisition instructions; document network, zone and OD identifiers; name every estimated or synthetic input; provide the executable model configuration; and retain results that map back to the same physical network. A small actual subarea is acceptable. Renaming a synthetic regression as a city is not.

If trajectories or observations are not available, state the missing layer in the data card. Do not invent an observation layer or display calculated routes as GPS traces. All new executable commands must be backed by an implementation and a tested example.

## Beyond one instance

Use one complete case to exercise the interfaces before adding a second city. Hong Kong, Melbourne, Cairo and Paris are candidate extensions, not bundled city datasets. They should differ through data and configuration rather than independent solver rewrites.

[Network catalog](datasets.md) · [Visual results](visualizations.md) · [Development roadmap](roadmap.md)
