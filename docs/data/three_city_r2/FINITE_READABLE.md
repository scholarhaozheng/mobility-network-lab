| Metric | Boston · 10 OD | Sioux · 200 OD | Sioux · 250 OD | Hong Kong · 10 OD |
|---|---|---|---|---|
| Selected physical subnetwork | 90 nodes / 125 links | 24 nodes / 64 links | 24 nodes / 69 links | 100 nodes / 111 links |
| Selected OD demands | 10 | 200 | 250 | 10 |
| One model time step | 3 s | seconds not reported | seconds not reported | 30 s |
| Number of model steps | 100 | not reported in public summary | not reported in public summary | 50 |
| Elapsed model horizon | 300 s | not derivable from released summary | not derivable from released summary | 1,500 s |
| Dynamic graph | 9,110 nodes / 22,217 arcs | 1,192 nodes / 9,406 arcs | 1,292 nodes / 11,254 arcs | 11,954 nodes / 24,910 arcs |
| Same-graph reference LP objective | 64.396861511530 | 943,155.589771 | 1,521,090.83662 | 75.036329857948 |
| CG Phase-I zero round | 90 | 51 | 62 | 12 |
| Final CG column pool | 167 | 446 | 567 | 25 |
| CG independent full-DAG pricing | Independent pricing closure established; 10/10 | Not established | Not established | Independent pricing closure established; 10/10 |
| Lagrangian status / gap | Gated; 1.1002% exceeds frozen 1% gate | Accepted; 0.0746% duality gap | Accepted; 0.3177% duality gap | Verified bounded case; 0.7444% duality gap |
| ADMM status / own-LP difference | Verified bounded case; R2_S own-LP gap 6.68e−6 | Accepted R2_S; 6.30e−6 | Accepted R2_S; 7.16e−6 | Gated; first local conservation residual 0.082467622 PCE |

Fixed-cost, hard-capacity finite problems; each column is a separate graph. Objective values are vehicle-minutes, but no cross-city ranking is implied. CG pricing closure does not transfer to Lagrangian or ADMM.

[Machine-readable CSV](../three_city_r1/THREE_CITY_FINITE_TIME_EXPANDED_STATISTICS.csv) · [Readable-table source record](FINITE_READABLE.source.json).
