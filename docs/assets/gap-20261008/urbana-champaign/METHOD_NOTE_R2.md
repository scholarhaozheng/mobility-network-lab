# C02 service-day transit revision: frozen method

## Declared case and source

`UC_MODE_TRANSIT_EXTENSION_20261008_R2` extends the accepted 21-zone, 418-positive-OD central Champaign–Urbana HBW engineering scenario. It uses the CUMTD GTFS ZIP downloaded from the agency's developer endpoint, SHA-256 `49201ba617ce2bde637ffa95f5530a8c618414dac516c66b89dbd69693aed1ad`, and selects 2026-10-07 in `America/Chicago`. The older generation, distribution, road graph, parameter values and S72/T4 algorithm inputs remain fixed.

## Timetable and access calculation

The compiler applies `calendar.txt` and `calendar_dates.txt`, joins active `trips.txt` with ordered `stop_times.txt`, and respects pickup and drop-off prohibitions. It scans actual consecutive trip calls with departures in a declared 08:00–11:00 local search window. Four uniformly weighted traveler departure samples represent 08:00–09:00: 08:00, 08:15, 08:30 and 08:45. The compiler selects the earliest arrival itinerary for each origin, destination and sample, counting a transit option only when it contains at least one GTFS ride leg. Transfers occur at the same stop with at least two minutes between trips. An OD receives a transit cost only when all four samples find such an itinerary.

The access point for each model zone remains the accepted midpoint of a directed GMNS road link. Pedestrian travel follows the frozen directed links whose `allowed_uses` includes `walk`, at the accepted 75 m/min engineering speed. A GTFS stop attaches to its nearest walk-network node only within 100 m; each access or egress side is capped at 1,200 m. The stop-to-node connector uses straight-line distance and has no inspected sidewalk, curb or barrier certificate.

The midpoint direction rule is explicit. For a directed source link `a→b`, an origin exits toward `b` and a destination enters from `a`. The other endpoint becomes available only when an explicit reverse `walk` arc `b→a` exists. Source links `1242` and `8862` lacked this reverse arc. The first candidate allowed both endpoints, so it is preserved solely as a superseded diagnostic under `diagnostic_access_v1/`. This R2 correction changes only access representation; it does not change demand, road capacity, logit coefficients or convergence thresholds.

The cost record separates vehicle ride, initial wait, transfer wait, access plus egress, and adult cash fare. The published GTFS fare table provides USD 1 for a single ride and one free full-fare transfer within 3,600 seconds. A traveler-specific zero-fare iStop entitlement is not assumed. The four component means feed the accepted logit cost schema; USD fare converts to minutes with the frozen USD 18/hour value of time. The path search minimizes arrival time, then evaluates the cost of that chosen valid path. It does not estimate real passenger route selection, actual delay or reliability.

## Affected stages and checks

The active input revision changes the Stage 3 transit availability and generalized cost. The accepted conditional multinomial logit recomputes all positive OD mode probabilities with `λ=0.08` per generalized minute and unchanged ASCs. Only modeled drive person trips pass through the fixed 1.25-person occupancy and unit PCE factor into Stage 4. The accepted turn-expanded static FW implementation solves that new road OD on the original network with the original `1e-4` gap threshold. A separate checker reconstructs GTFS ride legs from source stop times, verifies all component sums and fares, recomputes every OD probability and person/PCE ledger, and independently audits original-link path flow, BPR objective and the signed full-graph gap.

The S72 tap-b supplement has its own frozen instance and will not consume the transit revision. Its integer node relabeling and TNTP permutation preserve all 26,602 directed arcs, 72 OD volumes, BPR coefficients and turn permissions exactly in binary64. A new Algorithm B run requires the shared heavy lock. The original FW endpoint is the same-instance objective reference; a new FW run on S72 is unnecessary.

The observation query reuses the accepted 2025 27-point GPS trace and E bridge. Only 33 of its 35 source links have frozen `P:` identities, and only 32 of 34 adjacent turns have frozen turn IDs. Query output leaves unmatched flow fields empty. The trace's mode is unknown and the photo dates differ, so no current link flow, speed or traveler mode claim derives from this evidence.
