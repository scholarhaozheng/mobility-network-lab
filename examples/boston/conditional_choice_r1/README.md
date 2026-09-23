# Boston conditional absolute-attribute choice sensitivity

The [standard-library evaluator and exact reduced specification](../../../algorithms/mode_choice_conditional/BASELINE_SPECIFICATION.md) were used previously on a frozen 108-object HBW midday panel. Four alternatives (DA, S2, S3, TW) are conditional on a sufficient-vehicle household; 87 objects had known four-mode inputs and 21 remained unknown. Only 78 common objects were loaded on 26 endpoint OD pairs. The archived complete input skims are not reproduced in this compact public folder, so the evaluator is a published implementation/specification, not a promise that the full old panel can be rebuilt from this folder alone.

`od_baseline_probabilities.csv` and `scenario_comparison.csv` are previously saved **derived** project outputs; `PARAMETER_REGISTER.csv` and `VARIABLE_MAPPING.csv` document the reduced transfer specification. `demand_abs_obs_exploratory.csv` and `fw_abs_obs_exploratory_solution.csv` are the saved static FW input/output for the exploratory service scenario. Its 203.6573680559407 modeled vehicle trips and Beckmann F=707.043586277782 are distinct from ABS_PLANNED's 203.6604786350987 and F=707.0579230712884. The older semantic S1 baseline (about 202.078384) is a third, separately labelled line.

The reduced sensitivity does not reproduce official complete TDM23 utility/availability, estimate local choice parameters, validate AM forecasts or infer regional traffic. The report-derived parameters, price-year conversion, zero terminal/parking/toll sensitivity and missing alternatives are qualified in the [model specification](../../../algorithms/mode_choice_conditional/BASELINE_SPECIFICATION.md). No source PDF, raw GTFS, private skims or unsent correspondence is distributed here.

```bash
python -B tools/mcl_results.py show --run boston-abs-obs-exploratory-fw
python -B tools/mcl_results.py verify-saved --run boston-abs-obs-exploratory-fw
```
