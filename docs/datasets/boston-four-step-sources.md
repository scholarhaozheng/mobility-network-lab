# Boston four-step figures: display data and provenance

These three new charts render accepted saved results. They do not execute trip generation, IPF, mode choice, GPS matching or assignment. The existing Boston maps remain unchanged.

| Figure | Saved source | Display operation | Download |
|---|---|---|---|
| 01 · Trip generation | `public_component/data/trip_generation_by_purpose.csv` | Sum `productions_person_trips_daily` by original purpose code | [Six totals](../assets/boston/four_step_results_r1/data/generation_by_purpose.csv) |
| 02 · Trip distribution | `derived/regional_od_h3.csv` in the full English public asset | Filter `purpose=HBW`; pivot the saved `person_trips_midday_od` into stable H3 order | [Matrix](../assets/boston/four_step_results_r1/data/hbw_midday_matrix.csv) · [ID order](../assets/boston/four_step_results_r1/data/zone_order.csv) |
| 03 · Mode response | `public_component/data/od_mode_probabilities.csv` | Select `panel_od_019`, `12:30:00`, `mu_transit_sensitivity=1`; compute 100 × (S2−S1) | [Saved probabilities and percentage-point change](../assets/boston/four_step_results_r1/data/selected_mode_response.csv) |
| Numeric GPS trace | `public_component/data/feedback_trace.csv` | Read the single published source-keyed trace | [Display copy](../assets/boston/four_step_results_r1/data/selected_feedback_trace.json) |

[Exact member hashes and transformations](../assets/boston/four_step_results_r1/data/PROVENANCE.json) identify the accepted English data archive (`a3f33648c4dff3d3f462e4bbf4ebedb198665afd165688d0f481c88cded31d71`). Full precision is retained in display data; chart text is rounded for legibility.

The generation chart uses modeled workday **person trips**. The OD image uses modeled **midday HBW person trips**, not the whole daily total. Its `log(1+x)` colors have original-unit tick labels; blank means no exported entry, not a measured zero. The mode chart uses **percentage points**, with all nine source leaves retained. These scopes must not be added together.

The 36-OD panel is a selected subset. Its approximately 202 vehicle trips are not the full regional demand. S1 shares are a common regional baseline; S2 is a nested pivot response. The illustrated GPS event does not necessarily match the segment in the separate road-projection map.

## Render the supplied display data

Use an existing environment with NumPy and Matplotlib, then run from the repository root:

```bash
python -B tools/visuals/render_boston_four_step_results.py
```

The script reads the included display CSVs and writes PNG/SVG files under `docs/assets/boston/four_step_results_r1/`. It checks totals, zone order and probability sums before plotting. It makes no network request and does not change numerical results. Rendering libraries may produce different file bytes across versions even with identical numerical data.

The credited underlying sources remain ACS, MassGIS, CTPS TDM23 and MBTA, as registered by the public Boston component. [Population/household source versions, fields, preserved tables and reproduction](boston-population-households.md) now document the upstream step. The original [network/map credits](boston-visual-sources.md) continue to apply to the retained maps. Project-derived display tables are not a new release of household microdata or raw vehicle archives.

[Four-step result](boston-behavior-feedback.md) · [Network and earlier layers](boston-central.md)
