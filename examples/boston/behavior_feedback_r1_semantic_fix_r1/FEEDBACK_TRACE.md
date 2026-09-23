# From Transit Observations to Road Flows

This walkthrough follows one saved result from a transit observation through the Central Boston model. It demonstrates an executable dependency chain, not a measured causal effect or an independently validated travel forecast.

[Component overview](README.md) · [Data dictionary](SCHEMA.md) · [Machine-readable trace](data/feedback_trace.csv)

## 1. Identify the observation and its scope

The registered observation is:

```text
Observation: gps-stop-pair:mbtav:cccdb505033abedc:s01:5-10
MBTA trip:   78591067
Route:       749
Direction:   1
Stop pair:   1788 -> 5093
```

The derived elapsed time is **86 seconds**, compared with **180 seconds** in the corresponding planned interval. These are sample-derived interval estimates; a vehicle-position snapshot at a stop is not an exact door-open or door-close event.

The overlay parameter `gps_midday_stop_pair_09` stores an approximate ratio of `0.477778`. It is disabled by default and applies only within its declared exploratory scope. Each of the 13 registered adjustments has one supporting event; they are not 13 independently validated population parameters.

## 2. Update the declared service input

S1 retains the scheduled-service reference. S2 applies the named interval adjustment to the declared services and propagates the resulting permitted timetable changes. Its transfer to other trips within the declared direction and interval is a modeling assumption.

The road network, panel objects and person weights, base transit feed, baseline mode shares, non-overlay inputs, and assignment solver are held fixed. The scenario changes the service overlay and recomputes the dependent itineraries, travel costs, mode responses, and vehicle demand.

## 3. Recompute the passenger's transit alternative

For `panel_od_019` at `12:30:00`, the saved outcomes are:

| Quantity | S1 | S2 |
|---|---:|---:|
| Transit journey time | 29.052381 min | 27.485714 min |
| Selected-itinerary adult CharlieCard fare | USD 1.70 | USD 1.70 |
| Walk-access-transit probability, `mu_transit=1` branch | 0.040990 | 0.042246 |
| Walk-access-transit person trips | 0.111465 | 0.114880 |
| Private/occupied ride-service vehicle trips | 2.164631 | 2.161796 |

Each available transit alternative contains a permitted ride. Its leg records expose access, waiting, riding, transfers, and egress rather than treating a pure walking route as transit.

The zero fare difference here follows from the selected paths' equal fares. It is not a rule that all service changes have zero monetary effect. The implementation retains the actual path-derived cost difference and its declared price-year conversion when applicable.

The mode response is a nested adjustment around a common regional baseline. It is not a newly estimated local baseline-choice model. The reported row uses the explicitly declared `mu_transit=1` sensitivity branch.

## 4. Pass vehicle demand to the common assignment model

The changed mode demand is converted to vehicles under the registered occupancy and loading assumptions. The complete eligible panel is assigned using the same static Frank-Wolfe implementation and road parameters in S1 and S2.

On link `16105`, aggregate panel flow changes from **19.280398** to **19.273796** vehicle trips. This road-link difference aggregates all contributing panel OD cases; it must not be attributed entirely to the single OD highlighted above.

Across the panel, assigned demand is **202.078384** vehicle trips in S1 and **202.070733** in S2. Empty ride-service repositioning is not modeled, and unimplemented transit-auto access legs are not loaded.

## 5. Check the dependency by disabling the overlay

Srestore rebuilds the affected service connections without the overlay and recomputes the downstream journey costs, probabilities, and vehicle demand. Its comparable outcomes return to S1 within the recorded numerical tolerances.

This restoration check establishes that the named service input is connected to the reported response. It does not establish that a new day or an unobserved population will behave as predicted.

## Reproduce the public inspection

From this component directory:

```bash
python -B build_public_database.py
python -B query_behavior_feedback.py trace
python -B query_behavior_feedback.py response
python -B query_behavior_feedback.py parameters
```

These commands rebuild and query the saved CSV results. They do not rerun observation extraction, passenger routing, mode-choice estimation, or assignment. Re-executing those upstream stages requires the documented source inputs and their applicable permissions.
