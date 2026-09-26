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

The [Hong Kong GMNS/data pilot](cases/hong-kong-gmns-pilot.md) supplies official-derived saved tables, five SVGs and offline validation/trace commands, but **no assignment-ready instance**. The [Lagrangian R2 component](methods/distributed-assignment.md) and [ADMM R2_S source with authored analytic/C0/C1 fixtures](../examples/admm-r2-fixtures/README.md) support public inspection and bounded tests; these small fixtures do not reconstruct the private historical Sioux/Boston dynamic instances. Earlier ADMM R1 material remains available.

The [Algorithm B public candidate](../algorithms/origin_based_algorithm_b/README.md) supplies task-local adapter/evaluator code and accepted derived Sioux/Boston B1 outputs. Its original frozen inputs and native tap-b executable are not bundled, so the published files support inspection and new-input preparation rather than a self-contained rerun of the accepted cases. [Two reproduction routes](integrations/taplab-tapb.md).
