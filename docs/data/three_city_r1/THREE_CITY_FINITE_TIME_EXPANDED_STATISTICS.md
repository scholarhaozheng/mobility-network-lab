| city | physical_subnetwork_nodes_links | dynamic_od_demands | time_step_horizon | dynamic_nodes_arcs | reference_lp_objective_vehicle_min | cg_phase_i_zero_round | final_column_pool | lagrangian_status_gap | admm_status_residual_gate | independent_pricing_closure |
|---|---|---|---|---|---|---|---|---|---|---|
| Boston | 90 / 125 | 10 | 3 s / 100 steps | 9,110 / 22,217 | 64.396861511530 | 90 | 167 | Gated; 1.1002% exceeds frozen 1% gate | Verified bounded case; R2_S own-LP gap 6.68e−6 | Independent pricing closure established; 10/10 |
| Sioux Falls (200 / 250 OD) | 24 / 64 or 69 | 200 / 250 | Not stated in released summary | 1,192 / 9,406; 1,292 / 11,254 | 943,155.589771 / 1,521,090.83662 | 51 / 62 | 446 / 567 | Verified bounded case; 0.0746% / 0.3177% duality gaps | Verified bounded case; R2_S own-LP gaps 6.30e−6 / 7.16e−6 | Not established |
| Hong Kong | 100 / 111 | 10 | 30 s / 50 steps | 11,954 / 24,910 | 75.036329857948 | 12 | 25 | Verified bounded case; 0.7444% duality gap | Gated; first local conservation residual 0.082467622 PCE | Independent pricing closure established; 10/10 |

Each row is a different bounded finite graph. Sioux 200/250 values are paired in consistent order; its retained historical pricing closure is not established. Dynamic objectives are vehicle-minutes on separate graphs.
