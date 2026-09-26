# ADMM R1 public component

This directory contains the selected public ADMM source, C0 synthetic fixture, saved 200-OD result/history, accepted 200/250-OD final-metric [summary](ADMM_ACCEPTED_RESULT_SUMMARY.csv), and figures. The scientific contract is a bounded selected-OD finite time-expanded fixed-cost shared-capacity model; it is not static UE or the full Sioux 528-OD network.

The final objective differences from each same-graph arc-flow LP are **0.000434%** (200 OD) and **0.000607%** (250 OD). Both passed the declared primal/dual residual and independent conservation/capacity gates. The 200-OD public figure/history supports its trajectory; the 250-OD public evidence supports **final metrics only**. `plot_saved_objective_differences.py` makes one 300-dpi PNG/SVG per case from the summary CSV, without optimization or synthetic 250-OD history. `admm.py` is source for an explicit new run, not invoked by the public renderer.

The Boston transfer failed local conservation and is not accepted. [Method explanation and case captions](../../../docs/methods/distributed-assignment.md).
