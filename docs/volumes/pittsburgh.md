<a id="document-top"></a>

MOBILITY COMPUTATION LAB / STATIC CITY RECORD

# Pittsburgh

An East End morning HBW case grouping selected blocks into 41 tract-ID zones, with 1,406 positive vehicle OD pairs and an accepted initial assignment check.

The figures show saved method results, physical-flow maps and original-unit diagnostics. Drawing these figures invokes no optimizer.

<span id="pittsburgh-late-status-20261008"></span>
<span id="pittsburgh-final-v4-status"></span>
<a id="gap-20261008"></a>

## Latest received evidence · 8 October 2026

Current accepted results preserve each frozen model, demand instance and numerical unit. The figures below read the received public evidence without additional optimization.

<dl class="accepted-method-notes"><dt>Both original representations pass at outer14; raw maximum OD residuals are 8.0701×10−8 and 2.6256×10−7 PCE, below the original 1e−6 gate.</dt><dd>PIT_G05 contains fourteen saved states per rank. The complete accepted trajectory retains original outers 1–8 and the continuation 9–14, with full-gap, nonnegativity and reconstruction checks.</dd><dt>Existing exact-DAG LP, CG, LR and ADMM accepted states are retained without rerunning. CG has one row per phase, LR one row, ADMM one completed update.</dt><dd>0.0450275485 PCE pulse &lt; 2.5 PCE minimum physical time-arc capacity; all capacity rows are redundant. This scope is separate from the new S72 Native result.</dd><dt>PIT_G05 is the newly received S72 Native conservation trajectory. PIT_T05 remains the earlier T4 ADMM residual-versus-gate figure.</dt><dd>PIT_T05 lines compare residuals with stopping thresholds, not the start and end of an iterative trajectory. Its prior unit correction remains.</dd><dt>The actual matcher returned zero route links from 173 selected one-Hz inputs.</dt><dd>No matched-route, layer, turn-legality or local-calibration success is claimed. The original HiGHS resource limit and unrun tier2 ADMM remain.</dd></dl>

[Homepage city cards](<../index.html?atlas-view=full#pittsburgh>) · [Figure guide and saved-state interpretation](<../figure-update-status.html#top>) · [Earlier frozen chapters and history](<#gap-earlier-cutoff>)

### Received figure evidence

<span id="released-pit-s02"></span>
<a id="figure-gap-pit-g05"></a>

##### Native conservation through outer 14

[![Native conservation through outer 14](<../assets/figure-contract-r11/figures/pittsburgh/pit-native-conservation.svg>)](<../assets/figure-contract-r11/figures/pittsburgh/pit-native-conservation.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

Each rank has 14 saved outer states. The divider separates original outers 1–8 from continuation 9–14. At outer 14 the rank 26/52 residuals are 8.0701348e−8 and 2.6256443e−7 PCE; the original gate is 1e−6 PCE. Other original-space gates are checked separately. Frozen East End S72 post-diagnostic Native outer14, not GPS calibration. © OpenStreetMap contributors, ODbL: https://www.openstreetmap.org/copyright.

</details>

[PNG](<../assets/figure-contract-r11/figures/pittsburgh/pit-native-conservation.png>) · [SVG](<../assets/figure-contract-r11/figures/pittsburgh/pit-native-conservation.svg>) · [PDF](<../assets/figure-contract-r11/figures/pittsburgh/pit-native-conservation.pdf>) · [Source record](<../assets/figure-contract-r11/figures/pittsburgh/pit-native-conservation.source.json>)

<a id="gap-notice-pittsburgh-be10445e70"></a>

### Source and scope notice

Frozen East End S72 Native outer-14 results and separate fixed-cost T4 results are engineering scenarios, not GPS calibration. © OpenStreetMap contributors; ODbL 1.0: https://www.openstreetmap.org/copyright.

### Complete approved source chapters

The following chapters are retained in full, including numerical tables and historical source-time statements. Their figures link to the same figure anchors above.

<details id="gap-source-endpoint-volume-appendix-v3" markdown="1">
<summary>Approved source chapter — ENDPOINT_VOLUME_APPENDIX_v3.md</summary>

Reading edition of the approved source, SHA-256 f8c28354b5e9ccb53922566a42ab285b6d46271ffa54eb461a3ab9250b2ad45e . Download original source text . The linked original preserves the complete source record; this reading edition displays accepted results.

### Pittsburgh C04 science endpoint

Frozen core C02 v002 and OUT-state first-link convention remain byte-identical. The East End S72 modeled hour has 72 positive vehicle OD and 149.921423895 PCE. Finite and FW were previously accepted. Native rank26 outer14 max raw OD residual 8.07013475569e-08 PCE; rank52 outer14 2.62564432214e-07 PCE. The declared OD absolute gate is 1e-6 PCE. The saved original-space checker also passed full gap, nonnegativity and link reconstruction; the new independent check recomputed OD from C\_od\_path and the saved basis coordinates. These are post-diagnostic continuations, not a fresh city holdout or empirical calibration.

The original T4 fixed-cost DAG model has accepted exact LP, CG, LR and ADMM states. Those methods were not rerun. The original four-stage Trip Generation, Distribution, Mode Choice and Assignment chain remains the previously accepted R3 state.

PIT\_G05 is rendered from saved raw Native checks. Existing Pittsburgh figures and long-form city volume remain in the accepted baseline; the accompanying Volume Handoff is an addendum for S0, not a website edit.

</details>

<a id="gap-earlier-cutoff"></a>

Original four-stage chapters retain their original demand, input identity and engineering assumptions.

**Private presentation preview.** Saved result verified; Prior fresh-run receiver acceptance reused for unchanged inputs

Input snapshot: `mcl_s0_to_v_presentation_inputs_r3_v1@2026-10-05T03:57:54.309662+00:00`. Input version: `PITTSBURGH_EAST_END_2020_TRACTS_R2; frozen configuration SHA-256 4af671215d6d43668298ef1ef66ff45348a3f8b3cc91c84dac0b00547598466b`.

<a id="scope"></a>

## Scope and model instance

Pittsburgh's demand boundary is a 19.77 km² East End rectangle around Oakland, Shadyside and Squirrel Hill. In WGS84 it spans −79.985 to −79.925 longitude and 40.425 to 40.460 latitude. A routing halo extends to −79.990/−79.920 and 40.420/40.465. CMU is a map landmark, not the population denominator or the extent of a campus travel survey.

The model generates resident-household HBW travel for a synthetic weekday 08:00–09:00 hour. It is a static, single-pass engineering case. It neither estimates all traffic on East End roads nor covers every purpose, freight movement or university journey. The earlier 4.35 km² CMU/Oakland preflight is a separate source product; the larger boundary was selected before assignment.

<a id="inputs"></a>

## Inputs and preparation

<a id="coverage-row-01"></a>

<a id="coverage-row-02"></a>

<a id="coverage-row-03"></a>

Selection uses the internal points of 1,130 official 2020 Census blocks. Grouping those selected blocks by their 2020 tract IDs creates 41 zones. These are selected-block aggregates, not totals for 41 complete administrative tracts. The selected blocks contain 71,684 people and 32,432 occupied housing units; the latter serves as the scenario's household proxy.

The same block set has 91,801 workplace jobs in 2023 Pennsylvania LODES WAC C000. Workplace jobs determine attraction weights, not trip counts. Census 2020, LODES 2023 and the OSM 2026 extract have different vintages, so the scenario cannot reconstruct one observed morning. Eight bounded OSM tiles preserve original way and node identity; crossing map lines alone do not create road connections.

Separate LODES home-work relationships inform two scalar demand assumptions. Of 22,603 Pennsylvania-resident relationships originating in selected blocks, 6,505 also end inside the rectangle, giving an internal-capture proxy of 28.779%. Within those internal relationships, 9.608% have both ends in one model tract. Neither share is a measured hourly travel rate, and the zonal OD relationship counts are not copied into the gravity matrix.

<a id="figure-r3-sources"></a>

##### Retained physical road graph

[![Retained physical road graph](<../assets/figure-contract-r11/figures/pittsburgh/sources.svg>)](<../assets/figure-contract-r11/figures/pittsburgh/sources.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

17,534 retained physical directed traversals in the saved 08:00–09:00 HBW model, shown in EPSG:26917. This is the retained model graph, not a claim to draw every road in the source archive. Virtual movements are excluded; colour has no traffic meaning. © OpenStreetMap contributors / ODbL. Reciprocal directed arcs can share geometry; no assigned flow is encoded. This drawing uses the frozen run\_001 evidence. Later supplementary datasets are separate and are not implied to have entered this scenario.

</details>

[PNG](<../assets/figure-contract-r11/figures/pittsburgh/sources.png>) · [SVG](<../assets/figure-contract-r11/figures/pittsburgh/sources.svg>) · [PDF](<../assets/figure-contract-r11/figures/pittsburgh/sources.pdf>) · [Source record](<../assets/figure-contract-r11/figures/pittsburgh/sources.source.json>)

<a id="figure-r3-population"></a>

##### Population and household inputs

[![Population and household inputs](<../assets/figure-contract-r11/figures/pittsburgh/population.svg>)](<../assets/figure-contract-r11/figures/pittsburgh/population.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

Selected 2020 blocks grouped by tract ID; not whole-tract totals. All 41 zones are retained; population total 71,684. Occupied units total 32,432. Missing household fields are unknown, not zero. Census/ACS allocation is an input, not a simulated traffic quantity. This drawing uses the frozen run\_001 evidence. Later supplementary datasets are separate and are not implied to have entered this scenario.

</details>

[PNG](<../assets/figure-contract-r11/figures/pittsburgh/population.png>) · [SVG](<../assets/figure-contract-r11/figures/pittsburgh/population.svg>) · [PDF](<../assets/figure-contract-r11/figures/pittsburgh/population.pdf>) · [Source record](<../assets/figure-contract-r11/figures/pittsburgh/population.source.json>)

<a id="figure-r3-transit"></a>

##### Transit source geography

[![Transit source geography](<../assets/figure-contract-r11/figures/pittsburgh/transit.svg>)](<../assets/figure-contract-r11/figures/pittsburgh/transit.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

Earlier bounded preflight stop tags; no timetable. 109 saved stop records. Stop tags and road proximity do not prove legal walk access or operating service. The frozen scenario has no accepted service-day transit paths; no zero-demand transit bar is implied. The gray retained road graph is geographic context, not a transit route model. Source stops and route shapes do not establish legal pedestrian access, operating service, or observed ridership. This drawing uses the frozen run\_001 evidence. Later supplementary datasets are separate and are not implied to have entered this scenario.

</details>

[PNG](<../assets/figure-contract-r11/figures/pittsburgh/transit.png>) · [SVG](<../assets/figure-contract-r11/figures/pittsburgh/transit.svg>) · [PDF](<../assets/figure-contract-r11/figures/pittsburgh/transit.pdf>) · [Source record](<../assets/figure-contract-r11/figures/pittsburgh/transit.source.json>)

<a id="generation"></a>

## 01 / Trip generation

<a id="coverage-row-06"></a>

A transferred HBW rate of 1.90 person trips per occupied unit per day is combined with an assumed 25% share for the morning hour. Applied to 32,432 occupied units, this gives 15,405.2 scenario person trips. The rate is linked to the accepted Boston regional-demand reference; Pittsburgh observations did not estimate it.

The scalar capture and intrazonal proxies leave 10,971.681175065 external or uncaptured persons, 425.972216078 intrazonal persons and 4,007.546608857 internal interzonal persons. Attractions are normalized from local workplace-job weights to this last total. The updated generation graphic shows all 41 selected-block tract-ID zones by production and attraction, alongside the full demand ledger. An employment-rich area can attract many modeled trips without treating every regional worker as a resident-generated trip.

<a id="figure-fs-g01"></a>

##### Trip generation and demand accounting

[![Trip generation and demand accounting](<../assets/figure-contract-r11/figures/pittsburgh/generation.svg>)](<../assets/figure-contract-r11/figures/pittsburgh/generation.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

All 41 zones; 08:00–09:00 HBW. The left panel shows saved interzonal productions/attractions. The right panel accounts for all generated persons, including excluded and intrazonal components. No top-12 truncation. Scenario assumptions, not measured trip counts. External and intrazonal components do not enter interzonal assignment; attractions are normalized to productions. This drawing uses the frozen run\_001 evidence. Later supplementary datasets are separate and are not implied to have entered this scenario.

</details>

[PNG](<../assets/figure-contract-r11/figures/pittsburgh/generation.png>) · [SVG](<../assets/figure-contract-r11/figures/pittsburgh/generation.svg>) · [PDF](<../assets/figure-contract-r11/figures/pittsburgh/generation.pdf>) · [Source record](<../assets/figure-contract-r11/figures/pittsburgh/generation.source.json>)

<a id="distribution"></a>

## 02 / Trip distribution

<a id="coverage-row-07"></a>

Free-flow drive impedance on the declared turn-expanded graph enters exp(−0.08 × minutes). The 0.08 min⁻¹ coefficient is transferred from the Boston method and is not locally fitted. IPF reaches a maximum margin residual of 1.616832407×10⁻⁶ persons in four iterations.

The frozen morning direction is 100% forward and 0% reverse. This convention conserves the 4,007.546608857 PA total in directed OD; it does not claim that reverse commuting is absent in reality. Of 1,640 potential ordered interzonal pairs, 1,406 have positive demand once zero margins are accounted for. Every positive drive pair has a route on the declared graph.

The updated heatmap uses the complete input order of all 41 model zones. Zones tract2020\_42003080900 and tract2020\_42003241300 have no positive OD entries, so their zero rows and columns are explicitly retained. The earlier positive-only index contained 39 IDs. Zero margins are model results, not missing data. The log(1 + persons) scale is a presentation transform only.

<a id="figure-fs-d01"></a>

##### Trip distribution and directed OD margins

[![Trip distribution and directed OD margins](<../assets/figure-contract-r11/figures/pittsburgh/distribution.svg>)](<../assets/figure-contract-r11/figures/pittsburgh/distribution.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

Full 41×41 model-zone matrix including zero cells; 1406 positive OD pairs and 4,007.546608857 persons in 08:00–09:00 HBW. Colours are log(1+persons); margins are untransformed directed OD totals after PA direction. Every model zone is retained. Zero rows and columns remain visible; intrazonal cells are structural zeros. Labels use the final six digits of long zone IDs. This drawing uses the frozen run\_001 evidence. Later supplementary datasets are separate and are not implied to have entered this scenario.

</details>

[PNG](<../assets/figure-contract-r11/figures/pittsburgh/distribution.png>) · [SVG](<../assets/figure-contract-r11/figures/pittsburgh/distribution.svg>) · [PDF](<../assets/figure-contract-r11/figures/pittsburgh/distribution.pdf>) · [Source record](<../assets/figure-contract-r11/figures/pittsburgh/distribution.source.json>)

<a id="mode"></a>

## 03 / Mode choice

<a id="coverage-row-04"></a>

<a id="coverage-row-08"></a>

Driving follows the same declared road topology; walking follows eligible OSM links where a route exists. Walking assumes 4.8 km/h and one minute of access. Driving adds four access minutes, USD 2 parking and USD 0.20 per routed kilometre. With USD 20/hour value of time, zero alternative constants and utility slope −0.07 per generalized minute, costs vary by OD rather than applying one fixed modal split.

Walking is unavailable on 114 of the 1,640 possible interzonal pairs, including 105 positive-demand pairs. Driving covers every positive OD, so all internal interzonal persons have an available alternative. The result is approximately 3,138.9 drive persons (78.3%) and 868.6 walk persons (21.7%). Occupancy 1.2 converts driving once to 2,615.767323562 vehicles, with PCE factor one. Pedestrian capacity is not modeled.

Transit is Not modelled. The existence of Pittsburgh Regional Transit is not in doubt; the bounded case lacks the accepted timetable/path input needed for a cost-based alternative. OSM stop and route references cannot substitute for that input. The two-mode result is therefore incomplete for broader transport-policy interpretation even though its implemented choice calculation passes verification.

<a id="figure-fs-m01"></a>

##### Mode choice: demand, cost and availability

[![Mode choice: demand, cost and availability](<../assets/figure-contract-r11/figures/pittsburgh/mode.svg>)](<../assets/figure-contract-r11/figures/pittsburgh/mode.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

Saved OD-specific choice in 08:00–09:00 HBW; sums over every positive-demand OD. Persons, person-weighted generalized minutes, and available OD counts have separate axes. Transit is not modeled; no zero bar is shown. Generalized cost includes model time and money terms. Person totals precede the separate occupancy-to-PCE conversion. This drawing uses the frozen run\_001 evidence. Later supplementary datasets are separate and are not implied to have entered this scenario.

</details>

[PNG](<../assets/figure-contract-r11/figures/pittsburgh/mode.png>) · [SVG](<../assets/figure-contract-r11/figures/pittsburgh/mode.svg>) · [PDF](<../assets/figure-contract-r11/figures/pittsburgh/mode.pdf>) · [Source record](<../assets/figure-contract-r11/figures/pittsburgh/mode.source.json>)

<a id="assignment"></a>

## 04 / Physical-link assignment

<a id="coverage-row-09"></a>

The final network has 17,534 physical auto traversal arcs and 38,850 virtual movement arcs, totaling 56,384 arcs on 35,068 solver nodes. A physical road gets one BPR traversal regardless of how many upstream movements enter it. Road maps exclude the movement arcs, preventing fictitious duplication of road geometry.

Zone loading uses 41 distinct OUT-state physical-link-end points in the retained connected graph. The origin state's convention omits travel time and distance on the first physical link and charges subsequent traversals. This can matter for short OD pairs and must remain explicit. It cannot be changed to upstream loading, or subtracted a second time, during presentation.

OSM supplies speed tags for 6,999 physical links and usable lane totals for 7,280. Engineering speed proxies cover 10,535 links and lane/capacity proxies another 10,254. Capacities are expressed in PCE per modeled hour; BPR uses α=0.15 and β=4. The source records 140 bridge-tagged links, eighteen tunnel-tagged links and 188 with nonzero layer. Topology, not a line crossing, determines connectivity; a shared source node may still form a legitimate ramp junction across differing layer tags.

The restriction source contains 214 relations. The adapter handles 124 node-turn restrictions, applies five conservative final-exit closures for via-way cases and quarantines known ways associated with six malformed active relations. Sixty-three relations have no drivable movement in the filtered graph; eleven no\_turn\_on\_red relations are phase-dependent rather than universal turn bans. Relevant weekday-AM conditions are considered. Recorded checks find 109 prohibited-pair exclusions and 23 only-turn exclusions, with none of those forbidden arcs surviving. Conservative handling can also remove permissible alternatives and does not replace checking current street signs.

All 1,406 positive vehicle OD pairs are loaded. The saved initial gap is 4.773992564434884×10⁻⁷; the earlier receiver's independent full-graph value is 4.773992537349287×10⁻⁷. Both are below the frozen 10⁻⁴ threshold, so there are zero FW updates. The objective is 12,081.066645895 PCE-min. Path projection reproduces physical-link flows, 4,971 physical links carry positive demand and maximum v/c is 0.924094112.

The updated FS\_A01 places physical-flow and v/c maps side by side, using the same saved solution. Loading-detail charts use physical roads, and FS\_A02 presents the actual initial gap with its threshold. Static soft-capacity BPR allows ratios above one in principle; the low result here is conditional on the internal-demand-only scenario, not measured congestion.

<a id="figure-r9-fw-physical-flow"></a>

##### Frank–Wolfe: physical flow and distribution

[![Frank–Wolfe: physical flow and distribution](<../assets/figure-contract-r11/figures/pittsburgh/fw-physical-flow.svg>)](<../assets/figure-contract-r11/figures/pittsburgh/fw-physical-flow.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

Saved Pittsburgh static Frank–Wolfe endpoint for 08:00–09:00 HBW. The map and 22-bin histogram use the same complete 17,534-link physical-flow vector, including 12,563 exact-zero links; 4,971 links exceed 1e-6 PCE. Flow is PCE accumulated during the declared one-hour period, not persons or flow per simulation time step. The map uses a square-root sequential color scale with original-unit ticks and gray road context; histogram counts are linear and no links are omitted. Turn, access and other nonphysical solver arcs are excluded. Only the saved iteration-0 initialization exists; FW performed zero subsequent updates. Reciprocal directed arcs may overlap geometrically; flows are not summed. This full saved static case is distinct from the separate S72 and T4 method-transfer instances. This is a modeled engineering scenario, not observed traffic. © OpenStreetMap contributors / ODbL 1.0. R11 layout repair: map and all-link histogram share measured top and bottom panel bounds. The original saved physical-link IDs, exact flow vector, geographic vertices, display offsets, histogram edges and counts remain unchanged.

</details>

[PNG](<../assets/figure-contract-r11/figures/pittsburgh/fw-physical-flow.png>) · [SVG](<../assets/figure-contract-r11/figures/pittsburgh/fw-physical-flow.svg>) · [PDF](<../assets/figure-contract-r11/figures/pittsburgh/fw-physical-flow.pdf>) · [Source record](<../assets/figure-contract-r11/figures/pittsburgh/fw-physical-flow.source.json>)

<details markdown="1">
<summary>Saved initial checks and original endpoint views</summary>

<a id="figure-fs-a01"></a>

</details>

<a id="figure-fs-a03"></a>

##### Frank–Wolfe: physical-road loading

[![Frank–Wolfe: physical-road loading](<../assets/figure-contract-r11/figures/pittsburgh/pittsburgh-fs_a03.svg>)](<../assets/figure-contract-r11/figures/pittsburgh/pittsburgh-fs_a03.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

All used physical links are shown, excluding virtual turn arcs. Points retain the saved PCE, v/c and BPR segment travel time. The OUT-state convention omits the first physical link when loading a path; the figure does not alter that endpoint convention. Single-pass engineering scenario; no local empirical calibration. 4,971 used physical links · maximum v/c = 0.924094

</details>

[PNG](<../assets/figure-contract-r11/figures/pittsburgh/pittsburgh-fs_a03.png>) · [SVG](<../assets/figure-contract-r11/figures/pittsburgh/pittsburgh-fs_a03.svg>) · [PDF](<../assets/figure-contract-r11/figures/pittsburgh/pittsburgh-fs_a03.pdf>) · [Source record](<../assets/figure-contract-r11/figures/pittsburgh/pittsburgh-fs_a03.source.json>)

<a id="results"></a>

## Saved results and assignment checks

<a id="coverage-row-10"></a>

R3 saved-result replay passed for Pittsburgh. The fresh-solve and independent full-graph acceptance comes from earlier receiver evidence for these unchanged identities, which R3 reuses explicitly. The receiver did not substitute a previous preflight, Boston or Hong Kong result.

Checks cover generation units and boundaries, IPF margins and zero structure, PA direction, OD availability and probability, person-to-PCE conversion, physical/virtual path reconstruction, BPR objective, node conservation and shortest-path gap. Earlier fresh and saved outputs differ only within reported floating-point tolerance. Six corrupted copies were rejected, including rehashed OD or probability changes, unknown zone/link references and deletion of a new result despite a historical result being present.

<details markdown="1">
<summary>Saved initial checks and original endpoint views</summary>

<a id="figure-fs-a02"></a>

##### Frank–Wolfe: the saved initial check

<a id="table-r11-pittsburgh-initial-fw"></a>

[![Frank–Wolfe: the saved initial check](<../assets/figure-contract-r12/figures/pittsburgh/pittsburgh-initial-fw.svg>)](<../assets/figure-contract-r12/figures/pittsburgh/pittsburgh-initial-fw.svg>)

Only the actual saved iteration 0 is shown: objective 12081.0666458954 PCE·min/h and relative gap 4.77399256443488e-07, against the unchanged 0.0001 stopping gate. There were zero updates. Each panel contains a single numerical point; no missing trajectory or second state is inferred. The companion physical-flow map reads this method’s own saved vector. This frozen original demand instance is not relabelled as a later selected-demand or transit-revision run.

[SVG](<../assets/figure-contract-r12/figures/pittsburgh/pittsburgh-initial-fw.svg>) · [PNG](<../assets/figure-contract-r12/figures/pittsburgh/pittsburgh-initial-fw.png>) · [PDF](<../assets/figure-contract-r12/figures/pittsburgh/pittsburgh-initial-fw.pdf>) · [Source data](<../assets/figure-contract-r12/figures/pittsburgh/pittsburgh-initial-fw.source.json>)

</details>

<a id="parity-pittsburgh-static-inputs"></a>

## Static assignment: demand margins and physical endpoints

<a id="figure-parity-pittsburgh-assignment-margins"></a>

##### Static assignment demand margins

[![Static assignment demand margins](<../assets/template-parity-20261008/static-inputs/pittsburgh/assignment-margins.svg>)](<../assets/template-parity-20261008/static-inputs/pittsburgh/assignment-margins.svg>)

Pittsburgh S72: origin and destination margins from the exact frozen 72-OD vehicle-demand table, after its existing person-to-vehicle conversion. Each map sums to 149.921423895065 PCE/h; all 41 model zones remain, including zero selected margins. Both panels use the same square-root colour normalization with original-unit ticks. The source-zone ledger is joined exactly to actual prepared node OD rows, rather than to person-trip generation or all-mode distribution. This S72 selection is separate from the original 1,406-OD city assignment; unselected OD is not added. The source polygons are saved selected-block groups by tract ID, not full-tract population regions. All saved road geometry is retained as pale context and clipped only at the common display viewport. These are model inputs, not observed travel or an optimization trajectory. Private local derivative; no new public release is claimed. © OpenStreetMap contributors, ODbL 1.0; source-zone geography as documented in the frozen case.

[Complete evidence · same figure](<#figure-parity-pittsburgh-assignment-margins>) · [SVG](<../assets/template-parity-20261008/static-inputs/pittsburgh/assignment-margins.svg>) · [PNG](<../assets/template-parity-20261008/static-inputs/pittsburgh/assignment-margins.png>) · [PDF](<../assets/template-parity-20261008/static-inputs/pittsburgh/assignment-margins.pdf>) · [Plot data](<../assets/template-parity-20261008/static-inputs/pittsburgh/assignment-margins.plot.json>) · [Source record](<../assets/template-parity-20261008/static-inputs/pittsburgh/assignment-margins.source.json>) · [Caption](<../assets/template-parity-20261008/static-inputs/pittsburgh/assignment-margins.caption.md>)

<a id="figure-parity-pittsburgh-assignment-endpoints"></a>

##### Physical demand endpoints

[![Physical demand endpoints](<../assets/template-parity-20261008/static-inputs/pittsburgh/assignment-endpoints.svg>)](<../assets/template-parity-20261008/static-inputs/pittsburgh/assignment-endpoints.svg>)

Pittsburgh S72: the exact prepared 72-OD demand is aggregated only for display at its real origin and destination loading nodes, with 34 positive origin nodes and 34 positive destination nodes. Each side sums to 149.921423895065 PCE/h. Light open circles retain all 41 saved model access nodes; filled markers share a square-root colour scale, while fixed marker area does not add another quantity. Every solver OUT:link\_id maps to the end coordinate of that directed physical road, not its midpoint or IN state. This preserves the frozen OUT-state loading convention, which omits the origin-link traversal; no repair or new interpretation is applied. Both panels use identical geographic extent and road/zone context. The demand table, zone-access ledger and network instance hashes were checked together. These are engineering loading points, not observed trip ends or parcel entrances. Private local derivative; no new public release is claimed. © OpenStreetMap contributors, ODbL 1.0.

[Complete evidence · same figure](<#figure-parity-pittsburgh-assignment-endpoints>) · [SVG](<../assets/template-parity-20261008/static-inputs/pittsburgh/assignment-endpoints.svg>) · [PNG](<../assets/template-parity-20261008/static-inputs/pittsburgh/assignment-endpoints.png>) · [PDF](<../assets/template-parity-20261008/static-inputs/pittsburgh/assignment-endpoints.pdf>) · [Plot data](<../assets/template-parity-20261008/static-inputs/pittsburgh/assignment-endpoints.plot.json>) · [Source record](<../assets/template-parity-20261008/static-inputs/pittsburgh/assignment-endpoints.source.json>) · [Caption](<../assets/template-parity-20261008/static-inputs/pittsburgh/assignment-endpoints.caption.md>)

<a id="parity-pittsburgh-construction"></a>

## Time-expanded network and path examples

<a id="figure-parity-pittsburgh-time-layers"></a>

##### Time-expanded network in layers

[![Time-expanded network in layers](<../assets/template-parity-20261008/construction/pittsburgh/time-layers.svg>)](<../assets/template-parity-20261008/construction/pittsburgh/time-layers.svg>)

Pittsburgh: selected time layers 40–44 use 30 seconds per time step. Every arrow is an actual saved arc; only node-time states occurring as saved endpoints are drawn. The highlighted continuous chain is selected from saved construction records to explain incidence; it is not an optimized or observed trajectory. State aliases: A− = IN:36, A+ = OUT:36, B− = IN:37, B+ = OUT:37. Pale arrows show other saved arcs in this local slice. Time planes and horizontal placement are schematic; this is neither a full graph nor observed traffic. Roads 36 and 37 are opposite directions of the same physical segment; their routing entry/exit states remain distinct. The saved zero-time turn is a structural input arc, not a claim that an optimized route performs this turn. Origin loading elsewhere starts at OUT state; no change to that historical model convention.

[Complete evidence · same figure](<#figure-parity-pittsburgh-time-layers>) · [SVG](<../assets/template-parity-20261008/construction/pittsburgh/time-layers.svg>) · [PNG](<../assets/template-parity-20261008/construction/pittsburgh/time-layers.png>) · [PDF](<../assets/template-parity-20261008/construction/pittsburgh/time-layers.pdf>) · [Plot data](<../assets/template-parity-20261008/construction/pittsburgh/time-layers.plot.json>) · [Source record](<../assets/template-parity-20261008/construction/pittsburgh/time-layers.source.json>) · [Caption](<../assets/template-parity-20261008/construction/pittsburgh/time-layers.caption.md>)

<a id="figure-parity-pittsburgh-local-details"></a>

##### Local construction details

[![Local construction details](<../assets/template-parity-20261008/construction/pittsburgh/local-details.svg>)](<../assets/template-parity-20261008/construction/pittsburgh/local-details.svg>)

Pittsburgh: the physical road chain is mapped to routing entry/exit states and then to exact time-indexed arcs in the saved construction slice. Panel c contains all 26 retained arcs, with exact endpoint times; strong teal/blue highlights the same continuous chain used in the companion layered figure. The highlighted continuous chain is selected from saved construction records to explain incidence; it is not an optimized or observed trajectory. All layout coordinates are schematic. Source/sink terminal bookkeeping is outside this excerpt and must not be read as road travel or waiting. Roads 36 and 37 are opposite directions of the same physical segment; their routing entry/exit states remain distinct. The saved zero-time turn is a structural input arc, not a claim that an optimized route performs this turn. Origin loading elsewhere starts at OUT state; no change to that historical model convention.

[Complete evidence · same figure](<#figure-parity-pittsburgh-local-details>) · [SVG](<../assets/template-parity-20261008/construction/pittsburgh/local-details.svg>) · [PNG](<../assets/template-parity-20261008/construction/pittsburgh/local-details.png>) · [PDF](<../assets/template-parity-20261008/construction/pittsburgh/local-details.pdf>) · [Plot data](<../assets/template-parity-20261008/construction/pittsburgh/local-details.plot.json>) · [Source record](<../assets/template-parity-20261008/construction/pittsburgh/local-details.source.json>) · [Caption](<../assets/template-parity-20261008/construction/pittsburgh/local-details.caption.md>)

<a id="parity-pittsburgh-finite"></a>

## Optimization on the time-expanded network

<a id="figure-parity-pittsburgh-cg-phase1"></a>

##### Phase I: artificial-flow clearance

[![Phase I: artificial-flow clearance](<../assets/template-parity-20261008/optimization/pittsburgh/cg-phase1.svg>)](<../assets/template-parity-20261008/optimization/pittsburgh/cg-phase1.svg>)

The sole saved Phase I restricted-master solution contains four path-flow variables followed by 233 nonnegative artificial capacity-slack variables. They relax shared physical-arc capacity rows; this model has no commodity-level artificial-flow variables. Both panels use the saved state directly: the total is exactly 0 PCE and every one of the 233 capacity slacks is exactly zero. Panel b preserves the complete saved capacity-row order; plot data link each row to its original dynamic-arc index and ID. The dotted line is the original 1e−8 PCE tolerance on total artificial slack; the heatmap uses 0 to that same value only as its color reference. Four input-cost seed paths already satisfy the bounded instance. A single recorded solve is shown without an invented multi-round trajectory. Phase I capacity feasibility remains separate from Phase II real cost and independent full-DAG pricing. Private local derivative of the saved numerical state; no new public asset release or optimizer run is claimed.

[Complete evidence · same figure](<#figure-parity-pittsburgh-cg-phase1>) · [SVG](<../assets/template-parity-20261008/optimization/pittsburgh/cg-phase1.svg>) · [PNG](<../assets/template-parity-20261008/optimization/pittsburgh/cg-phase1.png>) · [PDF](<../assets/template-parity-20261008/optimization/pittsburgh/cg-phase1.pdf>) · [Plot data](<../assets/template-parity-20261008/optimization/pittsburgh/cg-phase1.plot.json>) · [Source record](<../assets/template-parity-20261008/optimization/pittsburgh/cg-phase1.source.json>) · [Caption](<../assets/template-parity-20261008/optimization/pittsburgh/cg-phase1.caption.md>)

<a id="figure-parity-pittsburgh-cg-phase2"></a>

##### Phase II objective

[![Phase II objective](<../assets/figure-contract-r12/figures/pittsburgh/cg-phase2.svg>)](<../assets/figure-contract-r12/figures/pittsburgh/cg-phase2.svg>)

One actual saved Phase II round. CG real cost is 0.24793241990274609 PCE·min; the separate same-graph LP reference is 0.24793241990274612 PCE·min. The marker and dashed reference can coincide at displayed precision. No Phase I artificial objective is connected to this real-cost objective. No new column after the four seed paths.

[Complete evidence · same figure](<#figure-parity-pittsburgh-cg-phase2>) · [SVG](<../assets/figure-contract-r12/figures/pittsburgh/cg-phase2.svg>) · [PNG](<../assets/figure-contract-r12/figures/pittsburgh/cg-phase2.png>) · [PDF](<../assets/figure-contract-r12/figures/pittsburgh/cg-phase2.pdf>) · [Plot data](<../assets/figure-contract-r12/figures/pittsburgh/cg-phase2.plot.json>) · [Source record](<../assets/figure-contract-r12/figures/pittsburgh/cg-phase2.source.json>)

<a id="figure-parity-pittsburgh-cg-pricing"></a>

##### Independent pricing closure

[![Independent pricing closure](<../assets/figure-contract-r12/figures/pittsburgh/cg-pricing.svg>)](<../assets/figure-contract-r12/figures/pittsburgh/cg-pricing.svg>)

The saved full-DAG pricing check is zero in both phases, against the frozen absolute tolerance 1e-7. Phase I reduced cost is dimensionless; Phase II reduced cost is minutes, so they have separate axes. Each phase has one actual round, four seed paths, and no new columns. Public data contain the global minimum per phase, not separate per-demand minima; no per-demand bars are fabricated.

[Complete evidence · same figure](<#figure-parity-pittsburgh-cg-pricing>) · [SVG](<../assets/figure-contract-r12/figures/pittsburgh/cg-pricing.svg>) · [PNG](<../assets/figure-contract-r12/figures/pittsburgh/cg-pricing.png>) · [PDF](<../assets/figure-contract-r12/figures/pittsburgh/cg-pricing.pdf>) · [Plot data](<../assets/figure-contract-r12/figures/pittsburgh/cg-pricing.plot.json>) · [Source record](<../assets/figure-contract-r12/figures/pittsburgh/cg-pricing.source.json>)

<a id="figure-parity-pittsburgh-lr-bounds"></a>

##### Lagrangian bounds and certified gap

[![Lagrangian bounds and certified gap](<../assets/figure-contract-r12/figures/pittsburgh/lr-bounds.svg>)](<../assets/figure-contract-r12/figures/pittsburgh/lr-bounds.svg>)

One actual LR iteration. Best valid lower is 0.2479324199027457 PCE·min; own recovered feasible upper is 0.2479324199027457 PCE·min. The certified gap is max(0,(U−L)/max(1,|U|)) = 0; the frozen gate is 1%. Lower and upper are separate markers at the same recorded iteration; they coincide to displayed precision. Tiny signed floating-point differences remain in the plot data. Capacities are nonbinding in this T4 pulse; this does not prove that city area caused the short trace.

[Complete evidence · same figure](<#figure-parity-pittsburgh-lr-bounds>) · [SVG](<../assets/figure-contract-r12/figures/pittsburgh/lr-bounds.svg>) · [PNG](<../assets/figure-contract-r12/figures/pittsburgh/lr-bounds.png>) · [PDF](<../assets/figure-contract-r12/figures/pittsburgh/lr-bounds.pdf>) · [Plot data](<../assets/figure-contract-r12/figures/pittsburgh/lr-bounds.plot.json>) · [Source record](<../assets/figure-contract-r12/figures/pittsburgh/lr-bounds.source.json>)

<a id="figure-parity-pittsburgh-lr-prices"></a>

##### Capacity prices at the best dual bound

[![Capacity prices at the best dual bound](<../assets/template-parity-20261008/optimization/pittsburgh/lr-prices.svg>)](<../assets/template-parity-20261008/optimization/pittsburgh/lr-prices.svg>)

The saved best-bound multiplier vector contains 1,811,888 original dynamic-arc entries, all exactly zero. Consequently there is no nonempty top-price ranking. The second panel sums every timed multiplier by its real 30-second departure index, including the zero sums; source/sink entries without a time suffix are excluded only from the time aggregation. Empty positive support is shown explicitly, not replaced with another city or method. These numerical details remain a private local preview.

[Complete evidence · same figure](<#figure-parity-pittsburgh-lr-prices>) · [SVG](<../assets/template-parity-20261008/optimization/pittsburgh/lr-prices.svg>) · [PNG](<../assets/template-parity-20261008/optimization/pittsburgh/lr-prices.png>) · [PDF](<../assets/template-parity-20261008/optimization/pittsburgh/lr-prices.pdf>) · [Plot data](<../assets/template-parity-20261008/optimization/pittsburgh/lr-prices.plot.json>) · [Source record](<../assets/template-parity-20261008/optimization/pittsburgh/lr-prices.source.json>) · [Caption](<../assets/template-parity-20261008/optimization/pittsburgh/lr-prices.caption.md>)

<a id="figure-parity-pittsburgh-lr-recovery"></a>

##### Path-pool growth and primal recovery

[![Path-pool growth and primal recovery](<../assets/template-parity-20261008/optimization/pittsburgh/lr-recovery.svg>)](<../assets/template-parity-20261008/optimization/pittsburgh/lr-recovery.svg>)

One actual path-pool record and one actual feasible recovery call are shown in separate panels. The four paths belong to this method’s own pool; the objective is the saved recovered feasible upper bound. No intermediate call, pool growth or capacity-price effect is invented. A filled marker denotes a feasible call, as in Boston/Hong Kong.

[Complete evidence · same figure](<#figure-parity-pittsburgh-lr-recovery>) · [SVG](<../assets/template-parity-20261008/optimization/pittsburgh/lr-recovery.svg>) · [PNG](<../assets/template-parity-20261008/optimization/pittsburgh/lr-recovery.png>) · [PDF](<../assets/template-parity-20261008/optimization/pittsburgh/lr-recovery.pdf>) · [Plot data](<../assets/template-parity-20261008/optimization/pittsburgh/lr-recovery.plot.json>) · [Source record](<../assets/template-parity-20261008/optimization/pittsburgh/lr-recovery.source.json>) · [Caption](<../assets/template-parity-20261008/optimization/pittsburgh/lr-recovery.caption.md>)

<a id="reproduction"></a>

## Reproduction and input identity

Current S0 reception and the released algorithm figures are integrated in [the current method record](<#algorithm-transfer-r2>). [Public reception summary](<../assets/algorithm-transfer-r8/CURRENT_STATUS.json>) · [Source and scope notice](<../assets/algorithm-transfer-r8/NOTICE.md>). Private solver inputs, checkpoints and complete compute archives are outside this figure release.

<a id="coverage-row-19"></a>

The public reproducibility archive is not yet available.

Runtime versions above are recorded producer facts. The V presentation task does not replace or upgrade the frozen numerical environment.

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

The model has no demand-congestion feedback cycle or dynamic loading. External entering commuters, freight, commercial traffic, deliveries and non-HBW purposes are outside the assigned matrix. LODES separately reports 82,644 Pennsylvania-resident job relationships entering the rectangle and 2,652 from outside Pennsylvania; neither statistic supplies an hourly inbound trip estimate. Their presence in reference data must not be advertised as assigned incoming traffic.

Missing local counts, behavioral calibration, transit paths and independent traffic observations constrain interpretation. Speed and capacity proxies affect more than half the physical links, and conservative via-way closures can distort alternatives. A map of accepted model flow is therefore unsuitable as a claim about total observed road traffic.

The declared OUT-state loading and selected-block aggregation remain visible. The updated OD matrix displays all 41 zones, including the two zones without positive OD entries. Archived scope, receipts, command records and full tables preserve those conventions. Source acknowledgments cover Census, LEHD LODES and © OpenStreetMap contributors under ODbL; only the separately allowed derived content enters the preview.

The smaller preflight included source, grade-separation, GPS and image investigations, but they are not newly validated observations of the four-stage demand. This presentation carries forward their boundary as context while excluding raw trajectories and unlisted photographs. No campus population survey or current route observation was created by the static calculation.

<a id="sources"></a>

## Sources and display provenance

- [2020 Census P.L. 94-171 data](<https://www.census.gov/programs-surveys/decennial-census/about/rdo/summary-files.html>)
- [2023 LODES Workplace Area Characteristics file](<https://lehd.ces.census.gov/data/lodes/LODES8/pa/wac/pa_wac_S000_JT00_2023.csv.gz>)
- [Census LODES documentation](<https://lehd.ces.census.gov/data/lodes/LODES8/LODESTechDoc8.3.pdf>)
- [OpenStreetMap](<https://www.openstreetmap.org/copyright>)
- [CTPS TDM23.2.0 household trip summaries](<https://ctps.org/pub/tdm23_sc/tdm23.2.0/tdm23_sensitivity.html>)
- [Census public data](<https://www.census.gov/data.html>)
- [LODES](<https://lehd.ces.census.gov/data/>)

[Return to the city atlas](<../index.html#pittsburgh>) · [Back to top](<#document-top>)

<a id="r3-method-transfer"></a>

<a id="algorithm-transfer-r2"></a>

## Pittsburgh East End 四阶段成果的算法迁移追加片段

Accepted S72 evidence includes FW, finite-path and Native26/52 through outer 14, preserving all 14 saved checks per rank. Their final original-OD residuals are 8.07013475568935e−8 and 2.6256443221356536e−7 PCE/h. The separate T4 exact-DAG LP, CG, LR and ADMM results remain accepted. Primal stopping quantities use PCE; rho-scaled dual stopping quantities use minutes.

<dl class="accepted-method-notes"><dt>S72 FW / finite</dt><dd>S0 ACCEPTED · 72 OD; 149.92142389506478 PCE/h. Shared objective 763.227941458126 PCE·min; zero FW updates.</dd><dt>T4 exact-DAG LP</dt><dd>Accepted · Complete reachable-domain primal/dual certificate; original conservation and capacity checks pass.</dd><dt>T CG / LR / ADMM</dt><dd>S0 ACCEPTED · Same tiny four-OD T4 pulse; capacities are nonbinding. ADMM has one actual outer step and independent cold-start confirmation.</dd><dt>Version-bound reception</dt><dd>v7 / 478 protected payloads · S0 checked the external v7 chain and preserved the embedded v6 / 477 receipt under its original identity.</dd><dt>PIT_T05 corrected display</dt><dd>S0 SINGLE-FIGURE RELEASE RECEIVED · Corrected primal/PCE and rho-scaled dual/min display, using the unchanged saved iteration-1 values. The original twelve released figure families and their method statuses remain unchanged.</dd></dl>

**Unit correction to the received prose.** The saved ADMM dual residual is 1.511×10⁻¹³ **min**, while primal residual is in PCE. The original prose’s PCE label is corrected here under the S0 single-figure notice; the value is unchanged. The corrected PIT\_T05 is now displayed in the ADMM section under the separate S0 single-figure release.

**版本与定位。** 本文是 Pittsburgh 既有四阶段城市大卷的独立追加片段，实验号 PITTSBURGH\_BERKELEY\_C2A\_TRANSFER\_R2\_20261006。旧 R2/R3 的 Trip Generation、Trip Distribution、Mode Choice、Traffic Assignment 接收状态不因本轮改变。本轮在旧 Stage 3 已产生的车辆 OD 和求解图上，检验静态 FW、finite、Native，以及同一有限时空图上的 LP、CG、LR、ADMM。East End 实例在前轮已经参与诊断；本次是工程算法迁移，不是未见城市 holdout、当地 GPS 速度或需求实测标定，也不是动态网络装载或动态用户均衡。文中的 ACCEPTED 仅指所列方法在冻结数值合同下通过核验。

<a id="algorithm-transfer-r2-section-1"></a>

### 1. 输入身份与装载语义

原场景为 Pittsburgh East End 2020 tract 范围的合成工作日 08:00—09:00 AM HBW drive/walk。R3 compute capsule 的 57 个文件逐个与 manifest 的 SHA-256 和字节数核对，六份沿用 R2 的核心源文件又与原件逐字节相同。41 个入口区、1,406 个正车辆 OD 和 2,615.767323562197 PCE/小时是全量背景；静态新试验只选 72 个 OD，需求 149.92142389506478 PCE/小时。Stage 3 数值已经是车辆 PCE，本轮没有再次除乘员率或乘车辆系数。原求解图含 17,534 条实体道路与 38,850 条非实体转向弧，合计 56,384 条 solver 弧。实体段记行程成本与容量，非实体 movement 保留原工程 epsilon，不能再复制路段长度、容量或强加 30 秒。

原 R2 从入口道路下游 OUT:origin 状态装载，第一条合法弧是从该 OUT 状态通向下一 IN 状态的转向弧；起点道路 P:origin 不在保存路径中。本轮对全部 1,406 条 R2 路径重放起点、方向、连续性及目的地，结果通过。S 与 T 沿用这个首段规则。把起点换成上游 IN:origin 会改变问题，本文没有求解该变体。仅作为诊断算术，将原保存路径补上起点实体段会增加 182.3435812275791 PCE·min 的流量加权自由流成本；它不是本轮优化结果。

<a id="released-pit-at00"></a>

<a id="algorithm-transfer-r2-section-2"></a>

### 2. 求解前固定的两个问题

方向可达的 1,406 个正 OD 按冻结网络哈希、起点、终点的 SHA-256 排序。静态 S72 取前 72，路径池对每个 OD 最多五条真实、合法、简单路径。候选池最终有 360 条路径，约束矩阵有 66,420 个非零关联，所有路径通过冻结公共核的独立回放。另一 T 问题先按输入资源估计十 OD 档，再依据预登记的 4 GiB 单重进程上限取前四条 OD；未选 OD 与其余十一个五分钟 bin 均留在选择账目中。T4 在首个五分钟 bin 的中点 08:02:30 施加 0.045027548453549955 PCE 脉冲，不将脉冲误称为实测 30 秒交通量。

T 的时间步长 30 秒，四条 OD 的取整最短时间为 54、102、33、32 步，出发步 5 加最长路 102 步和预留 10 步得到 H=117。原零时 movement 的 35,068 个状态有无环拓扑序。实际构建的时空图签名是 ecc72753a7afff8188eecdf95bb68fb207ffd9b36cfa566e65369fc40db55225，含 1,811,888 条时空弧：350,106 条实体行驶、779,805 条转向、681,742 条显式等待、4 条源连接和 231 条终端台账连接。终端零成本连接用于守恒，不代表车辆排队到 H。T 模型独立检查通过；所有 T 方法使用这个签名及相同成本、需求、实体映射。静态 Beckmann 目标与 T 固定成本目标虽然单位同为 PCE·min，但问题不同，不应互作性能排序。

<a id="released-pit-t01"></a>

<a id="pittsburgh-r3-input-construction-ledger"></a>

##### Time-expanded network: saved arc roles

<a id="table-r11-pittsburgh-t4-construction"></a>

[![Time-expanded network: saved arc roles](<../assets/figure-contract-r12/figures/pittsburgh/t4-arc-roles.svg>)](<../assets/figure-contract-r12/figures/pittsburgh/t4-arc-roles.svg>)

Counts come from the saved T4 construction: 350,106 physical-road arcs, 779,805 turn arcs, 681,742 wait arcs, 4 source connectors and 231 sink connectors. The model uses 30-second steps over 117 steps and four selected departure demands. This composition chart is a count summary, not a geometric reconstruction of the full time-expanded graph; the real road-network view remains separate.

[SVG](<../assets/figure-contract-r12/figures/pittsburgh/t4-arc-roles.svg>) · [PNG](<../assets/figure-contract-r12/figures/pittsburgh/t4-arc-roles.png>) · [PDF](<../assets/figure-contract-r12/figures/pittsburgh/t4-arc-roles.pdf>) · [Source data](<../assets/figure-contract-r12/figures/pittsburgh/t4-arc-roles.source.json>)

<a id="released-pit-t02"></a>

##### Four selected departure demands

<a id="table-r11-pittsburgh-t4-demand"></a>

[![Four selected departure demands](<../assets/figure-contract-r12/figures/pittsburgh/t4-input-demand.svg>)](<../assets/figure-contract-r12/figures/pittsburgh/t4-input-demand.svg>)

The four input-selected demands total 0.04502754845355 PCE. These are the bounded time-network departure pulses after the saved hourly-to-time factor 1/12, not hourly observed counts. Input commodities are not optimizer iterations. Full source/destination identities are retained in the public plot data.

[SVG](<../assets/figure-contract-r12/figures/pittsburgh/t4-input-demand.svg>) · [PNG](<../assets/figure-contract-r12/figures/pittsburgh/t4-input-demand.png>) · [PDF](<../assets/figure-contract-r12/figures/pittsburgh/t4-input-demand.pdf>) · [Source data](<../assets/figure-contract-r12/figures/pittsburgh/t4-input-demand.source.json>)

<a id="algorithm-transfer-r2-section-3"></a>

### 3. Accepted S72 static methods

#### FW and finite: accepted same-instance reference

原冻结 FW 实现首先在 1,800 秒守护预算内未产出解，保存了准确超时回执。任务内候选仅将相同 BPR 行成本计算向量化；独立小自检的目标求和差为 2.98×10⁻⁸，相对 2.34×10⁻¹⁶，逐弧成本完全一致。改用相对 1×10⁻¹⁰ 的该项自检尺度后，候选在原 AON 初始装载即满足既定停止门槛。冻结公共核对保存结果的全图相对 gap 为 6.405×10⁻¹⁵，逐 OD 和链路重建残差均为零；Beckmann 目标 763.227941458126 PCE·min。零次 FW 更新说明此 S72 档的初始装载已经足够，不能据此声称大规模拥堵加速。

冻结原 K=5 Yen 路径池也达到 1,800 秒守护时限。任务内 A\* oracle 维持 Yen 根、spur 和候选排序，在小 fixture 及本城一条真实 OD 的五条有序路径及成本上与原实现完全相同；全池生成后又由冻结 load\_pool 检验。非压缩 finite 在一轮内得到同一目标，独立全图相对 gap 1.490×10⁻¹⁵、池内 gap 5.958×10⁻¹⁵，OD 与链路重建误差为零。这是有限池的可重建性和该档数值一致性，不能代表其他需求档也同样简单。

<a id="figure-r9-pittsburgh-s72-fw-flow"></a>

##### Frank–Wolfe: physical-road flow and distribution

[![Frank–Wolfe: physical-road flow and distribution](<../assets/figure-contract-r11/figures/pittsburgh/pittsburgh-pittsburgh-s72-fw-flow.svg>)](<../assets/figure-contract-r11/figures/pittsburgh/pittsburgh-pittsburgh-s72-fw-flow.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

Frank–Wolfe on the frozen Pittsburgh S72 static instance: 72 directed OD, 149.92142389506472 PCE in the modeled hour, independent checked Beckmann objective 763.227941458126 PCE min and full-graph relative gap 6.405076187649018e-15 against the unchanged 1e-5 gate. The map and linear-count 22-bin histogram use all 17,534 physical traversal arc values from this method’s own complete 56,384-solver-link vector, joined exactly by P:physical\_link\_id to original geometry. Every physical link is drawn as a grey base road, while the constant-width colored overlay includes only flow greater than 1e-12 PCE/hour. Exact and near-zero values remain unchanged in the all-link histogram and plot data; the 38,850 turn arcs are excluded from map and histogram. Both method views use identical absolute flow color limits and histogram bins. FW initial loading passed; zero FW updates. The finite endpoint is not synthesized from the FW vector. S72 excludes the original city case’s other 1,334 OD; it must not be merged with that 1,406-OD experiment. The original OUT-state loading omits the origin-link traversal and is preserved. A static endpoint map/distribution does not depict convergence speed. Modeled scenario, not observed traffic. Local saved-result derivative; no new S0 release claimed.

</details>

[PNG](<../assets/figure-contract-r11/figures/pittsburgh/pittsburgh-pittsburgh-s72-fw-flow.png>) · [SVG](<../assets/figure-contract-r11/figures/pittsburgh/pittsburgh-pittsburgh-s72-fw-flow.svg>) · [PDF](<../assets/figure-contract-r11/figures/pittsburgh/pittsburgh-pittsburgh-s72-fw-flow.pdf>) · [Source record](<../assets/figure-contract-r11/figures/pittsburgh/pittsburgh-pittsburgh-s72-fw-flow.source.json>)

<a id="figure-r9-pittsburgh-s72-finite-flow"></a>

##### Finite-path: physical-road flow and distribution

[![Finite-path: physical-road flow and distribution](<../assets/figure-contract-r11/figures/pittsburgh/pittsburgh-pittsburgh-s72-finite-flow.svg>)](<../assets/figure-contract-r11/figures/pittsburgh/pittsburgh-pittsburgh-s72-finite-flow.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

Finite-path on the frozen Pittsburgh S72 static instance: 72 directed OD, 149.92142389506472 PCE in the modeled hour, independent checked Beckmann objective 763.227941458126 PCE min and full-graph relative gap 1.4895526017788486e-15 against the unchanged 1e-5 gate. The map and linear-count 22-bin histogram use all 17,534 physical traversal arc values from this method’s own complete 56,384-solver-link vector, joined exactly by P:physical\_link\_id to original geometry. Every physical link is drawn as a grey base road, while the constant-width colored overlay includes only flow greater than 1e-12 PCE/hour. Exact and near-zero values remain unchanged in the all-link histogram and plot data; the 38,850 turn arcs are excluded from map and histogram. Both method views use identical absolute flow color limits and histogram bins. Own 360-path finite solution; one recorded SLSQP iteration. The finite endpoint is not synthesized from the FW vector. S72 excludes the original city case’s other 1,334 OD; it must not be merged with that 1,406-OD experiment. The original OUT-state loading omits the origin-link traversal and is preserved. A static endpoint map/distribution does not depict convergence speed. Modeled scenario, not observed traffic. Local saved-result derivative; no new S0 release claimed.

</details>

[PNG](<../assets/figure-contract-r11/figures/pittsburgh/pittsburgh-pittsburgh-s72-finite-flow.png>) · [SVG](<../assets/figure-contract-r11/figures/pittsburgh/pittsburgh-pittsburgh-s72-finite-flow.svg>) · [PDF](<../assets/figure-contract-r11/figures/pittsburgh/pittsburgh-pittsburgh-s72-finite-flow.pdf>) · [Source record](<../assets/figure-contract-r11/figures/pittsburgh/pittsburgh-pittsburgh-s72-finite-flow.source.json>)

<details markdown="1">
<summary>Approved scalar check and selected-link bar chart</summary>

<a id="released-pit-s01"></a>

</details>

<details markdown="1">
<summary>Approved scalar check and selected-link bar chart</summary>

<a id="released-pit-s03"></a>

</details>

#### Native: accepted original-coordinate continuation

Native rank26与rank52保留完整56,384条原求解弧的评估语义。minor路径矩阵有49,109个全零列；工作空间固定全部路径不支持的49,108条链路，差异的一条链路由major路径使用。严格零消元不裁剪全图最短路检查。每个rank保留14次实际outer记录；outer14的原OD最大残差分别为8.07013475568935e−8和2.6256443221356536e−7 PCE/h，满足原1e−6门及其他原空间检查。

<a id="released-pit-s04"></a>

<a id="algorithm-transfer-r2-section-4"></a>

### 4. T4 同图 LP、CG、LR 与 ADMM

#### Accepted exact-DAG LP certificate

同一完整可达域的精确 DAG LP 证书随后实际完成。四 OD 总脉冲 0.045027548453549955 PCE 小于最小实体时间弧容量 2.5 PCE，故每条实体容量行在该档都由总需求上界蕴含，不会绑定；去掉冗余容量行不改变此档原 LP 的可行集。原坐标检查的最小 reduced cost 为约 −1.77×10⁻¹⁵，流守恒及容量违例为零。原始目标 0.24793241990274612、对偶目标 0.2479324199027458 PCE·min，原始对偶差 3.05×10⁻¹⁶。该证书对应同一 T4 的完整可达变量域。

#### Column generation: feasibility, objective and full-DAG pricing

CG 从本城数据生成四条列。Phase I 人工需求归零，Phase II 得到 0.2479324199027457 PCE·min；独立检查为每一 commodity 在完整 DAG 的合法弧上重新定价，最小 reduced cost 为零，原始对偶差约 3.6×10⁻¹⁶。

<a id="released-pit-t03"></a>

##### Column generation: one certificate per phase

<a id="table-r11-pittsburgh-t4-cg-check"></a>

###### Column generation: Phase I feasibility

[![Column generation: Phase I feasibility](<../assets/figure-contract-r12/figures/pittsburgh/cg-phase1.svg>)](<../assets/figure-contract-r12/figures/pittsburgh/cg-phase1.svg>)

Phase I has one actual saved restricted-master round. Its total artificial flow is 0 PCE. A single marker retains that real record; there is no interpolated trajectory. Four seed paths suffice. Commodity-level artificial-flow history was not included in these public plot files, so no heatmap is inferred. Phase I feasibility is separate from Phase II real cost and full-DAG pricing closure.

[SVG](<../assets/figure-contract-r12/figures/pittsburgh/cg-phase1.svg>) · [PNG](<../assets/figure-contract-r12/figures/pittsburgh/cg-phase1.png>) · [PDF](<../assets/figure-contract-r12/figures/pittsburgh/cg-phase1.pdf>) · [Source data](<../assets/figure-contract-r12/figures/pittsburgh/cg-phase1.source.json>)

[Phase II objective](<#figure-parity-pittsburgh-cg-phase2>)

[Independent pricing closure](<#figure-parity-pittsburgh-cg-pricing>)

<a id="released-pit-t06"></a>

##### Generated routes: flow, cost and arc roles

<a id="table-r11-pittsburgh-t4-route-counts"></a>

[![Generated routes: flow, cost and arc roles](<../assets/figure-contract-r12/figures/pittsburgh/generated-route-profile.svg>)](<../assets/figure-contract-r12/figures/pittsburgh/generated-route-profile.svg>)

Each category is one of the four saved demand commodities, not a solver iteration. Panels retain the method’s own generated path flow, fixed route cost, and separate counts of movement, turn, and waiting arcs. All four paths have zero waiting arcs. The ordered dynamic arc sequences and existing route maps remain separate geographic evidence; a fixed cost in minutes is not the rounded arrival clock.

[SVG](<../assets/figure-contract-r12/figures/pittsburgh/generated-route-profile.svg>) · [PNG](<../assets/figure-contract-r12/figures/pittsburgh/generated-route-profile.png>) · [PDF](<../assets/figure-contract-r12/figures/pittsburgh/generated-route-profile.pdf>) · [Source data](<../assets/figure-contract-r12/figures/pittsburgh/generated-route-profile.source.json>)

#### Lagrangian relaxation: own lower bound and feasible recovery

LR 也从自身最短路生成四条路径，保存非负乘子对应的有效对偶下界与独立可行恢复的上界，两端同为约 0.247932419902746 PCE·min，证书 gap 约 3.6×10⁻¹⁶。这两项的路径来源和停止证书均有原始文件，不能仅凭目标数值相同认定通过。

<a id="released-pit-t04"></a>

##### Lagrangian relaxation: one evaluated state

<a id="table-r11-pittsburgh-t4-lr-check"></a>

[Lagrangian bounds and certified gap](<#figure-parity-pittsburgh-lr-bounds>)

###### Lagrangian prices and recovery

[![Lagrangian prices and recovery](<../assets/figure-contract-r12/figures/pittsburgh/lr-prices-recovery.svg>)](<../assets/figure-contract-r12/figures/pittsburgh/lr-prices-recovery.svg>)

At saved iteration 1 the positive capacity-price count is 0, so there are no positive-price arcs for a top-price map or time histogram. One actual recovery call uses the four paths in this method’s own pool and returns a feasible upper bound. Filled recovery marker follows the Boston/Hong Kong feasible-recovery convention. No additional calls or multipliers are invented.

[SVG](<../assets/figure-contract-r12/figures/pittsburgh/lr-prices-recovery.svg>) · [PNG](<../assets/figure-contract-r12/figures/pittsburgh/lr-prices-recovery.png>) · [PDF](<../assets/figure-contract-r12/figures/pittsburgh/lr-prices-recovery.pdf>) · [Source data](<../assets/figure-contract-r12/figures/pittsburgh/lr-prices-recovery.source.json>)

#### ADMM: accepted one-step endpoint and physical flow

ADMM 从该城冻结输入冷启动，rho 由本城正成本与正 OD 量的中位数公式裁剪为 1.0。主档在第一个 outer 终点达到数值门：x 目标 0.2479324199052491 PCE·min，primal residual 为零、dual residual 为 1.511×10⁻¹³ min、最大守恒误差 2.785×10⁻¹⁵ PCE；物理链路回投误差为零。与同图 LP 的绝对目标差为 2.503×10⁻¹² PCE·min，因 LP 目标小于 1，另报真实相对差 1.010×10⁻¹¹，未把合同的 max(1,|fLP|) 归一差冒充相对误差。独立同配置、同原输入冷启动确认也在一轮结束，完整 x、z、w、z\_previous、local\_q、potential 状态逐项相等，两份 NPZ SHA-256 完全相同。独立端点检查与确认回执使 ADMM 标为 ACCEPTED；预注册第二精度档未触发，也没有借用 LP 流、对偶或列初始化。

<a id="figure-r9-pittsburgh-admm-main"></a>

##### ADMM residuals and objective agreement

<a id="table-r11-pittsburgh-t4-admm-check"></a>

[![ADMM residuals and objective agreement](<../assets/figure-contract-r12/figures/pittsburgh/admm-saved-state.svg>)](<../assets/figure-contract-r12/figures/pittsburgh/admm-saved-state.svg>)

Four diagnostic panels follow the Hong Kong ADMM figure: original-unit feasibility, primal consensus, rho-scaled dual update, and log10 absolute objective error against the independent same-graph reference. This instance saved exactly one completed outer update, shown as a point rather than an invented convergence curve. Balance, capacity, and primal use PCE; rho-scaled dual and its own threshold use minutes. Only exact-zero residuals use a labeled 1e-16 display floor; positive residuals are unchanged. Objective-error display floor is 1e-15 PCE·min. Saved internal thresholds and the 1e-5 PCE feasibility gate are retained. All displayed states meet the frozen independent gates; objective agreement is not a claim of identical link flows.

[SVG](<../assets/figure-contract-r12/figures/pittsburgh/admm-saved-state.svg>) · [PNG](<../assets/figure-contract-r12/figures/pittsburgh/admm-saved-state.png>) · [PDF](<../assets/figure-contract-r12/figures/pittsburgh/admm-saved-state.pdf>) · [Source data](<../assets/figure-contract-r12/figures/pittsburgh/admm-saved-state.source.json>)

<a id="figure-r9-pittsburgh-admm-conservation"></a>

##### ADMM: final commodity conservation

[![ADMM: final commodity conservation](<../assets/figure-contract-r11/figures/pittsburgh/pittsburgh-pittsburgh-admm-conservation.svg>)](<../assets/figure-contract-r11/figures/pittsburgh/pittsburgh-pittsburgh-admm-conservation.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

At the single saved completed ADMM iteration 1, reconstruct original-unit outflow minus inflow minus commodity supply using the exact saved arc order and the original loader’s lexically sorted 700,226 time-node identities. All four commodity maximum residuals and their worst-node IDs match the previously saved independent check exactly; the overall maximum is 2.7850292342213303e−15 PCE against the unchanged 1e−5 PCE gate. The heatmap shows the 35 nodes with largest maximum residual over all four commodities, with lexical node-order tie breaking; all nodes were included in selection. Values ≤1e−15 use a display-floor color without changing data. The color ceiling is the gate, and the figure does not imply an iteration history. Original OUT-state loading is unchanged. Modeled scenario, not observed traffic. Local saved-result derivative; no new S0 asset release is claimed. The heatmap is the saved final spatial conservation state, not an iteration-history heatmap. The displayed color floor and unchanged gate are retained; all exact raw residual values remain in the linked public plot data.

</details>

[PNG](<../assets/figure-contract-r11/figures/pittsburgh/pittsburgh-pittsburgh-admm-conservation.png>) · [SVG](<../assets/figure-contract-r11/figures/pittsburgh/pittsburgh-pittsburgh-admm-conservation.svg>) · [PDF](<../assets/figure-contract-r11/figures/pittsburgh/pittsburgh-pittsburgh-admm-conservation.pdf>) · [Source record](<../assets/figure-contract-r11/figures/pittsburgh/pittsburgh-pittsburgh-admm-conservation.source.json>)

<a id="figure-r9-pittsburgh-admm-physical"></a>

##### ADMM: physical-road flow comparison

[![ADMM: physical-road flow comparison](<../assets/figure-contract-r11/figures/pittsburgh/pittsburgh-pittsburgh-admm-physical.svg>)](<../assets/figure-contract-r11/figures/pittsburgh/pittsburgh-pittsburgh-admm-physical.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

The 9,106 physical GMNS links instantiated in the frozen Pittsburgh T4 graph are mapped from their exact physical\_road arc IDs and summed across commodities and time. All instantiated links, including zero-flow links, appear in the map and scatter. The other 8,428 of the 17,534 physical roads are grey context, not solved zeros. ADMM x and exact-DAG LP own saved vectors use a common square-root color scale; the signed difference map uses a separate symmetric scale and displays roundoff-sized differences, not a congestion effect. Each physical\_fraction is exactly 1 and the P:link-to-GMNS mapping is one-to-one; turns/waits/connectors are excluded. The original OUT-state origin convention omits the first origin-link traversal and is preserved without repair. This is one saved ADMM update on a nonbinding-capacity four-OD pulse, not observed traffic or a convergence-rate comparison. Local saved-result derivative; no new S0 asset release is claimed.

</details>

[PNG](<../assets/figure-contract-r11/figures/pittsburgh/pittsburgh-pittsburgh-admm-physical.png>) · [SVG](<../assets/figure-contract-r11/figures/pittsburgh/pittsburgh-pittsburgh-admm-physical.svg>) · [PDF](<../assets/figure-contract-r11/figures/pittsburgh/pittsburgh-pittsburgh-admm-physical.pdf>) · [Source record](<../assets/figure-contract-r11/figures/pittsburgh/pittsburgh-pittsburgh-admm-physical.source.json>)

<details markdown="1">
<summary>Approved stopping-gate view and top-link endpoint bars</summary>

PIT\_T05 compares a saved residual with its stopping threshold. Its horizontal axis is quantity, not iteration. The top-link bars are retained but do not replace the full physical-road comparison.

<a id="released-pit-t05"></a>

</details>

<details markdown="1">
<summary>Approved stopping-gate view and top-link endpoint bars</summary>

PIT\_T05 compares a saved residual with its stopping threshold. Its horizontal axis is quantity, not iteration. The top-link bars are retained but do not replace the full physical-road comparison.

<a id="released-pit-t07"></a>

</details>

#### Same frozen T4: objective agreement and its limits

<a id="released-pit-t08"></a>

##### Accepted methods on the same finite graph

<a id="table-r11-pittsburgh-t4-objectives"></a>

[![Accepted methods on the same finite graph](<../assets/figure-contract-r12/figures/pittsburgh/time-method-objectives.svg>)](<../assets/figure-contract-r12/figures/pittsburgh/time-method-objectives.svg>)

The methods share this exact four-OD finite graph and fixed-cost objective. Categories are independent method endpoints, not an optimization timeline. Left: each saved objective with the independent reference. Right: signed differences retain full numerical precision, including negative roundoff. All shown methods currently satisfy their independent acceptance conditions. Objective proximity by itself is not a feasibility certificate and does not imply identical physical-link flow.

[SVG](<../assets/figure-contract-r12/figures/pittsburgh/time-method-objectives.svg>) · [PNG](<../assets/figure-contract-r12/figures/pittsburgh/time-method-objectives.png>) · [PDF](<../assets/figure-contract-r12/figures/pittsburgh/time-method-objectives.pdf>) · [Source data](<../assets/figure-contract-r12/figures/pittsburgh/time-method-objectives.source.json>)

<a id="algorithm-transfer-r2-section-5"></a>

### 5. 图件、复现与可公开边界

输入身份和方法结果分别展示：静态图使用各方法自身保存的流量、目标、守恒与维数；T4图展示实际时空弧、输入脉冲、CG两阶段与完整图定价、LR上下界、ADMM真实残差、生成路径及物理流。ADMM primal量使用PCE，rho-scaled dual量使用分钟。原公开数据与图件字节保留，缺少道路geometry时不推造地图；模型流量与实地观测严格区分。

复现入口、固定源哈希及各方法证书随完整科学包保存。当前网页直接引用获准公开的保存结果，未运行优化。此档容量不绑定，结果不能支持拥堵改善结论；GPS、照片元数据和图像没有参与当地速度或需求校准。真实拥堵推断需要另行匹配观测、动态装载与需求设计。

**Source and scope notice.** © OpenStreetMap contributors; road-derived data ODbL 1.0: https://www.openstreetmap.org/copyright; numerical results are engineering scenarios, not observed traffic. East End synthetic HBW; S72 and T4 selected subsets. T4 pulse capacity is nonbinding; accepted methods do not show measured congestion improvement. Census/LODES proxies retain their source identities. [Complete notice](<../assets/algorithm-transfer-r8/NOTICE.md>).

<a id="pit-r3-static-reference"></a>

##### Static objective and optimality checks

<a id="table-r11-pittsburgh-s72-endpoints"></a>

[![Static objective and optimality checks](<../assets/figure-contract-r12/figures/pittsburgh/pittsburgh-s72-endpoints.svg>)](<../assets/figure-contract-r12/figures/pittsburgh/pittsburgh-s72-endpoints.svg>)

Independent FW and finite-path endpoints on the same selected Pittsburgh S72 demand. Both checked objectives equal 763.227941458126 PCE·min/h and both saved OD and reconstruction residuals are zero. Categorical points are never connected as an iteration history. The companion method-specific maps and distributions retain all 17,534 physical traversal links from each method’s own 56,384-solver-arc vector, excluding 38,850 turn arcs.

[SVG](<../assets/figure-contract-r12/figures/pittsburgh/pittsburgh-s72-endpoints.svg>) · [PNG](<../assets/figure-contract-r12/figures/pittsburgh/pittsburgh-s72-endpoints.png>) · [PDF](<../assets/figure-contract-r12/figures/pittsburgh/pittsburgh-s72-endpoints.pdf>) · [Source data](<../assets/figure-contract-r12/figures/pittsburgh/pittsburgh-s72-endpoints.source.json>)

<a id="pittsburgh-r3-input-time-layer-excerpt"></a>

##### Time-expanded network: saved input layers

[![Time-expanded network: saved input layers](<../assets/figure-contract-r11/figures/pittsburgh/pittsburgh-input-time-layer-excerpt.svg>)](<../assets/figure-contract-r11/figures/pittsburgh/pittsburgh-input-time-layer-excerpt.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

INPUT ONLY / NOT OPTIMIZED. 26 actual dynamic\_arc rows connect 4 selected physical/IN/OUT states over steps 40–44 (20–22 minutes after 08:00). Time coordinates and edge directions come directly from the frozen input; vertical spacing is schematic. Pittsburgh distinguishes IN→OUT physical roads, OUT→IN zero-time turns, and one-step waits. Connector examples are also exact saved records; their sink-time jumps are ledger bookkeeping, not observed waiting. No optimized flow/path is shown. Structural excerpt selected from records; arrows carry no assigned flow and no optimized path. Saved bookkeeping examples outside this local excerpt: Source: source\_C04\_OD\_01\_tract2020\_42003151700\_tract2020\_42003980500\_t5 → OUT:36036@t5; t=5→5; cost=0 min Sink: OUT:3537@t59 → sink\_C04\_OD\_01\_tract2020\_42003151700\_tract2020\_42003980500\_t117; t=59→117; cost=0 min Ledger jumps align arrival bookkeeping to H; they are not physical travel or waiting. State spacing is schematic. Full graph support and nonselected neighbours are omitted from this excerpt; all shown edges are saved input rows.

</details>

[PNG](<../assets/figure-contract-r11/figures/pittsburgh/pittsburgh-input-time-layer-excerpt.png>) · [SVG](<../assets/figure-contract-r11/figures/pittsburgh/pittsburgh-input-time-layer-excerpt.svg>) · [PDF](<../assets/figure-contract-r11/figures/pittsburgh/pittsburgh-input-time-layer-excerpt.pdf>) · [Source record](<../assets/figure-contract-r11/figures/pittsburgh/pittsburgh-input-time-layer-excerpt.source.json>)
