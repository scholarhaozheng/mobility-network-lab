# Berkeley atlas: functions, metrics and reading guide

This local reading revision uses saved results only. It does not rerun an optimizer, alter an acceptance gate, or manufacture missing iterations. All original accepted figures and captions remain available in the Berkeley volume.

## Shared visual language

The actual currently displayed Boston and Hong Kong atlas uses the selected C compact layout, A/B navy–blue–teal palette, white background and DejaVu Serif. `atlas_style.py` preserves the current `figure_style.py` functions `configure`, `new_figure`, `format_axes`, and `compact_header`; `plot_common.py:save` exports PNG at 300 dpi, PDF with embedded TrueType fonts, and SVG with editable text and embedded WOFF font subsets. `selected-style.json` records the selected specification.

Absolute physical-flow maps use real road geometry and square-root normalization (`PowerNorm(0.5)`) with the original units on colorbars. Comparable absolute maps share a scale. Signed differences have a separate symmetric, zero-centered scale. The difference scale is not evidence of a large difference: always read its units and magnitude. Axes retain observed data; no smoothing or fabricated intermediate records is used.

## Scientific boundaries

- S72: 72 loaded OD pairs, 953.049842713612 PCE over a one-hour static period, 2,150 physical links, and a 360-path finite pool. FW, finite-path, and Native rank 26/52 share that instance. Native path coordinates (98/124) exclude the 2,150 explicit link variables; total variable counts are 2,248/2,274. No speedup claim follows from these dimensions.
- T4: four OD/departure records, 10.439304601026278 PCE, 30-second steps and 165 steps. LP, CG, LR and accepted ADMM refer to this separate fixed-cost finite graph. Objective units are PCE·min; a movement-only physical projection has PCE units over the horizon, not automatically PCE/h.
- ADMM: all 170 actual saved updates are retained (38 C1 + 132 C2a under its disclosed new wall budget). The 300-update ceiling is not a trace. The relative objective acceptance criterion stays `abs(J−J_LP)/max(abs(J_LP),1) <= 1e-4`. Feasibility uses its frozen `1e-5 PCE` gate; primal and dual use their own recorded thresholds.
- Balance/capacity and primal residuals have PCE units. The dual residual `rho * norm(z_k−z_(k−1))` has minute units because rho has min/PCE units. Only exact-zero feasibility values receive a disclosed log-display value of `1e-16 PCE`; positive values are not clipped.
- Objective agreement and flow agreement are separate. T4 ADMM has objective 43.66974694298355 against LP 43.66742440800644 PCE·min (relative difference 0.00531869%); its largest physical-link difference from LP is 0.990967760238112 PCE. LP, CG and LR have identical saved movement projections. All 2,150 physical links are retained, including 137 without a movement arc in T4.

Boston and Hong Kong do not use one interchangeable ADMM objective metric: Boston G-F065 plots raw objective on linear axes with an LP reference; Hong Kong G-F097 plots log10 absolute objective error. This revision makes absolute and relative error explicit. The independent HK4 gate is 1e-3, not Berkeley's 1e-4. HK10 CG/LR, HK4 ADMM and the full-city static problem are distinct instances. Boston's LR final gap is 1.1002%, above its frozen 1% criterion; Hong Kong HK10 is 0.744419%, below 1%.

## Reproduce only the figures

The `renderers/` directory is self-contained with the neighboring `data/` directory. With Python, NumPy, Matplotlib, Pillow, fontTools, and Shapely available, run `python render_static.py`, `python render_finite.py`, `python render_admm.py`, and `python render_flow_maps.py` from `renderers/`. Outputs go into `renderers/regenerated/`. The complete project also contains these scripts under `tools/visuals/berkeley_alignment_r2/`. Neither route invokes a solver. Per-figure source records contain input/output SHA-256 hashes and renderer function names. PNG/SVG/PDF, exact plot data, caption, and source record are linked beside every figure.

## Figure-by-figure definitions

### ADMM original-coordinate feasibility

`accuracy_local_and_capacity_gates` — `render_admm.py:local:110`.

```json
{
  "a": "local_balance_pce; exact-zero-only display floor 1e-16",
  "b": "capacity_excess_pce; exact-zero-only display floor 1e-16"
}
```

Original-unit local balance error and capacity excess from all 170 saved ADMM updates, in PCE. Both are compared with their unchanged 1e-5 PCE scientific gate. Exact zeros alone are drawn at 1e-16 PCE for log display; this artificial display position is not a measured positive residual. Every positive value remains unchanged, including positive values below 1e-16. Zero counts: local balance 0; capacity excess 71. The vertical separator follows the 38 C1 updates. These original-coordinate scientific checks are separate from primal consensus and the rho-scaled dual update. No smoothing, fabricated iterations or new solve.

Inputs: `data/accuracy_local_and_capacity_gates.plot_data.json`.

### ADMM objective: absolute and relative error

`accuracy_objective_vs_lp` — `render_admm.py:objective:82`.

```json
{
  "a": "log10(abs(objective-LP)/(1 PCE·min))",
  "b": "abs(objective-LP)/max(abs(LP),1), semilog y"
}
```

Two views of the same 170 saved ADMM own-x objective values, with the independent same-T4 LP reference 43.66742440800644 PCE·min. Panel a is log10 absolute difference relative to one PCE·min, following the current Hong Kong absolute-objective-error representation; Boston uses raw objective against LP. Panel b is abs(ADMM−LP)/max(abs(LP),1), a dimensionless quantity on a logarithmic y axis. Its horizontal 1e-4 gate equals 0.01%; the final value 5.31869009587e-5 equals 0.00531869%. The equivalent gate is also marked on panel a. Every saved point is positive and is displayed without a floor, smoothing or interpolation. The separator follows outer 38; the actual selected run ends at outer 170, while the registered ceiling remains 300. Reaching the objective criterion earlier did not mean all stopping conditions had passed. This objective comparison does not establish identical physical-link flows.

Inputs: `data/accuracy_objective_vs_lp.plot_data.json`.

### ADMM primal and dual stopping checks

`accuracy_primal_dual_internal_gates` — `render_admm.py:internal:97`.

```json
{
  "a": "primal_residual and recorded_primal_threshold (PCE)",
  "b": "dual_residual and recorded_dual_threshold (min)"
}
```

All saved primal and dual residuals with their recorded stopping thresholds. Primal residuals have PCE units. The dual residual rho times the norm of the consensus update has minutes as its unit because frozen rho is min/PCE; it is not another PCE feasibility residual. The internal stop changes from C1 to the accepted C2a absolute/relative policy 1e-6/1e-5 after outer 38, while rho stays fixed. Neither that internal stopping policy nor this plot replaces the unchanged original-coordinate feasibility and same-LP scientific gates. All points are positive; no log floor, interpolation or smoothing is applied. The final primal and dual checks both pass at cumulative outer 170.

Inputs: `data/accuracy_primal_dual_internal_gates.plot_data.json`.

### ADMM convergence and objective agreement

`admm_convergence` — `render_admm.py:convergence:54`.

```json
{
  "a": "local_balance_pce and capacity_excess_pce; semilog y, exact-zero-only 1e-16 PCE display floor",
  "b": "primal_residual and recorded_primal_threshold; PCE; semilog y",
  "c": "dual_residual and recorded_dual_threshold; min; semilog y",
  "d": "log10(abs(ADMM_objective_pce_minutes - same_T4_LP_objective_pce_minutes)/(1 PCE·min)); no zero floor needed"
}
```

Accepted Berkeley T4 ADMM saved history, all 170 recorded outer iterations. The four panels follow the current Boston/Hong Kong diagnostic objects: original-unit balance and capacity feasibility, primal consensus, dual update, and log10 absolute objective error against the independent LP on the same T4 graph. Balance/capacity and primal residuals are PCE. The dual residual is rho times the consensus change and is in minutes: rho has min/PCE units. The dotted scientific feasibility gate is 1e-5 PCE; the internal thresholds are the recorded values. The objective gate line is the unchanged 1e-4 relative criterion expressed on the absolute-error axis. Only exact-zero feasibility values use a display value of 1e-16 PCE; every positive value, including smaller positives, is retained unchanged. The vertical separator is after C1 outer 38; C2a contributes 132 further updates under its disclosed new wall budget. The actual trace ends at 170; the registered 300-outer ceiling is not an extrapolated trace. Final own-x objective is 43.66974694298355 PCE·min against LP 43.66742440800644 PCE·min, absolute difference 0.00232253497711 PCE·min and relative difference 0.00531869%. Objective agreement is separate from physical-link flow agreement. No smoothing, interpolation or solver call.

Inputs: `data/accuracy_objective_vs_lp.plot_data.json`, `data/accuracy_primal_dual_internal_gates.plot_data.json`, `data/accuracy_local_and_capacity_gates.plot_data.json`.

### ADMM and LP physical-link flow

`admm_physical_flow_comparison` — `render_flow_maps.py:<module>:1`.

```json
[
  "ADMM physical projection",
  "Independent LP physical projection",
  "Signed physical-link difference",
  "All-link identity comparison"
]
```

Saved Berkeley T4 physical-link projections for four assumed first-bin OD pulses (10.439304601 PCE), using the accepted ADMM own x at completed outer 170 and an independently solved same-graph LP. Panels a–b share a PowerNorm(0.5) absolute color scale. Panel c uses a separate symmetric ADMM-minus-LP scale; panel d contains all 2,150matched physical IDs and an identity line. The maximum physical-flow difference is 0.990967760238112 PCE, despite a relative objective difference of 0.00531869%. The objective gate does not establish link-flow equality. All 2,150 original road geometries are retained with longitude/latitude aspect correction. The 137 links without a movement arc in the bounded T4 graph remain zero and are shown dotted; missing sparse LP entries are zero-filled by physical ID. Flows are PCE over this bounded departure instance, not hourly counts or observed traffic. No optimizer was rerun. © OpenStreetMap contributors, ODbL 1.0.

Inputs: `data/admm_physical_flow.csv`, `data/physical_geometry.csv`.

### LP, CG and LR share this physical projection

`lp_cg_lr_physical_flow` — `render_flow_maps.py:<module>:1`.

```json
[
  "Common full-road physical projection",
  "All-link equality comparison"
]
```

The independent LP, complete-pricing CG and LR’s own feasible recovery give identical saved aggregate physical-link projections in this Berkeley T4 instance. The map uses the full 2,150-link road inventory and the same absolute PowerNorm(0.5) scale as the ADMM–LP comparison. The scatter plots all 2,150 IDs; both CG and LR coincide with the identity line at stored precision. Each original sparse flow table stores 340 links; other physical IDs are zero-filled, including 137 without movement support in this bounded graph. This equality of physical projections does not imply identical paths, identical optimization trajectories, or equality in other instances. T4 contains four assumed first-bin OD pulses, not the full hourly demand. Units are PCE per bounded instance. No optimizer was rerun. © OpenStreetMap contributors, ODbL 1.0.

Inputs: `data/admm_physical_flow.csv`, `data/physical_geometry.csv`.

### S72 flow support and frozen path pool

`s01_geography_pool` — `render_static.py:s01_geography_pool:73`.

```json
[
  {
    "id": "a",
    "metric": "FW physical-link flow",
    "unit": "PCE/h",
    "rows": 2150,
    "transform": "PowerNorm(gamma=0.5); line width=0.4+1.35*sqrt(flow/maxflow); all nonzero values retained",
    "join": "positive_links left-joined to physical_geometry.link_id; absent values independently verified zero"
  },
  {
    "id": "b",
    "metric": "path count by rank_in_od",
    "unit": "path count",
    "rows": 360,
    "transform": "groupby rank_in_od; 0 designated major; ranks 1..4 minor"
  },
  {
    "id": "c",
    "metric": "all-link flow histogram",
    "x_unit": "PCE/h",
    "y_unit": "physical-link count",
    "transform": "20 equal bins over [0,400]; logarithmic count axis; zero-flow rows remain in first bin",
    "rows": 2150
  },
  {
    "id": "d",
    "metric": "origin_q_pce",
    "unit": "PCE/h in one declared hour",
    "rows": 9,
    "transform": "none; tract label suffix after five-character state/county prefix"
  }
]
```

Saved Berkeley S72 FW endpoint on all 2,150 frozen directed physical road links. The 670 positive entries are left-joined by persistent link ID; the other 1,480 links are exactly zero, verified against the complete saved physical-link table. The flow map uses all original road vertices, square-root colour normalization and widths, and local display kilometres; its gray background retains the full graph. The histogram includes all 2,150 links, including exact zeros in the first bin, with logarithmic count only. The nine positive origin totals sum to 953.049842713612 PCE in the one-hour model. The frozen K=5 pool has 360 paths for 72 OD pairs: one designated major and four minor paths per OD, 72 major and 288 minor in total. The candidate paths and access points are not drawn in this new map. This is an uncalibrated engineering scenario, not surveyed traffic. © OpenStreetMap contributors, ODbL 1.0. Saved-result derivative; the original accepted source figure remains available.

Inputs: `data/s01_geography_pool.plot_data.json`, `data/physical_geometry.csv`, `data/s72_pool_structure.json`.

### S72 same-instance method diagnostics

`s02_same_instance_methods` — `render_static.py:s02_same_instance_methods:147`.

```json
[
  {
    "id": "a",
    "metric": "(saved_objective - saved_FW_objective) * 1e6",
    "unit": "micro PCE·min",
    "rows": 4,
    "transform": "linear; signed"
  },
  {
    "id": "b",
    "metric": "full_relative_gap",
    "unit": "dimensionless",
    "rows": 4,
    "transform": "symlog(linthresh=1e-14,linscale=1)",
    "scientific_gate": "|full_relative_gap| <= 1e-5",
    "formula": "(sum_a v_path[a]*t_a(v_path[a]) - sum_od q_od*shortest_path_cost_od_on_full_graph_at_final_costs) / max(sum_a v_path[a]*t_a(v_path[a]), 1e-12)",
    "negative_signed_value_retained": true
  },
  {
    "id": "c",
    "metric": [
      "max_od_residual",
      "max_link_reconstruction"
    ],
    "unit": "PCE",
    "rows": 4,
    "transform": "multiply by 1e10 for linear display; exact zeros preserved"
  },
  {
    "id": "d",
    "metric": "finite path coordinates; Native major-plus-rank coordinates and explicit physical-link variables",
    "unit": "count",
    "rows": 3,
    "transform": "stacked counts; no speed or total-dimension advantage claim"
  }
]
```

Four saved terminal checks of the same S72 graph, demand, BPR coefficients and K=5 pool; all four have ACCEPTED_FULL_GRAPH status. (a) The saved objective minus the FW objective is shown in micro PCE·minutes; the tiny rank-26 negative difference is retained. (b) The signed full-graph relative gaps use a symmetric-log display with a linear interval of ±10⁻¹⁴. Both bounds of the accepted |full-graph relative gap| ≤ 10⁻⁵ gate are shown; no positive value is clipped, and the negative rank-26 numerical gap is not converted to an absolute value. (c) Maximum OD mass and physical-link reconstruction residuals are shown on a linear axis in 10⁻¹⁰ PCE; exact zeros remain zero. (d) The finite pool has 360 path coordinates. Native ranks 26 and 52 use 98 and 124 representation coordinates (72 major plus rank), but each also contains 2,150 explicit physical-link variables, for raw totals of 2,248 and 2,274. Thus the compact path representation is not a claim of fewer total variables or faster computation. Native records contain three outer iterations per rank; this terminal comparison is not a convergence trace. Only one engineering scenario is shown, with no uncertainty interval or measured-traffic validation.

Inputs: `data/s02_same_instance_methods.plot_data.json`, `data/physical_geometry.csv`, `data/s72_diagnostic_definition.json`.

### Native and FW physical-link flow

`s03_native_flows` — `render_static.py:s03_native_flows:239`.

```json
[
  {
    "id": "a",
    "metric": "FW_flow_pce_per_hour",
    "rows": 2150,
    "unit": "PCE/h",
    "transform": "shared PowerNorm(gamma=0.5); width=0.4+1.35*sqrt(abs(flow)/shared absolute maximum)",
    "shared_colour_min": -4.380487468063516e-47,
    "shared_colour_max": 390.318194730158
  },
  {
    "id": "b",
    "metric": "Native26_flow_pce_per_hour",
    "rows": 2150,
    "unit": "PCE/h",
    "transform": "shared PowerNorm(gamma=0.5); width=0.4+1.35*sqrt(abs(flow)/shared absolute maximum)",
    "shared_colour_min": -4.380487468063516e-47,
    "shared_colour_max": 390.318194730158
  },
  {
    "id": "c",
    "metric": "Native52_flow_pce_per_hour",
    "rows": 2150,
    "unit": "PCE/h",
    "transform": "shared PowerNorm(gamma=0.5); width=0.4+1.35*sqrt(abs(flow)/shared absolute maximum)",
    "shared_colour_min": -4.380487468063516e-47,
    "shared_colour_max": 390.318194730158
  },
  {
    "id": "d",
    "metric": "Native26_minus_FW",
    "rows": 2150,
    "unit": "micro PCE/h",
    "transform": "actual saved Native explicit v minus actual FW flow; multiply 1e6; shared symmetric linear colour and shared sqrt width maximum",
    "colour_bounds_micro": [
      -1.585378498702994,
      1.585378498702994
    ],
    "max_abs_difference_pce_per_hour": 2.6458621960046003e-08
  },
  {
    "id": "e",
    "metric": "Native52_minus_FW",
    "rows": 2150,
    "unit": "micro PCE/h",
    "transform": "actual saved Native explicit v minus actual FW flow; multiply 1e6; shared symmetric linear colour and shared sqrt width maximum",
    "colour_bounds_micro": [
      -1.585378498702994,
      1.585378498702994
    ],
    "max_abs_difference_pce_per_hour": 1.585378498702994e-06
  },
  {
    "id": "f",
    "metric": "Native minus FW against FW physical-link flow",
    "rows_per_method": 2150,
    "x_unit": "PCE/h",
    "y_unit": "micro PCE/h",
    "transform": "linear axes; all points including exact overlap"
  }
]
```

Actual saved FW and Native rank-26/rank-52 explicit physical-link vectors, each joined one-to-one to all 2,150 frozen S72 link geometries. Finite-path flow is not used as a Native substitute. The three absolute maps share a square-root colour scale and the same geographic bounds; the two signed Native−FW maps share a symmetric zero-centred scale. Differences are magnified into 10⁻⁶ PCE/h and retain their signs. Maximum absolute differences are 2.645862196e-08 PCE/h for rank 26 and 1.585378499e-06 PCE/h for rank 52. Panel f includes every physical link, including overlapping points at zero. These are tiny numerical endpoint differences, not traffic improvement, diversion sensitivity or measured accuracy. Rank-52 raw flow includes numerical negatives down to −4.380487468063516×10⁻⁴⁷ PCE/h; they remain in the source and the common colour normalization lower bound, without clipping. Line widths use absolute magnitude with the same maximum within each comparison family. Local display kilometres preserve the original road vertices. © OpenStreetMap contributors, ODbL 1.0. One bounded uncalibrated one-hour engineering scenario; no new solver run.

Inputs: `data/s72_physical_flow.csv`, `data/physical_geometry.csv`.

### Computed column: route, cost and model time

`t01_computed_column` — `render_finite.py:t01_computed_column:40`.

```json
{
  "a": "Actual ordered movement path joined to physical road geometry",
  "b": "Saved distance against elapsed rounded model clock",
  "c": "Fixed cost, physical elapsed clock and terminal bookkeeping time"
}
```

Saved positive T02 column 1 carries 7.5 PCE. Panel a joins all 89 saved, ordered movement link IDs to the real physical-road geometry; consecutive endpoints and time steps are verified. The map shows the route with nearby model roads as context, using longitude/latitude and a latitude-adjusted aspect ratio. Panel b retains all 91 supplied distance/time vertices for these movements; positions use the rounded 30-second state clock, not an observed trajectory. The path accumulates 2.6023 km, departs at 08:02:30 and physically arrives at 08:47:00 (44.5 elapsed minutes). Panel c separates the unchanged 3.90345 fixed objective minutes from that rounded elapsed time and the H165 sink at 09:22:30 (80 minutes after departure). The terminal sink is accounting, not extra physical travel. This is a computed route, not a schematic full time-layer network.

Inputs: `data/t01_computed_column.plot_data.json`, `data/t01_selected_path.csv`, `data/physical_geometry.csv`.

### Column generation: feasibility and pricing

`t02_cg_phases` — `render_finite.py:t02_cg_phases:108`.

```json
{
  "a": "Phase I artificial flow",
  "b": "Phase II real-cost objective and same-T4 LP",
  "c": "Full-graph reduced costs on separate phase-unit axes",
  "d": "Column-pool size at every saved checkpoint"
}
```

All five Phase I and three Phase II saved records are shown. Phase I minimizes artificial flow in PCE and clears it at round 4. Phase II minimizes real PCE·min cost, reaching the independent same-T4 LP value 43.66742440800644 at saved round 1; its complete-graph pricing record then closes at round 2 with minimum reduced cost −4.4408920985e−16 minutes and ten columns. Panel c gives Phase I's dimensionless reduced costs and Phase II's minute-valued reduced costs separate axes. The actual frozen tolerances are 1e−8 PCE artificial flow and 1e−8 dimensionless negative reduced cost in Phase I, and 1e−7 minutes negative reduced cost in Phase II; a column is added only when reduced cost is below the negative tolerance. Zero is the plotted reference line; the Phase II tolerance is annotated separately because the two are indistinguishable at this scale. Panel d retains the repeated eight-column checkpoint at the phase transition. Lines connect saved records; no unsaved rounds, smoothed values or extra solver iterations are inserted.

Inputs: `data/t02_cg_phases.plot_data.json`, `data/accuracy_objective_vs_lp.plot_data.json`, `data/t02_frozen_pricing_gates.json`.

### Lagrangian bounds and primal recovery

`t03_lr_bounds_physical` — `render_finite.py:t03_lr_bounds_physical:153`.

```json
{
  "a": "Best valid dual and available feasible upper versus same-T4 LP",
  "b": "Available certified gap against frozen1%gate",
  "c": "Saved path-pool growth",
  "d": "Two actual separate recovery LP attempts"
}
```

All ten saved Berkeley T4 Lagrangian iterations are retained. The best valid dual bound is 43.58459836422644 PCE·min; individual relaxed dual iterates are different and are not feasible primal costs. The own-pool recovery is infeasible at iteration 1 with four paths and feasible at iteration 10 with six paths, yielding 43.667424408006426 PCE·min. Its certified relative gap is 0.0018967467145784354 (0.18967467145784354%), within the frozen 1% gate. Before iteration 10, best-primal and gap values are absent and remain unplotted. The same-graph LP value 43.66742440800644 is a separate numerical reference, not a substituted LR flow. Panel d shows exactly the two saved recovery calls, with the infeasible call's null objective kept missing. The original 340-row positive physical-flow comparison is retained unchanged in the accompanying plot-data record; this diagnostic figure does not imply that those rows cover the entire 2,150-link physical graph.

Inputs: `data/t03_lr_bounds_physical.plot_data.json`, `data/t03_recovery_history.json`, `data/accuracy_objective_vs_lp.plot_data.json`.

