<a id="document-top"></a>

MOBILITY COMPUTATION LAB / FOUR-STAGE AND ALGORITHM RECORD

# Berkeley

A 13-zone central Berkeley morning HBW model with 90 positive person OD pairs and 72 positive vehicle OD pairs on a conservatively restricted network.

The figures show saved method results, physical-flow maps and original-unit diagnostics. Drawing these figures invokes no optimizer.

**Local review · current S0-approved increment integrated.** Berkeley S72 and bounded T4 ADMM170 remain receiver accepted; original LR10 and the separate LR300 diagnostic retain their distinct identities.

Input snapshot: `mcl_s0_to_v_presentation_inputs_r3_v1@2026-10-05T03:57:54.309662+00:00`. Input version: `BERKELEY_CENTRAL_TWO_TILE_URBAN_SUBAREA_R2; frozen configuration SHA-256 f73c4abc3f73bdcca09f582c69242e9f7c655ac8002dcabc683882be9a3262d5`.

<a id="scope"></a>

## Scope and model instance

The Berkeley case concerns a 3.884 km² union of two research tiles covering downtown, the edge of UC Berkeley and a western residential corridor. Thirteen clipped tract zones describe this bounded urban area. Neither campus property nor the complete city or Bay Area is the demand boundary.

The modeled movement is one-way HBW during a weekday 08:00–09:00 local hour. A single forward calculation passes generated persons into a gravity distribution, an OD-specific mode model and static road assignment. Congested assignment times are not fed back into destination or mode choice. University location provides context, not a surveyed campus demand sample.

<a id="inputs"></a>

## Inputs and preparation

<a id="coverage-row-01"></a>

<a id="coverage-row-02"></a>

<a id="coverage-row-03"></a>

A larger 10.803 km² acquisition envelope was used to find candidate blocks and transit stops. For demand, however, a block contributes only if its official internal point lies inside a model zone. This discrete selection gives 31,821 residents from the 2020 Census and 16,583 primary workplace jobs from 2023 LODES WAC. Housing units are a separate field and were not relabelled as households.

The 4 October 2026 OSM/GMNS source has 8,991 physical links in the earlier preflight. The current automobile model retains 2,150 directed links after access and restriction screening. The node-based solver cannot express every one of the 41 recorded restriction relations. Its conservative policy removes 105 links on restriction from-ways, thereby preventing prohibited transitions but also eliminating some otherwise lawful alternatives. Another 21 auto links fail access screening.

Eleven zones have an auto access node in the retained strong component, while all thirteen have a walking node. These are engineering connections rather than certified parcel entrances or accessible crossings. The inherited F01 shows preflight road geography and is kept separate from the current flow result.

<a id="figure-r3-source-geography"></a>

[![Source geography and accepted model support](<../assets/city-alignment-r3/berkeley/source_geography.svg>)](<../assets/city-alignment-r3/berkeley/source_geography.svg>)

**Source geography and accepted model support.** All 13 model-zone polygons and all 2,150 accepted directed physical road links are shown. Number labels follow the complete generation/OD zone order. Teal points are the 11 saved auto access nodes; the two zones without an auto node remain in the geographic context. Road color is contextual and encodes no flow. This screened model differs from the inherited 8,991-link preflight source map. Display coordinates use the same local kilometre convention as Boston. © OpenStreetMap contributors, ODbL 1.0; zone geometry is derived from 2020 Census geography.

[SVG](<../assets/city-alignment-r3/berkeley/source_geography.svg>) · [PNG](<../assets/city-alignment-r3/berkeley/source_geography.png>) · [PDF](<../assets/city-alignment-r3/berkeley/source_geography.pdf>) · [Plot data](<../assets/city-alignment-r3/berkeley/source_geography.plot_data.json>) · [Source record](<../assets/city-alignment-r3/berkeley/source_geography.source.json>)

<a id="figure-f01-network"></a>

<a id="berkeley-population-evidence"></a>

## Population and workplace-source geography

The maps separate 2020 residents from 2023 primary jobs. Both use the same complete 13-zone indexing as the generation and OD tables. Counts follow the saved source-block internal-point selection; the color maps do not imply density or local empirical calibration.

<a id="figure-r3-population-jobs"></a>

[![Population and jobs in the 13 model zones](<../assets/city-alignment-r3/berkeley/population_jobs.svg>)](<../assets/city-alignment-r3/berkeley/population_jobs.svg>)

**Population and jobs in the 13 model zones.** The two maps retain all 13 model zones, with independent linear count color scales. Population sums to 31,821 residents (2020 Census); attraction weights sum to 16,583 primary workplace jobs (2023 LODES WAC). Counts follow the saved discrete rule: a source block contributes when its official internal point lies inside the model zone. Values are not whole-tract totals, density, or household counts. Different years and concepts must not be treated as synchronous population and employment observations. The numbered zones match the full OD matrix. Roads are only context. Census/LODES source counts; © OpenStreetMap contributors for the road context.

[SVG](<../assets/city-alignment-r3/berkeley/population_jobs.svg>) · [PNG](<../assets/city-alignment-r3/berkeley/population_jobs.png>) · [PDF](<../assets/city-alignment-r3/berkeley/population_jobs.pdf>) · [Plot data](<../assets/city-alignment-r3/berkeley/population_jobs.plot_data.json>) · [Source record](<../assets/city-alignment-r3/berkeley/population_jobs.source.json>)

<a id="berkeley-transit-evidence"></a>

## Scheduled transit: geography, availability and time

The source geography, direct-OD availability and selected-day service profile are distinct evidence. The following figures use scheduled AC Transit source derivatives and the accepted direct-option table; they do not use private GPS traces or mix the retained BART date into the mode-choice input.

<a id="figure-r3-transit-network"></a>

[![Scheduled transit geography and model availability](<../assets/city-alignment-r3/berkeley/transit_network.svg>)](<../assets/city-alignment-r3/berkeley/transit_network.svg>)

**Scheduled transit geography and model availability.** Left: all 168 AC Transit stops in the frozen source envelope, shown at their supplied coordinates against the 2,150-link model road context. Equal symbol size identifies stops, not ridership or frequency. Right: the saved direct-service option exists on 38 of 156 directed interzonal pairs in the complete 13-zone system. A stop on the map does not by itself guarantee an OD alternative, legal crossing, accessible entrance, or transfer. BART from a different service date and documentary Bear Transit maps are excluded from this selected-day calculation. Service date 5 October 2026; feed S1000256; no observed-operations inference. © OpenStreetMap contributors for road context; AC Transit scheduled source.

[SVG](<../assets/city-alignment-r3/berkeley/transit_network.svg>) · [PNG](<../assets/city-alignment-r3/berkeley/transit_network.png>) · [PDF](<../assets/city-alignment-r3/berkeley/transit_network.pdf>) · [Plot data](<../assets/city-alignment-r3/berkeley/transit_network.plot_data.json>) · [Source record](<../assets/city-alignment-r3/berkeley/transit_network.source.json>)

<a id="figure-r3-transit-service"></a>

[![Scheduled service and direct-option time components](<../assets/city-alignment-r3/berkeley/transit_service.svg>)](<../assets/city-alignment-r3/berkeley/transit_service.svg>)

**Scheduled service and direct-option time components.** Panel a counts all 14,649 scheduled stop-departure events in the frozen source-envelope table for 5 October 2026, preserving timetable hours beyond midnight. These are stop events: one trip contributes at multiple stops, so this is not a count of vehicles, unique trips or observed service. The highlighted 08:00–09:00 interval matches the engineering demand hour. Panel b shows every one of the 38 saved direct OD options, with deterministic sorted offsets to reveal overlapping values. In-vehicle and access times are saved option values; the identical ten-minute waits are an explicit assumption. Transfers are zero and fare is USD 2.50 in this case. No ridership or wait-time observations are inferred.

[SVG](<../assets/city-alignment-r3/berkeley/transit_service.svg>) · [PNG](<../assets/city-alignment-r3/berkeley/transit_service.png>) · [PDF](<../assets/city-alignment-r3/berkeley/transit_service.pdf>) · [Plot data](<../assets/city-alignment-r3/berkeley/transit_service.plot_data.json>) · [Source record](<../assets/city-alignment-r3/berkeley/transit_service.source.json>)

<a id="generation"></a>

## 01 / Trip generation

<a id="coverage-row-06"></a>

Generation assumes 0.65 one-way HBW movements per resident per day and allocates 35% to the morning hour. The resulting total is 7,239.2775 person trips. A 35% capture fraction and a 6% intrazonal fraction of captured demand determine the boundary ledger; none of these shares is locally estimated.

The ledger records 4,705.530375 external or uncaptured trips, 152.0248275 intrazonal trips and 2,381.7222975 internal interzonal trips. Resident counts determine production mass and primary jobs determine attraction weights. Their aggregate equality is imposed by balancing, so similar regional totals do not imply identical zonal patterns. The generation figure keeps all thirteen zones.

<a id="figure-f10-generation"></a>

##### Trip generation

[![Trip generation](<../assets/figure-contract-r11/figures/berkeley/f10_generation.svg>)](<../assets/figure-contract-r11/figures/berkeley/f10_generation.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

Saved productions and job-weighted attractions for all 13 model zones. Population and jobs use different source years (2020 and 2023). The captured interzonal total is 2,381.7222975 person trips in 08:00–09:00; 4,705.530375 external/uncaptured and 152.0248275 intrazonal person trips remain separate. This bounded engineering scenario is not locally calibrated. Single-pass engineering scenario; no local empirical calibration.

</details>

[PNG](<../assets/figure-contract-r11/figures/berkeley/f10_generation.png>) · [SVG](<../assets/figure-contract-r11/figures/berkeley/f10_generation.svg>) · [PDF](<../assets/figure-contract-r11/figures/berkeley/f10_generation.pdf>) · [Source record](<../assets/figure-contract-r11/figures/berkeley/f10_generation.source.json>)

<a id="distribution"></a>

## 02 / Trip distribution

<a id="coverage-row-07"></a>

Unlike the road-impedance choices in some other cities, this case uses directed shortest times on the screened walking graph for its gravity distribution. The exponential deterrence parameter is 0.04 per minute. IPF respects the feasible pair set; disconnected pairs remain zero instead of receiving an artificially large finite travel time.

Seven balancing iterations produce a maximum margin residual of 2.14531534×10⁻⁵ persons. The 2,381.7222975 PA persons are converted once using a 90% forward and 10% reverse share. There are ninety positive directed person OD pairs. The matrix panel retains thirteen-zone context; its companion distribution panel concerns positive OD quantities. Neither panel is a top-ten substitute for the full demand.

<a id="figure-f11-distribution"></a>

##### Trip distribution

[![Trip distribution](<../assets/figure-contract-r11/figures/berkeley/f11_distribution.svg>)](<../assets/figure-contract-r11/figures/berkeley/f11_distribution.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

The complete saved 13 × 13 one-hour HBW matrix has 90 positive directed OD pairs. Pale cells are structural zero interzonal demand; the gray diagonal excludes intrazonal demand. All 156 interzonal impedance records are available. The full positive-OD histogram retains 12 bins; saved PA and OD totals agree at 2,381.7222975 person trips/h, with seven IPF iterations and a maximum margin residual of 2.1453153408401704e-05. Single-pass engineering scenario; no local empirical calibration.

</details>

[PNG](<../assets/figure-contract-r11/figures/berkeley/f11_distribution.png>) · [SVG](<../assets/figure-contract-r11/figures/berkeley/f11_distribution.svg>) · [PDF](<../assets/figure-contract-r11/figures/berkeley/f11_distribution.pdf>) · [Source record](<../assets/figure-contract-r11/figures/berkeley/f11_distribution.source.json>)

<a id="mode"></a>

## 03 / Mode choice

<a id="coverage-row-04"></a>

<a id="coverage-row-08"></a>

Available drive, direct AC Transit and walk alternatives compete through OD-specific generalized costs. Driving adds an assumed five minutes of access and a USD 2 charge. Walking uses the screened OSM graph. The AC Transit input is a direct scheduled option from feed S1000256 for 5 October 2026, with stop-to-walk-network snapping limited to 120 m.

Transit is available on 38 directed zone pairs. Its assumed wait is ten minutes and its fare USD 2.50. The scenario values time at USD 20/hour and uses logit sensitivity 0.07 per generalized minute with zero alternative constants. BART's retained sample belongs to 24 August 2026, so it is not mixed into the selected-day calculation. Bear Transit PDF maps remain documentary context, and transfers are not modeled.

Every internal interzonal person has at least one implemented alternative. The aggregate choices are approximately 1,238.96 drive, 169.67 transit and 973.09 walk persons, totaling 2,381.72. Drive persons are divided once by occupancy 1.30 and multiplied by PCE 1.0, yielding 953.049842714 PCE. Seventy-two OD pairs have positive vehicle demand, even though ninety have positive person demand. This difference follows from availability and mode choice; it is not unexplained OD removal.

<a id="figure-f12-mode-choice"></a>

##### Mode choice

[![Mode choice](<../assets/figure-contract-r11/figures/berkeley/f12_mode_choice.svg>)](<../assets/figure-contract-r11/figures/berkeley/f12_mode_choice.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

Saved OD-specific logit probabilities apply only over available alternatives. Modeled one-hour demand is 1,238.9647955 drive, 169.6685413 direct-transit and 973.0889606 walk person trips; shares and trip-weighted generalized costs are copied from frozen plotdata. Direct AC Transit is available for a subset of zone pairs. All costs and behavior remain engineering assumptions, without a local behavioral fit. Single-pass engineering scenario; no local empirical calibration.

</details>

[PNG](<../assets/figure-contract-r11/figures/berkeley/f12_mode_choice.png>) · [SVG](<../assets/figure-contract-r11/figures/berkeley/f12_mode_choice.svg>) · [PDF](<../assets/figure-contract-r11/figures/berkeley/f12_mode_choice.pdf>) · [Source record](<../assets/figure-contract-r11/figures/berkeley/f12_mode_choice.source.json>)

<a id="assignment"></a>

## 04 / Physical-link assignment

<a id="coverage-row-09"></a>

The road solver receives all seventy-two positive vehicle OD pairs unchanged. BPR uses α=0.15 and β=4; absent capacity observations are replaced by declared per-lane proxies, with source speeds where available and facility-class values elsewhere. The model represents static travel-time response, not finite-hour queue storage.

The initial all-or-nothing flow has relative gap 1.6551133727449009×10⁻¹⁵ against tolerance 10⁻⁴. No subsequent FW update is required. The saved objective is 2,746.094414979 PCE-min, and 670 of 2,150 retained roads carry positive modeled flow. Maximum v/c is about 0.434. A valid initial stop at these assumed costs is not evidence about measured Berkeley congestion.

F13 preserves the distinct flow, v/c, travel-time and initial-check information of the original multipanel result. Its width must be handled by layout rather than flattening the map. The R3 geographic companion joins the same saved flows to frozen GMNS geometry. Restriction-based link removals can lengthen modeled routes, so neither map should be treated as precise legal navigation.

<a id="figure-r3-static-source-margins"></a>

[![Demand ledger and vehicle assignment margins](<../assets/city-alignment-r3/berkeley/static_source_margins.svg>)](<../assets/city-alignment-r3/berkeley/static_source_margins.svg>)

**Demand ledger and vehicle assignment margins.** The first panel retains the complete one-hour person ledger: 4,705.530375 external/uncaptured, 152.0248275 intrazonal and 2,381.7222975 internal-interzonal person trips. The second panel aggregates all 72 positive vehicle OD pairs by all 13 possible origin/destination zones. Each side sums to 953.049842713612 PCE/h, after the single person-to-vehicle conversion; absence of positive vehicle demand remains zero. This separates the boundary/capture ledger from the actual assignment margins. The assumptions are 0.65 HBW movements/resident/day, 35% morning allocation, 35% capture, 6% intrazonal share, and 1.30 occupancy; these are engineering values, not locally fitted rates.

[SVG](<../assets/city-alignment-r3/berkeley/static_source_margins.svg>) · [PNG](<../assets/city-alignment-r3/berkeley/static_source_margins.png>) · [PDF](<../assets/city-alignment-r3/berkeley/static_source_margins.pdf>) · [Plot data](<../assets/city-alignment-r3/berkeley/static_source_margins.plot_data.json>) · [Source record](<../assets/city-alignment-r3/berkeley/static_source_margins.source.json>)

<a id="figure-r3-static-endpoints"></a>

[![Where the vehicle demand enters and leaves](<../assets/city-alignment-r3/berkeley/static_endpoints.svg>)](<../assets/city-alignment-r3/berkeley/static_endpoints.svg>)

**Where the vehicle demand enters and leaves.** Origin and destination margins from all 72 positive vehicle OD rows are placed at the actual saved auto access nodes. Both panels share the same color and symbol-area scale, with area proportional to PCE/h and zero-demand symbols omitted. All 13 polygons and all 2,150 retained road links remain as context; zone numbering is consistent with the OD matrix. Source and sink are engineering access nodes, not surveyed parcel entrances or observed trip endpoints. Each side sums to 953.049842713612 PCE/h. © OpenStreetMap contributors; Census-derived zone geography.

[SVG](<../assets/city-alignment-r3/berkeley/static_endpoints.svg>) · [PNG](<../assets/city-alignment-r3/berkeley/static_endpoints.png>) · [PDF](<../assets/city-alignment-r3/berkeley/static_endpoints.pdf>) · [Plot data](<../assets/city-alignment-r3/berkeley/static_endpoints.plot_data.json>) · [Source record](<../assets/city-alignment-r3/berkeley/static_endpoints.source.json>)

<a id="figure-f13-assignment"></a>

<a id="figure-r9-fw-map-distribution"></a>

[![Frank–Wolfe physical loading and distribution](<../assets/plot-semantics-r9/berkeley/fw-map-distribution.svg>)](<../assets/plot-semantics-r9/berkeley/fw-map-distribution.svg>)

**Frank–Wolfe physical loading and distribution.** Frank–Wolfe own saved physical-link vector on the unchanged Berkeley S72 model: 72 positive vehicle OD pairs, 953.049842713612 PCE in one declared hour, 360 frozen candidate paths and all 2,150 directed physical road links. The left map retains every original road vertex and full gray graph; the right 22-bin histogram includes all 2,150 links, including 1,480 exact zeros. Both figures use the same square-root colour scale in PCE/hour and constant overlay width. FW and finite have exactly equal saved link vectors in this particular instance; each figure reads its own saved column. FW stopped at its initial check with zero updates; these maps are endpoint loading, not evidence of iterative progress. Values with absolute magnitude at most 1e-12 PCE/h are hidden only from coloured map overlays, not removed from the histogram or plot data.

[SVG](<../assets/plot-semantics-r9/berkeley/fw-map-distribution.svg>) · [PNG](<../assets/plot-semantics-r9/berkeley/fw-map-distribution.png>) · [PDF](<../assets/plot-semantics-r9/berkeley/fw-map-distribution.pdf>) · [Plot data](<../assets/plot-semantics-r9/berkeley/fw-map-distribution.plot_data.json>) · [Caption](<../assets/plot-semantics-r9/berkeley/fw-map-distribution.caption.md>) · [Source record](<../assets/plot-semantics-r9/berkeley/fw-map-distribution.source.json>) · [Same figure on homepage](<../index.html?atlas-view=full#atlas-r9-berkeley-fw-map-distribution>)

<a id="figure-r9-finite-map-distribution"></a>

[![Finite-path reference and physical support](<../assets/plot-semantics-r9/berkeley/finite-map-distribution.svg>)](<../assets/plot-semantics-r9/berkeley/finite-map-distribution.svg>)

**Finite-path reference and physical support.** Finite-path own saved physical-link vector on the unchanged Berkeley S72 model: 72 positive vehicle OD pairs, 953.049842713612 PCE in one declared hour, 360 frozen candidate paths and all 2,150 directed physical road links. The left map retains every original road vertex and full gray graph; the right 22-bin histogram includes all 2,150 links, including 1,480 exact zeros. Both figures use the same square-root colour scale in PCE/hour and constant overlay width. FW and finite have exactly equal saved link vectors in this particular instance; each figure reads its own saved column. FW stopped at its initial check with zero updates; these maps are endpoint loading, not evidence of iterative progress. Values with absolute magnitude at most 1e-12 PCE/h are hidden only from coloured map overlays, not removed from the histogram or plot data.

[SVG](<../assets/plot-semantics-r9/berkeley/finite-map-distribution.svg>) · [PNG](<../assets/plot-semantics-r9/berkeley/finite-map-distribution.png>) · [PDF](<../assets/plot-semantics-r9/berkeley/finite-map-distribution.pdf>) · [Plot data](<../assets/plot-semantics-r9/berkeley/finite-map-distribution.plot_data.json>) · [Caption](<../assets/plot-semantics-r9/berkeley/finite-map-distribution.caption.md>) · [Source record](<../assets/plot-semantics-r9/berkeley/finite-map-distribution.source.json>) · [Same figure on homepage](<../index.html?atlas-view=full#atlas-r9-berkeley-finite-map-distribution>)

<a id="figure-r9-native-map-differences"></a>

[![Native L3 physical flows against S72 FW](<../assets/plot-semantics-r9/berkeley/native-map-differences.svg>)](<../assets/plot-semantics-r9/berkeley/native-map-differences.svg>)

**Native L3 physical flows against S72 FW.** The upper row shows Berkeley S72 Native rank 26 own saved explicit physical-link flow, then signed rank 26−FW and rank 52−FW differences; the bottom 22-bin histogram contains all 2,150 rank 26 physical links, including zero/near-zero values. The absolute map uses the same square-root colour scale as the companion FW and finite cards. The signed maps use one shared symmetric zero-centred scale in PCE/hour; no micro-unit magnification changes the quantity. Maximum absolute differences are 2.645862196e-08 PCE/h and1.5853784987e-06 PCE/h. These tiny numerical differences are not traffic improvement. Raw saved numerical values, including rank 52 negatives down to −4.380487468063516e-47 PCE/h, remain in plot data; |flow|≤1e-12 only suppresses coloured map overlays, with the full geographic base retained. The Native vectors are actual saved explicit v, not substituted FW/finite vectors. This bounded low-congestion same-instance agreement establishes neither a difficult congestion test nor speedup. © OpenStreetMap contributors, ODbL 1.0; modelled one-hour engineering scenario, not observations.

[SVG](<../assets/plot-semantics-r9/berkeley/native-map-differences.svg>) · [PNG](<../assets/plot-semantics-r9/berkeley/native-map-differences.png>) · [PDF](<../assets/plot-semantics-r9/berkeley/native-map-differences.pdf>) · [Plot data](<../assets/plot-semantics-r9/berkeley/native-map-differences.plot_data.json>) · [Caption](<../assets/plot-semantics-r9/berkeley/native-map-differences.caption.md>) · [Source record](<../assets/plot-semantics-r9/berkeley/native-map-differences.source.json>) · [Same figure on homepage](<../index.html?atlas-view=full#atlas-r9-berkeley-native-map-differences>)

<details markdown="1">
<summary>Original stopping, scalar comparison and flow diagnostics</summary>

<a id="figure-r3-fw-saved-check"></a>

##### Frank–Wolfe: the saved initial check

<a id="table-r11-berkeley-fw-initial-check"></a>

[![Frank–Wolfe: the saved initial check](<../assets/figure-contract-r12/figures/berkeley/berkeley-fw-initial-check.svg>)](<../assets/figure-contract-r12/figures/berkeley/berkeley-fw-initial-check.svg>)

Only the actual saved iteration 0 is shown: objective 2746.09441497946 PCE·min/h and relative gap 9.93068023646942e-16, against the unchanged 1e-05 stopping gate. There were zero updates. Each panel contains a single numerical point; no missing trajectory or second state is inferred. The companion physical-flow map reads this method’s own saved vector. The saved signed gap numerator is 2.7284841053187847e−12 PCE·min/h; the independent endpoint evaluator remains a separate numerical evaluation.

[SVG](<../assets/figure-contract-r12/figures/berkeley/berkeley-fw-initial-check.svg>) · [PNG](<../assets/figure-contract-r12/figures/berkeley/berkeley-fw-initial-check.png>) · [PDF](<../assets/figure-contract-r12/figures/berkeley/berkeley-fw-initial-check.pdf>) · [Source data](<../assets/figure-contract-r12/figures/berkeley/berkeley-fw-initial-check.source.json>)

</details>

<a id="results"></a>

## Saved results and assignment checks

<a id="coverage-row-10"></a>

R3 saved-result replay passed. Fresh-solve acceptance and independent full-graph checks are supported by the earlier receiver evidence for the unchanged frozen inputs; R3 does not claim that it repeated that fresh solve. The recorded maximum node-conservation residual is 8.53×10⁻¹⁴ PCE.

The verifier reconstructs OD demand and link loading from saved paths, checks generation and distribution margins, recomputes probability and person/vehicle conversion, and checks BPR costs and the full-graph gap. Six negative fixtures reject missing upstream or current results, changed OD or probability values, and nonexistent zone or link references. Receipt hashes connect the stages without substituting a historical smoke output.

<a id="berkeley-static-algorithms"></a>

## Static S72: finite paths and Native L3

This extension starts from the accepted one-hour Berkeley vehicle OD, retaining all 72 positive vehicle pairs and 953.049842714 PCE on the same 2,150-link conservative R2 graph. It does not regenerate demand or insert the local turn sidecar. The frozen K=5 pool has 360 legal paths (72 designated major, 288 minor). All comparisons below use the original BPR integral; the finite pool and complete solver graph have separate checks.

<dl class="accepted-method-notes"><dt>Fresh Frank–Wolfe</dt><dd>Initial check; 0 updates · 2746.0944149794555 · 4.96534e-16</dd><dt id="berkeley-finite-reference">Finite-path SLSQP</dt><dd>360 paths; 1 iteration · 2746.0944149794555 · 4.96534e-16</dd><dt id="berkeley-native-l3">Native L3 rank 26</dt><dd>3 outer steps · 2746.094414979262 · −7.00113e-14</dd><dt>Native L3 rank 52</dt><dd>3 outer steps · 2746.0944154632957 · 1.76101e-10</dd></dl>

The independent checker rebuilt ordered path incidence, OD mass and physical-link flow, recomputed the BPR integral, then ran shortest paths on the entire declared graph at final costs. All four pass the original 1e-5 full-graph gap and original-coordinate feasibility gates. The tiny negative signed rank-26 gap is numerical evidence, not a negative traffic cost. The input-only initial vector built the Native basis; neither Native rank used the finite optimum as its basis.

Native ranks 26 and 52 have 98 and 124 path-representation coordinates (72 major plus rank), versus 360 finite-pool path coordinates. Each Native model also includes 2,150 explicit link variables, for raw totals of 2,248 and 2,274. This is a representation result, not a total-variable or speed advantage. Reconstructed minor-path mass is only about 1.23e-7 and 1.01e-5 PCE, so this input shows little diversion sensitivity.

<a id="figure-s01-geography-pool"></a>

<a id="table-r11-berkeley-s72-pool"></a>

<a id="figure-private-berkeley-native-history"></a>

##### Native L3: all 3 saved outer iterations

[![Native L3: all 3 saved outer iterations](<../assets/private-native-history-20261008/berkeley/native-complete-history.svg>)](<../assets/private-native-history-20261008/berkeley/native-complete-history.svg>)

All 3 saved outer checks are plotted for each Native rank on the same frozen S72 instance (72 positive OD, 953.049842714 PCE/h). Each marker is an actual saved check at outer 1–3; the connecting segments do not add intermediate observations. Rank 26 uses open circles and rank 52 filled squares; near-coincident lines are both retained. Panels separate checked BPR/Beckmann objective, signed full-graph relative gap, maximum original-OD residual, and physical-flow reconstruction residual. The horizontal FW value is an independent same-instance endpoint, not an additional Native iteration. Early checked objectives lie below that endpoint while OD conservation has not yet reached its frozen gate; these are not feasible upper bounds or better traffic solutions. Signed negative gaps remain negative and are not interpreted as superior optimality. The gap axis is symmetric-log with a linear interval of ±10⁻¹²; OD/reconstruction axes are logarithmic in their original PCE/h units. The original gap bounds ±10⁻⁵, OD absolute gate 10⁻⁶ PCE/h, and reconstruction gate 10⁻⁷ PCE/h are unchanged. Both runs reach their original acceptance checks at outer 3; other relative-OD/nonnegativity gates remain in the source records. Berkeley objective values are taken from the per-outer checker; the independently evaluated public endpoint differs by at most 2.73×10⁻¹² PCE·min/h and is not substituted into this history. These early states belong to the ultimately accepted run; no separate failed trial is added. Endpoint comparison and method-specific physical-flow maps remain separate evidence. Private local preview of complete saved numerical history: public release currently covers endpoints, not these per-iteration values. Engineering scenario, not observed traffic or measured policy effect.

[SVG](<../assets/private-native-history-20261008/berkeley/native-complete-history.svg>) · [PNG](<../assets/private-native-history-20261008/berkeley/native-complete-history.png>) · [PDF](<../assets/private-native-history-20261008/berkeley/native-complete-history.pdf>) · [Plot data](<../assets/private-native-history-20261008/berkeley/native-complete-history.plot.json>) · [Source and access](<../assets/private-native-history-20261008/berkeley/native-complete-history.source.json>) · [Caption](<../assets/private-native-history-20261008/berkeley/native-complete-history.caption.md>)

<details markdown="1">
<summary>Original stopping, scalar comparison and flow diagnostics</summary>

<a id="figure-s02-same-instance-methods"></a>

##### Accepted static endpoints and feasibility

<a id="table-r11-berkeley-s72-endpoints"></a>

[![Accepted static endpoints and feasibility](<../assets/figure-contract-r12/figures/berkeley/berkeley-s72-endpoints.svg>)](<../assets/figure-contract-r12/figures/berkeley/berkeley-s72-endpoints.svg>)

Independent accepted endpoints on S72 · 72 OD · 953.049842714 PCE/h. Panels show signed objective difference from the same-instance FW endpoint (2746.09441497946 PCE·min/h), signed full-graph relative gap, and maximum original-OD and link-reconstruction residuals. Categories are method identities, not iteration numbers; no connecting trajectory is drawn. The signed symmetric-log axes retain exact zeros and negative roundoff, with a linear interval of ±1e−15 in each panel’s stated unit. The accompanying method-specific physical-flow figures remain the map evidence; scalar agreement does not imply identical flow.

[SVG](<../assets/figure-contract-r12/figures/berkeley/berkeley-s72-endpoints.svg>) · [PNG](<../assets/figure-contract-r12/figures/berkeley/berkeley-s72-endpoints.png>) · [PDF](<../assets/figure-contract-r12/figures/berkeley/berkeley-s72-endpoints.pdf>) · [Source data](<../assets/figure-contract-r12/figures/berkeley/berkeley-s72-endpoints.source.json>)

</details>

<details markdown="1">
<summary>Original stopping, scalar comparison and flow diagnostics</summary>

<a id="figure-s03-native-flows"></a>

</details>

<a id="parity-berkeley-construction"></a>

## Time-expanded network and path examples

<a id="figure-parity-berkeley-time-layers"></a>

##### Time-expanded network in layers

[![Time-expanded network in layers](<../assets/template-parity-20261008/construction/berkeley/time-layers.svg>)](<../assets/template-parity-20261008/construction/berkeley/time-layers.svg>)

Berkeley: selected time layers 5–10 use 30 seconds per time step. Every arrow is an actual saved arc; only node-time states occurring as saved endpoints are drawn. The first three movements of the saved positive T02 column (7.5 PCE) are highlighted. The complete column has 89 movements; this local display is not its entire route. State aliases: A = 2838, B = 2837, C = 2836, D = 1535. Pale arrows show other saved arcs in this local slice. Time planes and horizontal placement are schematic; this is neither a full graph nor observed traffic. No independent turn connector exists in this T4 representation. Blue dashed waiting arcs are available local context; the selected three movements contain no wait. Elapsed rounded model time and fixed arc cost are different quantities.

[Complete evidence · same figure](<#figure-parity-berkeley-time-layers>) · [SVG](<../assets/template-parity-20261008/construction/berkeley/time-layers.svg>) · [PNG](<../assets/template-parity-20261008/construction/berkeley/time-layers.png>) · [PDF](<../assets/template-parity-20261008/construction/berkeley/time-layers.pdf>) · [Plot data](<../assets/template-parity-20261008/construction/berkeley/time-layers.plot.json>) · [Source record](<../assets/template-parity-20261008/construction/berkeley/time-layers.source.json>) · [Caption](<../assets/template-parity-20261008/construction/berkeley/time-layers.caption.md>)

<a id="figure-parity-berkeley-local-details"></a>

##### Local construction details

[![Local construction details](<../assets/template-parity-20261008/construction/berkeley/local-details.svg>)](<../assets/template-parity-20261008/construction/berkeley/local-details.svg>)

Berkeley: the physical road chain is mapped to physical-node states and then to exact time-indexed arcs in the saved construction slice. Panel c contains all 35 retained arcs, with exact endpoint times; strong teal/blue highlights the same continuous chain used in the companion layered figure. The first three movements of the saved positive T02 column (7.5 PCE) are highlighted. The complete column has 89 movements; this local display is not its entire route. All layout coordinates are schematic. Source/sink terminal bookkeeping is outside this excerpt and must not be read as road travel or waiting. No independent turn connector exists in this T4 representation. Blue dashed waiting arcs are available local context; the selected three movements contain no wait. Elapsed rounded model time and fixed arc cost are different quantities.

[Complete evidence · same figure](<#figure-parity-berkeley-local-details>) · [SVG](<../assets/template-parity-20261008/construction/berkeley/local-details.svg>) · [PNG](<../assets/template-parity-20261008/construction/berkeley/local-details.png>) · [PDF](<../assets/template-parity-20261008/construction/berkeley/local-details.pdf>) · [Plot data](<../assets/template-parity-20261008/construction/berkeley/local-details.plot.json>) · [Source record](<../assets/template-parity-20261008/construction/berkeley/local-details.source.json>) · [Caption](<../assets/template-parity-20261008/construction/berkeley/local-details.caption.md>)

<a id="berkeley-time-construction"></a>

## Finite-time construction: layers and an actual computed route

The local layered view and the complete computed route answer different questions. The first shows actual node-time incidence; the second follows the saved positive column and separates fixed objective cost, rounded model time and terminal bookkeeping time.

<a id="figure-r3-time-layers"></a>

[![Road states across selected time layers](<../assets/city-alignment-r3/berkeley/time_layers.svg>)](<../assets/city-alignment-r3/berkeley/time_layers.svg>)

**Road states across selected time layers.** A declared local fragment of the accepted T4 graph shows seven real road nodes across time indices 5–11 (08:02:30–08:05:30). Every drawn edge is a saved dynamic arc with both endpoints in this node/time window. Teal marks the first six actual movement arcs of positive computed column 1; blue marks waiting arcs, and gray marks other retained movements. Both panels display the same 57-arc fragment, first in actual local geographic coordinates and then as a discrete node/time graph. Only node-time states present as endpoints in the saved arc subset are marked. This is a construction view, not a whole-city dynamic simulation or the complete 89-movement route. Arc costs and rounded 30-second time increments are different quantities; the following route figure retains that distinction.

[SVG](<../assets/city-alignment-r3/berkeley/time_layers.svg>) · [PNG](<../assets/city-alignment-r3/berkeley/time_layers.png>) · [PDF](<../assets/city-alignment-r3/berkeley/time_layers.pdf>) · [Plot data](<../assets/city-alignment-r3/berkeley/time_layers.plot_data.json>) · [Source record](<../assets/city-alignment-r3/berkeley/time_layers.source.json>)

<a id="figure-t01-computed-column"></a>

##### Computed column: route, cost and model time

[![Computed column: route, cost and model time](<../assets/figure-contract-r11/figures/berkeley/t01_computed_column.svg>)](<../assets/figure-contract-r11/figures/berkeley/t01_computed_column.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

Saved positive T02 column 1 carries 7.5 PCE. Panel a joins all 89 saved, ordered movement link IDs to the real physical-road geometry; consecutive endpoints and time steps are verified. The map shows the route with nearby model roads as context, using longitude/latitude and a latitude-adjusted aspect ratio. Panel b retains all 91 supplied distance/time vertices for these movements; positions use the rounded 30-second state clock, not an observed trajectory. The path accumulates 2.6023 km, departs at 08:02:30 and physically arrives at 08:47:00 (44.5 elapsed minutes). Panel c separates the unchanged 3.90345 fixed objective minutes from that rounded elapsed time and the H165 sink at 09:22:30 (80 minutes after departure). The terminal sink is accounting, not extra physical travel. This is a computed route, not a schematic full time-layer network.

</details>

[PNG](<../assets/figure-contract-r11/figures/berkeley/t01_computed_column.png>) · [SVG](<../assets/figure-contract-r11/figures/berkeley/t01_computed_column.svg>) · [PDF](<../assets/figure-contract-r11/figures/berkeley/t01_computed_column.pdf>) · [Source record](<../assets/figure-contract-r11/figures/berkeley/t01_computed_column.source.json>)

<a id="berkeley-finite-algorithms"></a>

## Finite-time T4: LP, CG, LR and ADMM

T4 is a separate bounded linear experiment on the same physical road graph. Four input-hash-selected OD pairs contribute only their assumed first five-minute departure pulse, 10.439304601026278 PCE at 08:02:30. The other hourly OD demand is outside T4. The 30-second step and H165 horizon yield 92,578 time states and 250,886 arcs after exact reachability pruning. Each road arc keeps original free-flow minutes as objective cost while its state-clock duration rounds up to 30-second steps; the H165 zero-cost sink is accounting after physical destination arrival.

The fixed-cost shared-capacity model has no queue storage, spillback, dynamic network loading feedback or observed second-by-second departure profile. T4 PCE·min objectives cannot be compared as the same mathematical objective with the nonlinear one-hour S72 Beckmann integral.

<dl class="accepted-method-notes"><dt id="berkeley-t-lp">Full arc-flow HiGHS LP</dt><dd>43.66742440800644 primal; 43.66742440800643 dual · Full admissible-arc, balance, capacity and reduced-cost check; gap ≈7.1e-15. The accepted process solved the unchanged LP.</dd><dt id="berkeley-t-cg">Two-phase column generation</dt><dd>43.667424408006426 primal and dual · Phase-I artificial flow zero; ten columns; exact full-DAG pricing, minimum reduced cost −4.44e-16 min.</dd><dt id="berkeley-t-lr">Lagrangian relaxation</dt><dd>Extended diagnostic (300 iterations): valid lower 43.667424408006; feasible upper 43.667424408006 · Certified gap 0%; first 1% certificate at iteration 10. Original accepted run stops at 10; extension keeps its model and gate.</dd><dt id="berkeley-t-admm">ADMM, post-diagnostic C2a</dt><dd>Its own x objective 43.66974694298355; same-T4 LP 43.66742440800644 · Relative objective difference 5.31869009587e-5 (0.00531869%), below unchanged 1e-4 gate.</dd></dl>

<a id="berkeley-time-semantics"></a>

The saved 7.5-PCE T02 column leaves at the assumed 08:02:30, uses 89 road movement arcs, incurs 3.90345 fixed objective minutes and reaches its physical destination at 08:47 by the rounded state clock (44.5 elapsed minutes). Its later 09:22:30 H165 sink is bookkeeping, not travel or a measured delay.

<a id="figure-lp-cg-lr-physical-flow"></a>

##### LP, CG and recovered LR physical flow

[![LP, CG and recovered LR physical flow](<../assets/figure-contract-r11/figures/berkeley/lp_cg_lr_physical_flow.svg>)](<../assets/figure-contract-r11/figures/berkeley/lp_cg_lr_physical_flow.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

The 300-iteration same-rule cold-start LR diagnostic retains the original T4 model and the official 1% gate, first met at iteration 10. The map uses LR’s own selected feasible recovery (saved recovery iteration 10), joined by physical-link ID to all 2,150 road geometries. The scatter includes every road ID and compares the unchanged independent LP and CG projections with the selected LR projection. Maximum absolute differences from LP are 0 PCE for CG and 0 PCE for LR. The stored aggregate physical projections coincide exactly in this instance. Colors and widths use PowerNorm(0.5), retaining the absolute scale used by the existing ADMM–LP map unless new values require a larger maximum. The 137 physical links with no admitted T4 movement arc remain distinct as dotted background links. Flows are PCE over the bounded departure instance, not PCE/hour. The original accepted 10-iteration evidence is retained separately. No LP flow was substituted for the LR recovery. © OpenStreetMap contributors, ODbL 1.0. Independent diagnostic audit passed. The extended saved record passed all 23 original formal-entry checks.

</details>

[PNG](<../assets/figure-contract-r11/figures/berkeley/lp_cg_lr_physical_flow.png>) · [SVG](<../assets/figure-contract-r11/figures/berkeley/lp_cg_lr_physical_flow.svg>) · [PDF](<../assets/figure-contract-r11/figures/berkeley/lp_cg_lr_physical_flow.pdf>) · [Source record](<../assets/figure-contract-r11/figures/berkeley/lp_cg_lr_physical_flow.source.json>)

<a id="berkeley-r3-cg"></a>

### Column generation: feasibility, objective and closure

<a id="figure-r3-cg-phase-one"></a>

[![Column generation: Phase I feasibility](<../assets/city-alignment-r3/berkeley/cg_phase_one.svg>)](<../assets/city-alignment-r3/berkeley/cg_phase_one.svg>)

**Column generation: Phase I feasibility.** All five saved Phase-I records are retained. Total artificial flow stays at 1.2003774460867707 PCE through rounds 0–3 and reaches zero at round 4; the available pool grows from four to eight columns. The frozen artificial-flow tolerance is 1e−8 PCE. The saved records contain aggregate artificial flow, not its OD-by-round allocation, so the second panel shows real saved pool growth rather than an invented per-OD artificial-flow heatmap. Phase-I reduced costs are dimensionless and appear in the separate closure figure.

[SVG](<../assets/city-alignment-r3/berkeley/cg_phase_one.svg>) · [PNG](<../assets/city-alignment-r3/berkeley/cg_phase_one.png>) · [PDF](<../assets/city-alignment-r3/berkeley/cg_phase_one.pdf>) · [Plot data](<../assets/city-alignment-r3/berkeley/cg_phase_one.plot_data.json>) · [Source record](<../assets/city-alignment-r3/berkeley/cg_phase_one.source.json>)

<a id="figure-r3-cg-phase-two"></a>

[![Phase II objective](<../assets/city-alignment-r3/berkeley/cg_phase_two.svg>)](<../assets/city-alignment-r3/berkeley/cg_phase_two.svg>)

**Phase II objective. **Boston-matched raw-objective post-step view of all three saved Phase-II states (rounds 0–2), not a normalized or logarithmic error plot. The hollow initial circle, filled decrease circle and hollow unchanged square classify adjacent recorded objective values; the Berkeley trace does not store Boston commit-classification labels, so no degenerate-commit claim is made. Objective decreases from 46.81717881521473 to 43.667424408006426 PCE·min at round 1 and is unchanged at round 2. The same-T4 independent LP is 43.66742440800644 PCE·min. Round 1 agrees with LP within floating-point precision but still has minimum full-graph reduced cost −0.06717 min; pricing closes only at round 2 (−4.44e−16 min). Only saved states are drawn. This is the four-OD finite T4 instance, not S72.

[SVG](<../assets/city-alignment-r3/berkeley/cg_phase_two.svg>) · [PNG](<../assets/city-alignment-r3/berkeley/cg_phase_two.png>) · [PDF](<../assets/city-alignment-r3/berkeley/cg_phase_two.pdf>) · [Plot data](<../assets/city-alignment-r3/berkeley/cg_phase_two.plot_data.json>) · [Source record](<../assets/city-alignment-r3/berkeley/cg_phase_two.source.json>)

<a id="figure-r3-cg-pricing-closure"></a>

[![Complete-graph pricing closure](<../assets/city-alignment-r3/berkeley/cg_pricing_closure.svg>)](<../assets/city-alignment-r3/berkeley/cg_pricing_closure.svg>)

**Complete-graph pricing closure.** Every saved minimum complete-graph reduced cost is shown on its own phase axis. Phase I uses dimensionless costs; Phase II uses minutes. The frozen negative-reduced-cost tolerances are 1e−8 and 1e−7 minutes respectively. Zero is drawn as a reference; the distinct tolerances are annotated because they are indistinguishable from zero at this scale. Final Phase-I pricing is zero; final Phase-II pricing is −4.4408920985e−16 minutes, with ten available columns. No exhaustion label or extra curve is inferred from these saved fields.

[SVG](<../assets/city-alignment-r3/berkeley/cg_pricing_closure.svg>) · [PNG](<../assets/city-alignment-r3/berkeley/cg_pricing_closure.png>) · [PDF](<../assets/city-alignment-r3/berkeley/cg_pricing_closure.pdf>) · [Plot data](<../assets/city-alignment-r3/berkeley/cg_pricing_closure.plot_data.json>) · [Source record](<../assets/city-alignment-r3/berkeley/cg_pricing_closure.source.json>)

<details markdown="1">
<summary>Retained combined CG figure and original complete source links</summary>

<a id="figure-t02-cg-phases"></a>

</details>

<a id="berkeley-r3-lr"></a>

### Lagrangian relaxation: bounds, prices and recovery

<a id="berkeley-lr-current-status-20261007"></a>

### Current LR reception · S0 batch\_v001

S0 received the existing formal PASS for the separate 300-iteration cold-start LR diagnostic and reused its duplicate package identity. All 23 original formal-entry checks passed. The original ten-iteration run remains the accepted 1% result; LR300 is not checkpoint continuation and is not a new result from uploading the same package again.

The best lower first improves at iteration 19 and reaches 43.66742440800643 PCE·min at iteration 256. At iteration 300 the current dual is 43.66228345703368 PCE·min, distinct from the running best. The recovered upper is 43.667424408006426 PCE·min; a reported zero gap means floating-point closure. The existing figure order and original LR10 evidence remain intact.

© OpenStreetMap contributors; road-derived data are subject to [ODbL 1.0](<https://www.openstreetmap.org/copyright>). Berkeley T4 is the frozen 30-second/H165 engineering instance. ADMM170 is a post-diagnostic C2a result; LR300 is a separate post-certificate cold-start diagnostic and does not replace accepted LR10. These results are not observed traffic, DNL/DUE or local demand calibration.

[Released LR300 plot data](<../assets/algorithm-transfer-r8/berkeley/LR_EXTENDED_PLOT_DATA.csv>) · [Current acceptance and release summary](<../assets/algorithm-transfer-r8/CURRENT_STATUS.json>) · [Source and scope notice](<../assets/algorithm-transfer-r8/NOTICE.md>).

<a id="lr-extended-diagnostic-r6"></a>

The same-rule cold-start LR record contains 300 actual iterations. Its unchanged 1% certificate is first met at iteration 10; final best lower and feasible upper agree at approximately 43.66742440801 PCE·min. The 23 original formal-entry checks pass. The separate original ten-iteration run retains its own stopping decision.

<a id="figure-r3-lr-bounds"></a>

##### Lagrangian bounds and certified gap

[![Lagrangian bounds and certified gap](<../assets/figure-contract-r11/figures/berkeley/lr_bounds.svg>)](<../assets/figure-contract-r11/figures/berkeley/lr_bounds.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

The original accepted run remains separately preserved at iteration 10. This view uses 300 actual saved records from run BERKELEY\_T4\_LR\_EXTENDED\_DIAGNOSTIC\_R1, through iteration 300. The extended trace is a diagnostic experiment and does not retroactively change the original stopping decision. Independent diagnostic audit passed. The 300-round saved record passed all 23 original formal-entry checks. The formal 1% certificate is first met at saved iteration 10; later rounds, when present, are shaded as post-gate diagnostics. Teal denotes the saved best dual lower bound and blue the separately recovered feasible upper. The right panel shows 100 times the saved dimensionless certificate on a linear percentage axis, against the unchanged gate. Missing upper/gap records remain unplotted. Final best lower is 43.66742440800643 PCE·min; best upper is 43.66742440800643 PCE·min and gap is 0%. The highest saved best bound first appears at iteration 256. The final current relaxed dual is separately 43.66228345703368 PCE·min; it is not substituted for the running best bound. The certificate is max(0, (U−L)/max(1,|U|)). The final signed U−L is -7.10543e-15 PCE·min. A saved zero gap here denotes numerical agreement at floating-point precision, not an algebraic proof of exact equality. The independent LP scalar remains in metadata and is not substituted for an LR upper bound. No smoothing, invented points, or optimizer calls are used by this renderer.

</details>

[PNG](<../assets/figure-contract-r11/figures/berkeley/lr_bounds.png>) · [SVG](<../assets/figure-contract-r11/figures/berkeley/lr_bounds.svg>) · [PDF](<../assets/figure-contract-r11/figures/berkeley/lr_bounds.pdf>) · [Source record](<../assets/figure-contract-r11/figures/berkeley/lr_bounds.source.json>)

<a id="figure-r3-lr-prices"></a>

##### Lagrangian prices and relaxed capacity violations

[![Lagrangian prices and relaxed capacity violations](<../assets/figure-contract-r11/figures/berkeley/lr_prices.svg>)](<../assets/figure-contract-r11/figures/berkeley/lr_prices.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

The original accepted run remains separately preserved at iteration 10. This view uses 300 actual saved records from run BERKELEY\_T4\_LR\_EXTENDED\_DIAGNOSTIC\_R1, through iteration 300. The extended trace is a diagnostic experiment and does not retroactively change the original stopping decision. Independent diagnostic audit passed. The 300-round saved record passed all 23 original formal-entry checks. The formal 1% certificate is first met at saved iteration 10; later rounds, when present, are shaded as post-gate diagnostics. Every saved current-iterate maximum capacity multiplier, strictly positive multiplier count and maximum relaxed capacity excess is shown. Multiplier units are minutes, from a PCE·min objective divided by a PCE capacity; relaxed excess is PCE. These current-iterate summaries are distinct from the saved best-dual multiplier state. Relaxed excess is not the feasibility residual of separately recovered primal flow. A closed best-bound certificate does not imply that subsequent current multipliers stop changing; the full diagnostic retains those changes. No smoothing or per-arc history is inferred.

</details>

[PNG](<../assets/figure-contract-r11/figures/berkeley/lr_prices.png>) · [SVG](<../assets/figure-contract-r11/figures/berkeley/lr_prices.svg>) · [PDF](<../assets/figure-contract-r11/figures/berkeley/lr_prices.pdf>) · [Source record](<../assets/figure-contract-r11/figures/berkeley/lr_prices.source.json>)

<a id="figure-r3-lr-recovery"></a>

##### Path-pool growth and separate primal recovery

[![Path-pool growth and separate primal recovery](<../assets/figure-contract-r11/figures/berkeley/lr_recovery.svg>)](<../assets/figure-contract-r11/figures/berkeley/lr_recovery.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

The original accepted run remains separately preserved at iteration 10. This view uses 300 actual saved records from run BERKELEY\_T4\_LR\_EXTENDED\_DIAGNOSTIC\_R1, through iteration 300. The extended trace is a diagnostic experiment and does not retroactively change the original stopping decision. Independent diagnostic audit passed. The 300-round saved record passed all 23 original formal-entry checks. The formal 1% certificate is first met at saved iteration 10; later rounds, when present, are shaded as post-gate diagnostics. Panel a retains all 300 saved path-pool sizes; panel b shows exactly 31 actual recovery calls (30 feasible, 1 infeasible). Filled circles are feasible calls and open squares are infeasible calls. Null objectives remain missing and are never zero-imputed. Pool growth is not a sequence of feasible upper bounds. The call records and own recovered physical flow retain their separate source identities.

</details>

[PNG](<../assets/figure-contract-r11/figures/berkeley/lr_recovery.png>) · [SVG](<../assets/figure-contract-r11/figures/berkeley/lr_recovery.svg>) · [PDF](<../assets/figure-contract-r11/figures/berkeley/lr_recovery.pdf>) · [Source record](<../assets/figure-contract-r11/figures/berkeley/lr_recovery.source.json>)

<details markdown="1">
<summary>Retained combined LR figure and original complete source links</summary>

<a id="figure-t03-lr-bounds-physical"></a>

</details>

<a id="berkeley-admm-accuracy-r3"></a>

### Accepted T4 ADMM accuracy continuation

**S0 received · batch\_v001, 7 October 2026.** ADMM C2a outer170 reuses the prior formal PASS. The three released original figures are linked beneath the existing V displays; the established figure order is preserved.

The finite Berkeley T4 experiment uses four first-bin OD pulses on the frozen 92,578-state, 250,886-arc, 30-second/H165 time-expanded graph. Its demand, arc order, fixed cost, shared capacities and input-derived rho (0.131931364425587) are the same as in the corrected R1 and C1 records. The static four-stage model and the finite T4 LP, CG and LR certificates were not recomputed. Earlier C1 repaired a genuine local quadratic-subproblem defect by exact source-to-sink DAG variable elimination, local node numbering and a potential gauge. That repair took the same T4 from zero outer iterations to a saved 38-outer state, where all internal R3 gates passed but the ADMM objective was still 4.3879087e-4 relatively above the same-instance LP, missing the original 1e-4 gate.

#### Why the continuation was needed

The C1 driver stopped when its own primal, dual and capacity criteria were met. The external same-instance LP comparison was an independent acceptance gate and was not part of that internal stop. Repeating the old driver would therefore stop at outer 38 again. This R3 continuation preserved the exact C1 local QP, projection, scaled-dual update and fixed rho, and tightened only internal absolute/relative residual tolerances to 1e-6/1e-5 for C2a. It restored the complete C1 post-dual-update state, recomputed the next local target from z−w and began at outer 39. A separate small-fixture execution showed exact equality of 5 uninterrupted outer updates and 2 saved plus 3 resumed updates in all six state arrays, objective and residuals. This is a seen-case, post-diagnostic accuracy experiment; the staged stop rule was frozen before the new T4 run.

The 50, 100 and 150 outer checkpoints were registered as observations, not as a search for the most favorable objective. At outer 100, the relative LP difference was 1.11306e-4 and the new dual and capacity gates were still unmet. At outer 150, the saved objective difference had fallen below 1e-4, but the new dual stop remained unmet. The solver continued to its own complete C2a endpoint at outer **170**; no C2b extension or rho change was needed. The C1 history 1–38 is retained byte-for-byte in the parent bundle and shown as an explicit boundary in the figures. Later history consists only of actual saved updates.

#### Original-coordinate acceptance

The selected C2a x flow has objective **43.669746942984 PCE·min**, compared with the independently accepted same-graph LP optimum **43.667424408006 PCE·min**. The absolute relative difference is **5.3186900959e-05**, below the frozen **1e-4** gate. The independent evaluator recomputed every commodity's source and sink balance, nonnegativity, forbidden-connector flow, shared capacity, x−z primal residual, rho-weighted dual residual, capacity projection, scaled-dual update, full original-coordinate local KKT, objective and physical-link back projection. All 18 original gates in the saved check are true; this is a result from ADMM's own x, not a substitution from LP, CG or LR.

The new internal stop is separate: primal **0.00092678345** versus **0.0017258811**, dual **0.00082762004** versus **0.0010021451**. The process-tree RSS peak was **574,197,760 bytes**, below the inherited **687,203,942-byte** ceiling, and the stage completed within its newly registered 7,200-second continuation budget. C2a used 132 new outer iterations after the 38 C1 updates, so its cumulative endpoint remains inside the original 300-outer count. The larger wall allowance is disclosed as new R3 computation effort, not retroactively attributed to C1.

#### Reproduction and interpretation

The frozen C2 driver, T4 CSVs, original C1 parent state, C2a endpoint and full saved iteration rows are in the Private Full archive. The formal read-only replay entry rehashes inputs, validates saved state and stage identity, and launches an optimizer-free original-coordinate check outside the protected extraction. Fresh shortest-path initialization confirmation is **PASS**; formal corrupted-copy tests are **12/12** rejected. The fixed graph, costs and H165 sink bookkeeping do not constitute a measured queue, dynamic network loading or a Berkeley travel-time calibration. S0 batch\_v001 has now received the accepted identity and released this prose, the three original summary figure families and the separate LR300 plot data with their notices. This website integration performs no new scientific computation.

© OpenStreetMap contributors; road-derived data are subject to [ODbL 1.0](<https://www.openstreetmap.org/copyright>). Berkeley T4 is the frozen 30-second/H165 engineering instance. ADMM170 is a post-diagnostic C2a result; LR300 is a separate post-certificate cold-start diagnostic and does not replace accepted LR10. These results are not observed traffic, DNL/DUE or local demand calibration. [Current acceptance and release summary](<../assets/algorithm-transfer-r8/CURRENT_STATUS.json>) · [Source and scope notice](<../assets/algorithm-transfer-r8/NOTICE.md>).

<a id="figure-admm-convergence"></a>

##### ADMM convergence and objective agreement

[![ADMM convergence and objective agreement](<../assets/figure-contract-r11/figures/berkeley/admm_convergence.svg>)](<../assets/figure-contract-r11/figures/berkeley/admm_convergence.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

Accepted Berkeley T4 ADMM saved history, all 170 recorded outer iterations. The four panels follow the current Boston/Hong Kong diagnostic objects: original-unit balance and capacity feasibility, primal consensus, dual update, and log10 absolute objective error against the independent LP on the same T4 graph. Balance/capacity and primal residuals are PCE. The dual residual is rho times the consensus change and is in minutes: rho has min/PCE units. The dotted scientific feasibility gate is 1e-5 PCE; the internal thresholds are the recorded values. The objective gate line is the unchanged 1e-4 relative criterion expressed on the absolute-error axis. Only exact-zero feasibility values use a display value of 1e-16 PCE; every positive value, including smaller positives, is retained unchanged. The vertical separator is after C1 outer 38; C2a contributes 132 further updates under its disclosed new wall budget. The actual trace ends at 170; the registered 300-outer ceiling is not an extrapolated trace. Final own-x objective is 43.66974694298355 PCE·min against LP 43.66742440800644 PCE·min, absolute difference 0.00232253497711 PCE·min and relative difference 0.00531869%. Objective agreement is separate from physical-link flow agreement. No smoothing, interpolation or solver call.

</details>

[PNG](<../assets/figure-contract-r11/figures/berkeley/admm_convergence.png>) · [SVG](<../assets/figure-contract-r11/figures/berkeley/admm_convergence.svg>) · [PDF](<../assets/figure-contract-r11/figures/berkeley/admm_convergence.pdf>) · [Source record](<../assets/figure-contract-r11/figures/berkeley/admm_convergence.source.json>)

<a id="parity-berkeley-finite"></a>

## Optimization on the time-expanded network

<a id="figure-parity-berkeley-admm-final-conservation"></a>

##### Commodity conservation at the final state

[![Commodity conservation at the final state](<../assets/template-parity-20261008/admm/berkeley/admm-final-conservation.svg>)](<../assets/template-parity-20261008/admm/berkeley/admm-final-conservation.svg>)

Final saved ADMM own-x state at completed outer 170. Reconstruct outflow minus inflow minus commodity supply in the original units and exact saved arc order, with the loader's lexical node order. The heatmap selects the 35 nodes with the largest maximum absolute residual across all four commodities; ties retain lexical node order. All 92,578 nodes were included in this selection. The complete per-commodity maximum residuals and worst-node IDs reproduce the saved independent check exactly; overall maximum is 3.74010259123591e-12 PCE against the unchanged 1e−5 PCE gate. Colors show log10(max(|residual|,1e−15 PCE)/(1 PCE)); sub-floor values and exact zeros share the floor color, with their raw signed and absolute values preserved in plot data. This is a final spatial conservation diagnostic, not an iteration-history heatmap. It complements the existing 170-record convergence and ADMM-versus-LP physical-flow figures; it does not replace the latter or imply link-flow equality. Private local derivative of the accepted saved result; no new public asset release or optimizer run is claimed. Engineering scenario, not observed traffic.

[Complete evidence · same figure](<#figure-parity-berkeley-admm-final-conservation>) · [SVG](<../assets/template-parity-20261008/admm/berkeley/admm-final-conservation.svg>) · [PNG](<../assets/template-parity-20261008/admm/berkeley/admm-final-conservation.png>) · [PDF](<../assets/template-parity-20261008/admm/berkeley/admm-final-conservation.pdf>) · [Plot data](<../assets/template-parity-20261008/admm/berkeley/admm-final-conservation.plot.json>) · [Source record](<../assets/template-parity-20261008/admm/berkeley/admm-final-conservation.source.json>) · [Caption](<../assets/template-parity-20261008/admm/berkeley/admm-final-conservation.caption.md>)

<a id="figure-admm-physical-flow-comparison"></a>

##### ADMM and LP physical-link flow

[![ADMM and LP physical-link flow](<../assets/figure-contract-r11/figures/berkeley/admm_physical_flow_comparison.svg>)](<../assets/figure-contract-r11/figures/berkeley/admm_physical_flow_comparison.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

Saved Berkeley T4 physical-link projections for four assumed first-bin OD pulses (10.439304601 PCE), using the accepted ADMM own x at completed outer 170 and an independently solved same-graph LP. Panels a–b share a PowerNorm(0.5) absolute color scale. Panel c uses a separate symmetric ADMM-minus-LP scale; panel d contains all 2,150matched physical IDs and an identity line. The maximum physical-flow difference is 0.990967760238112 PCE, despite a relative objective difference of 0.00531869%. The objective gate does not establish link-flow equality. All 2,150 original road geometries are retained with longitude/latitude aspect correction. The 137 links without a movement arc in the bounded T4 graph remain zero and are shown dotted; missing sparse LP entries are zero-filled by physical ID. Flows are PCE over this bounded departure instance, not hourly counts or observed traffic. No optimizer was rerun. © OpenStreetMap contributors, ODbL 1.0.

</details>

[PNG](<../assets/figure-contract-r11/figures/berkeley/admm_physical_flow_comparison.png>) · [SVG](<../assets/figure-contract-r11/figures/berkeley/admm_physical_flow_comparison.svg>) · [PDF](<../assets/figure-contract-r11/figures/berkeley/admm_physical_flow_comparison.pdf>) · [Source record](<../assets/figure-contract-r11/figures/berkeley/admm_physical_flow_comparison.source.json>)

The movement-only backprojection uses the accepted ADMM `x` and the independent LP on the same finite graph. All 2,150 physical links are retained in the comparison, including 137 with no movement arc in T4. The maximum absolute ADMM–LP physical-link difference is 0.990967760238112 PCE; agreement in objective value does not establish a unique or identical link-flow vector.

<a id="figure-accuracy-objective-vs-lp"></a>

<a id="figure-accuracy-primal-dual-internal-gates"></a>

<a id="figure-accuracy-local-and-capacity-gates"></a>

<a id="plotting-methods"></a>

## How to read the method figures

The updated views use the same compact layout, blue–teal palette and DejaVu Serif font as the current Boston and Hong Kong atlas. They are derived from saved Berkeley data. S72 remains a one-hour nonlinear static instance; T4 remains a separate four-OD fixed-cost finite graph.

| Evidence | Displayed quantities | Interpretation |
| --- | --- | --- |
| Static / Native | Physical-link flow, distribution, signed objective/gap diagnostics and representation dimensions | Use actual method-specific saved vectors. Small deviations do not establish speedup or a hard compression benchmark. |
| CG / LR | Artificial flow, objective, reduced cost, valid lower/feasible upper bounds, gap, pool and saved recovery | Keep phases and units separate. Missing primal results stay missing; no iteration is invented. |
| ADMM residuals | Balance/capacity and primal in PCE; dual in min | Each residual has its own scientific or recorded stopping threshold. Rho has min/PCE units. |
| ADMM objective | Absolute error in PCE·min and dimensionless LP-relative error | Hong Kong uses log10 absolute error; Boston retains raw objective versus LP. Berkeley provides the absolute and relative views explicitly. Its gate remains 1e-4. |
| ADMM / LP maps | Movement-only physical-link PCE, signed difference and all-link scatter | Shared absolute scales and a separate symmetric difference scale; objective agreement is not flow identity. |

Original accepted figures and captions remain accessible below each updated figure. [Plotting functions, metrics and source-data guide](<../assets/berkeley-atlas-r2/PLOTTING_GUIDE.md>).

The additional source, population, transit, demand-margin, endpoint, time-layer and separated CG/LR figures use the same selected functions and styles. [Detailed figure-to-function and metric guide](<../assets/city-alignment-r3/berkeley/PLOTTING_GUIDE.md>) · [Python renderer](<../assets/city-alignment-r3/berkeley/render_figures.py>) · [Input identities](<../assets/city-alignment-r3/berkeley/data/INPUT_PROVENANCE.json>).

<a id="reproduction"></a>

## Reproduction and input identity

<a id="lr-r6-reproduction"></a>

R6 LR update: the separately audited 300-iteration diagnostic, full saved history, multiplier timing and all five figure families are provided in the [extended-diagnostic plotting guide](<../assets/berkeley-lr-r6/PLOTTING_GUIDE.md>). The original R1 commands below reproduce the historical accepted 10-iteration LR result. R6 plotting uses the included saved data and does not launch a new solver. Current formal validation now passes all 23 checks; [Formal 23-check report](<../assets/current-status-20261007/DIAGNOSTIC_FORMAL_EVALUATION.json>) · [Current LR handoff](<../assets/current-status-20261007/HANDOFF_TO_MAINLINE.json>). Frozen R6 receipts and plotting inputs retain their at-export identity.

<a id="coverage-row-19"></a>

The page is a local reading candidate. Exact model inputs, checkpoints, solver source, private observation records and full compute archives are not distributed by this website. Scientific acceptance and permission to redistribute an asset are separate decisions; new algorithm assets remain subject to their item-level S0 release record.

### Package identity and saved replay

Use the corrected R1 package for S72 and T4 LP/CG/LR, and the separate accuracy R3 package for the currently accepted ADMM endpoint. These archives have different historical ADMM outcomes. Extract each archive separately; preserve its directory structure and manifest. For a read-only replay, set `PYTHONDONTWRITEBYTECODE=1` and direct output to a new directory outside the extraction.

| Archive and working directory | Saved replay | Expected result |
| --- | --- | --- |
| `MCL_Berkeley_Algorithm_R1_Corrected_R2_Private_Full.zip`; its `berkeley_algorithm_transfer_r1` directory | `python verify_saved.py --output-root <external-replay-directory>` | Accepted S72 FW/finite/Native and T4 LP/CG/LR saved checks. Current ADMM reproduction uses the separate accepted R3 package. |
| `MCL_Berkeley_ADMM_Accuracy_R3_Private_Full.zip`; extraction root | `python verify_saved.py --output-root <external-replay-directory>` | Exit 0 and `PASS_ACCEPTED`; `ACCEPTED_BOUNDED_BERKELEY_T4_ADMM_POST_DIAGNOSTIC`, cumulative outer 170, relative LP difference approximately `5.31869009587e-5`. |

The corrected R1 ZIP SHA-256 is `709a8490078a12c54958bc43d1824e72bca1cf4869522d9ffd242fb2ec6703a3`; the accuracy R3 ZIP SHA-256 is `eb67e2626cc5617d44d651f0645586d73c3ea0fdc0eec1ce16aae7d24b0eefa5`. Both saved replay entries call no optimizer. The R3 receiver performed two formal saved replays and 12/12 corrupted-copy formal-entry rejection tests. Original four-stage saved replay and its six negative fixtures are a separate evidence set.

<details markdown="1">
<summary>Fresh S72 and T4 LP/CG/LR solves</summary>

The following are documented commands, not work performed by the website. Run only in a separate writable copy of corrected R1. Bind `$basePython` to the compatible existing controller Python, `$guard` to the original `mcl_batch_guard.py`, and `$locks` to the existing shared coordination directory. The wrapper acquires that original heavy lock and refuses an existing output path. Do not create a second lock pool. Run one selected method at a time.

```powershell
& $basePython .\rebuild_selected.py S_FW --output .\fresh_S_FW --guard $guard --lock-root $locks
& $basePython .\rebuild_selected.py S_finite --output .\fresh_S_finite --guard $guard --lock-root $locks
& $basePython .\rebuild_selected.py S_Native26 --output .\fresh_S_Native26 --guard $guard --lock-root $locks --worker-python $nativePython --ipopt $ipopt
& $basePython .\rebuild_selected.py S_Native52 --output .\fresh_S_Native52 --guard $guard --lock-root $locks --worker-python $nativePython --ipopt $ipopt
& $basePython .\rebuild_selected.py T_LP --output .\fresh_T_LP --guard $guard --lock-root $locks
& $basePython .\rebuild_selected.py T_CG --output .\fresh_T_CG --guard $guard --lock-root $locks
& $basePython .\rebuild_selected.py T_LR --output .\fresh_T_LR --guard $guard --lock-root $locks
```

Native additionally requires the existing compatible worker Python and IPOPT binary through $nativePython and $ipopt . The packaged S\_paths , S\_basis26 and S\_basis52 selections reproduce the K=5 pool and input-only bases. Selected Native solves use the frozen corresponding pool/basis; neither basis is built from the finite optimum. Use the dedicated R3 continuation commands for the current ADMM result.

LR's solve-dual result is a lower-bound record. Recover its own-column feasible primal and evaluate the certificate as separate steps, under the same original shared heavy guard:

```powershell
& $basePython $guard --root $locks --kind heavy --timeout 7200 --wait 600 --cwd (Get-Location).Path -- $basePython .\source\time\lr\cli.py recover-primal --case .\runs\T_case\case_manifest.json --run .\fresh_T_LR --output .\fresh_T_LR_recovery
& $basePython $guard --root $locks --kind heavy --timeout 7200 --wait 600 --cwd (Get-Location).Path -- $basePython .\source\time\lr\cli.py evaluate --case .\runs\T_case\case_manifest.json --run .\fresh_T_LR --plan .\T_LR_PLAN.json --recovery .\fresh_T_LR_recovery --output .\fresh_T_LR_evaluation.json
```

<dl class="accepted-method-notes"><dt>S72 FW / finite reference</dt><dd>Objective 2746.0944149794555 PCE·min; signed complete-graph gap approximately 4.96534e-16 ; FW 0 updates, finite 1 iteration.</dd><dt>S72 Native rank 26 / 52</dt><dd>Objectives 2746.094414979262 / 2746.0944154632957 PCE·min; original-coordinate feasibility and original 1e-5 complete-graph gap gate; 3 outer steps each.</dd><dt>T4 LP</dt><dd>Primal 43.66742440800644 , dual 43.66742440800643 PCE·min; complete admissible-arc and primal-dual checks.</dd><dt>T4 CG</dt><dd>43.667424408006426 PCE·min; zero Phase-I artificial flow, 10 columns, complete-DAG pricing and minimum reduced cost approximately −4.44e-16 min.</dd><dt>T4 LR</dt><dd>Original accepted 10-iteration replay: Valid lower 43.58459836422644 , feasible upper 43.667424408006426 PCE·min; certified relative gap approximately 0.1896747% , below 1% . The separate R6 extended diagnostic is reported above; this replay retains the original stopping rule.</dd></dl>

Compare new results with the frozen input signatures and independent original-coordinate checks, not only a solver's success message. Different methods can return different arc-by-arc primal flows on this linear problem while satisfying the same optimality or accuracy certificate. Do not overwrite packaged accepted results to make a new run resemble the reference.

</details>

<details markdown="1">
<summary>Fresh ADMM R3 continuation and cold confirmation</summary>

In a separate writable copy of the accuracy R3 extraction, C2a resumes the immutable `input/C1_checkpoint` after outer 38. It uses the frozen plan's absolute/relative internal tolerances `1e-6/1e-5`, fixed input-derived rho `0.13193136442558714`, cumulative ceiling 300, new solver wall budget 7,200 s and process-tree RSS ceiling 687,203,942 bytes. The saved outer monitor used 7,300 s to cover process overhead. The objective gate remains `1e-4`. C2b was a registered contingency and is not the selected accepted result.

With the same `$basePython`, original `$guard` and `$locks`, the following preserves the saved monitor interfaces and places new reports in fresh paths:

```powershell
$r3 = (Get-Location).Path
& $basePython $guard --root $locks --kind heavy --timeout 7400 --wait 600 --cwd $r3 -- $basePython .\resource_monitor.py --report .\fresh_monitor\resource.json --stdout .\fresh_monitor\stdout.log --stderr .\fresh_monitor\stderr.log --memory-bytes 687203942 --wall-seconds 7300 -- $basePython .\source\admm_solver_accuracy.py --stage C2a --parent .\input\C1_checkpoint --output .\fresh_C2a
& $basePython .\check_stage_endpoint.py --checkpoint .\fresh_C2a\final_checkpoint --resource .\fresh_monitor\resource.json --output-root .\fresh_C2a_check
```

For a fresh initialization confirmation, use the same guard and resource monitor with new report filenames, replacing the inner solver command with `python confirm_cold.py --stage C2a --output .\fresh_cold_confirmation`. Its initialization uses input-cost shortest paths, not LP flow. `check_cold_confirmation.py` is a saved-package checker with fixed packaged paths; it does not accept a fresh-output path argument. The receiver compared the provider's six saved arrays (`x`, `z`, `w`, `z_previous`, `local_q`, `potential`) rather than rerunning that cold solve in the browser.

The accepted reference endpoint is cumulative outer 170 (38 parent + 132 new), own-x objective `43.66974694298355` PCE·min and relative LP difference `5.31869009587e-5 = 0.00531869%`. The objective threshold was first reached at outer 110; that did not mean every stop condition passed at 110. Outer 170 is the actual terminal state. Require `NUMERIC_PASS_WITH_NEW_INTERNAL_STOP`, every original scientific/resource gate, and both new internal stop checks in the fresh endpoint report. `check_stage_endpoint.py` returning zero means it read a valid saved endpoint; by itself it does not mean that endpoint passed all gates. Fresh run timings are new measurements, not the provider's recorded timings.

</details>

### Recorded environments and public boundary

The original four-stage producer used Python 3.11.4, NetworkX 3.1, Shapely 2.1.2, pyproj 3.7.2, Matplotlib 3.7.1 and NumPy 1.24.3. S72 Native used a separate Python 3.9.25 worker with NumPy 2.0.2, SciPy 1.13.1, Pyomo 6.9.5 and IPOPT/MUMPS; its controller and LP/CG/LR used the existing base environment described in corrected R1 `REPRODUCE.md`. Accuracy R3's `DEPENDENCY_LOCK.json` records Python 3.11.4, NumPy 1.24.3, SciPy 1.10.1, Matplotlib 3.7.1 and psutil 5.9.0, with BLAS thread counts set to one. The archives do not bundle interpreters or IPOPT and do not establish platform-independent binary reproduction.

This website exposes only the current local reading assets and item-level permitted public material. It does not include private Full ZIPs, checkpoints, precise GPS traces, camera pins, evidence SQLite databases or a runnable public compute package. S72's one-hour nonlinear assignment and T4's four-OD first-pulse fixed-cost experiment retain their separate scope and result meaning.

<a id="local-turn-candidate"></a>

## Local turn engineering candidate

This bounded sidecar is separate from the accepted R2 conservative deletion and from the saved OD/FW result.

<a id="r11-evidence-berkeley-turn-candidate"></a>

##### Local turn engineering candidate

[![Local turn engineering candidate](<../assets/figure-contract-r11/figures/berkeley/berkeley-turn_candidate.svg>)](<../assets/figure-contract-r11/figures/berkeley/berkeley-turn_candidate.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

Local turn engineering candidate Shattuck / Center. 6 prohibited of 16 directed pairs at one frozen via node. Engineering variant; no assignment or policy effect.

</details>

[PNG](<../assets/figure-contract-r11/figures/berkeley/berkeley-turn_candidate.png>) · [SVG](<../assets/figure-contract-r11/figures/berkeley/berkeley-turn_candidate.svg>) · [PDF](<../assets/figure-contract-r11/figures/berkeley/berkeley-turn_candidate.pdf>) · [Source record](<../assets/figure-contract-r11/figures/berkeley/berkeley-turn_candidate.source.json>)

[SVG](<../assets/six-city-evidence-r2/berkeley/turn_candidate.svg>) · [PNG](<../assets/six-city-evidence-r2/berkeley/turn_candidate.png>)

<a id="berkeley-observations"></a>

## Observation and mapping evidence

The separate Berkeley evidence R2 processed a rights-recorded 2009 Commons view and two public OSM GPS clips (22 and 21 points) with frozen-window map matching. Their matched directed connections were 12/12 and 11/11; 95th-percentile lateral distances were 10.60 m and 6.70 m. Modes and surveyed route truth remain unknown. Precise traces, camera pins, original photos, S2 trace cells and the offline inspector stay in the private evidence package; they are not reproduced here.

On the frozen source-to-R2 bridge, 134 of 170 source auto links matched exact R2 physical identities and 36 remained removed by the accepted policy or access screen. The E v001 S2 12/14/16 mapping covered 62 typed objects; local read-only multi-table query and parent/direct roll-up/weight checks passed in the private evidence record. These object and trajectory joins help locate model objects; they do not calibrate OD, road capacity, traffic counts or observed travel time. The public Shattuck/Center figure above is the S0 v002 released local engineering candidate, not a replacement solver graph.

The private evidence Full includes the frozen SQLite database and SQL. Its read-only E v001 query entry is `python mcl_e_core.py query --input-root . --output-root queries/output --database private/evidence.sqlite --sql queries/object_to_model.sql --output-name object_to_model.csv`; the accepted run returned 21 object-to-model rows with a receipt. The turn query returned 16 rows. These counts and the saved-state verification are reproducible from the private package, while the database and precise trace rows remain outside this page.

<a id="berkeley-figure-availability"></a>

## Figure coverage and evidence still needed

The nine-stage sequence now follows the Boston/Hong Kong reading order. A missing experiment or unsaved internal history is identified below; neither is filled with a substitute city or a fabricated curve. Existing full source tables, accepted endpoints and earlier composite figures remain available.

| Unavailable comparison or panel | Current evidence and reason | Input needed |
| --- | --- | --- |
| A multi-iteration Frank–Wolfe convergence trajectory | Accepted S72 history contains one initial check and zero updates. A truthful one-point objective/gap figure is supplied; there is no saved multi-step curve to redraw. | A separately accepted run that actually performs FW updates and preserves its full history. The current accepted one-point run must not be relabelled as a convergence series. |
| Same-S72 Algorithm B result and convergence figure | The accepted Berkeley transfer contains FW, finite full-path SLSQP and Native L3 rank-26/rank-52 results. It does not contain an accepted Algorithm B result for this exact identity. | An accepted Algorithm B run on the identical S72 graph, demand, cost and gate, with endpoint flow, iteration history and independent full-graph checks. |
| CG Phase-I per-OD artificial-flow heatmap | All five saved aggregate artificial-flow values and per-OD reduced-cost values exist, but the per-OD artificial-flow trajectory is not saved. Reduced costs are not artificial flows. | Per-OD artificial variables from every saved Phase-I restricted-master solve, bound to round and OD IDs. |
| Saved mode-response sensitivity experiment | The accepted four-stage case saves one OD-specific mode-choice scenario, with drive/direct-transit/walk probabilities and totals. No accepted fare, time, or parameter perturbation sweep is present. | A declared and verified sensitivity sweep with the varied variable, unchanged controls and all saved alternative probabilities, or approval for a separate new experiment. |
| Public observed GPS trace and photo panels comparable to the Boston/Hong Kong observation cards | Berkeley has separately documented private photo/GPS/map-matching evidence, but the current page explicitly excludes precise traces, camera pins, original photos, S2 trace cells and the private inspector. The new transit figures therefore use scheduled public-source derivatives only. | A reviewed release-safe observation derivative with explicit rights, privacy treatment and trace-to-model provenance. No additional private/raw material is needed for the scheduled-service figures already supplied. |
| Finite full-path optimizer iteration curve | Finite SLSQP has an accepted endpoint and one reported iteration, but no per-iteration objective/feasibility series is retained. Its full endpoint comparison and flow evidence are preserved. | Saved callback history from that exact finite-path run, or a separately accepted instrumented run; a terminal result is insufficient to reconstruct the internal trajectory. |

<a id="limitations"></a>

## Model limits and observations

<a id="coverage-row-05"></a>

<a id="coverage-row-11"></a>

<a id="coverage-row-12"></a>

<a id="coverage-row-13"></a>

<a id="coverage-row-14"></a>

<a id="coverage-row-15"></a>

<a id="coverage-row-16"></a>

<a id="coverage-row-17"></a>

<a id="coverage-row-18"></a>

This is a conservative restriction-screened engineering network, not a complete turn-aware representation. It lacks locally estimated HBW and utility parameters, observed OD, independent link counts and certified pedestrian access. The 2020 population, 2023 workplace data and 2026 network do not constitute one common-year observation.

The transit option covers a direct-bus simplification only. Transfers, BART and Bear Transit are excluded from the selected-day choice model, and a successful stop snap is not proof of safe access. Walk and transit person demand is retained but is not capacity assigned.

The public assignment sidecar uses a portable evidence identifier for the node source. The original absolute-path sidecar remains protected as evidence, with its hash preserved. No frozen configuration or numerical result is edited to achieve that presentation cleanup. Source attribution follows Census TIGERweb, LEHD LODES, AC Transit feed documentation and © OpenStreetMap contributors under ODbL.

The preflight network drawing documents an earlier data layer, not an additional assignment experiment. University entrances, pedestrian legal movements and traffic counts were not field audited for this case. Consequently the presentation separates numerical verification from observed transport performance.

<a id="sources"></a>

## Sources and display provenance

- [US Census TIGERweb block layer](<https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Tracts_Blocks/MapServer/2>)
- [Census LEHD LODES8 WAC](<https://lehd.ces.census.gov/data/lodes/LODES8/ca/wac/>)
- [OpenStreetMap contributors, ODbL](<https://www.openstreetmap.org/copyright>)
- [Mobility Database AC Transit feed catalog](<https://mobilitydatabase.org/feeds/gtfs/mdb-2455>)

[Return to the city atlas](<../index.html#berkeley>) · [Back to top](<#document-top>)
