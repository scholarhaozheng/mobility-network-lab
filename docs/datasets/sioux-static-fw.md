# Sioux Falls · static Frank–Wolfe

**Historical approximate static assignment result.**

| Quantity | Value |
|---|---:|
| Physical nodes / directed links | 24 / 76 |
| OD records | 528 |
| Total provided demand | 360,600 |
| Saved iterations | 100 |
| Recomputed Beckmann objective | 4,236,715.140437842 |
| Maximum aggregate node-balance residual | 1.4552e-11 |
| Fixed-flow gap / Beckmann objective | 0.236154949% |

BPR travel times, the saved link flows and the Beckmann objective were recomputed. The gap above uses the final saved flow and the provided OD matrix, with the Beckmann objective as denominator. It is not interchangeable with a gap normalized by total travel cost. The original iteration log used a pre-update point, while its final CSV used the post-update flow.

This is not a high-precision UE ground truth. Runtime OD-file hashes and a complete OD/path disaggregation were not preserved, so aggregate node balance is not presented as a full OD-level feasibility certificate.

Raw input and output tables are not included in this public result record. The retained [static implementation](../../algorithms/static_fw/) is separate from the space–time CG run command.
