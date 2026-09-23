# Central Boston visual sources and units

The [five-map gallery](boston-central.md#boston-visual-gallery) uses images under the repository-relative directory `docs/assets/boston/visual_release_r1/`. The same directory holds `mcl_boston_hero.png` / `.svg` and the separate `mcl_social_preview.png` for a manual repository Social preview setting. The cover depicts geography, not traffic. Each analytical PNG also has a static SVG counterpart with the same stem; the figures have English labels, units and attribution in the image and gallery.

| Image stem | Saved source and version | Encoded quantity / boundary |
|---|---|---|
| `boston_network_zones` | GMNS Plus `21_Boston`, commit `116447ab641cca1ed34797d019c8e704063393c3`; project H3 r9/r7 zones and one ordered corridor | Physical directed roads, zones and kilometres; parcel outlines are context, not building footprints |
| `boston_activity_prior` | MassGIS Property Tax Parcels, Boston FY2023 and Cambridge FY2026; activity run `boston_activity_prior_r1_20260922` | Selected residential assessment field `RES_AREA`, square feet allocated to zones; 145 nonmissing, 32 blank; not trips or population |
| `boston_gps_projection` | MassDOT / MBTA V3 derived position progression, quality run `boston_quality_r1_20260922` | One quality-eligible 12-point segment, lateral offsets in metres; not passenger OD or an overall matching-accuracy estimate |
| `boston_panel_flow_s1` | Saved `behavior_feedback_r1_semantic_fix_r1` S1 planned-service assignment | Directed modeled vehicle trips in the fixed HBW panel; no background traffic |
| `boston_panel_flow_delta` | Saved semantic-fix S2 exploratory GPS overlay minus S1 on the same directed links | Signed modeled vehicle-trip difference, symmetric legend; maximum absolute change about `0.00660264` |

All geographic display scales use WGS84 / UTM zone 19N (`EPSG:32619`); source network geometry remains WGS84 (`EPSG:4326`). The flow maps share a viewport. The chosen activity field and GPS segment are separate source examples and are not claimed to be the exact event behind the fixed-panel feedback trace.

Road source: [GMNS Plus Dataset](https://github.com/HanZhengIntelliTransport/GMNS_Plus_Dataset), Apache-2.0; retain its source license and notice. Parcel source and credit: [MassGIS Property Tax Parcels](https://www.mass.gov/info-details/massgis-data-property-tax-parcels), MassGIS (Bureau of Geographic Information), Commonwealth of Massachusetts EOTSS. Position source: MassDOT / MBTA V3, subject to the [MassDOT developer license](https://www.mass.gov/doc/developers-license-agreement-11132009/download) and provider acknowledgement. Project-derived zones, matched progression and saved assignment figures: Mobility Computation Lab. Consult [data licenses](../../DATA_LICENSES.md), [third-party notices](../../THIRD_PARTY_NOTICES.md) and [Boston data sources](../../examples/boston/DATA_SOURCES.md) for the wider release terms.

The public [renderer and required input mapping](../../tools/visuals/README.md) accept explicit saved geometry and result files. The seven PNGs are not a self-contained source-data pipeline; no new data or model run is needed to view them.
