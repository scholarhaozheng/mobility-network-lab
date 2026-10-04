"""Independent restricted-path LP. Its result is a feasible upper bound only."""
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix

from path_pool_manager import PathPool


def recover(problem, pool):
    paths = [(k, path) for k, group in enumerate(pool.paths) for path in group]
    if any(not group for group in pool.paths):
        return {"feasible": False, "message": "empty commodity pool", "path_count": len(paths)}
    row, col, value = [], [], []
    for j, (_, path) in enumerate(paths):
        for a in path:
            row.append(a)
            col.append(j)
            value.append(1.0)
    aub = coo_matrix((value, (row, col)), shape=(len(problem["ids"]), len(paths))).tocsr()
    aeq = coo_matrix((np.ones(len(paths)), ([k for k, _ in paths], range(len(paths)))),
                     shape=(len(pool.paths), len(paths))).tocsr()
    costs = np.asarray([sum(problem["cost"][list(path)]) for _, path in paths])
    result = linprog(costs, A_ub=aub, b_ub=problem["cap"], A_eq=aeq,
                     b_eq=[c["volume"] for c in problem["commodities"]],
                     bounds=(0, None), method="highs")
    if not result.success:
        return {"feasible": False, "message": result.message, "path_count": len(paths)}
    positive = [(k, path, float(flow)) for (k, path), flow in zip(paths, result.x) if flow > 1e-9]
    return {"feasible": True, "objective": float(result.fun), "path_count": len(paths),
            "positive_paths": positive, "message": result.message}


def _write_csv(path, fields, records):
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(fields)
        writer.writerows(records)


def recover_saved_pool(problem, pool_file, output_dir):
    """Re-solve from the algorithm's saved paths without solver state or reference data."""
    output_dir = Path(output_dir)
    if output_dir.exists():
        raise FileExistsError(output_dir)
    with Path(pool_file).open(newline="", encoding="utf-8") as handle:
        events = list(csv.DictReader(handle))
    ids = {name: i for i, name in enumerate(problem["ids"])}
    commodities = {item["id"]: i for i, item in enumerate(problem["commodities"])}
    pool = PathPool(len(commodities), max(len(events), 1))
    for row in events:
        k = commodities[row["demand_id"]]
        path = tuple(ids[name] for name in json.loads(row["arc_ids_json"]))
        if not pool.add(k, path, int(row["iteration"]), row["source"]):
            raise ValueError("duplicate saved path")
    candidate = recover(problem, pool)
    output_dir.mkdir(parents=True)
    pool_sha = hashlib.sha256(Path(pool_file).read_bytes()).hexdigest()
    summary = {"feasible": candidate["feasible"], "objective": candidate.get("objective"),
               "path_count": candidate["path_count"], "message": candidate["message"],
               "pool_sha256": pool_sha, "model_signature": problem["model_signature"]}
    if candidate["feasible"]:
        _write_csv(output_dir / "positive_paths.csv", ["demand_id", "arc_ids_json", "flow"],
                   ((problem["commodities"][k]["id"],
                     json.dumps([problem["ids"][a] for a in path], separators=(",", ":")),
                     format(value, ".17g")) for k, path, value in candidate["positive_paths"]))
        flows, physical = {}, {}
        for k, path, value in candidate["positive_paths"]:
            for a in path:
                flows[k, a] = flows.get((k, a), 0) + value
                if problem["types"][a] == "movement":
                    link = problem["arcs"][a]["physical_link_id"]
                    physical[link] = physical.get(link, 0) + value
        _write_csv(output_dir / "commodity_arc_flow.csv", ["demand_id", "arc_id", "flow"],
                   ((problem["commodities"][k]["id"], problem["ids"][a], format(value, ".17g"))
                    for (k, a), value in sorted(flows.items())))
        _write_csv(output_dir / "physical_link_flow.csv", ["physical_link_id", "flow"],
                   ((link, format(value, ".17g")) for link, value in sorted(physical.items())))
    (output_dir / "recovery_result.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary
