<a id="document-top"></a>

MOBILITY COMPUTATION LAB / STATIC CITY RECORD

# Urbana–Champaign

A 21-zone morning HBW scenario for the 19.303 km² Champaign–Urbana subarea, with drive/walk demand and 418 positive vehicle OD pairs.

The figures show saved method results, physical-flow maps and original-unit diagnostics. Drawing these figures invokes no optimizer.

<span id="urbana-champaign-late-status-20261008"></span>
<a id="gap-20261008"></a>

## Latest received evidence · 8 October 2026

Current accepted results preserve each frozen model, demand instance and numerical unit. The figures below read the received public evidence without additional optimization.

<dl class="accepted-method-notes"><dt>CUMTD service-day input changes mode choice and static FW: 1,667.089946 PCE/h was actually assigned; the accepted generation, distribution and road graph are retained.</dt><dd>The new FW has one initialization record and zero updates under the original 1e−4 gate. This is a different demand from the baseline 1,963.648313 PCE/h and must not relabel the old physical-flow map.</dd><dt>Same-instance Algorithm B is accepted on the original 321.629660 PCE/h S72; Native26/52 outer9 acceptance remains.</dt><dd>B is not a solve of the new 418-OD demand.</dd><dt>CG retains one record per phase; LR retains one iteration; ADMM retains one complete cold-start update.</dt><dd>0.0516231483 PCE pulse is below 3.75 PCE minimum physical time-arc capacity. The capacity-redundancy certificate explains this easy T4; it does not explain every static FW initialization or prove an area effect.</dd><dt>1,672 rows are 418 OD × four schedule-departure queries.</dt><dd>They are not observed boardings, GPS traces or local calibration. DNL/DUE is not established.</dd></dl>

[Homepage city cards](<../index.html?atlas-view=full#urbana-champaign>) · [Figure guide and saved-state interpretation](<../figure-update-status.html#top>) · [Earlier frozen chapters and history](<#gap-earlier-cutoff>)

### Received figure evidence

<a id="figure-gap-uc-gap-c1"></a>

##### Mode demand under two transit inputs

[![Mode demand under two transit inputs](<../assets/figure-contract-r11/figures/urbana-champaign/uc-mode-demand.svg>)](<../assets/figure-contract-r11/figures/urbana-champaign/uc-mode-demand.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

The person total is 2,989.8528 across 418 OD. The timetable revision predicts 461.581416 transit person trips and 1,667.089946 PCE/h, versus 1,963.648313 PCE/h under the earlier mode inputs. Both totals are engineering predictions; their different demands do not compare solver quality. Engineering scenario, not observed ridership or local calibration. Data provided by Champaign-Urbana Mass Transit District; dated 2026-10-07 timetable, not live rider advice. © OpenStreetMap contributors, ODbL: https://www.openstreetmap.org/copyright. CUMTD terms: https://developer.mtd.org/terms-of-use/

</details>

[PNG](<../assets/figure-contract-r11/figures/urbana-champaign/uc-mode-demand.png>) · [SVG](<../assets/figure-contract-r11/figures/urbana-champaign/uc-mode-demand.svg>) · [PDF](<../assets/figure-contract-r11/figures/urbana-champaign/uc-mode-demand.pdf>) · [Source record](<../assets/figure-contract-r11/figures/urbana-champaign/uc-mode-demand.source.json>)

<a id="figure-gap-uc-gap-c2"></a>

##### Scheduled transit cost components

[![Scheduled transit cost components](<../assets/figure-contract-r11/figures/urbana-champaign/uc-transit-cost.svg>)](<../assets/figure-contract-r11/figures/urbana-champaign/uc-transit-cost.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

Costs use the 2026-10-07 CUMTD schedule, directed walking access and a stated adult fare scenario. The 1,672 queries are 418 OD × four departure samples, not passenger observations. Engineering scenario, not observed ridership or local calibration. Data provided by Champaign-Urbana Mass Transit District; dated 2026-10-07 timetable, not live rider advice. © OpenStreetMap contributors, ODbL: https://www.openstreetmap.org/copyright. CUMTD terms: https://developer.mtd.org/terms-of-use/

</details>

[PNG](<../assets/figure-contract-r11/figures/urbana-champaign/uc-transit-cost.png>) · [SVG](<../assets/figure-contract-r11/figures/urbana-champaign/uc-transit-cost.svg>) · [PDF](<../assets/figure-contract-r11/figures/urbana-champaign/uc-transit-cost.pdf>) · [Source record](<../assets/figure-contract-r11/figures/urbana-champaign/uc-transit-cost.source.json>)

<a id="gap-notice-urbana-champaign-1cf1551e78"></a>

### Source and scope notice

Engineering scenario, not observed ridership or local calibration. Data provided by Champaign-Urbana Mass Transit District; dated 2026-10-07 timetable, not live rider advice. © OpenStreetMap contributors, ODbL: https://www.openstreetmap.org/copyright. CUMTD terms: https://developer.mtd.org/terms-of-use/

### Complete approved source chapters

The following chapters are retained in full, including numerical tables and historical source-time statements. Their figures link to the same figure anchors above.

<details id="gap-source-c02-gap-chapter" markdown="1">
<summary>Approved source chapter — C02_GAP_CHAPTER.md</summary>

Reading edition of the approved source, SHA-256 93b4e0889112e48dd07f2101a7f8c84d5476db0ada24ea5de416b32fc1ef4748 . Download original source text . The linked original preserves the complete source record; this reading edition displays accepted results.

### Urbana–Champaign: service-day transit input and bounded observation bridge

#### A scheduled transit option changes the engineering mode split

The accepted C02 four-stage model covers a 19.303 km² central Champaign–Urbana subarea with 21 tract zones. Its 08:00–09:00 home-based-work scenario generates 2,989.8528 directed interzonal person trips across 418 positive OD pairs. The original mode input made transit unavailable because it lacked a selected MTD service-day timetable. This extension retains the accepted generation, distribution, choice coefficients and road graph, and changes only the transit cost input, mode choice output and resulting static road assignment.

The source snapshot is the [CUMTD published GTFS feed](<https://developer.mtd.org/gtfs/google_transit.zip>), downloaded on 2026-10-08 with SHA-256 `49201ba617ce2bde637ffa95f5530a8c618414dac516c66b89dbd69693aed1ad`. The candidate's explicit input identity is `UC_MODE_TRANSIT_EXTENSION_20261008_R2`; the raw feed, frozen inputs, generated costs and solver outputs have separate hashes in the handoff. This model revision does not alter the original static S72 or time-expanded T4 instances.

We selected the published CUMTD GTFS feed's 2026-10-07 Wednesday service in the `America/Chicago` timezone. The feed supplies 1,937 active trips; the scan window contains 14,554 consecutive stop-to-stop schedule connections. For each positive OD we evaluated departures at 08:00, 08:15, 08:30 and 08:45 and selected the earliest arrival itinerary. Every one of the 1,672 OD-departure queries yielded a legal GTFS ride leg. A service path may change vehicles only at the same stop with at least two minutes between trips. We marked a transit OD available only when all four departures yielded a ride. This availability rule prevents a nearby stop or a walk-only connection from masquerading as bus service.

Access and egress use the frozen directed GMNS walk graph. We attached eligible GTFS stops to their nearest walk node within 100 m, started each zone at its accepted public-road link midpoint proxy, and limited each walk side to 1.2 km. For a midpoint on directed link a→b, access can exit toward b and egress can enter from a; the opposite endpoint is legal only when an explicit reverse walk arc exists. Two source midpoint links, `1242` and `8862`, have no such reverse arc. An earlier diagnostic allowed both exits and was withdrawn before acceptance. The corrected R2 costs passed a separate heap-Dijkstra check on all 2,948 zone–stop–direction connectors, with a maximum discrepancy of 5.33×10⁻¹⁵ minutes. The short stop-to-walk-node connector uses geometric distance; its sidewalk continuity and ADA status remain unverified. The cash fare scenario charges the GTFS adult single-ride price of USD 1 and permits one free transfer within 60 minutes. It does not assume UIUC student iStop eligibility. Scheduled vehicle minutes, initial wait, transfer wait, routed walk minutes and fare-equivalent minutes enter the accepted conditional logit with its unchanged 0.08 per generalized minute coefficient and USD 18 per hour value of time.

The corrected R2 mode output assigns 2,083.862 drive, 444.409 walk and 461.581 transit person trips. The original accepted run assigned 2,454.560 drive and 535.292 walk person trips while transit was unavailable in the model. Both outputs conserve the same 2,989.8528 person trips. The fixed 1.25 persons per drive vehicle converts the revised drive flow into 1,667.090 PCE per hour, versus 1,963.648 in the original run. Figure UC\_GAP\_C1 presents this input-revision comparison; it does not claim an observed change in traveler behavior.

The predicted transit-person-weighted generalized cost contains 11.39 minutes of access and egress, 2.04 minutes of initial wait, 6.80 minutes aboard vehicles, 0.48 minutes waiting to transfer and 3.36 fare-equivalent minutes (Figure UC\_GAP\_C2). The departure-grid mean represents the declared schedule scenario. Actual arrival at stops, vehicle adherence, traveler route choice and eligibility for zero fare remain unobserved.

#### The revised car OD passes the frozen static road test

The accepted turn-expanded road supply contains 26,602 directed arcs: 11,365 physical traversals and 15,237 permitted virtual turns. The revision passes 418 positive car OD pairs to the unchanged Frank–Wolfe implementation, with the original BPR functions and 10⁻⁴ relative-gap threshold. The new solve converges at its initial all-or-nothing loading. An independent saved-result evaluator recomputed OD choice, person-to-vehicle conversion, path continuity, link reconstruction, node balance, BPR costs, Beckmann objective and full-graph gap. It found 1,667.090 PCE, a 6,898.584 PCE-minute objective and zero numerical relative gap at the declared tolerance. The baseline's 8,041.087 PCE-minute objective belongs to a different demand input and is not an algorithm-quality comparison. Three re-signed invalid-state CLI copies were rejected for a probability change, missing vehicle OD commodity and illegal path arc.

The original S72 static FW, finite-path and Native 26/52 results retain their accepted S identity. The T4 exact-DAG LP, CG, LR and ADMM results retain their separate fixed-cost hard-capacity time-graph identity. The revision reuses those S/T endpoints because the GTFS input changes only the full four-stage mode-choice vehicle OD. Algorithm B's same-instance S72 supplement has a verified lossless two-stage node relabeling and frozen tap-b policy; the status ledger records its solve and independent certificate separately.

The same-instance Algorithm B supplement subsequently ran through the pinned public tap-b adapter after an in-lock 1 GiB RAM gate passed. Its reported gap was 3×10⁻¹⁴, but acceptance rests on the two saved-result checks. The fixed converted-space evaluator found no issues, zero OD residual, 1.78×10⁻¹⁵ PCE maximum link reconstruction error, and a 2.97×10⁻¹⁴ full-graph relative gap. A second audit mapped every returned path and flow to the original string IDs and recovered a 1,086.553543476 PCE-minute Beckmann objective, exactly the accepted same-instance FW reference at reported precision. This comparison concerns the frozen S72 problem; it is separate from the new 418-OD transit-revised road assignment.

#### The observed trace supports a local query with a visible boundary

The existing evidence branch holds one ordered 27-point GPS segment from 2025-07-29, matched to 35 directed North Randolph Street GMNS source links. The vehicle mode is unknown. Frozen source IDs and the accepted physical map connect the first 33 route links to `P:` traversals; 32 of 34 consecutive source turns appear in the frozen auto turn map. The two north-end links, source IDs `8528` and `8526`, lack frozen R2 physical identities. The local query returns modeled PCE for only those 33 mapped traversals and leaves the other two flow cells empty. Its modeled PCE is an engineering prediction; the GPS trace supplies no observed flow, peak speed or route ground truth. The 2016 scene photos do not validate a 2025 trajectory or 2026 service day.

#### Scope of inference and next consumer

This extension closes the missing timetable-path input for the declared service-day scenario. It does not establish local rate, mode-share or route-choice calibration. The available GPS sample cannot supply those quantities, and no count data have been aligned to the same date, hour, geography and vehicle class. A future validation study needs independent same-period transit boardings and road counts, plus a checked pedestrian access inventory. The current static network also lacks dynamic queues, spillback and within-hour departures.

The D handoff specifies the original physical-to-GMNS map, turn movements, 21 zone midpoint accesses and the revised 418-OD vehicle control total. It leaves the within-hour departure profile explicitly unspecified. A dynamic consumer must freeze loading, movement and queue semantics as a new problem and validate it separately; the accepted static S and hard-capacity T certificates do not certify D.

##### Figure and evidence pointers for volume integration

| Item | Meaning | Reproducible source |
| --- | --- | --- |
| UC\_GAP\_C1 | Original and GTFS-revision modeled person trips and car PCE | `figures/UC_GAP_C1.plot.json`, `figures/UC_GAP_C1.source.json` |
| UC\_GAP\_C2 | Scheduled transit generalized-cost components | `figures/UC_GAP_C2.plot.json`, `figures/UC_GAP_C2.source.json` |
| Transit paths | 1,672 service-day OD-departure itineraries | `UC_MODE_TRANSIT_EXTENSION/transit_itineraries.csv` |
| Independent checks | GTFS rides, directed walk, choice and assignment in original source spaces | `TRANSIT_INDEPENDENT_CHECK.json`, `WALK_DIRECTION_INDEPENDENT_CHECK.json`, `run_revision/REVISION_INDEPENDENT_CHECK.json` |
| Local trace query | 33/35 physical arcs, 32/34 turns; null tail retained | `observation/route_model_query.csv`, `observation/OBSERVATION_QUERY_CHECK.json` |
| Same-instance Algorithm B | Frozen S72 converted-space and original-ID checks | `TAPB_S72/solver/evaluation.json`, `TAPB_S72/solver/ORIGINAL_SPACE_INDEPENDENT_CHECK.json` |

</details>

<details id="gap-source-method-note-r2" markdown="1">
<summary>Approved source chapter — METHOD_NOTE_R2.md</summary>

Reading edition of the approved source, SHA-256 7af96c46fb33b0b8ec3fde9eb5ec9baea16f01ce9592f9e38a7fcda751af4002 . Download original source text . The linked original preserves the complete source record; this reading edition displays accepted results.

### C02 service-day transit revision: frozen method

#### Declared case and source

`UC_MODE_TRANSIT_EXTENSION_20261008_R2` extends the accepted 21-zone, 418-positive-OD central Champaign–Urbana HBW engineering scenario. It uses the CUMTD GTFS ZIP downloaded from the agency's developer endpoint, SHA-256 `49201ba617ce2bde637ffa95f5530a8c618414dac516c66b89dbd69693aed1ad`, and selects 2026-10-07 in `America/Chicago`. The older generation, distribution, road graph, parameter values and S72/T4 algorithm inputs remain fixed.

#### Timetable and access calculation

The compiler applies `calendar.txt` and `calendar_dates.txt`, joins active `trips.txt` with ordered `stop_times.txt`, and respects pickup and drop-off prohibitions. It scans actual consecutive trip calls with departures in a declared 08:00–11:00 local search window. Four uniformly weighted traveler departure samples represent 08:00–09:00: 08:00, 08:15, 08:30 and 08:45. The compiler selects the earliest arrival itinerary for each origin, destination and sample, counting a transit option only when it contains at least one GTFS ride leg. Transfers occur at the same stop with at least two minutes between trips. An OD receives a transit cost only when all four samples find such an itinerary.

The access point for each model zone remains the accepted midpoint of a directed GMNS road link. Pedestrian travel follows the frozen directed links whose `allowed_uses` includes `walk`, at the accepted 75 m/min engineering speed. A GTFS stop attaches to its nearest walk-network node only within 100 m; each access or egress side is capped at 1,200 m. The stop-to-node connector uses straight-line distance and has no inspected sidewalk, curb or barrier certificate.

The midpoint direction rule is explicit. For a directed source link `a→b`, an origin exits toward `b` and a destination enters from `a`. The other endpoint becomes available only when an explicit reverse `walk` arc `b→a` exists. Source links `1242` and `8862` lacked this reverse arc. The first candidate allowed both endpoints, so it is preserved solely as a superseded diagnostic under `diagnostic_access_v1/`. This R2 correction changes only access representation; it does not change demand, road capacity, logit coefficients or convergence thresholds.

The cost record separates vehicle ride, initial wait, transfer wait, access plus egress, and adult cash fare. The published GTFS fare table provides USD 1 for a single ride and one free full-fare transfer within 3,600 seconds. A traveler-specific zero-fare iStop entitlement is not assumed. The four component means feed the accepted logit cost schema; USD fare converts to minutes with the frozen USD 18/hour value of time. The path search minimizes arrival time, then evaluates the cost of that chosen valid path. It does not estimate real passenger route selection, actual delay or reliability.

#### Affected stages and checks

The active input revision changes the Stage 3 transit availability and generalized cost. The accepted conditional multinomial logit recomputes all positive OD mode probabilities with `λ=0.08` per generalized minute and unchanged ASCs. Only modeled drive person trips pass through the fixed 1.25-person occupancy and unit PCE factor into Stage 4. The accepted turn-expanded static FW implementation solves that new road OD on the original network with the original `1e-4` gap threshold. A separate checker reconstructs GTFS ride legs from source stop times, verifies all component sums and fares, recomputes every OD probability and person/PCE ledger, and independently audits original-link path flow, BPR objective and the signed full-graph gap.

The S72 tap-b supplement has its own frozen instance and will not consume the transit revision. Its integer node relabeling and TNTP permutation preserve all 26,602 directed arcs, 72 OD volumes, BPR coefficients and turn permissions exactly in binary64. A new Algorithm B run requires the shared heavy lock. The original FW endpoint is the same-instance objective reference; a new FW run on S72 is unnecessary.

The observation query reuses the accepted 2025 27-point GPS trace and E bridge. Only 33 of its 35 source links have frozen `P:` identities, and only 32 of 34 adjacent turns have frozen turn IDs. Query output leaves unmatched flow fields empty. The trace's mode is unknown and the photo dates differ, so no current link flow, speed or traveler mode claim derives from this evidence.

</details>

<a id="gap-earlier-cutoff"></a>

Original four-stage chapters retain their original demand, input identity and engineering assumptions.

**Local review · current S0-approved increment integrated.** The four-stage R3 case remains accepted; Native26/52 outer9 now pass S0 original-coordinate reception. Exact inputs and checkpoints remain private.

Input snapshot: `mcl_s0_to_v_presentation_inputs_r3_v1@2026-10-05T03:57:54.309662+00:00`. Input version: `central_champaign_urbana_2026_r2; frozen configuration SHA-256 9eb316749d925243d18c6a8ff7b5dcd5402506d7ca765333ea2a06878268f933`.

<a id="scope"></a>

## Scope and model instance

This case follows morning work travel within a 19.303 km² rectangle spanning central Champaign and Urbana. UIUC identifies the location; the rectangle includes residential and employment areas outside university property. Its bounds are 88.255°W to 88.204°W and 40.087°N to 40.127°N. The boundary follows the four OSM tiles acquired during preflight and was fixed before inspecting assignment results.

Twenty-one zones support a weekday 08:00–09:00 HBW scenario. Generation, distribution, mode choice and road loading form one forward pass. The calculation describes a bounded engineering experiment, with local source geography but assumed behavioral and road parameters. It does not estimate either municipality's complete travel or reproduce an observed UIUC commute survey.

<a id="inputs"></a>

## Inputs and preparation

<a id="coverage-row-01"></a>

<a id="coverage-row-02"></a>

<a id="coverage-row-03"></a>

The demographic adapter selected 725 Census blocks whose published internal points fall inside the rectangle. Joined 2020 PL 94-171 population and occupied-unit fields give 52,040 residents and 19,696 occupied housing units. The same block selection contains 43,602 workplace jobs in the Illinois 2023 LODES WAC C000 field. Residence, housing and workplace jobs remain different quantities and different vintages.

The selected-block totals must be kept separate from the earlier count of 84,805 residents in whole intersecting tracts. A tract may extend beyond the model. The original population/context figure therefore describes broader source geography and 2024 place outlines; it does not replace the block-based demand denominator. Selecting by block internal point also leaves uncertainty at the clipped edge.

The preflight GMNS conversion contains 24,775 nodes and 46,203 directed physical links before the automobile graph is screened. Its network figure records source geometry, whereas the assignment maps contain modeled loading on retained traversals. The frozen road construction keeps explicit physical-to-source mappings so that turn movements and split road traversals can be distinguished.

An MTD transit reference comes from the BTS National Transit Map archive dated 9 March 2026. It has 564 stop records and 607 route-shape records clipped to the area. These locations do not supply a verified service-day timetable. The corresponding figure is retained as source context; it is not a transit skim, ridership result or road-loading map.

<a id="figure-f01-network"></a>

##### Retained physical road graph

[![Retained physical road graph](<../assets/figure-contract-r11/figures/urbana-champaign/sources.svg>)](<../assets/figure-contract-r11/figures/urbana-champaign/sources.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

11,365 retained physical directed traversals in the saved 08:00–09:00 HBW model, shown in EPSG:26916. This is the retained model graph, not a claim to draw every road in the source archive. Virtual movements are excluded; colour has no traffic meaning. © OpenStreetMap contributors / ODbL. Reciprocal directed arcs can share geometry; no assigned flow is encoded. This drawing uses the frozen run\_v1 evidence. Later supplementary datasets are separate and are not implied to have entered this scenario.

</details>

[PNG](<../assets/figure-contract-r11/figures/urbana-champaign/sources.png>) · [SVG](<../assets/figure-contract-r11/figures/urbana-champaign/sources.svg>) · [PDF](<../assets/figure-contract-r11/figures/urbana-champaign/sources.pdf>) · [Source record](<../assets/figure-contract-r11/figures/urbana-champaign/sources.source.json>)

<a id="figure-f03-population"></a>

##### Earlier tract population geography

[![Earlier tract population geography](<../assets/figure-contract-r11/figures/urbana-champaign/urbana-champaign-f03_population.svg>)](<../assets/figure-contract-r11/figures/urbana-champaign/urbana-champaign-f03_population.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

Earlier tract and place geography; its whole-tract counts differ from the selected-block demand denominator. 2020 full-tract counts - clipped view

</details>

[PNG](<../assets/figure-contract-r11/figures/urbana-champaign/urbana-champaign-f03_population.png>) · [SVG](<../assets/figure-contract-r11/figures/urbana-champaign/urbana-champaign-f03_population.svg>) · [PDF](<../assets/figure-contract-r11/figures/urbana-champaign/urbana-champaign-f03_population.pdf>) · [Source record](<../assets/figure-contract-r11/figures/urbana-champaign/urbana-champaign-f03_population.source.json>)

<a id="figure-r3-population"></a>

##### Population and household inputs

[![Population and household inputs](<../assets/figure-contract-r11/figures/urbana-champaign/population.svg>)](<../assets/figure-contract-r11/figures/urbana-champaign/population.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

2020 blocks selected by internal point; not earlier whole-tract totals. All 21 zones are retained; population total 52,040. Occupied units total 19,696. Missing household fields are unknown, not zero. Census/ACS allocation is an input, not a simulated traffic quantity. This drawing uses the frozen run\_v1 evidence. Later supplementary datasets are separate and are not implied to have entered this scenario.

</details>

[PNG](<../assets/figure-contract-r11/figures/urbana-champaign/population.png>) · [SVG](<../assets/figure-contract-r11/figures/urbana-champaign/population.svg>) · [PDF](<../assets/figure-contract-r11/figures/urbana-champaign/population.pdf>) · [Source record](<../assets/figure-contract-r11/figures/urbana-champaign/population.source.json>)

<a id="figure-r3-transit"></a>

##### Transit source geography

[![Transit source geography](<../assets/figure-contract-r11/figures/urbana-champaign/transit.svg>)](<../assets/figure-contract-r11/figures/urbana-champaign/transit.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

BTS/NTM archive / 2026-03-09; timetable unknown. 564 stop records; 607 route-shape records, not unique routes or scheduled trips. The gray retained road graph is geographic context, not a transit route model. Source stops and route shapes do not establish legal pedestrian access, operating service, or observed ridership. This drawing uses the frozen run\_v1 evidence. Later supplementary datasets are separate and are not implied to have entered this scenario.

</details>

[PNG](<../assets/figure-contract-r11/figures/urbana-champaign/transit.png>) · [SVG](<../assets/figure-contract-r11/figures/urbana-champaign/transit.svg>) · [PDF](<../assets/figure-contract-r11/figures/urbana-champaign/transit.pdf>) · [Source record](<../assets/figure-contract-r11/figures/urbana-champaign/transit.source.json>)

<a id="generation"></a>

## 01 / Trip generation

<a id="coverage-row-06"></a>

Occupied housing is the production basis. The predeclared rate is 1.2 HBW person trips per occupied unit per day, multiplied by a 25% share for the modeled hour. Applying those assumptions to 19,696 units yields 5,908.8 person trips. Neither factor was fitted to a local travel survey.

A 55% internal capture and an 8% intrazonal fraction of captured demand partition that total into 2,658.96 external or uncaptured trips, 259.9872 intrazonal trips and 2,989.8528 internal interzonal trips. Jobs distribute attractions across zones; normalization ties their total to internal productions. Only the interzonal component advances through the rest of the chain. The updated generation chart shows all 21 zones in stable ID order, alongside the complete demand ledger.

<a id="figure-fs-g01"></a>

##### Trip generation and demand accounting

[![Trip generation and demand accounting](<../assets/figure-contract-r11/figures/urbana-champaign/generation.svg>)](<../assets/figure-contract-r11/figures/urbana-champaign/generation.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

All 21 zones; 08:00–09:00 HBW. The left panel shows saved interzonal productions/attractions. The right panel accounts for all generated persons, including excluded and intrazonal components. No top-12 truncation. Scenario assumptions, not measured trip counts. External and intrazonal components do not enter interzonal assignment; attractions are normalized to productions. This drawing uses the frozen run\_v1 evidence. Later supplementary datasets are separate and are not implied to have entered this scenario.

</details>

[PNG](<../assets/figure-contract-r11/figures/urbana-champaign/generation.png>) · [SVG](<../assets/figure-contract-r11/figures/urbana-champaign/generation.svg>) · [PDF](<../assets/figure-contract-r11/figures/urbana-champaign/generation.pdf>) · [Source record](<../assets/figure-contract-r11/figures/urbana-champaign/generation.source.json>)

<a id="distribution"></a>

## 02 / Trip distribution

<a id="coverage-row-07"></a>

The gravity kernel uses exp(−0.08 × minutes) with directed network impedance. Iterative proportional fitting adjusts the matrix to production and attraction margins. The 0.08 min⁻¹ deterrence coefficient is an engineering assumption. Intrazonal entries remain structural zeros because that demand was removed into the generation ledger.

The saved balance reaches a maximum margin discrepancy of 7.6423×10⁻⁶ person trips after five IPF iterations. Its 380 positive PA movements become 418 positive directed OD pairs under the declared 85% forward and 15% reverse convention. The directed total is 2,989.8528 persons. Two of the 420 possible directed interzonal pairs remain zero; the display must preserve those cells and the real zone-ID ordering. Heatmap color uses log(1 + persons) only for legibility.

<a id="figure-fs-d01"></a>

##### Trip distribution and directed OD margins

[![Trip distribution and directed OD margins](<../assets/figure-contract-r11/figures/urbana-champaign/distribution.svg>)](<../assets/figure-contract-r11/figures/urbana-champaign/distribution.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

Full 21×21 model-zone matrix including zero cells; 418 positive OD pairs and 2,989.852800000 persons in 08:00–09:00 HBW. Colours are log(1+persons); margins are untransformed directed OD totals after PA direction. Every model zone is retained. Zero rows and columns remain visible; intrazonal cells are structural zeros. Labels use the final six digits of long zone IDs. This drawing uses the frozen run\_v1 evidence. Later supplementary datasets are separate and are not implied to have entered this scenario.

</details>

[PNG](<../assets/figure-contract-r11/figures/urbana-champaign/distribution.png>) · [SVG](<../assets/figure-contract-r11/figures/urbana-champaign/distribution.svg>) · [PDF](<../assets/figure-contract-r11/figures/urbana-champaign/distribution.pdf>) · [Source record](<../assets/figure-contract-r11/figures/urbana-champaign/distribution.source.json>)

<a id="mode"></a>

## 03 / Mode choice

<a id="coverage-row-04"></a>

<a id="coverage-row-08"></a>

Driving and walking have separate costs for each OD. The drive alternative adds three minutes for parking and egress to its network time. Walking follows the walk-permitted OSM graph at an assumed 75 m/min with another 0.5 minute of access. These abstractions do not certify property entrances, crossing legality or step-free access.

A conditional logit uses a sensitivity of 0.08 per generalized minute, a drive constant of zero and a walk constant of 0.2. Drive probability varies by OD, approximately from 0.532 to 0.9977. Aggregation produces 2,454.5604 drive persons and 535.2924 walk persons; the split was not inserted as a fixed citywide percentage.

Transit is Not modelled. The archived route and stop geometries lack the selected-day trip and stop-time information required for an OD-specific cost. A transit entry must therefore not look like an ordinary bar predicting zero riders. All 2,989.8528 modeled persons are represented by the two implemented alternatives. Dividing drive persons once by 1.25 persons per vehicle and applying PCE 1.0 produces 1,963.6483 PCE for road assignment.

<a id="figure-fs-m01"></a>

##### Mode choice: demand, cost and availability

[![Mode choice: demand, cost and availability](<../assets/figure-contract-r11/figures/urbana-champaign/mode.svg>)](<../assets/figure-contract-r11/figures/urbana-champaign/mode.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

Saved OD-specific choice in 08:00–09:00 HBW; sums over every positive-demand OD. Persons, person-weighted generalized minutes, and available OD counts have separate axes. Transit is not modeled; no zero bar is shown. Generalized cost includes model time and money terms. Person totals precede the separate occupancy-to-PCE conversion. This drawing uses the frozen run\_v1 evidence. Later supplementary datasets are separate and are not implied to have entered this scenario.

</details>

[PNG](<../assets/figure-contract-r11/figures/urbana-champaign/mode.png>) · [SVG](<../assets/figure-contract-r11/figures/urbana-champaign/mode.svg>) · [PDF](<../assets/figure-contract-r11/figures/urbana-champaign/mode.pdf>) · [Source record](<../assets/figure-contract-r11/figures/urbana-champaign/mode.source.json>)

<a id="figure-f04-transit-reference"></a>

<a id="assignment"></a>

## 04 / Physical-link assignment

<a id="coverage-row-09"></a>

The screened network contains 11,365 physical traversal arcs and 15,237 turn arcs, totaling 26,602. Midpoint road-access proxies connect all 21 zones and all 420 possible interzonal pairs are reachable. Of 32 applicable core restrictions, 31 affect graph transitions and one is vacuous after filtering. Two red-signal-only tags are not treated as turn prohibitions in every signal phase. These are graph checks rather than field-certified parcel-access findings.

The frozen capacity/speed pairs, in PCE/h and km/h respectively, are 450/30 for residential, 550/35 for unclassified, 700/40 for tertiary, 950/45 for secondary and 1,500/50 for primary. BPR parameters are α=0.15 and β=4. At the saved solution, total loaded travel time is about 8,085.2324 PCE-min and the largest mapped segment carries about 546 PCE. Those physical-flow quantities differ from the integrated Beckmann objective.

Static Frank–Wolfe loads the exact Stage 3 vehicle OD on the declared turn-expanded graph. BPR travel time uses soft capacity: a v/c above one is permitted mathematically and does not constitute a hard-capacity violation. The initial loading already passes the 10⁻⁴ relative-gap threshold. The trace consequently contains an initial check and no FW updates; there is no multi-iteration performance experiment to display.

The saved maximum v/c is 1.21296. That fact rules out describing the case as uncongested merely because the update count is zero. The objective is 8,041.086812762 PCE-min at the saved demand of 1,963.648312713 PCE. These are values for this internal morning scenario, not observed network conditions.

The canonical spatial outputs are the city's original FS\_A04 flow and FS\_A05 v/c maps. Their physical mapping contains 11,365 traversal arcs and partitions split :A/:B links into the corresponding pieces of source geometry. The mapped length fractions conserve each source link. The separate A01/A03 charts remain useful model-arc diagnostics; turn arcs in those charts must not be described as additional roads.

<a id="figure-fs-a01"></a>

<a id="figure-fs-a03"></a>

##### Frank–Wolfe: physical-road loading

[![Frank–Wolfe: physical-road loading](<../assets/figure-contract-r11/figures/urbana-champaign/urbana-champaign-fs_a03.svg>)](<../assets/figure-contract-r11/figures/urbana-champaign/urbana-champaign-fs_a03.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

v/c and BPR travel time for top 10 loaded links; v/c&gt;1 is allowed in static BPR. Single-pass engineering scenario; no local empirical calibration. These rankings use the saved solver-arc table and remain separate from the physical-road maps; virtual arcs are not road geometry. 19.303 km2 central urban subarea / weekday AM HBW

</details>

[PNG](<../assets/figure-contract-r11/figures/urbana-champaign/urbana-champaign-fs_a03.png>) · [SVG](<../assets/figure-contract-r11/figures/urbana-champaign/urbana-champaign-fs_a03.svg>) · [PDF](<../assets/figure-contract-r11/figures/urbana-champaign/urbana-champaign-fs_a03.pdf>) · [Source record](<../assets/figure-contract-r11/figures/urbana-champaign/urbana-champaign-fs_a03.source.json>)

<a id="figure-r9-fw-physical-flow"></a>

##### Frank–Wolfe: physical flow and distribution

[![Frank–Wolfe: physical flow and distribution](<../assets/figure-contract-r11/figures/urbana-champaign/fw-physical-flow.svg>)](<../assets/figure-contract-r11/figures/urbana-champaign/fw-physical-flow.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

Saved Urbana–Champaign static Frank–Wolfe endpoint for 08:00–09:00 HBW. The map and 22-bin histogram use the same complete 11,365-link physical-flow vector, including 7,681 exact-zero links; 3,684 links exceed 1e-6 PCE. Flow is PCE accumulated during the declared one-hour period, not persons or flow per simulation time step. The map uses a square-root sequential color scale with original-unit ticks and gray road context; histogram counts are linear and no links are omitted. Turn, access and other nonphysical solver arcs are excluded. Only the saved iteration-0 initialization exists; FW performed zero subsequent updates. Reciprocal directed arcs may overlap geometrically; flows are not summed. Serial A/B road traversals retain their directed first/second geometry halves. These are 11,365 model physical traversals, not the 5,913-link preflight graph or the separate S72 transfer. This is a modeled engineering scenario, not observed traffic. © OpenStreetMap contributors / ODbL 1.0. R11 layout repair: map and all-link histogram share measured top and bottom panel bounds. The original saved physical-link IDs, exact flow vector, geographic vertices, display offsets, histogram edges and counts remain unchanged.

</details>

[PNG](<../assets/figure-contract-r11/figures/urbana-champaign/fw-physical-flow.png>) · [SVG](<../assets/figure-contract-r11/figures/urbana-champaign/fw-physical-flow.svg>) · [PDF](<../assets/figure-contract-r11/figures/urbana-champaign/fw-physical-flow.pdf>) · [Source record](<../assets/figure-contract-r11/figures/urbana-champaign/fw-physical-flow.source.json>)

<details markdown="1">
<summary>Saved initial checks and original endpoint views</summary>

<a id="figure-fs-a04"></a>

</details>

<a id="figure-fs-a05"></a>

##### Frank–Wolfe: physical-road volume / capacity

[![Frank–Wolfe: physical-road volume / capacity](<../assets/figure-contract-r11/figures/urbana-champaign/urbana-champaign-fs_a05.svg>)](<../assets/figure-contract-r11/figures/urbana-champaign/urbana-champaign-fs_a05.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

Actual saved assignment backprojected only to physical traversal segments; model zone access and turn arcs excluded. Single-pass engineering scenario; no local empirical calibration. 19.303 km2 central urban subarea / weekday AM HBW

</details>

[PNG](<../assets/figure-contract-r11/figures/urbana-champaign/urbana-champaign-fs_a05.png>) · [SVG](<../assets/figure-contract-r11/figures/urbana-champaign/urbana-champaign-fs_a05.svg>) · [PDF](<../assets/figure-contract-r11/figures/urbana-champaign/urbana-champaign-fs_a05.pdf>) · [Source record](<../assets/figure-contract-r11/figures/urbana-champaign/urbana-champaign-fs_a05.source.json>)

<a id="results"></a>

## Saved results and assignment checks

<a id="coverage-row-10"></a>

S0's R3 receiver accepted the stored solution, then performed a fresh four-stage replay from the frozen inputs. The saved-table comparison passed and all six negative controls were rejected. Earlier producer checks separately traced hashes through the stages, reconstructed path and link flows, checked OD probabilities and units, and recomputed the objective and full-network gap without calling the optimizer.

The producer's largest reported node-balance residual was 1.71×10⁻¹³ PCE. Its negative fixtures covered a missing generation result, altered OD quantity, an unknown zone, changed choice probability, an unknown saved-path link and deletion of the current assignment result. Computational acceptance establishes the stated model's internal consistency; it does not establish empirical traffic accuracy.

<details markdown="1">
<summary>Saved initial checks and original endpoint views</summary>

<a id="figure-fs-a02"></a>

##### Frank–Wolfe: the saved initial check

<a id="table-r11-urbana-champaign-initial-fw"></a>

[![Frank–Wolfe: the saved initial check](<../assets/figure-contract-r12/figures/urbana-champaign/urbana-champaign-initial-fw.svg>)](<../assets/figure-contract-r12/figures/urbana-champaign/urbana-champaign-initial-fw.svg>)

Only the actual saved iteration 0 is shown: objective 8041.08681276163 PCE·min/h and relative gap 0, against the unchanged 0.0001 stopping gate. There were zero updates. Each panel contains a single numerical point; no missing trajectory or second state is inferred. The companion physical-flow map reads this method’s own saved vector. This frozen original demand instance is not relabelled as a later selected-demand or transit-revision run.

[SVG](<../assets/figure-contract-r12/figures/urbana-champaign/urbana-champaign-initial-fw.svg>) · [PNG](<../assets/figure-contract-r12/figures/urbana-champaign/urbana-champaign-initial-fw.png>) · [PDF](<../assets/figure-contract-r12/figures/urbana-champaign/urbana-champaign-initial-fw.pdf>) · [Source data](<../assets/figure-contract-r12/figures/urbana-champaign/urbana-champaign-initial-fw.source.json>)

</details>

<a id="figure-f08-s2"></a>

##### Multiresolution geographic reference

[![Multiresolution geographic reference](<../assets/figure-contract-r11/figures/urbana-champaign/urbana-champaign-f08_s2.svg>)](<../assets/figure-contract-r11/figures/urbana-champaign/urbana-champaign-f08_s2.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

The earlier 29-object S2 sample, separate from the four-stage demand and assignment. S2 14/16 shown - 12 parent IDs

</details>

[PNG](<../assets/figure-contract-r11/figures/urbana-champaign/urbana-champaign-f08_s2.png>) · [SVG](<../assets/figure-contract-r11/figures/urbana-champaign/urbana-champaign-f08_s2.svg>) · [PDF](<../assets/figure-contract-r11/figures/urbana-champaign/urbana-champaign-f08_s2.pdf>) · [Source record](<../assets/figure-contract-r11/figures/urbana-champaign/urbana-champaign-f08_s2.source.json>)

<a id="parity-urbana-champaign-static-inputs"></a>

## Static assignment: demand margins and physical endpoints

<a id="figure-parity-urbana-champaign-assignment-margins"></a>

##### Static assignment demand margins

[![Static assignment demand margins](<../assets/template-parity-20261008/static-inputs/urbana-champaign/assignment-margins.svg>)](<../assets/template-parity-20261008/static-inputs/urbana-champaign/assignment-margins.svg>)

S72: 72 positive source-zone OD pairs, 72 loaded solver-node OD pairs and 321.629659883 PCE/hour. Origin and destination margins sum the selected assignment PCE by source zone, after the saved mode/occupancy conversion. All source-zone polygons, including any zero selected demand, use a common square-root normalization with ticks in original PCE/hour. S72 has 72 frozen source-zone OD pairs, separate from the original 418-OD city case. M states are the saved public-road midpoint access proxies. Coordinates use the original builder rule: arithmetic mean of the directed source link endpoint coordinates, not a zone centroid. These are modeled assignment-input quantities, not population generation, observed traffic or assigned link flow. Both panels share one map extent; context roads outside this input footprint are clipped only for display.

[Complete evidence · same figure](<#figure-parity-urbana-champaign-assignment-margins>) · [SVG](<../assets/template-parity-20261008/static-inputs/urbana-champaign/assignment-margins.svg>) · [PNG](<../assets/template-parity-20261008/static-inputs/urbana-champaign/assignment-margins.png>) · [PDF](<../assets/template-parity-20261008/static-inputs/urbana-champaign/assignment-margins.pdf>) · [Plot data](<../assets/template-parity-20261008/static-inputs/urbana-champaign/assignment-margins.plot.json>) · [Source record](<../assets/template-parity-20261008/static-inputs/urbana-champaign/assignment-margins.source.json>) · [Caption](<../assets/template-parity-20261008/static-inputs/urbana-champaign/assignment-margins.caption.md>)

<a id="figure-parity-urbana-champaign-assignment-endpoints"></a>

##### Physical demand endpoints

[![Physical demand endpoints](<../assets/template-parity-20261008/static-inputs/urbana-champaign/assignment-endpoints.svg>)](<../assets/template-parity-20261008/static-inputs/urbana-champaign/assignment-endpoints.svg>)

S72: 72 positive source-zone OD pairs, 72 loaded solver-node OD pairs and 321.629659883 PCE/hour. Original access records locate 19 loaded physical origins and 21 loaded physical destinations. Open circles show the frozen access system and filled colors show selected endpoint PCE/hour. The largest loaded endpoint in each panel is labelled by its physical source ID (or the saved M-state road-midpoint identifier). Each side sums to the same total; this aggregation is for display only. S72 has 72 frozen source-zone OD pairs, separate from the original 418-OD city case. M states are the saved public-road midpoint access proxies. Coordinates use the original builder rule: arithmetic mean of the directed source link endpoint coordinates, not a zone centroid. These are modeled assignment-input quantities, not population generation, observed traffic or assigned link flow. Both panels share one map extent; context roads outside this input footprint are clipped only for display.

[Complete evidence · same figure](<#figure-parity-urbana-champaign-assignment-endpoints>) · [SVG](<../assets/template-parity-20261008/static-inputs/urbana-champaign/assignment-endpoints.svg>) · [PNG](<../assets/template-parity-20261008/static-inputs/urbana-champaign/assignment-endpoints.png>) · [PDF](<../assets/template-parity-20261008/static-inputs/urbana-champaign/assignment-endpoints.pdf>) · [Plot data](<../assets/template-parity-20261008/static-inputs/urbana-champaign/assignment-endpoints.plot.json>) · [Source record](<../assets/template-parity-20261008/static-inputs/urbana-champaign/assignment-endpoints.source.json>) · [Caption](<../assets/template-parity-20261008/static-inputs/urbana-champaign/assignment-endpoints.caption.md>)

<a id="parity-urbana-champaign-construction"></a>

## Time-expanded network and path examples

<a id="figure-parity-urbana-champaign-time-layers"></a>

##### Time-expanded network in layers

[![Time-expanded network in layers](<../assets/template-parity-20261008/construction/urbana-champaign/time-layers.svg>)](<../assets/template-parity-20261008/construction/urbana-champaign/time-layers.svg>)

Urbana Champaign: the highlighted three saved arcs follow two physical road movements joined by a zero-time turn. The selected first fragment uses two full physical roads; the earlier split-road midpoint segment remains context only. Only the seven already public arcs are drawn; no additional graph arcs or alternative routes are asserted. Physical node labels are schematic roles, not invented node identifiers. A construction example is not an observed trajectory or capacity-active proof. The slanted planes and horizontal positions are schematic display coordinates. A−/A+ and B−/B+ denote entry/exit routing states, not original intersections. Exact state IDs, physical-road IDs and time indices are retained in plot data.

[Complete evidence · same figure](<#figure-parity-urbana-champaign-time-layers>) · [SVG](<../assets/template-parity-20261008/construction/urbana-champaign/time-layers.svg>) · [PNG](<../assets/template-parity-20261008/construction/urbana-champaign/time-layers.png>) · [PDF](<../assets/template-parity-20261008/construction/urbana-champaign/time-layers.pdf>) · [Plot data](<../assets/template-parity-20261008/construction/urbana-champaign/time-layers.plot.json>) · [Source record](<../assets/template-parity-20261008/construction/urbana-champaign/time-layers.source.json>) · [Caption](<../assets/template-parity-20261008/construction/urbana-champaign/time-layers.caption.md>)

<a id="figure-parity-urbana-champaign-local-construction"></a>

##### Local construction details

[![Local construction details](<../assets/template-parity-20261008/construction/urbana-champaign/local-construction.svg>)](<../assets/template-parity-20261008/construction/urbana-champaign/local-construction.svg>)

Urbana Champaign: panels map two source-directed physical roads to four routing entry/exit states and their time-indexed movements. The selected first fragment uses two full physical roads; the earlier split-road midpoint segment remains context only. Only the seven already public arcs are drawn; no additional graph arcs or alternative routes are asserted. Physical node labels are schematic roles, not invented node identifiers. A construction example is not an observed trajectory or capacity-active proof. The turn has zero elapsed time; physical road durations are positive. No waiting arc is drawn and terminal bookkeeping states are outside this local excerpt. Plot data carry all exact source IDs, field values, and short-label aliases.

[Complete evidence · same figure](<#figure-parity-urbana-champaign-local-construction>) · [SVG](<../assets/template-parity-20261008/construction/urbana-champaign/local-construction.svg>) · [PNG](<../assets/template-parity-20261008/construction/urbana-champaign/local-construction.png>) · [PDF](<../assets/template-parity-20261008/construction/urbana-champaign/local-construction.pdf>) · [Plot data](<../assets/template-parity-20261008/construction/urbana-champaign/local-construction.plot.json>) · [Source record](<../assets/template-parity-20261008/construction/urbana-champaign/local-construction.source.json>) · [Caption](<../assets/template-parity-20261008/construction/urbana-champaign/local-construction.caption.md>)

<a id="parity-urbana-champaign-finite"></a>

## Optimization on the time-expanded network

<a id="figure-parity-urbana-champaign-cg-phase1"></a>

##### Phase I: artificial-flow clearance

[![Phase I: artificial-flow clearance](<../assets/template-parity-20261008/optimization/urbana-champaign/cg-phase1.svg>)](<../assets/template-parity-20261008/optimization/urbana-champaign/cg-phase1.svg>)

The sole saved Phase I restricted-master solution contains four path-flow variables followed by 373 nonnegative artificial capacity-slack variables. They relax shared physical-arc capacity rows; this model has no commodity-level artificial-flow variables. Both panels use the saved state directly: the total is exactly 0 PCE and every one of the 373 capacity slacks is exactly zero. Panel b preserves the complete saved capacity-row order; plot data link each row to its original dynamic-arc index and ID. The dotted line is the original 1e−8 PCE tolerance on total artificial slack; the heatmap uses 0 to that same value only as its color reference. Four input-cost seed paths already satisfy the bounded instance. A single recorded solve is shown without an invented multi-round trajectory. Phase I capacity feasibility remains separate from Phase II real cost and independent full-DAG pricing. Private local derivative of the saved numerical state; no new public asset release or optimizer run is claimed.

[Complete evidence · same figure](<#figure-parity-urbana-champaign-cg-phase1>) · [SVG](<../assets/template-parity-20261008/optimization/urbana-champaign/cg-phase1.svg>) · [PNG](<../assets/template-parity-20261008/optimization/urbana-champaign/cg-phase1.png>) · [PDF](<../assets/template-parity-20261008/optimization/urbana-champaign/cg-phase1.pdf>) · [Plot data](<../assets/template-parity-20261008/optimization/urbana-champaign/cg-phase1.plot.json>) · [Source record](<../assets/template-parity-20261008/optimization/urbana-champaign/cg-phase1.source.json>) · [Caption](<../assets/template-parity-20261008/optimization/urbana-champaign/cg-phase1.caption.md>)

<a id="figure-parity-urbana-champaign-cg-phase2"></a>

##### Phase II objective

[![Phase II objective](<../assets/figure-contract-r12/figures/urbana-champaign/cg-phase2.svg>)](<../assets/figure-contract-r12/figures/urbana-champaign/cg-phase2.svg>)

One actual saved Phase II round. CG real cost is 0.3759836651335291 PCE·min; the separate same-graph LP reference is 0.37598366513352877 PCE·min. The marker and dashed reference can coincide at displayed precision. No Phase I artificial objective is connected to this real-cost objective. No new column after the four seed paths.

[Complete evidence · same figure](<#figure-parity-urbana-champaign-cg-phase2>) · [SVG](<../assets/figure-contract-r12/figures/urbana-champaign/cg-phase2.svg>) · [PNG](<../assets/figure-contract-r12/figures/urbana-champaign/cg-phase2.png>) · [PDF](<../assets/figure-contract-r12/figures/urbana-champaign/cg-phase2.pdf>) · [Plot data](<../assets/figure-contract-r12/figures/urbana-champaign/cg-phase2.plot.json>) · [Source record](<../assets/figure-contract-r12/figures/urbana-champaign/cg-phase2.source.json>)

<a id="figure-parity-urbana-champaign-cg-pricing"></a>

##### Independent pricing closure

[![Independent pricing closure](<../assets/figure-contract-r12/figures/urbana-champaign/cg-pricing.svg>)](<../assets/figure-contract-r12/figures/urbana-champaign/cg-pricing.svg>)

The saved full-DAG pricing check is zero in both phases, against the frozen absolute tolerance 1e-7. Phase I reduced cost is dimensionless; Phase II reduced cost is minutes, so they have separate axes. Each phase has one actual round, four seed paths, and no new columns. Public data contain the global minimum per phase, not separate per-demand minima; no per-demand bars are fabricated.

[Complete evidence · same figure](<#figure-parity-urbana-champaign-cg-pricing>) · [SVG](<../assets/figure-contract-r12/figures/urbana-champaign/cg-pricing.svg>) · [PNG](<../assets/figure-contract-r12/figures/urbana-champaign/cg-pricing.png>) · [PDF](<../assets/figure-contract-r12/figures/urbana-champaign/cg-pricing.pdf>) · [Plot data](<../assets/figure-contract-r12/figures/urbana-champaign/cg-pricing.plot.json>) · [Source record](<../assets/figure-contract-r12/figures/urbana-champaign/cg-pricing.source.json>)

<a id="figure-parity-urbana-champaign-lr-bounds"></a>

##### Lagrangian bounds and certified gap

[![Lagrangian bounds and certified gap](<../assets/figure-contract-r12/figures/urbana-champaign/lr-bounds.svg>)](<../assets/figure-contract-r12/figures/urbana-champaign/lr-bounds.svg>)

One actual LR iteration. Best valid lower is 0.3759836651335291 PCE·min; own recovered feasible upper is 0.37598366513352871 PCE·min. The certified gap is max(0,(U−L)/max(1,|U|)) = 0; the frozen gate is 1%. Lower and upper are separate markers at the same recorded iteration; they coincide to displayed precision. Tiny signed floating-point differences remain in the plot data. Capacities are nonbinding in this T4 pulse; this does not prove that city area caused the short trace.

[Complete evidence · same figure](<#figure-parity-urbana-champaign-lr-bounds>) · [SVG](<../assets/figure-contract-r12/figures/urbana-champaign/lr-bounds.svg>) · [PNG](<../assets/figure-contract-r12/figures/urbana-champaign/lr-bounds.png>) · [PDF](<../assets/figure-contract-r12/figures/urbana-champaign/lr-bounds.pdf>) · [Plot data](<../assets/figure-contract-r12/figures/urbana-champaign/lr-bounds.plot.json>) · [Source record](<../assets/figure-contract-r12/figures/urbana-champaign/lr-bounds.source.json>)

<a id="figure-parity-urbana-champaign-lr-prices"></a>

##### Capacity prices at the best dual bound

[![Capacity prices at the best dual bound](<../assets/template-parity-20261008/optimization/urbana-champaign/lr-prices.svg>)](<../assets/template-parity-20261008/optimization/urbana-champaign/lr-prices.svg>)

The saved best-bound multiplier vector contains 1,429,496 original dynamic-arc entries, all exactly zero. Consequently there is no nonempty top-price ranking. The second panel sums every timed multiplier by its real 30-second departure index, including the zero sums; source/sink entries without a time suffix are excluded only from the time aggregation. Empty positive support is shown explicitly, not replaced with another city or method. These numerical details remain a private local preview.

[Complete evidence · same figure](<#figure-parity-urbana-champaign-lr-prices>) · [SVG](<../assets/template-parity-20261008/optimization/urbana-champaign/lr-prices.svg>) · [PNG](<../assets/template-parity-20261008/optimization/urbana-champaign/lr-prices.png>) · [PDF](<../assets/template-parity-20261008/optimization/urbana-champaign/lr-prices.pdf>) · [Plot data](<../assets/template-parity-20261008/optimization/urbana-champaign/lr-prices.plot.json>) · [Source record](<../assets/template-parity-20261008/optimization/urbana-champaign/lr-prices.source.json>) · [Caption](<../assets/template-parity-20261008/optimization/urbana-champaign/lr-prices.caption.md>)

<a id="figure-parity-urbana-champaign-lr-recovery"></a>

##### Path-pool growth and primal recovery

[![Path-pool growth and primal recovery](<../assets/template-parity-20261008/optimization/urbana-champaign/lr-recovery.svg>)](<../assets/template-parity-20261008/optimization/urbana-champaign/lr-recovery.svg>)

One actual path-pool record and one actual feasible recovery call are shown in separate panels. The four paths belong to this method’s own pool; the objective is the saved recovered feasible upper bound. No intermediate call, pool growth or capacity-price effect is invented. A filled marker denotes a feasible call, as in Boston/Hong Kong.

[Complete evidence · same figure](<#figure-parity-urbana-champaign-lr-recovery>) · [SVG](<../assets/template-parity-20261008/optimization/urbana-champaign/lr-recovery.svg>) · [PNG](<../assets/template-parity-20261008/optimization/urbana-champaign/lr-recovery.png>) · [PDF](<../assets/template-parity-20261008/optimization/urbana-champaign/lr-recovery.pdf>) · [Plot data](<../assets/template-parity-20261008/optimization/urbana-champaign/lr-recovery.plot.json>) · [Source record](<../assets/template-parity-20261008/optimization/urbana-champaign/lr-recovery.source.json>) · [Caption](<../assets/template-parity-20261008/optimization/urbana-champaign/lr-recovery.caption.md>)

<a id="reproduction"></a>

## Reproduction and input identity

<a id="coverage-row-19"></a>

The public reproducibility archive is not yet available.

Python 3.11+ standard library for numerical stages/verifier

Matplotlib, NumPy, Shapely and Pillow for figures and publication checks

Python-Markdown for HTML rendering

Runtime versions above are recorded producer facts. The V presentation task does not replace or upgrade the frozen numerical environment.

<a id="historic-facility-photos"></a>

## Historic facility photos (2016)

These two credited 2016 Commons thumbnails give historical facility context only. They do not establish a present-day entrance, camera ground target, GPS mode or a shared trip with the 2025 trace. The C02 route, trace, geometry bridge and technical receipt remain private.

[![2016 U.S. Post Office / Springer Cultural Center facility front view](<../assets/six-city-evidence-r2/urbana-champaign/post_office_front_2016.jpg>)](<../assets/six-city-evidence-r2/urbana-champaign/post_office_front_2016.jpg>)

Killivalavan Solai / Wikimedia Commons, U.S. Post Office / Springer Cultural Center facility scene, 28 September 2016. Unmodified Commons thumbnail, CC BY-SA 4.0: https://creativecommons.org/licenses/by-sa/4.0/. Original: https://commons.wikimedia.org/wiki/File%3AU.S.\_Post\_Office\_front\_view.jpg. Historical facility context only; this photograph does not verify a present-day door, camera ground target, GPS travel mode or a shared trip with the 2025 trace. [Original Commons file](<https://commons.wikimedia.org/wiki/File%3AU.S._Post_Office_front_view.jpg>) · [CC BY-SA 4.0](<https://creativecommons.org/licenses/by-sa/4.0/>)

[![2016 U.S. Post Office / Springer Cultural Center facility oblique view](<../assets/six-city-evidence-r2/urbana-champaign/post_office_oblique_2016.jpg>)](<../assets/six-city-evidence-r2/urbana-champaign/post_office_oblique_2016.jpg>)

Killivalavan Solai / Wikimedia Commons, U.S. Post Office / Springer Cultural Center facility scene, 28 September 2016. Unmodified Commons thumbnail, CC BY-SA 4.0: https://creativecommons.org/licenses/by-sa/4.0/. Original: https://commons.wikimedia.org/wiki/File%3AU.S.\_Post\_Office\_oblique\_view.jpg. Historical facility context only; this photograph does not verify a present-day door, camera ground target, GPS travel mode or a shared trip with the 2025 trace. [Original Commons file](<https://commons.wikimedia.org/wiki/File%3AU.S._Post_Office_oblique_view.jpg>) · [CC BY-SA 4.0](<https://creativecommons.org/licenses/by-sa/4.0/>)

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

Road speed, capacity, access penalties, occupancy and utility parameters are explicit proxies. No observed link counts or local household travel sample calibrates this scenario. Excluded external and intrazonal travel is accounted for but is not routed as internal OD. Transit assignment, freight, emissions, safety, spillback and future-year forecasting are outside the calculation.

Frozen-input reproduction and source acquisition are different operations. A saved-result check invokes the verifier alone; a fresh solve writes a new output directory. Re-downloading OSM, Census or BTS data may produce new bytes and is outside a claim about the frozen hashes. Historical producer commands are retained as provenance, with the distributable command package still unavailable.

Map attribution remains © OpenStreetMap contributors, ODbL 1.0. Census PL and LEHD supply the demographic and workplace references. The BTS reference retains its CC BY 3.0 US notice. Publishing these derived displays does not authorize distributing raw feeds, private observations or unlisted material.

The older S2 illustration is retained because it contributes different information from the four-stage model. It covers 29 sample objects at levels 12, 14 and 16; it is not a complete demand allocation or full-area network representation.

Earlier observation work includes a screened, timed 27-point GPX segment without an accepted map-matched trip. OSM-tagged crossings, signals, stops and entrances also lack photo-confirmed geometry. A private iCAP pedestrian series and the historic GPX sample did not calibrate the HBW model. These source limits remain visible without publishing precise traces or private records.

<a id="sources"></a>

## Sources and display provenance

- [2020 Census PL 94-171 block release](<https://www2.census.gov/geo/tiger/TIGER2020PL/LAYER/TABBLOCK/2020/>)
- [Census LEHD LODES8 Illinois 2023 WAC file](<https://lehd.ces.census.gov/data/lodes/LODES8/il/wac/>)
- [US DOT/BTS National Transit Map](<https://www.bts.gov/national-transit-map>)
- [ODbL 1.0](<https://www.openstreetmap.org/copyright>)
- [CC BY 3.0 US](<https://creativecommons.org/licenses/by/3.0/us/>)

[Return to the city atlas](<../index.html#urbana-champaign>) · [Back to top](<#document-top>)

<a id="r3-method-transfer"></a>

## Accepted method results

The accepted 418-OD four-stage case, selected S72 (321.6296599 PCE/h) and T4 pulse (0.0516231483 PCE) remain separate instances. Native26/52 retain all nine saved outer checks and accepted outer-9 endpoints. The dated transit revision supports its own 418-OD FW assignment; the same-S72 Algorithm B result and T4 exact-DAG LP, CG, LR and ADMM are also accepted.

<dl class="accepted-method-notes"><dt>S_FW</dt><dd>ACCEPTED · initial loading passes; no FW update or acceleration claim</dd><dt>S_FINITE</dt><dd>ACCEPTED · same selected OD and complete 26,602 solver-link incidence</dd><dt>S_NATIVE26</dt><dd>S0 ACCEPTED · outer9 · Accepted original-space outer-9 endpoint.</dd><dt>S_NATIVE52</dt><dd>S0 ACCEPTED · outer9 · Accepted original-space outer-9 endpoint.</dd><dt>T_LP_EXACT_DAG</dt><dd>ACCEPTED · Accepted same-instance mathematical LP endpoint with complete-DAG primal/dual certificate.</dd><dt>T_CG</dt><dd>ACCEPTED · four self-generated paths; physical capacities nonbinding</dd><dt>T_LR</dt><dd>ACCEPTED · one-iteration bound closure is this low-demand case result</dd><dt>T_ADMM</dt><dd>ACCEPTED · main stage passed and exact-state cold confirmation; no tier2 run</dd></dl>

### Selected static methods

<a id="figure-r9-s72-fw-map-distribution"></a>

[![S72 Frank–Wolfe physical loading and distribution](<../assets/plot-semantics-r9/urbana-champaign/s72-fw-map-distribution.svg>)](<../assets/plot-semantics-r9/urbana-champaign/s72-fw-map-distribution.svg>)

**S72 Frank–Wolfe physical loading and distribution.** Saved S72 instance: 72 selected OD pairs, 321.6296598827645 PCE in one declared hour, and 360 frozen paths. Each method reads its own saved physical-link vector; none is substituted from another method. All 11,365 physical solver arcs are shown, including 42 separate A/B geometry halves for 21 split source links; turn movements are excluded. The all-link histogram includes exact zeros. Absolute maps share a square-root colour scale in PCE/hour and constant overlay width. Only coloured map overlays suppress absolute values at most 1e-12 PCE/h, while all values remain in plot data and histograms. This is distinct from the original 418-OD city case.  FW stopped at its initial check with zero updates. The figure represents the full saved endpoint loading, not a convergence trajectory.

[SVG](<../assets/plot-semantics-r9/urbana-champaign/s72-fw-map-distribution.svg>) · [PNG](<../assets/plot-semantics-r9/urbana-champaign/s72-fw-map-distribution.png>) · [PDF](<../assets/plot-semantics-r9/urbana-champaign/s72-fw-map-distribution.pdf>) · [Plot data](<../assets/plot-semantics-r9/urbana-champaign/s72-fw-map-distribution.plot_data.json>) · [Caption](<../assets/plot-semantics-r9/urbana-champaign/s72-fw-map-distribution.caption.md>) · [Source record](<../assets/plot-semantics-r9/urbana-champaign/s72-fw-map-distribution.source.json>) · [Same figure on homepage](<../index.html?atlas-view=full#atlas-r9-urbana-champaign-s72-fw-map-distribution>)

<a id="figure-r9-s72-finite-map-distribution"></a>

##### Finite paths: physical flow and distribution

[![Finite paths: physical flow and distribution](<../assets/figure-contract-r11/figures/urbana-champaign/s72-finite-map-distribution.svg>)](<../assets/figure-contract-r11/figures/urbana-champaign/s72-finite-map-distribution.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

Saved S72 instance: 72 selected OD pairs, 321.6296598827645 PCE in one declared hour, and 360 frozen paths. Each method reads its own saved physical-link vector; none is substituted from another method. All 11,365 physical solver arcs are shown, including 42 separate A/B geometry halves for 21 split source links; turn movements are excluded. The all-link histogram includes exact zeros. Absolute maps share a square-root colour scale in PCE/hour and constant overlay width. Only coloured map overlays suppress absolute values at most 1e-12 PCE/h, while all values remain in plot data and histograms. This is distinct from the original 418-OD city case. © OpenStreetMap contributors, ODbL 1.0; engineering scenario, not observed traffic. All 72 OD mass residuals are calculated from the 360 saved path flows minus the frozen per-OD demands; all are exactly zero. The frozen independent endpoint check is SOLVED\_WITHIN\_DECLARED\_TOLERANCE. No optimizer or path-generation code is run. R11 layout repair: the map and histogram share measured bounds. The 72 zero-valued OD residuals are retained in the linked endpoint table, with the frozen mass-balance gates (absolute 1e-6 PCE; relative 1e-8; total OD L1 relative 1e-8). Their absence from a third status-only plot does not remove any OD record or change the accepted status.

</details>

[PNG](<../assets/figure-contract-r11/figures/urbana-champaign/s72-finite-map-distribution.png>) · [SVG](<../assets/figure-contract-r11/figures/urbana-champaign/s72-finite-map-distribution.svg>) · [PDF](<../assets/figure-contract-r11/figures/urbana-champaign/s72-finite-map-distribution.pdf>) · [Source record](<../assets/figure-contract-r11/figures/urbana-champaign/s72-finite-map-distribution.source.json>) · [Complete OD endpoint table](<../assets/figure-contract-r11/figures/urbana-champaign/s72-finite-map-distribution.endpoint-table.md>)

<details markdown="1">
<summary>Original scalar comparison and selected static map</summary>

<a id="uc-r3-static-comparison"></a>

##### Static objective and optimality checks

<a id="table-r11-uc-s72-method-endpoints"></a>

[![Static objective and optimality checks](<../assets/figure-contract-r12/figures/urbana-champaign/uc-s72-method-endpoints.svg>)](<../assets/figure-contract-r12/figures/urbana-champaign/uc-s72-method-endpoints.svg>)

FW and finite-path K=5 each retain their own independent saved S72 endpoint. The identical Beckmann values are shown as two distinct method-category points, with signed full-graph gaps on a separate axis. Method categories are not iterations. The existing FW and finite-path physical-flow maps and all-link histograms remain the primary spatial evidence; these scalar checks are supplementary. The 418-OD full-city and revised-transit demands are separate instances.

[SVG](<../assets/figure-contract-r12/figures/urbana-champaign/uc-s72-method-endpoints.svg>) · [PNG](<../assets/figure-contract-r12/figures/urbana-champaign/uc-s72-method-endpoints.png>) · [PDF](<../assets/figure-contract-r12/figures/urbana-champaign/uc-s72-method-endpoints.pdf>) · [Source data](<../assets/figure-contract-r12/figures/urbana-champaign/uc-s72-method-endpoints.source.json>)

</details>

<a id="figure-r9-native-map-differences"></a>

[![Native L3 physical flows against S72 FW](<../assets/plot-semantics-r9/urbana-champaign/native-map-differences.svg>)](<../assets/plot-semantics-r9/urbana-champaign/native-map-differences.svg>)

**Native L3 physical flows against S72 FW.** Urbana–Champaign Native L3 accepted outer 9, on the unchanged S72 instance: 72 selected OD pairs, 321.6296598827645 PCE in one declared hour and 360 frozen paths. The upper row shows rank 26 own saved explicit physical-link v, followed by signed rank 26−FW and rank 52−FW differences from the same-instance own saved FW vector. The lower 22-bin linear histogram contains all 11,365 rank 26 physical solver arcs, including zeros and near-zero values. All 42 A/B halves for 21 split source roads retain their own saved values and geometry; serial pieces are never added together. The 15,237 turn-movement rows are excluded from these physical-road maps and histogram. The absolute map uses a square-root colour scale; the difference maps share one symmetric zero-centred scale, all in PCE/hour. Maximum absolute rank 26−FW and rank 52−FW physical-link differences are 5.94165001644e-08 and 2.7191668373e-05 PCE/h. These endpoint discrepancies are not evidence of traffic improvement or comparative solver speed. Raw vectors are unmodified, with no clipping or replacement; both own explicit vectors have minimum exactly zero. Only colored overlays hide absolute values at most 1e-12 PCE/h, while the complete gray road geometry, histogram and plot data retain every link. Both endpoints have saved original-space acceptance and two replay receipts; the existing current conservation figure remains complementary evidence. This bounded S72 case is distinct from the full 418-OD city case and the four-OD time-expanded experiment.

[SVG](<../assets/plot-semantics-r9/urbana-champaign/native-map-differences.svg>) · [PNG](<../assets/plot-semantics-r9/urbana-champaign/native-map-differences.png>) · [PDF](<../assets/plot-semantics-r9/urbana-champaign/native-map-differences.pdf>) · [Plot data](<../assets/plot-semantics-r9/urbana-champaign/native-map-differences.plot_data.json>) · [Caption](<../assets/plot-semantics-r9/urbana-champaign/native-map-differences.caption.md>) · [Source record](<../assets/plot-semantics-r9/urbana-champaign/native-map-differences.source.json>) · [Same figure on homepage](<../index.html?atlas-view=full#atlas-r9-urbana-champaign-native-map-differences>)

<a id="uc-r3-native-check"></a>

##### Native L3: original-OD conservation

<a id="table-r11-uc-native-od-gates"></a>

[![Native L3: original-OD conservation](<../assets/figure-contract-r12/figures/urbana-champaign/uc-native-od-conservation.svg>)](<../assets/figure-contract-r12/figures/urbana-champaign/uc-native-od-conservation.svg>)

All nine actual saved outer checks are retained for the accepted S72 Native26 and Native52 runs, using the original 72-OD conservation metric. The frozen gate is 1e−6 PCE/h; both runs first meet it at outer 9. Lines join actual saved iterations only, without smoothing or invented points. Earlier high residuals belong to these ultimately accepted trajectories. The two panels use identical ordinate limits. Rank 26 uses 98 path coordinates and rank 52 uses 124; each retains 26,602 explicit-link variables. These dimension counts are distinct from iteration counts.

[SVG](<../assets/figure-contract-r12/figures/urbana-champaign/uc-native-od-conservation.svg>) · [PNG](<../assets/figure-contract-r12/figures/urbana-champaign/uc-native-od-conservation.png>) · [PDF](<../assets/figure-contract-r12/figures/urbana-champaign/uc-native-od-conservation.pdf>) · [Source data](<../assets/figure-contract-r12/figures/urbana-champaign/uc-native-od-conservation.source.json>)

<details markdown="1">
<summary>Original scalar comparison and selected static map</summary>

<a id="uc-r3-static-map"></a>

</details>

### Finite graph and actual paths

<a id="uc-r3-time-layers"></a>

##### Column generation: saved time-layer route

[![Column generation: saved time-layer route](<../assets/figure-contract-r11/figures/urbana-champaign/urbana-champaign-time-layers.svg>)](<../assets/figure-contract-r11/figures/urbana-champaign/urbana-champaign-time-layers.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

Actual route through selected time layers The seven selected saved arcs follow one computed route: teal marks physical-road traversal and blue marks zero-time turn transitions. State spacing is schematic; no assigned-flow magnitude is encoded.

</details>

[PNG](<../assets/figure-contract-r11/figures/urbana-champaign/urbana-champaign-time-layers.png>) · [SVG](<../assets/figure-contract-r11/figures/urbana-champaign/urbana-champaign-time-layers.svg>) · [PDF](<../assets/figure-contract-r11/figures/urbana-champaign/urbana-champaign-time-layers.pdf>) · [Source record](<../assets/figure-contract-r11/figures/urbana-champaign/urbana-champaign-time-layers.source.json>)

<a id="uc-r3-computed-paths"></a>

##### Column generation: computed paths

[![Column generation: computed paths](<../assets/figure-contract-r11/figures/urbana-champaign/urbana-champaign-computed-paths.svg>)](<../assets/figure-contract-r11/figures/urbana-champaign/urbana-champaign-computed-paths.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

Computed paths: time layers and fixed costs

</details>

[PNG](<../assets/figure-contract-r11/figures/urbana-champaign/urbana-champaign-computed-paths.png>) · [SVG](<../assets/figure-contract-r11/figures/urbana-champaign/urbana-champaign-computed-paths.svg>) · [PDF](<../assets/figure-contract-r11/figures/urbana-champaign/urbana-champaign-computed-paths.pdf>) · [Source record](<../assets/figure-contract-r11/figures/urbana-champaign/urbana-champaign-computed-paths.source.json>)

<a id="scope-vs-demand-20261008"></a>

### Original T4: demand and capacity diagnosis

Private local review. The following data describe the accepted old T4 diagnostic. Frozen new-candidate rules do not constitute an executed candidate.

The original T4 selects four OD pairs by the frozen rule and loads only their first five-minute bin: 0.05162314826794134 PCE (0.6194777792152961 PCE/h before the 1/12 time factor). This is separate from both the old 418-OD hourly total and the later CUMTD choice revision. On this frozen graph, capacity is nonbinding: the minimum timed physical-arc capacity is 3.75 PCE and maximum used-arc utilization is 0.6775913418476398%. Geographic support effects have not been tested; this does not prove the area too small.

New candidate: rules frozen; not executed; waiting for the original shared compute lock. The recorded lock timeout occurred before input screening. No new time graph, solve, optimum or capacity-active conclusion exists. S0 acceptance here covers the old T4 diagnosis only.

<a id="uc-t4-demand-ledger"></a>

##### Original T4: selected demand and first five-minute bin

[![Original T4: selected demand and first five-minute bin](<../assets/choicefw-scope-20261008/urbana-champaign/FIG01_DEMAND_LEDGER.svg>)](<../assets/choicefw-scope-20261008/urbana-champaign/FIG01_DEMAND_LEDGER.svg>)

Original T4 demand accounting. The 418-OD hourly total, four selected hourly OD pairs, and selected first five-minute bin use different time windows. The four pairs follow frozen hash rank; the small first-bin mass is not a sampling rate. No new candidate is shown.

Private local review: detailed old-T4 plot data are linked below; they remain outside the public release.

[Full figure](<../assets/choicefw-scope-20261008/urbana-champaign/FIG01_DEMAND_LEDGER.svg>) · [PNG](<../assets/choicefw-scope-20261008/urbana-champaign/FIG01_DEMAND_LEDGER.png>) · [Approved caption](<../assets/choicefw-scope-20261008/urbana-champaign/FIG01_DEMAND_LEDGER.caption.md>) · [Source and scope](<../assets/choicefw-scope-20261008/urbana-champaign/SCOPE_VS_DEMAND_PUBLIC_NOTE.md>) · [Release and SHA](<../assets/choicefw-scope-20261008/CONSUMPTION.json>) · [Private plot data · OD ledger](<../assets/private-scope-vs-demand-r1/urbana-champaign/OD_LEDGER.csv>) · [Private source and SHA](<../assets/private-scope-vs-demand-r1/urbana-champaign/RECEIPT.json>)

<a id="uc-t4-capacity-use"></a>

##### Original T4: timed physical arc utilization

[![Original T4: timed physical arc utilization](<../assets/choicefw-scope-20261008/urbana-champaign/FIG02_T4_CAPACITY_USE.svg>)](<../assets/choicefw-scope-20261008/urbana-champaign/FIG02_T4_CAPACITY_USE.svg>)

Utilization on 373 used timed physical arcs of original T4, sorted by load/capacity. Maximum 0.6775913418476398%; dotted 0.5% is a visual guide, not a capacity threshold. No timed physical arc is shared across OD; 28 physical link IDs recur at different times. This does not certify a new candidate.

Private local review: detailed old-T4 plot data are linked below; they remain outside the public release.

[Full figure](<../assets/choicefw-scope-20261008/urbana-champaign/FIG02_T4_CAPACITY_USE.svg>) · [PNG](<../assets/choicefw-scope-20261008/urbana-champaign/FIG02_T4_CAPACITY_USE.png>) · [Approved caption](<../assets/choicefw-scope-20261008/urbana-champaign/FIG02_T4_CAPACITY_USE.caption.md>) · [Source and scope](<../assets/choicefw-scope-20261008/urbana-champaign/SCOPE_VS_DEMAND_PUBLIC_NOTE.md>) · [Release and SHA](<../assets/choicefw-scope-20261008/CONSUMPTION.json>) · [Private plot data · timed arcs](<../assets/private-scope-vs-demand-r1/urbana-champaign/T4_POSITIVE_ARCS.csv>) · [Private path composition](<../assets/private-scope-vs-demand-r1/urbana-champaign/T4_PATH_COMPOSITION.json>) · [Private physical paths](<../assets/private-scope-vs-demand-r1/urbana-champaign/T4_PHYSICAL_PATHS.json>) · [Private source and SHA](<../assets/private-scope-vs-demand-r1/urbana-champaign/RECEIPT.json>)

[Complete scoped source notice](<../assets/choicefw-scope-20261008/urbana-champaign/SCOPE_VS_DEMAND_PUBLIC_NOTE.md>) · [Saved semantic checks](<../assets/choicefw-scope-20261008/urbana-champaign/SEMANTIC_NEGATIVE_TESTS.json>)

### Finite-time optimization

<a id="uc-r3-cg-phase1"></a>

##### Column generation: Phase I feasibility

<a id="table-r11-uc-t4-cg-checks"></a>

[![Column generation: Phase I feasibility](<../assets/figure-contract-r12/figures/urbana-champaign/cg-phase1.svg>)](<../assets/figure-contract-r12/figures/urbana-champaign/cg-phase1.svg>)

Phase I has one actual saved restricted-master round. Its total artificial flow is 0 PCE. A single marker retains that real record; there is no interpolated trajectory. Four seed paths suffice. Commodity-level artificial-flow history was not included in these public plot files, so no heatmap is inferred. Phase I feasibility is separate from Phase II real cost and full-DAG pricing closure.

[SVG](<../assets/figure-contract-r12/figures/urbana-champaign/cg-phase1.svg>) · [PNG](<../assets/figure-contract-r12/figures/urbana-champaign/cg-phase1.png>) · [PDF](<../assets/figure-contract-r12/figures/urbana-champaign/cg-phase1.pdf>) · [Source data](<../assets/figure-contract-r12/figures/urbana-champaign/cg-phase1.source.json>)

<a id="uc-r3-cg-objective"></a>

##### Column generation: Phase II real cost

[Phase II objective](<#figure-parity-urbana-champaign-cg-phase2>)

<a id="uc-r3-cg-closure"></a>

##### Column generation: full-DAG pricing closure

[Independent pricing closure](<#figure-parity-urbana-champaign-cg-pricing>)

<a id="uc-r3-lr-bounds"></a>

##### Lagrangian bounds and certified gap

<a id="table-r11-uc-t4-lr-checks"></a>

[Lagrangian bounds and certified gap](<#figure-parity-urbana-champaign-lr-bounds>)

<a id="uc-r3-lr-prices"></a>

##### Lagrangian prices and recovery

[![Lagrangian prices and recovery](<../assets/figure-contract-r12/figures/urbana-champaign/lr-prices-recovery.svg>)](<../assets/figure-contract-r12/figures/urbana-champaign/lr-prices-recovery.svg>)

At saved iteration 1 the positive capacity-price count is 0, so there are no positive-price arcs for a top-price map or time histogram. One actual recovery call uses the four paths in this method’s own pool and returns a feasible upper bound. Filled recovery marker follows the Boston/Hong Kong feasible-recovery convention. No additional calls or multipliers are invented.

[SVG](<../assets/figure-contract-r12/figures/urbana-champaign/lr-prices-recovery.svg>) · [PNG](<../assets/figure-contract-r12/figures/urbana-champaign/lr-prices-recovery.png>) · [PDF](<../assets/figure-contract-r12/figures/urbana-champaign/lr-prices-recovery.pdf>) · [Source data](<../assets/figure-contract-r12/figures/urbana-champaign/lr-prices-recovery.source.json>)

<a id="uc-r3-lr-recovery"></a>

<a id="figure-r9-urbana-champaign-admm-main"></a>

##### ADMM residuals and objective agreement

<a id="table-r11-urbana-champaign-t4-admm-check"></a>

[![ADMM residuals and objective agreement](<../assets/figure-contract-r12/figures/urbana-champaign/admm-saved-state.svg>)](<../assets/figure-contract-r12/figures/urbana-champaign/admm-saved-state.svg>)

Four diagnostic panels follow the Hong Kong ADMM figure: original-unit feasibility, primal consensus, rho-scaled dual update, and log10 absolute objective error against the independent same-graph reference. This instance saved exactly one completed outer update, shown as a point rather than an invented convergence curve. Balance, capacity, and primal use PCE; rho-scaled dual and its own threshold use minutes. Only exact-zero residuals use a labeled 1e-16 display floor; positive residuals are unchanged. Objective-error display floor is 1e-15 PCE·min. Saved internal thresholds and the 1e-5 PCE feasibility gate are retained. All displayed states meet the frozen independent gates; objective agreement is not a claim of identical link flows.

[SVG](<../assets/figure-contract-r12/figures/urbana-champaign/admm-saved-state.svg>) · [PNG](<../assets/figure-contract-r12/figures/urbana-champaign/admm-saved-state.png>) · [PDF](<../assets/figure-contract-r12/figures/urbana-champaign/admm-saved-state.pdf>) · [Source data](<../assets/figure-contract-r12/figures/urbana-champaign/admm-saved-state.source.json>)

<a id="figure-r9-admm-final-balance"></a>

##### ADMM: final commodity conservation

[![ADMM: final commodity conservation](<../assets/figure-contract-r11/figures/urbana-champaign/urbana-champaign-admm-final-balance.svg>)](<../assets/figure-contract-r11/figures/urbana-champaign/urbana-champaign-admm-final-balance.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

Four-commodity finite T4 final state, one completed update The heatmap is the saved final spatial conservation state, not an iteration-history heatmap. The displayed color floor and unchanged gate are retained; all exact raw residual values remain in the linked public plot data.

</details>

[PNG](<../assets/figure-contract-r11/figures/urbana-champaign/urbana-champaign-admm-final-balance.png>) · [SVG](<../assets/figure-contract-r11/figures/urbana-champaign/urbana-champaign-admm-final-balance.svg>) · [PDF](<../assets/figure-contract-r11/figures/urbana-champaign/urbana-champaign-admm-final-balance.pdf>) · [Source record](<../assets/figure-contract-r11/figures/urbana-champaign/urbana-champaign-admm-final-balance.source.json>)

<a id="figure-r9-urbana-champaign-admm-stopping-corrected"></a>

<details markdown="1">
<summary>Original objective and stopping diagnostics</summary>

**Unit erratum:** the older dual-residual label in the retained source is incorrect. The rho-scaled dual residual and threshold use minutes, not PCE. Original numerical values are unchanged.

<a id="uc-r3-admm-objective"></a>

</details>

<details markdown="1">
<summary>Original objective and stopping diagnostics</summary>

**Unit erratum:** the older dual-residual label in the retained source is incorrect. The rho-scaled dual residual and threshold use minutes, not PCE. Original numerical values are unchanged.

<a id="uc-r3-admm-residuals"></a>

</details>

<a id="uc-r3-admm-physical"></a>

##### ADMM: physical-road flow comparison

[![ADMM: physical-road flow comparison](<../assets/figure-contract-r11/figures/urbana-champaign/urbana-champaign-admm-physical.svg>)](<../assets/figure-contract-r11/figures/urbana-champaign/urbana-champaign-admm-physical.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

ADMM and exact LP on physical roads Own ADMM physical-road vector and exact LP on the frozen four-OD pulse. The signed map shows roundoff-sized differences; this is a final spatial state comparison.

</details>

[PNG](<../assets/figure-contract-r11/figures/urbana-champaign/urbana-champaign-admm-physical.png>) · [SVG](<../assets/figure-contract-r11/figures/urbana-champaign/urbana-champaign-admm-physical.svg>) · [PDF](<../assets/figure-contract-r11/figures/urbana-champaign/urbana-champaign-admm-physical.pdf>) · [Source record](<../assets/figure-contract-r11/figures/urbana-champaign/urbana-champaign-admm-physical.source.json>)

<details markdown="1">
<summary>Original twelve method figures and numerical records</summary>

<a id="uc-original-uc_s01"></a>

<span id="native-candidate-1"></span>
<a id="uc-original-uc_s02"></a>

**Historical outer-8 Native endpoint.** Both ranks had maximum OD residual about 8.25e-5 PCE, above the original 1e-6 PCE gate. Those files and original records remain in the private historical archive. This batch does not redistribute the old UC\_S02 PNG, SVG, plot or source; [the current accepted outer9 figure](<#uc-r3-native-check>) occupies the Native display position.

<a id="uc-original-uc_s03"></a>

<a id="uc-original-uc_s04"></a>

<a id="table-r11-uc-s72-dimensions"></a>

<a id="uc-original-uc_t01"></a>

<a id="uc-original-uc_t02"></a>

<a id="uc-original-uc_t03"></a>

<a id="uc-original-uc_t04"></a>

<a id="uc-original-uc_t05"></a>

<a id="uc-original-uc_t06"></a>

##### Generated routes: flow, cost and arc roles

<a id="table-r11-urbana-champaign-t4-route-counts"></a>

[![Generated routes: flow, cost and arc roles](<../assets/figure-contract-r12/figures/urbana-champaign/generated-route-profile.svg>)](<../assets/figure-contract-r12/figures/urbana-champaign/generated-route-profile.svg>)

Each category is one of the four saved demand commodities, not a solver iteration. Panels retain the method’s own generated path flow, fixed route cost, and separate counts of movement, turn, and waiting arcs. All four paths have zero waiting arcs. The ordered dynamic arc sequences and existing route maps remain separate geographic evidence; a fixed cost in minutes is not the rounded arrival clock.

[SVG](<../assets/figure-contract-r12/figures/urbana-champaign/generated-route-profile.svg>) · [PNG](<../assets/figure-contract-r12/figures/urbana-champaign/generated-route-profile.png>) · [PDF](<../assets/figure-contract-r12/figures/urbana-champaign/generated-route-profile.pdf>) · [Source data](<../assets/figure-contract-r12/figures/urbana-champaign/generated-route-profile.source.json>)

<a id="uc-original-uc_t07"></a>

<a id="uc-original-uc_t08"></a>

</details>
