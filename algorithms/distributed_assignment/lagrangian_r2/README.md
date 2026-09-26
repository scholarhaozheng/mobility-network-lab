# Lagrangian capacity-pricing R2 public component

This directory contains the accepted public-safe solver/evaluator source, analytic/C0/C1 fixtures, frozen Sioux P07 history tables, figures and [exact accepted summary](SIOUX_ACCEPTED_RESULT_SUMMARY.csv). Its computational contract is selected-OD finite time-expanded fixed-cost shared-capacity flow, not static UE.

`src/lagrangian_dual_solver.py` generates paths and a dual lower bound; `src/restricted_primal_recovery_adapter.py` separately recovers a feasible restricted-path upper bound. `src/independent_lagrangian_evaluator.py` evaluates saved results without a solver call. The supplied Sioux 200/250 summaries are accepted saved evidence, **not** fully reconstructible numerical runs from the small synthetic fixtures. The 250-OD frozen 1% gate passed at 0.3177%; Boston R2 failed at 1.1002% and is intentionally not an accepted result here.

For a source/fixture inspection without optimization, open `fixtures/analytic/expected.json`, `figure_data/Sioux_200OD_P07_history.csv`, `figure_data/Sioux_250OD_P07_history.csv` and the summary CSV. Do not interpret the illustrative fixtures as the 200/250-OD network inputs. [Public interpretation and paired figures](../../../docs/methods/distributed-assignment.md).
