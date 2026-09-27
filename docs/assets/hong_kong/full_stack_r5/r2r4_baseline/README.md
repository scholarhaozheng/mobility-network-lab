# Hong Kong bounded full-stack technical case

![Bounded Hong Kong road and scenario overview](figures/hk_full_stack_overview.png)

| Component | Saved result |
|---|---|
| Turn-aware physical network | 1,239 directed links; 95 fine zones; 8,930 directed interzonal pairs reachable |
| Four-stage scenario | 723.191 PCE in the 08:00–09:00 one-hour drive assignment |
| Static FW and Algorithm B | Both independently accepted; same-problem Beckmann objective 1,676.0121 |
| Finite arc-flow LP | 10 OD, 24,910 arcs; independently verified objective 75.03633 vehicle-minutes |
| Frozen Lagrangian R3 | Feasible recovered primal; independent 0.7444% duality gap |
| Frozen CG | **Gated** in Phase I; 4.3502 artificial PCE remains at fixed enumeration limit |
| Frozen ADMM R2 | **Gated** at first local QP; 0.08247 PCE conservation residual |

The data and static core are accepted as a reproducible engineering scenario. The complete four-method transfer is gated. No locally calibrated forecast or empirical traffic validation is claimed. Read [the case](docs/cases/hong-kong.md), [evidence contract](docs/methods/hong-kong-evidence-contract.md), and [rights register](HONG_KONG_SOURCE_AND_RIGHTS_REGISTER.csv).
