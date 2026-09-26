# Reference examples

The source distribution includes two synthetic fixtures. They are intentionally separate from road-network result records.

## Capacity and zone access

`app/cases/capacity_zone_probe/` contains nodes, links, OD demand and zone access. Automatic K=1 initialization chooses a route whose capacity is insufficient for all demand. Phase-I adds the alternative route. The final flows are 3 and 7, with objective 27.

```bash
python tools/mnl.py run --input app/cases/capacity_zone_probe/input --config app/cases/capacity_zone_probe/case.json --seed-mode auto --seed-k 1 --output results/capacity-demo
python tools/mnl.py verify --run results/capacity-demo
```

## Automatic routes

`app/cases/external_auto_4node/` contains raw network and demand tables without a precomputed route pool. K=5 yields only the two actual feasible simple routes, not five duplicates. The finite-model objective is 10.

```bash
python tools/mnl.py run --input app/cases/external_auto_4node/input --config app/cases/external_auto_4node/case.json --seed-mode auto --seed-k 5 --output results/auto-demo
python tools/mnl.py verify --run results/auto-demo
```

Run expected-rejection checks when changing input validation. An input correctly rejected by its contract is a successful negative test, not a failed research experiment.

## Bounded city-data and method components

The [Hong Kong GMNS/data pilot](cases/hong-kong-gmns-pilot.md) supplies official-derived saved tables, five SVGs and offline validation/trace commands, but **no assignment-ready instance**. The [Lagrangian R2 and ADMM R1 components](methods/distributed-assignment.md) include synthetic fixtures and accepted saved Sioux selected-OD summaries; their small fixtures do not reconstruct the historical 200/250-OD networks.
