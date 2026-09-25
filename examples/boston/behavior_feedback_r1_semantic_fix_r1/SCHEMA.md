# Behavior-feedback semantic-fix schema

Identifiers—including H3, GTFS, source geography, source aliases and code-like
fields—load as SQLite `TEXT`; empty scientific values become `NULL`, never zero.

| Table | Key or grain | Corrected purpose |
|---|---|---|
| `source_registry` | `source_id` | canonical provenance records |
| `source_id_alias_map` | alias → canonical | retained spelling crosswalk |
| `parameter_registry` | `parameter_id` | values, units, price year and source |
| `pa_direction_conversion_ledger` | purpose | directional conservation and recovered demand |
| `validation_panel` | `od_id` | unchanged 36-OD panel and weights |
| `od_multimodal_skims` | OD/departure/scenario/mode | S1/S2/Srestore time, Fare v2 and availability |
| `itinerary_legs` | scenario/path/sequence | permitted boarding, ride, transfer and egress account |
| `mode_utility_delta_components` | OD/departure/target | time, nominal fare, CPI conversion and utility delta |
| `od_mode_probabilities` | OD/departure/scenario/μ/mode | regional-base-share nested-pivot sensitivity |
| `person_to_vehicle_crosswalk` | model grain | complete mode ledger, RS/TA loading status |
| `srestore_skim_comparison` | OD/departure/mode | S1 versus independent overlay-off skim |
| `srestore_model_comparison` | OD/departure/μ/mode | probability and person-demand restore errors |
| `assignment_result_by_scenario` | `link_id` | corrected panel-only S1/S2 FW delta |
| `feedback_trace` | `trace_id` | GPS→path/fare→utility→probability→vehicle→link chain |
| `feedback_scenario_registry` | `scenario_id` | S0/S1/S2/Srestore scope and identity |
| `readiness` | `readiness_area` | technical versus empirical status |
| `targeted_validation_checks` | check | 26 semantic acceptance results |

The remaining tables retain ACS allocation, trip generation, external-flow,
GPS observation, overlay and panel-sample evidence. `scenario_transit_response`
and `end_to_end_feedback_trace` expose the central comparisons. The manifest
contains row counts and SHA-256 hashes for every packaged CSV.
