# Conditional absolute OD-attribute HBW choice sensitivity

Status: **REDUCED_TRANSFER_SENSITIVITY**, executed on the frozen real Boston fixed panel. This is a directed midday OD/departure transfer, not exact TDM23 PA/tour-level reproduction or empirical calibration.

## Scope and equation

The modeled alternatives are DA, S2, S3 in the CTPS Auto nest and TW in the CTPS Transit nest. The scenario is a **conditional sufficient-vehicle household**. WK, BK, TA, and RS remain outside this conditional probability denominator; school bus is not an HBW alternative. No observed trip-weighted vehicle-category mixture is available, so probabilities are not unconditional Boston mode shares.

For each OD, departure, scenario, and alternative, the implemented utility is

`V = HBW_ASC + HBW_sufficient_vehicle_term + (-0.0201)*IVTT_minutes + (-0.0431)*OVTT_minutes + (-0.0613)*cost_2010_USD`.

IVTT, walk and wait, drive distance, and the selected itinerary fare come from each object's frozen path record. Auto operating cost is `0.244 * drive_distance_m / 1609.344`; it is **not** divided by S2/S3 occupancy, consistent with the report's revised shared-ride cost treatment. Fare is converted once from the recorded 2026 nominal year with the accepted CPI-U ratio `218.056/334.980`. The 0.244 price-year interpretation and official CTPS fare deflator remain unverified. Auto terminal minutes, parking, and tolls are fixed at zero **only for this named zero-context sensitivity**, because the panel lacks those values. These omitted costs are not observed zeros.

The DA HBW constant cell is blank in Table 45 and is treated as the reference normalization at zero, an explicit interpretation that requires implementation confirmation. S2, S3, and TW constants are the reported HBW values. Source path-distance shaping, land-use and intersection-density terms are deliberately omitted. They are not silently assigned observed zero values. The source's full availability and cost specification is therefore incomplete here.

The evaluator uses the report's Auto/Transit tree on this restricted set. Within nest `n`, `P(i|n)=exp(V_i/mu_n)/sum_j exp(V_j/mu_n)` and `IV_n=mu_n*logsumexp(V_j/mu_n)`; the root uses `P(n)=exp(IV_n)/sum_k exp(IV_k)`. The primary `mu_Auto=mu_Transit=1` is a unit-scale boundary. The second predeclared vector has `mu_Auto=0.7, mu_Transit=1`; it is a sensitivity, not an estimated scale. Transit has one child, so its within-nest scale is not identified by this restricted exercise. The official numeric scale vector remains unknown.

## Real-panel and comparison rules

The panel remains the frozen 36 HBW OD pairs at 12:30, 12:40, and 12:50 on 2026-09-21, with one third of each OD's engineering midday mass at each departure. All 108 objects remain in `exclusion_ledger.csv`. A four-mode probability is computed only when all four required alternatives have known path and fare inputs. An unknown TW path is not treated as physical unavailability or assigned zero probability. No old regional share enters a utility.

`REFERENCE_PIVOT_PLANNED` in the frozen release is a comparator. On the 78 old/new common objects, its DA/S2/S3/TW values are renormalized within the **same four-mode conditional subset** before model-specification comparison. `ABS_PLANNED` versus `ABS_OBS_EXPLORATORY` is the within-model service comparison. `ABS_RESTORE` independently uses the frozen overlay-off path rows and matches planned probabilities. Nine additional objects have known four-mode new inputs but no old comparator or accepted assignment node map; they appear in choice summaries but are not road-loaded. The 21 unknown four-mode objects retain their person-trip mass outside evaluation.

The solver receives only the same 78 common objects and 26 endpoint pairs. DA, S2, and S3 person trips are divided by 1, 2, and 3.627 persons/vehicle respectively. TW contributes no private road vehicle in this restricted specification. No auto-access, ride-service deadheading, city background flow, PCE multiplier, or hourly reinterpretation is applied. The frozen 2-hour effective-capacity link convention remains unchanged. A sample of midday departures is not measured two-hour traffic.

## Reproduce

Run from the research root with any Python 3.12+ interpreter for the choice calculation:

```powershell
python -B mode_choice_baseline_r1/build_and_evaluate.py --snapshot inputs_snapshot --spec mode_choice_baseline_r1/choice_spec.json --out mode_choice_baseline_r1/results
python -B mode_choice_baseline_r1/test_choice.py
python -B mode_choice_baseline_r1/summarize.py --results mode_choice_baseline_r1/results --fw-root mode_choice_baseline_r1/fw_runs
```

The two optional FW reruns require the existing project's pandas/numpy runtime plus task-local SciPy; the exact command and source hashes are in `fw_runs/*/run_summary.json`. The choice script itself uses the standard library. Reproduction begins from the accepted, hashed derived skims. Rebuilding those skims from raw GTFS/OSM/GMNS requires the original authorized source inputs and the accepted semantic adapter; those bulky original inputs are outside this small handoff.
