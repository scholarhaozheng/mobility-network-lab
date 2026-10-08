# Berkeley figure functions and reading contract

These figures use saved data with no solver runs. The exact selected C layout, DejaVu Serif font and blue/teal palette are shared with the Boston/Hong Kong workflow. The renderer is Python/matplotlib. SVG text remains editable; embedded font subsets ensure portable viewing.

| Figure | Function | Panels and metrics | Scope |
|---|---|---|---|
| Column generation: Phase I feasibility | `cg_phase_one` | Aggregate artificial flow at each saved phase-I round; Saved Phase-I pool size | finite |
| Phase II objective | `cg_phase_two` | Raw post-step objective, distinct saved-state markers and same-T4 LP reference | finite |
| Complete-graph pricing closure | `cg_pricing_closure` | Phase-I full-graph minimum reduced cost, unitless; Phase-II full-graph minimum reduced cost, minutes | finite |
| Frank–Wolfe: initial stopping check | `fw_saved_check` | Saved-state values; horizontal logarithmic relative gap versus gate; signed-gap guard | static |
| Lagrangian bounds and certified gap | `lr_bounds` | Teal best lower bound; blue recovered upper; percentage gap and 1% gate | finite |
| Lagrangian prices and relaxed capacity violations | `lr_prices` | Current maximum multiplier, min; Current positive multiplier count; Current relaxed maximum capacity excess, PCE | finite |
| Path-pool growth and separate primal recovery | `lr_recovery` | All saved path-pool sizes; Exactly two recovery calls and their feasibility | finite |
| Population and jobs in the 13 model zones | `population_jobs` | 2020 resident count by model zone; 2023 primary job count by model zone | population |
| Source geography and accepted model support | `source_geography` | Actual zones, roads, access nodes; no quantitative road-flow encoding | sources |
| Where the vehicle demand enters and leaves | `static_endpoints` | Origin demand at actual access nodes; Destination demand at actual access nodes | static |
| Demand ledger and vehicle assignment margins | `static_source_margins` | Person-trip generation boundary ledger; Complete 13-zone vehicle origin and destination margins | static |
| Road states across selected time layers | `time_layers` | Actual geographic 3D local graph at seven time layers; Same saved arc subset in a node-ID/time-index graph | construction |
| Scheduled transit geography and model availability | `transit_network` | All 168 source-envelope stop coordinates; Binary direct-transit OD availability, all 13 × 13 cells | transit |
| Scheduled service and direct-option time components | `transit_service` | Selected-day stop-event count by timetable hour; All 38 option times; sorted point offsets, median ticks | transit |

All quantitative panels preserve the saved values. No uncertainty bands, samples, runtime benchmark, sensitivity experiment, or unsaved iterations are inferred. The source record beside each figure lists its input SHA-256 identities.

The static case is one declared hour. Its demand and link-flow rates are PCE/h. T4 is a distinct finite instance; flow is PCE across its modeled horizon, and objective is PCE·min. The same independent T4 LP is a numerical reference rather than a replacement for another method’s flow.

To reproduce the new figures from the attached data and the installed Python plotting environment, run `python render_figures.py`; exports are written to `figures/`. This performs no scientific solve.

## Evidence not available for equivalent panels

- **A multi-iteration Frank–Wolfe convergence trajectory**: Accepted S72 history contains one initial check and zero updates. A direct saved-state ledger and stopping-threshold diagnostic are supplied; no later iteration is missing. Needed: A separately accepted run that actually performs FW updates and preserves its full history. The current accepted one-point run must not be relabelled as a convergence series.
- **Same-S72 Algorithm B result and convergence figure**: The accepted Berkeley transfer contains FW, finite full-path SLSQP and Native L3 rank-26/rank-52 results. It does not contain an accepted Algorithm B result for this exact identity. Needed: An accepted Algorithm B run on the identical S72 graph, demand, cost and gate, with endpoint flow, iteration history and independent full-graph checks.
- **CG Phase-I per-OD artificial-flow heatmap**: All five saved aggregate artificial-flow values and per-OD reduced-cost values exist, but the per-OD artificial-flow trajectory is not saved. Reduced costs are not artificial flows. Needed: Per-OD artificial variables from every saved Phase-I restricted-master solve, bound to round and OD IDs.
- **Saved mode-response sensitivity experiment**: The accepted four-stage case saves one OD-specific mode-choice scenario, with drive/direct-transit/walk probabilities and totals. No accepted fare, time, or parameter perturbation sweep is present. Needed: A declared and verified sensitivity sweep with the varied variable, unchanged controls and all saved alternative probabilities, or approval for a separate new experiment.
- **Public observed GPS trace and photo panels comparable to the Boston/Hong Kong observation cards**: Berkeley has separately documented private photo/GPS/map-matching evidence, but the current page explicitly excludes precise traces, camera pins, original photos, S2 trace cells and the private inspector. The new transit figures therefore use scheduled public-source derivatives only. Needed: A reviewed release-safe observation derivative with explicit rights, privacy treatment and trace-to-model provenance. No additional private/raw material is needed for the scheduled-service figures already supplied.
- **Finite full-path optimizer iteration curve**: Finite SLSQP has an accepted endpoint and one reported iteration, but no per-iteration objective/feasibility series is retained. Its full endpoint comparison and flow evidence are preserved. Needed: Saved callback history from that exact finite-path run, or a separately accepted instrumented run; a terminal result is insufficient to reconstruct the internal trajectory.

## R4: requested two-figure alignment

CG Phase II now matches Boston’s raw-objective post-step view. Point classes are derived from saved adjacent objective values and are not imported solver commit labels. LR uses the Hong Kong/Boston teal lower / blue recovered upper / percentage gap convention; the independent LP scalar is kept in source metadata, not drawn as a recovered upper trajectory. Berkeley has three CG states and only one feasible LR recovery at iteration 10. No smoothing, imputation or solver call is used.

## R5: FW initial stopping check

The FW card shows its complete saved iteration-0 state directly, with the relative gap and frozen threshold on a horizontal logarithmic metric axis. There is no objective zoom or iteration axis. Both relative-gap and signed-gap stopping conditions pass before any update. The objective is the Beckmann integral; it is not the total-travel-cost denominator used by the relative-gap formula. Other physical-flow maps and R4 CG/LR figures are preserved.
