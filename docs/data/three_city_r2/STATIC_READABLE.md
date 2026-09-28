| Metric | Boston B1 · conditional 2 h | Sioux Falls · classic 528 OD | Hong Kong · bounded 1 h |
|---|---|---|---|
| Physical-node / positive OD pairs | 453 | 528 | 8930 |
| Assigned demand and period | 1936.238475 PCE / 2 h | 360600 vehicles | 723.191228 PCE / 1 h |
| Mathematical problem | static BPR / Beckmann | static BPR / Beckmann | turn-aware static BPR / Beckmann |
| FW evidence | Verified bounded case | Verified historical run; input-identity caveat | Verified bounded case |
| Algorithm B route | Verified bounded case; task-local TAPLab-compatible lossless adapter | Verified; official TAPLab registered-adapter parity | Verified bounded case; task-local lossless adapter |
| Objective and independent gap | Beckmann 7922.083942188 PCE-min; independent relative gap -2.3e-16 | Beckmann 4231335.287110682 vehicle-min; independent relative gap 4.5e-09 | Beckmann 1676.012131329 PCE-min; independent relative gap 4.21e-15 |
| Path-to-link reconstruction | Verified; max path/link mismatch 5.68e-14 PCE | Verified; max path/link mismatch 5.46e-11 vehicles | Verified; max path/link mismatch 1.42e-13 PCE |

Boston B1 is a matched-method holdout, not Boston's largest accepted FW tier. Objectives and demands are not comparable across cities or with finite fixed-cost models.

[Machine-readable CSV](../three_city_r1/THREE_CITY_STATIC_ASSIGNMENT_STATISTICS.csv) · [Readable-table source record](STATIC_READABLE.source.json).
