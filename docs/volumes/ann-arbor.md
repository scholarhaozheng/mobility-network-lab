<a id="document-top"></a>

MOBILITY COMPUTATION LAB / STATIC CITY RECORD

# Ann Arbor

A 25-zone central Ann Arbor model linking household-based demand, OD distribution, three-mode choice and static road assignment for the weekday morning hour.

<dl class="ann-metrics"><div><dt>Demand area</dt><dd>19.633 km²</dd></div><div><dt>Model zones</dt><dd>25</dd></div><div><dt>Directed OD pairs</dt><dd>600</dd></div><div><dt>Weekday HBW period</dt><dd>08:00–09:00</dd></div></dl>

The figures show saved method results, physical-flow maps and original-unit diagnostics. Drawing these figures invokes no optimizer.

<a id="choicefw-current-status"></a>

## Current choice-to-assignment status

The new timetable-based choice and road-assignment scenario has passed S0 scientific intake. Its new figures, detailed model data, and long prose await confirmed public rights for University of Michigan timetable derivatives. Keep the existing Ann Arbor static entry and approved assets unchanged. The old S600 and S72 are comparison baselines.

Original R2, later frozen S600 and independent S72 results below retain their own identities. Native600 and finite time-expanded T1/T4 remain incomplete.

[S0 approved status](<../assets/choicefw-scope-20261008/ann-arbor/CHOICE_FW_PUBLIC_STATUS.md>) · [Release and SHA](<../assets/choicefw-scope-20261008/CONSUMPTION.json>)

<a id="choicefw-private-v002"></a>

## New timetable choice → actual FW assignment

**Private local review · S0 scientific intake passed · public rights pending.**

The new timetable-based choice produced 600 positive vehicle OD pairs totalling 1,569.500896674 PCE/h, and these values actually entered Frank–Wolfe on the unchanged original directed road graph. One actual update was saved. The provider checks passed, and S0 accepted the saved numerical result as S0\_ACCEPTED\_NEW\_CHOICE\_FW\_SAVED\_NUMERIC. New figures, plot data and detailed prose remain restricted to this private preview pending the public basis for University of Michigan timetable derivatives.

### Field chain and input identity

Frozen generation and distribution → unchanged person OD → OD-specific timetable-based mode choice → drive persons ÷ 1.2 persons/vehicle × 1 PCE/vehicle → 600 positive vehicle OD → ChoiceR1 demand.volume → actual FW update → original physical-road flow. Assignment reads the already converted PCE demand directly. Transit and walk remain person-mode results, not extra road vehicles. The one-hour period makes PCE/period numerically equal to PCE/h.

<a id="figure-ann-choice-fw-network-v002"></a>

##### New timetable demand and its physical road assignment

[![New timetable demand and its physical road assignment](<../assets/private-choicefw-v002/ann-arbor/figures/ANN_CHOICE_FW_NETWORK.svg>)](<../assets/private-choicefw-v002/ann-arbor/figures/ANN_CHOICE_FW_NETWORK.svg>)

This new-choice instance alone uses 600 positive vehicle OD pairs and 1,569.500896674 PCE/h. The left panel is vehicle OD demand (PCE/h per OD); the right panel is the resulting assigned flow (PCE/h per directed physical road arc), with separate colour scales. All 5,138 physical roads are retained: 1,998 have positive flow and 3,140 have zero flow. Grey roads represent zero flow; overlapping directions remain separate data rows. The 9,065 turn arcs are not counted as physical roads. Summing road flows counts a trip on multiple roads and is not the total vehicle demand. Engineering timetable scenario, not observed or locally calibrated traffic.

[Full figure](<../assets/private-choicefw-v002/ann-arbor/figures/ANN_CHOICE_FW_NETWORK.svg>) · [PNG](<../assets/private-choicefw-v002/ann-arbor/figures/ANN_CHOICE_FW_NETWORK.png>) · [Plot data · Vehicle\_demand.private.csv](<../assets/private-choicefw-v002/ann-arbor/figures/Vehicle_demand.private.csv>) · [Plot data · Assigned\_physical\_flow.private.csv](<../assets/private-choicefw-v002/ann-arbor/figures/Assigned_physical_flow.private.csv>) · [Source · FIGURE\_SOURCES.json](<../assets/private-choicefw-v002/ann-arbor/figures/FIGURE_SOURCES.json>) · [Source · FIELD\_CHAIN.csv](<../assets/private-choicefw-v002/ann-arbor/FIELD_CHAIN.csv>) · [Source · FIELD\_CHAIN\_HASHES.csv](<../assets/private-choicefw-v002/ann-arbor/FIELD_CHAIN_HASHES.csv>) · [Source · FW\_CHECK.json](<../assets/private-choicefw-v002/ann-arbor/verification/FW_CHECK.json>) · [S0 scope and SHA](<../assets/private-choicefw-v002/ann-arbor/RECEIPT.json>)

<a id="figure-ann-choice-fw-convergence-v002"></a>

##### Frank–Wolfe: one actual update on the new choice demand

[![Frank–Wolfe: one actual update on the new choice demand](<../assets/private-choicefw-v002/ann-arbor/figures/ANN_CHOICE_FW_CONVERGENCE.svg>)](<../assets/private-choicefw-v002/ann-arbor/figures/ANN_CHOICE_FW_CONVERGENCE.svg>)

The two markers are the actual saved iteration 0 and iteration 1 of ANN\_TRANSIT\_CHOICE\_FW\_V002; they are not sampled from another experiment. Beckmann objective decreases from 7,511.797008491 to 7,511.745981436 PCE·min (0.051027055 PCE·min); the left panel displays excess above the final objective. Independent full-graph relative gap decreases from 3.6149991422457574e−5 to 5.078039901982526e−15 against the fixed 1e−5 gate. Solver-native final gap is separately retained as 3.627171358558947e−15 because the independent sum order differs. Initial max v/c is 0.6830239071239427; the separately checked final max v/c happens to have the same value. A short curve does not prove the region too small, and the initial state belongs to this accepted run rather than a separate failed trial.

[Full figure](<../assets/private-choicefw-v002/ann-arbor/figures/ANN_CHOICE_FW_CONVERGENCE.svg>) · [PNG](<../assets/private-choicefw-v002/ann-arbor/figures/ANN_CHOICE_FW_CONVERGENCE.png>) · [Plot data · CONVERGENCE.plot.json](<../assets/private-choicefw-v002/ann-arbor/figures/CONVERGENCE.plot.json>) · [Plot data · history.csv](<../assets/private-choicefw-v002/ann-arbor/S/ChoiceR1/FW/history.csv>) · [Source · CHECKPOINT\_AUDIT.json](<../assets/private-choicefw-v002/ann-arbor/verification/CHECKPOINT_AUDIT.json>) · [Source · FW\_EXECUTION.json](<../assets/private-choicefw-v002/ann-arbor/FW_EXECUTION.json>) · [Source · FW\_POLICY.json](<../assets/private-choicefw-v002/ann-arbor/FW_POLICY.json>) · [S0 scope and SHA](<../assets/private-choicefw-v002/ann-arbor/RECEIPT.json>)

### Separate baselines and comparison limits

The original R2 600-OD initial check remains a separate historical record: zero updates under its original 1e−4 gate. The later frozen S600 baseline (ANN\_ARBOR\_R2\_S600\_20261008) uses 1,647.816622273 PCE/h and one update under 1e−5. The separate S72 baseline (ANN\_ARBOR\_R2\_S72\_20261008) uses 72 OD and 243.071388651 PCE/h, with zero updates at 1e−5; its Native26/52 initial acceptance is limited to S72. S600 and S72 are reused accepted comparison baselines, with zero new optimizer runs in this intake. The new ChoiceR1 experiment (ANN\_TRANSIT\_CHOICE\_FW\_V002; model ANN\_ARBOR\_CHOICE\_TIMETABLE\_R1) is the only new solve here. Do not combine these records into one trajectory or count the two reused baselines as new experiments. Native600 and finite time-expanded T1/T4 remain incomplete; this FW result does not pass them.

The same network, access, BPR rules and original person OD are retained, but mode choice changes the vehicle-demand vector. New demand is 4.752696662% below old S600 and the saved Beckmann objectives differ by −360.149153578 PCE·min. These are different engineering demand scenarios; the objective difference is not same-instance algorithm performance or an observed causal policy effect. All three later cohorts retain the approximately 19.633 km² Central Ann Arbor urban subregion and the original routing halo. Geographic adequacy was not tested.

S0 has accepted the saved numerical result. These unchanged source figures still contain their producer-era pending-public-release label; this refers to public rights, not a missing scientific intake. The new figures and detailed data are private review material pending the U-M timetable-derived public basis. Transit scheduling, geographic, and real-time data provided by permission of AAATA/TheRide. © OpenStreetMap contributors; road-derived data ODbL 1.0.

[Complete field chain](<../assets/private-choicefw-v002/ann-arbor/MODEL_AND_FIELD_CHAIN.md>) · [Comparison scope](<../assets/private-choicefw-v002/ann-arbor/SCALE_AND_COMPARABILITY.md>) · [Producer chapter](<../assets/private-choicefw-v002/ann-arbor/ANN_ARBOR_CITY_VOLUME_INCREMENT.md>) · [Source notice](<../assets/private-choicefw-v002/ann-arbor/SOURCE_NOTICE.md>)

<a id="gap-20261008"></a>

## Latest received evidence · 8 October 2026

Current accepted results preserve each frozen model, demand instance and numerical unit. The figures below read the received public evidence without additional optimization.

<dl class="accepted-method-notes"><dt>New saved FW, sparse fixed-path FW and Algorithm B checks pass on the original 600-OD static demand.</dt><dd>The stricter S600 FW uses a 1e−5 gate and records iteration0 and1: one real update. The earlier R2 initial check passed 1e−4 with zero updates; both scopes remain visible.</dd><dt>Native26/52 initial states pass the original-coordinate checks with zero optimization updates.</dt><dd>This is initial-state acceptance, not an iterative compression-performance result. S72 does not establish Native600 success; Native600 remains unpassed.</dd><dt>A revised vehicle-demand output exists, but no new FW assignment was run on that revision.</dt><dd>New U-M-derived figure families remain targeted holds; no held demand figures or omitted numeric contents are imported. T1 and T4 remain unsolved.</dd></dl>

[Homepage city cards](<../index.html?atlas-view=full#ann-arbor>) · [Figure guide and saved-state interpretation](<../figure-update-status.html#top>) · [Earlier frozen chapters and history](<#gap-earlier-cutoff>)

### Received figure evidence

<a id="figure-gap-aa-gap-static"></a>

##### Static optimality on two separate demand instances

<a id="table-r11-aa-static-endpoints"></a>

[![Static optimality on two separate demand instances](<../assets/figure-contract-r12/figures/ann-arbor/aa-static-signed-gaps.svg>)](<../assets/figure-contract-r12/figures/ann-arbor/aa-static-signed-gaps.svg>)

Accepted static endpoints are grouped by their own frozen demand instance. S600 has separate FW, sparse fixed-path FW and Algorithm B results; S72 has FW, finite-path and Native26/52 endpoints. Method categories are not iterations and are not joined. Signed near-zero gaps retain the exact precision printed in the approved SVG, including negative floating-point roundoff. The later S600 FW and finite-path FW have two saved rows (iterations 0 and 1); no unsupplied numerical intermediate is constructed. S72 Native methods accepted initialization with zero updates. Existing method-specific physical maps remain the spatial evidence.

[SVG](<../assets/figure-contract-r12/figures/ann-arbor/aa-static-signed-gaps.svg>) · [PNG](<../assets/figure-contract-r12/figures/ann-arbor/aa-static-signed-gaps.png>) · [PDF](<../assets/figure-contract-r12/figures/ann-arbor/aa-static-signed-gaps.pdf>) · [Source data](<../assets/figure-contract-r12/figures/ann-arbor/aa-static-signed-gaps.source.json>)

<a id="gap-notice-ann-arbor-5f0fcbc7c1"></a>

### Source and scope notice

Separate frozen S600 and S72 static instances. S72 Native passed at initialization with zero updates; Native600 remains incomplete. New timetable-choice FW has since passed S0 scientific intake; its new derivatives await public rights. © OpenStreetMap contributors, ODbL: https://www.openstreetmap.org/copyright; U.S. Census/LEHD.

### Complete approved source chapters

The following chapters are retained in full, including numerical tables and historical source-time statements. Their figures link to the same figure anchors above.

<details id="gap-source-aa-static-gap-addendum-s0" markdown="1">
<summary>Approved source chapter — AA_STATIC_GAP_ADDENDUM_S0.md</summary>

Reading edition of the approved source, SHA-256 6fca56bed8abf88aee5c28558b9c7091a451bcf5d5b14da043a281e6b8fece0d . Download original source text . The linked original preserves the complete source record; this reading edition displays accepted results.

### Ann Arbor static gap addendum (S0 receiver edition)

The old six-city R3 static state remains 6/6 accepted. New saved S600 FW, sparse fixed-path FW and Algorithm B checks pass, alongside separately frozen S72 Native26/52 initial checks with zero optimization updates. This does not establish Native600 success.

The new timetable-based choice and road-assignment scenario has passed S0 scientific intake. Its new figures, detailed model data and long prose await confirmed public rights for University of Michigan timetable derivatives. Earlier exact-SHA figures retain their original identities; Native600 and finite T1/T4 remain incomplete.

© OpenStreetMap contributors (ODbL); U.S. Census/LEHD original allocation inputs. Engineering model only, not observed travel calibration.

</details>

<a id="gap-earlier-cutoff"></a>

Original four-stage chapters retain their original demand, input identity and engineering assumptions.

**Local reading preview.** The four-stage calculation has been completed and independently checked. This reading edition brings its saved methods and numerical summaries together; the underlying materials have not all been cleared for public release.

<a id="scope"></a>

## Scope and model instance

The Ann Arbor case models weekday home-based work (HBW) travel during 08:00–09:00 in a **19.633 km² central urban subregion**. A 2.5 km circle centered near the University of Michigan Diag includes downtown, surrounding homes, workplaces and connected streets. The university is a geographic reference and a source of bus schedules; the model population is not a count of students, university commuters or campus property users.

A fixed 5 × 5 metric grid clipped to the circle produces 25 model zones. A 400 m routing halo supplies surrounding paths without extending the demand boundary. All 600 possible directed interzonal pairs are reachable and carry positive modeled demand. Generation, distribution, mode choice and static assignment form one forward pass; assignment does not feed back into mode choice or trip generation.

This is an engineering scenario built from local geography, source statistics and explicit behavioral assumptions. It is useful for examining a reproducible calculation, but has not been calibrated to a local household survey or validated against observed link counts. Its boundary and source years must remain attached to every reported result.

<a id="results-overview"></a>

## Four-stage results at a glance

Saved results for the same 25-zone, 08:00–09:00 HBW scenario. Values below are rounded for reading.

| Stage | Saved result | How to read it |
| --- | --- | --- |
| [01 / Generation](<#generation>) | 6,596.065 person-trip opportunities | 3,627.836 external or uncaptured; 237.458 intrazonal; 2,730.771 internal interzonal. Only the last component advances to the OD model. |
| [02 / Distribution](<#distribution>) | 2,730.771 persons across 600 directed OD pairs | 25 zones; no interzonal OD subsampling. Intrazonal cells are zero by the declared accounting convention. |
| [03 / Mode choice](<#mode>) | Drive 1,977.380; U-M bus 244.808; walk 508.583 persons | OD-specific availability and costs determine the split. Drive converts once to 1,647.817 PCE for road assignment. |
| [04 / Assignment](<#assignment>) | 600 vehicle ODs; relative gap 5.103 × 10<sup>−5</sup> | The initial all-or-nothing loading passes the frozen 10<sup>−4</sup> gap threshold. Frank–Wolfe performs zero update iterations. |

Persons and passenger-car equivalents (PCE) are different units. These are saved model results for local review, not measured travel volumes or a new public data release.

<a id="inputs"></a>

## Inputs and preparation

<a id="coverage-row-01"></a>

<a id="coverage-row-02"></a>

<a id="coverage-row-03"></a>

The household and population inputs come from the [2020–2024 ACS five-year tables](<#source-census>); employment comes from [2021 Michigan LODES workplace jobs](<#source-lodes>). Area allocation from 60 intersecting Census block groups gives approximately 52,954 residents, 19,287 households and 69,183 workplace jobs in the circle. These are allocated source estimates, not an observed 2026 census of the study area. The generation calculation retains the unrounded household total of approximately 19,286.74.

Source statistics, model geography and transport inputs retain separate identities.

| Input | Role in this case | Scope or limitation |
| --- | --- | --- |
| ACS population and households | Resident context and household-based generation | 2020–2024 five-year estimates, allocated by area rather than a local commute survey. |
| 2021 LODES workplace jobs | Relative attraction weights | Jobs are normalized to internal productions; job counts are not an independent total of trips. |
| Census-derived geography | Allocation into the fixed 25-zone grid | Source block groups and final model zones are different objects; see the [geography-vintage note](<#source-vintage>). |
| OpenStreetMap routing extract | Road impedance, tagged access and static assignment | Fixed circle plus routing halo; 5,138 directed physical road arcs in the accepted four-stage graph. |
| U-M GTFS, 5 October 2026 service day | Bus availability and generalized travel costs | U-M buses only. It does not represent the complete TheRide network or an exact departure-time itinerary. |

The four-stage routing graph was newly compiled from tagged OSM data. It is separate from the earlier City Road Centerline preflight network, which had 4,059 directed source links. Their link counts, geometry and provenance must not be mixed. The accepted static graph contains 5,138 physical traversal arcs within 14,203 total graph arcs; turn and other graph arcs are not additional physical roads.

Tagged direction and motor access are applied before routing. The construction removes 127 explicit forbidden turn pairs and uses conservative closures for five via-way relations; 29 other restriction relations could not be matched to eligible movements. Zone access uses in-zone motor-road entries on the strongly connected graph. These are documented model rules, not a field certification of current legal access.

This local reading revision adds eight figures drawn from the accepted saved 25-zone four-stage inputs and outputs. All 600 directed OD pairs and the actual 5,138 physical traversal arcs are retained; no solver was rerun. The original released generation/distribution figures remain available below, together with the historical photograph and all source links. New local derivatives do not constitute a public release.

<a id="ann-r3-sources"></a>

[![Model zones, physical roads and access](<../assets/city-alignment-r3/ann-arbor/aa-s01.svg>)](<../assets/city-alignment-r3/ann-arbor/aa-s01.svg>)

**AA-S01 — Model zones, physical roads and access** The accepted 25-zone circle and 5,138 directed OSM physical traversal arcs, with 25 in-zone road-entry points. The full turn-expanded graph has 14,203 arcs; turn arcs are not additional roads. EPSG:26917 coordinates are displayed relative to the study-area center in km. This is the accepted four-stage graph, not the earlier 4,059-link centerline preflight. © OpenStreetMap contributors, ODbL 1.0. Local reading revision.

[SVG](<../assets/city-alignment-r3/ann-arbor/aa-s01.svg>) · [PNG](<../assets/city-alignment-r3/ann-arbor/aa-s01.png>) · [PDF](<../assets/city-alignment-r3/ann-arbor/aa-s01.pdf>) · [Source](<../assets/city-alignment-r3/ann-arbor/aa-s01.source.json>) · [Plot data](<../assets/city-alignment-r3/ann-arbor/aa-s01.plot_data.json>)

<a id="ann-r3-population"></a>

[![Population, households and workplace jobs](<../assets/city-alignment-r3/ann-arbor/aa-p01.svg>)](<../assets/city-alignment-r3/ann-arbor/aa-p01.svg>)

**AA-P01 — Population, households and workplace jobs** Area-allocated source estimates across all 25 final model zones: ACS 2020–2024 population and households, and 2021 Michigan LODES workplace jobs. Each panel has its own linear color scale and unit. Job weights are normalized to internal productions downstream; they are not independently counted trips. Source statistics are not a campus population or a 2026 census. U.S. Census Bureau, ACS and LEHD/LODES. Local reading revision.

[SVG](<../assets/city-alignment-r3/ann-arbor/aa-p01.svg>) · [PNG](<../assets/city-alignment-r3/ann-arbor/aa-p01.png>) · [PDF](<../assets/city-alignment-r3/ann-arbor/aa-p01.pdf>) · [Source](<../assets/city-alignment-r3/ann-arbor/aa-p01.source.json>) · [Plot data](<../assets/city-alignment-r3/ann-arbor/aa-p01.plot_data.json>)

<a id="ann-r3-transit"></a>

##### Scheduled stops and modeled mode availability

[![Scheduled stops and modeled mode availability](<../assets/figure-contract-r11/figures/ann-arbor/aa-t01.svg>)](<../assets/figure-contract-r11/figures/ann-arbor/aa-t01.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

Left: the 63 saved U-M GTFS stop locations used as input to the accepted mode-cost build, over the accepted 25-zone OSM physical network. Right: actual availability in 600 directed OD pairs—drive 600, U-M bus 110, walk 366. The modeled U-M service uses 109 scheduled route-stop legs and frequency-based waits; 11 zones are within the stop-access rule. Stop symbols are planned service locations, not observed GPS. No TheRide service, exact departure-time itinerary or verified pedestrian connector is implied. © OpenStreetMap contributors; University of Michigan GTFS. Local reading revision. R11 layout repair: both panels share the actual map top and bottom bounds; the stop count is stated here rather than overprinted on the map.

</details>

[PNG](<../assets/figure-contract-r11/figures/ann-arbor/aa-t01.png>) · [SVG](<../assets/figure-contract-r11/figures/ann-arbor/aa-t01.svg>) · [PDF](<../assets/figure-contract-r11/figures/ann-arbor/aa-t01.pdf>) · [Source record](<../assets/figure-contract-r11/figures/ann-arbor/aa-t01.source.json>)

<a id="generation"></a>

## 01 / Trip generation

<a id="coverage-row-06"></a>

The generation rule multiplies area-allocated households by 1.90 HBW person-trip opportunities per household per weekday and an 18% share for the modeled hour. The 1.90 rate is transferred from [Boston Region MPO TDM23.2.0, Table 74](<#source-boston-rate>); the hourly share is an engineering assumption. Neither was fitted to Ann Arbor observations.

An assumed 45% internal capture and an 8% intrazonal share of captured demand partition the result. Workplace jobs distribute attractions across zones, then normalization matches their total to internal productions. The ledger prevents external and within-zone travel from being silently assigned to the internal interzonal road model.

HBW person-trip opportunities in the modeled hour.

| Demand component | Person trips | Destination in the workflow |
| --- | --- | --- |
| Generated total | 6,596.065080003 | Starting opportunity ledger |
| External or uncaptured | 3,627.835794002 | Reported separately; not assigned inside the subregion |
| Intrazonal | 237.458342880 | Reported separately; omitted from interzonal OD cells |
| Internal interzonal | 2,730.770943121 | Passed to distribution, mode choice and the appropriate mode-specific loading |

The new geographic figure shows all 25 production and attraction zones on a common scale, followed by the complete generation ledger. The earlier released figure retained below shows the twelve largest production zones; that selected plot was not a reduced model.

<a id="ann-r3-generation"></a>

[![Internal demand margins and the generation ledger](<../assets/city-alignment-r3/ann-arbor/aa-g01.svg>)](<../assets/city-alignment-r3/ann-arbor/aa-g01.svg>)

**AA-G01 — Internal demand margins and the generation ledger** All 25 zones are shown. The two maps share a linear person-trip color scale and display the internal interzonal production and job-weighted attraction passed to distribution. The ledger partitions 6,596.065080 generated opportunities into 3,627.835794 external/uncaptured, 237.458343 intrazonal and 2,730.770943 internal interzonal persons. Only the final component proceeds to the OD model. The 1.90 HBW rate is transferred; hour/capture/intrazonal shares are engineering assumptions. ACS 2020–2024 and LODES 2021, U.S. Census Bureau. Local reading revision.

[SVG](<../assets/city-alignment-r3/ann-arbor/aa-g01.svg>) · [PNG](<../assets/city-alignment-r3/ann-arbor/aa-g01.png>) · [PDF](<../assets/city-alignment-r3/ann-arbor/aa-g01.pdf>) · [Source](<../assets/city-alignment-r3/ann-arbor/aa-g01.source.json>) · [Plot data](<../assets/city-alignment-r3/ann-arbor/aa-g01.plot_data.json>)

<details markdown="1">
<summary>Earlier released figure — original image and source notice</summary>

<a id="figure-fs-g01"></a>

</details>

<a id="distribution"></a>

## 02 / Trip distribution

<a id="coverage-row-07"></a>

A doubly constrained gravity calculation combines the generation margins with directed road-network impedance. Its deterrence kernel is exp(−0.08 × minutes); the coefficient is an engineering assumption. Iterative proportional fitting (IPF) balances production and attraction margins before a declared 90% forward / 10% reverse period convention is applied once to obtain directed OD demand.

The saved matrix contains 2,730.770943121 person trips over all 600 feasible directed interzonal pairs. IPF takes five iterations, with a maximum absolute margin residual of 1.18622395 × 10<sup>−7</sup> person trips. Intrazonal entries remain structural zeros. No small OD sample substitutes for the full matrix, and unreachable pairs are not represented by an artificial large finite cost.

The 25-zone heatmap uses log(1 + person trips) to keep small and large cells legible. Its color scale does not change the stored demand or units. Without a local observed OD matrix, this is a model-generated travel pattern rather than validated commuting behavior.

<a id="ann-r3-distribution"></a>

[![Complete directed OD demand and road impedance](<../assets/city-alignment-r3/ann-arbor/aa-d01.svg>)](<../assets/city-alignment-r3/ann-arbor/aa-d01.svg>)

**AA-D01 — Complete directed OD demand and road impedance** The complete 25 × 25 directed matrix contains 600 positive interzonal pairs and structural zeros on the intrazonal diagonal. Color is log(1 + person trips), with original-unit tick labels; no values are discarded. The scatter shows the same 600 saved OD demands against their actual directed road impedance, without a fitted trend. Doubly constrained gravity/IPF and the one-time 90% forward / 10% reverse convention determine these modeled demands. © OpenStreetMap contributors; U.S. Census Bureau ACS/LODES. Local reading revision, not an observed commuting matrix.

[SVG](<../assets/city-alignment-r3/ann-arbor/aa-d01.svg>) · [PNG](<../assets/city-alignment-r3/ann-arbor/aa-d01.png>) · [PDF](<../assets/city-alignment-r3/ann-arbor/aa-d01.pdf>) · [Source](<../assets/city-alignment-r3/ann-arbor/aa-d01.source.json>) · [Plot data](<../assets/city-alignment-r3/ann-arbor/aa-d01.plot_data.json>)

<details markdown="1">
<summary>Earlier released figure — original image and source notice</summary>

<a id="figure-fs-d01"></a>

</details>

<a id="mode"></a>

## 03 / Mode choice

<a id="coverage-row-04"></a>

<a id="coverage-row-08"></a>

Mode choice has already been computed for the same OD matrix and hour. It compares drive, U-M bus and walk using OD-specific generalized minutes, with a logit sensitivity of 0.07 per generalized minute and a value of time of $20 per hour. An unavailable mode receives zero probability for that OD; it is different from a modeled alternative attracting very few trips.

All 600 OD pairs have driving available. Walking is available on 366 pairs under a 45-minute choice limit. U-M bus is available on 110 pairs using schedule-derived route-stop legs, at most 700 m of straight-line stop access, a ×1.3 access-distance proxy and frequency-based waiting. These are approximate costs, not fully timed multimodal itineraries or verified parcel-access routes.

Saved mode-choice summaries for local review. All values are person trips unless stated otherwise.

| Mode | Available OD pairs | Modeled persons | Use in the next stage |
| --- | --- | --- | --- |
| Drive | 600 | 1,977.380 (72.41%) | ÷ 1.2 persons/vehicle × 1.0 PCE/vehicle = 1,647.817 PCE |
| U-M bus | 110 | 244.808 (8.96%) | Retained as a modal result; not added to the vehicle-OD assignment |
| Walk | 366 | 508.583 (18.62%) | Retained as a modal result; no pedestrian capacity assignment |

The split represents all 2,730.771 internal interzonal persons, with none dropped. Percentages can differ from 100% by rounding. These are outcomes of the limited U-M service representation and assumed utilities, not measured local modal shares. The mode-choice figure below and its selected plot data are included for local reading. They remain outside the existing public asset release; this revision does not change that release status.

<a id="ann-r3-mode"></a>

[![Mode choice over every directed OD pair](<../assets/city-alignment-r3/ann-arbor/aa-m01.svg>)](<../assets/city-alignment-r3/ann-arbor/aa-m01.svg>)

**AA-M01 — Mode choice over every directed OD pair** All 600 OD pairs enter OD-specific three-mode choice. The three heatmaps use a common 0–1 probability scale; gray intrazonal cells were not modeled, while zero probabilities include unavailable alternatives. The bar chart weights probabilities by each OD demand: drive 1,977.380 persons, U-M bus 244.808, walk 508.583. Only driving converts to road demand, once: persons ÷ 1.2 × 1.0 = 1,647.816622 PCE. These are saved engineering-scenario probabilities, not measured mode shares. U-M schedule-derived inputs; local reading revision, not a new public release.

[SVG](<../assets/city-alignment-r3/ann-arbor/aa-m01.svg>) · [PNG](<../assets/city-alignment-r3/ann-arbor/aa-m01.png>) · [PDF](<../assets/city-alignment-r3/ann-arbor/aa-m01.pdf>) · [Source](<../assets/city-alignment-r3/ann-arbor/aa-m01.source.json>) · [Plot data](<../assets/city-alignment-r3/ann-arbor/aa-m01.plot_data.json>)

<a id="assignment"></a>

## 04 / Physical-link assignment

<a id="coverage-row-09"></a>

<a id="coverage-row-10"></a>

The vehicle-demand conversion is applied once, giving 1,647.816622273 PCE for all 600 positive vehicle ODs. Static Frank–Wolfe assignment loads this exact demand on the frozen turn-expanded graph. BPR travel time uses α = 0.15 and β = 4; declared road-class and lane proxies supply missing speed or capacity fields. This model uses soft capacity and does not represent time-dependent queues or spillback.

The initial all-or-nothing loading already meets the frozen relative-gap threshold of 10<sup>−4</sup>. The saved gap is 5.10282992009334 × 10<sup>−5</sup>, so Frank–Wolfe stops at iteration 0. That means zero update steps after the initial loading; it does not mean assignment was skipped, nor does it support an iterative convergence-speed comparison.

Accepted saved static solution, summarized for local review.

| Quantity | Saved value | Interpretation |
| --- | --- | --- |
| Vehicle OD pairs | 600 | All positive vehicle ODs are loaded |
| Assigned demand | 1,647.816622273 PCE | Demand passed directly from mode choice |
| Beckmann objective | 7,871.970629927 PCE-min | Integrated static objective; not total person travel time |
| Full-graph relative gap | 5.10282992009334 × 10<sup>−5</sup> | Below the predeclared 10<sup>−4</sup> tolerance |
| Frank–Wolfe updates | 0 | A single initial gap check, not a multi-step trace |
| Maximum node-balance residual | 5.684 × 10<sup>−13</sup> PCE | Independent flow-conservation reconstruction |
| Physical road projection | 5,138 directed road arcs | Road travel times and v/c recomputed with zero maximum discrepancy in the recorded projection check |
| Maximum physical-road v/c | Approximately 0.718 | Model loading/capacity ratio for this scenario, not an observed traffic condition |

Turn and connector arcs stay in the graph solution but are excluded from physical-road loading charts. The physical-flow and initialization-diagnostic figures below are included in this local reading revision. Numerical acceptance and permission to redistribute an image or dataset remain separate questions; these additions do not change the approved public image set.

<a id="figure-r9-fw-physical-flow"></a>

##### Frank–Wolfe: physical flow and distribution

[![Frank–Wolfe: physical flow and distribution](<../assets/figure-contract-r11/figures/ann-arbor/fw-physical-flow.svg>)](<../assets/figure-contract-r11/figures/ann-arbor/fw-physical-flow.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

Saved Ann Arbor static Frank–Wolfe endpoint for 08:00–09:00 HBW. The map and 22-bin histogram use the same complete 5,138-link physical-flow vector, including 3,147 exact-zero links; 1,991 links exceed 1e-6 PCE. Flow is PCE accumulated during the declared one-hour period, not persons or flow per simulation time step. The map uses a square-root sequential color scale with original-unit ticks and gray road context; histogram counts are linear and no links are omitted. Turn, access and other nonphysical solver arcs are excluded. Only the saved iteration-0 initialization exists; FW performed zero subsequent updates. Opposite directed geometries retain a 3 m display offset; values and IDs are unchanged. This is a modeled engineering scenario, not observed traffic. © OpenStreetMap contributors / ODbL 1.0. R11 layout repair: map and all-link histogram share measured top and bottom panel bounds. The original saved physical-link IDs, exact flow vector, geographic vertices, display offsets, histogram edges and counts remain unchanged.

</details>

[PNG](<../assets/figure-contract-r11/figures/ann-arbor/fw-physical-flow.png>) · [SVG](<../assets/figure-contract-r11/figures/ann-arbor/fw-physical-flow.svg>) · [PDF](<../assets/figure-contract-r11/figures/ann-arbor/fw-physical-flow.pdf>) · [Source record](<../assets/figure-contract-r11/figures/ann-arbor/fw-physical-flow.source.json>)

<details markdown="1">
<summary>Saved initial checks and original endpoint views</summary>

<a id="ann-r3-static-flow"></a>

</details>

<details markdown="1">
<summary>Saved initial checks and original endpoint views</summary>

<a id="ann-r3-static-check"></a>

##### Frank–Wolfe: the saved initial check

<a id="table-r11-aa-original-initial-check"></a>

[![Frank–Wolfe: the saved initial check](<../assets/figure-contract-r12/figures/ann-arbor/aa-original-initial-check.svg>)](<../assets/figure-contract-r12/figures/ann-arbor/aa-original-initial-check.svg>)

Only the actual saved iteration 0 is shown: objective 7871.97062992656 PCE·min/h and relative gap 5.10282992009334e-05, against the unchanged 0.0001 stopping gate. There were zero updates. Each panel contains a single numerical point; no missing trajectory or second state is inferred. The companion physical-flow map reads this method’s own saved vector. This original 1e−4-gate instance is distinct from the later S600 1e−5-gate run, which saved iterations 0 and 1.

[SVG](<../assets/figure-contract-r12/figures/ann-arbor/aa-original-initial-check.svg>) · [PNG](<../assets/figure-contract-r12/figures/ann-arbor/aa-original-initial-check.png>) · [PDF](<../assets/figure-contract-r12/figures/ann-arbor/aa-original-initial-check.pdf>) · [Source data](<../assets/figure-contract-r12/figures/ann-arbor/aa-original-initial-check.source.json>)

</details>

<a id="parity-ann-arbor-static-inputs"></a>

## Static assignment: demand margins and physical endpoints

<a id="figure-parity-ann-arbor-assignment-margins"></a>

##### Static assignment demand margins

[![Static assignment demand margins](<../assets/template-parity-20261008/static-inputs/ann-arbor/assignment-margins.svg>)](<../assets/template-parity-20261008/static-inputs/ann-arbor/assignment-margins.svg>)

New choice600: 600 positive source-zone OD pairs, 600 loaded solver-node OD pairs and 1569.500896674 PCE/hour. Origin and destination margins sum the selected assignment PCE by source zone, after the saved mode/occupancy conversion. All source-zone polygons, including any zero selected demand, use a common square-root normalization with ticks in original PCE/hour. New choice600 is separate from old S600, S72 and the original R2 scenario. Drive-person demand has already been converted by saved occupancy and PCE factors; it is not converted again. Native600 and finite-time status are not changed. These are modeled assignment-input quantities, not population generation, observed traffic or assigned link flow. Both panels share one map extent; context roads outside this input footprint are clipped only for display.

[Complete evidence · same figure](<#figure-parity-ann-arbor-assignment-margins>) · [SVG](<../assets/template-parity-20261008/static-inputs/ann-arbor/assignment-margins.svg>) · [PNG](<../assets/template-parity-20261008/static-inputs/ann-arbor/assignment-margins.png>) · [PDF](<../assets/template-parity-20261008/static-inputs/ann-arbor/assignment-margins.pdf>) · [Plot data](<../assets/template-parity-20261008/static-inputs/ann-arbor/assignment-margins.plot.json>) · [Source record](<../assets/template-parity-20261008/static-inputs/ann-arbor/assignment-margins.source.json>) · [Caption](<../assets/template-parity-20261008/static-inputs/ann-arbor/assignment-margins.caption.md>)

<a id="figure-parity-ann-arbor-assignment-endpoints"></a>

##### Physical demand endpoints

[![Physical demand endpoints](<../assets/template-parity-20261008/static-inputs/ann-arbor/assignment-endpoints.svg>)](<../assets/template-parity-20261008/static-inputs/ann-arbor/assignment-endpoints.svg>)

New choice600: 600 positive source-zone OD pairs, 600 loaded solver-node OD pairs and 1569.500896674 PCE/hour. Original access records locate 25 loaded physical origins and 25 loaded physical destinations. Open circles show the frozen access system and filled colors show selected endpoint PCE/hour. The largest loaded endpoint in each panel is labelled by its physical source ID (or the saved M-state road-midpoint identifier). Each side sums to the same total; this aggregation is for display only. New choice600 is separate from old S600, S72 and the original R2 scenario. Drive-person demand has already been converted by saved occupancy and PCE factors; it is not converted again. Native600 and finite-time status are not changed. These are modeled assignment-input quantities, not population generation, observed traffic or assigned link flow. Both panels share one map extent; context roads outside this input footprint are clipped only for display.

[Complete evidence · same figure](<#figure-parity-ann-arbor-assignment-endpoints>) · [SVG](<../assets/template-parity-20261008/static-inputs/ann-arbor/assignment-endpoints.svg>) · [PNG](<../assets/template-parity-20261008/static-inputs/ann-arbor/assignment-endpoints.png>) · [PDF](<../assets/template-parity-20261008/static-inputs/ann-arbor/assignment-endpoints.pdf>) · [Plot data](<../assets/template-parity-20261008/static-inputs/ann-arbor/assignment-endpoints.plot.json>) · [Source record](<../assets/template-parity-20261008/static-inputs/ann-arbor/assignment-endpoints.source.json>) · [Caption](<../assets/template-parity-20261008/static-inputs/ann-arbor/assignment-endpoints.caption.md>)

<a id="parity-ann-arbor-construction"></a>

## Time-expanded network and path examples

<a id="figure-parity-ann-arbor-time-layers"></a>

##### Time-expanded network in layers

[![Time-expanded network in layers](<../assets/template-parity-20261008/construction/ann-arbor/time-layers.svg>)](<../assets/template-parity-20261008/construction/ann-arbor/time-layers.svg>)

Ann Arbor: the frozen 30-second construction rule is illustrated on an actual allowed two-road chain. Frozen construction rule applied to an actual allowed two-road chain. The full graph has not been built and no time-expanded solver has run. The displayed turn is an actual allowed static-network turn chosen for illustration; this is not a saved assignment path. Displayed timing is the deterministic frozen 30-second rule applied to original free-flow minutes, not a measured or computed route time. This input-only illustration does not change Native600 or finite-time reception status. The slanted planes and horizontal positions are schematic display coordinates. A−/A+ and B−/B+ denote entry/exit routing states, not original intersections. Exact state IDs, physical-road IDs and time indices are retained in plot data.

[Complete evidence · same figure](<#figure-parity-ann-arbor-time-layers>) · [SVG](<../assets/template-parity-20261008/construction/ann-arbor/time-layers.svg>) · [PNG](<../assets/template-parity-20261008/construction/ann-arbor/time-layers.png>) · [PDF](<../assets/template-parity-20261008/construction/ann-arbor/time-layers.pdf>) · [Plot data](<../assets/template-parity-20261008/construction/ann-arbor/time-layers.plot.json>) · [Source record](<../assets/template-parity-20261008/construction/ann-arbor/time-layers.source.json>) · [Caption](<../assets/template-parity-20261008/construction/ann-arbor/time-layers.caption.md>)

<a id="figure-parity-ann-arbor-local-construction"></a>

##### Local construction details

[![Local construction details](<../assets/template-parity-20261008/construction/ann-arbor/local-construction.svg>)](<../assets/template-parity-20261008/construction/ann-arbor/local-construction.svg>)

Ann Arbor: panels map two source-directed physical roads to four routing entry/exit states and their time-indexed movements. Frozen construction rule applied to an actual allowed two-road chain. The full graph has not been built and no time-expanded solver has run. The displayed turn is an actual allowed static-network turn chosen for illustration; this is not a saved assignment path. Displayed timing is the deterministic frozen 30-second rule applied to original free-flow minutes, not a measured or computed route time. This input-only illustration does not change Native600 or finite-time reception status. The turn has zero elapsed time; physical road durations are positive. No waiting arc is drawn and terminal bookkeeping states are outside this local excerpt. Plot data carry all exact source IDs, field values, and short-label aliases.

[Complete evidence · same figure](<#figure-parity-ann-arbor-local-construction>) · [SVG](<../assets/template-parity-20261008/construction/ann-arbor/local-construction.svg>) · [PNG](<../assets/template-parity-20261008/construction/ann-arbor/local-construction.png>) · [PDF](<../assets/template-parity-20261008/construction/ann-arbor/local-construction.pdf>) · [Plot data](<../assets/template-parity-20261008/construction/ann-arbor/local-construction.plot.json>) · [Source record](<../assets/template-parity-20261008/construction/ann-arbor/local-construction.source.json>) · [Caption](<../assets/template-parity-20261008/construction/ann-arbor/local-construction.caption.md>)

<a id="verification"></a>

## Verification and method coverage

<a id="coverage-row-11"></a>

<a id="coverage-row-12"></a>

<a id="coverage-row-13"></a>

<a id="coverage-row-14"></a>

<a id="coverage-row-15"></a>

<a id="coverage-row-16"></a>

<a id="coverage-row-17"></a>

<a id="coverage-row-18"></a>

The independent verifier checks five parts of the saved run: receipt-hash continuity; the household and period generation ledger; constrained OD margins and direction; mode availability, probability and person-to-PCE conservation; and path/link/objective/gap reconstruction for assignment. Six deliberately corrupted or incomplete fixtures are rejected by the expected checks.

Verifier v4 checks the frozen solver configuration and saved scientific outputs. Separate package extraction and saved-result replay reproduce the recorded checks. The current acceptance reuses existing fresh-run evidence without claiming another solve.

**The accepted method here is static BPR–Beckmann assignment with Frank–Wolfe.** Official tap-b Algorithm B, the separate finite-path reference, Native Diagnostic L3 and finite time-expanded LP/LR/ADMM/PWL experiments are not implemented Ann Arbor results in this record. A completed static four-stage chain should not be read as evidence of dynamic assignment, hard-capacity feasibility or the methods available in the Boston, Sioux Falls and Hong Kong records.

<a id="reproduction"></a>

## Reproduction and saved input identity

<a id="coverage-row-19"></a>

The registered case is `six-city-ann-arbor-four-stage-r2`. Its frozen compute capsule includes the input identity, stage receipts, saved outputs, independent verifier and reproduction entry point. The package is available through the existing private project handoff; it is not offered here as a public download.

Within that capsule's `compute_repo`, the following commands inspect its registration or verify an existing run. They are documentation for a recipient who already has the package; they are not commands that work after downloading this webpage alone.

```text
python -B tools/mcl_reproduce.py list
python -B tools/mcl_reproduce.py describe six-city-ann-arbor-four-stage-r2
python -B tools/mcl_reproduce.py verify six-city-ann-arbor-four-stage-r2 --run SAVED_RUN
```

Saved-run verification reconstructs checks without optimizing a new solution. The recorded environment uses Python 3.11+ and the frozen numerical and geospatial dependencies supplied with the capsule. This page revision does not rerun the model or replace that environment. The two earlier released result figures remain available in labeled disclosures below the new figures, with their original captions and download links.

<a id="observations"></a>

## Local observations and city context

<a id="coverage-row-05"></a>

The later local-evidence work is separate from the accepted static scenario. It studies historical observations, source-to-model geometry candidates and spatial queries. Its producer-side checks do not establish accepted source/model identity, legal turns, current facilities or a locally validated travel model. It is not used here to calibrate the four-stage totals.

Exact trajectories, matched routes, observation joins and the local inspector remain outside this page. A historical photograph can provide city context without exposing those records. It cannot establish current signal timing, present-day facility geometry, modeled demand or observed link flows.

<a id="evidence-photo"></a>

[![State Street, Ann Arbor, photographed in 2013](<../assets/six-city-evidence-r2/ann-arbor/state_street_2013.jpg>)](<../assets/six-city-evidence-r2/ann-arbor/state_street_2013.jpg>)

Michael Barera, [Ann Arbor August 2013 02 (State Street).jpg](<https://commons.wikimedia.org/wiki/File:Ann_Arbor_August_2013_02_(State_Street).jpg>), photographed 17 August 2013, unmodified; [CC BY-SA 4.0](<https://creativecommons.org/licenses/by-sa/4.0/>). Retain creator, original, license and share-alike notice on reuse.

<a id="availability"></a>

## What can be viewed and reused

Calculation status and material availability are reported separately.

| Material | Current presentation | Boundary |
| --- | --- | --- |
| Generation and distribution figures | Shown here, with SVG and PNG links | Existing approved image bytes and source/model notices are preserved. |
| 2013 State Street photograph | Shown with creator, original and license information | Historical context; retain attribution and the applicable share-alike notice. |
| Four-stage numerical summaries | Included in this local reading draft | This editorial revision is not an additional public release. Mode-choice and assignment derivatives retain their existing release hold. |
| U-M-derived mode and assignment plots/data | Completed results exist in the project handoff; figures and underlying tables are not linked here | Their source-specific display and redistribution review is still open. |
| Earlier City road map and later OSM-only candidate map | Not added | The City map has a separate source-rights issue; the later OSM-only candidate has not received a file-specific release. |
| Exact GPS and observation database | Not included | Private observation material; a geometric candidate is not an accepted identity match. |

<a id="sources"></a>

## Sources, vintages and interpretation

<a id="source-census"></a>

**Population and households.** U.S. Census Bureau, 2024 ACS five-year [B01003 population](<https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/data/5YRData/acsdt5y2024-b01003.dat>) and [B11001 household](<https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/data/5YRData/acsdt5y2024-b11001.dat>) tables, representing 2020–2024 estimates. The model's area allocation is an analyst estimate derived from these sources.

<a id="source-lodes"></a>

**Employment.** U.S. Census Bureau, [LODES8 Michigan workplace-area characteristics](<https://lehd.ces.census.gov/data/lodes/LODES8/mi/wac/>), 2021 WAC C000 total jobs. Employment year and ACS period remain distinct.

<a id="source-osm"></a>

**Routing.** © [OpenStreetMap contributors](<https://www.openstreetmap.org/copyright>), ODbL 1.0. Frozen source tags and declared engineering proxies define the computational graph; they do not certify current restrictions or field conditions.

<a id="source-transit"></a>

**U-M transit.** University of Michigan [Campus Transit](<https://ltp.umich.edu/campus-transit/>) and its producer GTFS feed for the selected 5 October 2026 service day. The source snapshot's feed period is 23 August 2026–2 January 2027. This local reading edition shows selected schedule-derived figures and their plot data; it does not publish the GTFS feed or declare a new public release.

<a id="source-boston-rate"></a>

**Transferred generation parameter.** Boston Region MPO TDM23.2.0, Table 74, as recorded in the frozen parameter-provenance register. The transfer supplies a documented engineering input; it is not a measured Ann Arbor trip rate.

<a id="source-vintage"></a>

**Geography-vintage note.** The old frozen scope prose called the block-group geometry “2020-vintage,” while the saved source register and service metadata identify TIGERweb ACS2024 and 2024-01-01. This reading edition identifies the discrepancy instead of repeating the old wording as a settled fact. It does not alter source geometry, zone assignments or numerical outputs.

**Model limits.** There is no local behavioral calibration, observed traffic validation, assignment-to-mode feedback, complete TheRide model, pedestrian/transit capacity assignment or accepted dynamic Ann Arbor experiment here. Different cities use different boundaries, vintages, costs and units, so their objectives and modal shares are not controlled cross-city performance comparisons.

[Return to the nine-city comparison table](<../index.html#03-case-coverage-and-selected-evidence>) · [Open Ann Arbor in the evidence atlas](<../index.html#ann-arbor>)
