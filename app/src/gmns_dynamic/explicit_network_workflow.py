"""Shared explicit-allowed-network build, reference, CG, and export workflow.

This module deliberately contains orchestration only.  The time-expanded model
is built by ``build_explicit_allowed_network`` and the two-phase solver and
final exact-pool exports remain in ``run_full_cg_v1``.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from external_sioux_static_to_dynamic import (
    DYNAMIC_ARC_FIELDS,
    DYNAMIC_COLUMN_FIELDS,
    DYNAMIC_DEMAND_FIELDS,
    DYNAMIC_NODE_FIELDS,
    ExplicitAllowedNetworkConfig,
    build_explicit_allowed_network,
    solve_small_subset_arc_lp,
)
from run_full_cg_v1 import run_full_cg_v1


@dataclass(frozen=True)
class ExplicitWorkflowSettings:
    max_phase_i_rounds: int
    max_phase_ii_rounds: int
    max_candidates_per_demand_per_round: int
    runtime_cap_seconds: int
    phase_ii_pricing_mode: str
    phase_ii_add_policy: str
    k_shortest_k: int
    max_phase_ii_candidates_per_demand: int
    max_phase_ii_candidates_per_round: int
    strict_phase_ii_candidate_round_cap: bool = False


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    resolved_fields = fields or (list(rows[0]) if rows else [])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=resolved_fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def make_namespace(manifest_path: Path, output_dir: Path, manifest: dict[str, Any]) -> argparse.Namespace:
    return argparse.Namespace(
        input_manifest=str(manifest_path),
        output_dir=str(output_dir),
        benchmark_id=str(manifest["benchmark_id"]),
        max_phase_i_rounds=int(manifest["max_phase_i_rounds"]),
        max_phase_ii_rounds=int(manifest["max_phase_ii_rounds"]),
        max_candidates_per_demand=int(manifest["max_candidates_per_demand_per_round"]),
        phase_ii_pricing_mode=str(manifest["phase_ii_pricing_mode"]),
        k_shortest_k=int(manifest["k_shortest_k"]),
        phase_ii_add_policy=str(manifest["phase_ii_add_policy"]),
        max_phase_ii_candidates_per_demand=int(manifest["max_phase_ii_candidates_per_demand"]),
        max_phase_ii_candidates_per_round=int(manifest["max_phase_ii_candidates_per_round"]),
        strict_phase_ii_candidate_round_cap=bool(manifest["strict_phase_ii_candidate_round_cap"]),
        runtime_cap_seconds=int(manifest["runtime_cap_seconds"]),
        no_mutate_accepted_outputs=True,
        write_review_artifacts=False,
        preflight_only=False,
        skip_phase_ii=False,
        reference_objective=None,
        reference_summary=None,
    )


def run_explicit_workflow(
    *,
    nodes: list[dict[str, Any]],
    allowed_links: list[dict[str, Any]],
    demands: list[dict[str, Any]],
    seed_columns: list[dict[str, Any]],
    model_config: ExplicitAllowedNetworkConfig,
    output_dir: Path,
    benchmark_id: str,
    settings: ExplicitWorkflowSettings,
    provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run the existing explicit model/reference/CG stack once.

    The caller owns raw-input normalization and seed creation.  Seeds are passed
    only as the initial RMP pool; the allowed physical links define the model.
    """
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    model = build_explicit_allowed_network(nodes, allowed_links, demands, seed_columns, model_config)
    dynamic_dir = output_dir / "dynamic_inputs"
    write_csv(dynamic_dir / "dynamic_node.csv", model["dynamic_nodes"], DYNAMIC_NODE_FIELDS)
    write_csv(dynamic_dir / "dynamic_arc.csv", model["dynamic_arcs"], DYNAMIC_ARC_FIELDS)
    write_csv(dynamic_dir / "dynamic_demand.csv", model["dynamic_demands"], DYNAMIC_DEMAND_FIELDS)
    write_csv(dynamic_dir / "dynamic_columns.csv", model["dynamic_columns"], DYNAMIC_COLUMN_FIELDS)
    write_json(output_dir / "explicit_model_summary.json", model)

    reference = solve_small_subset_arc_lp(model["dynamic_arcs"], model["dynamic_demands"])
    reference.update(
        {
            "benchmark_id": benchmark_id,
            "network_mode": model["network_mode"],
            "model_schema_version": model["model_schema_version"],
            "model_signature": model["model_signature"],
            "reference_and_cg_share_exact_dynamic_graph": True,
        }
    )
    write_json(output_dir / "arc_lp_reference_summary.json", reference)
    if reference.get("reference_status") != "REFERENCE_GENERATED":
        raise RuntimeError(f"reference LP failed: {reference.get('blockers', [])}")

    run_dir = output_dir / "full_cg_v1_run"
    manifest = {
        "benchmark_id": benchmark_id,
        "scope_label": model_config.scope_label,
        "network_mode": model["network_mode"],
        "model_schema_version": model["model_schema_version"],
        "model_signature": model["model_signature"],
        "seed_pool_signature": model["seed_pool_signature"],
        "dynamic_data_dir": str(dynamic_dir),
        "demand_file": str(dynamic_dir / "dynamic_demand.csv"),
        "dynamic_arc_file": str(dynamic_dir / "dynamic_arc.csv"),
        "current_candidate_pool_file": str(dynamic_dir / "dynamic_columns.csv"),
        "output_root": str(run_dir),
        **asdict(settings),
        "no_mutate": True,
        "reference_comparison_policy": "objective_level_when_reference_available",
        "stop_certificate_policy": "always_write",
        "claim_boundary_policy": "bounded_finite_fixture_only",
        "arc_lp_reference_objective": reference["objective_value"],
        "arc_lp_reference_summary_path": str(output_dir / "arc_lp_reference_summary.json"),
        "reference_and_cg_share_exact_dynamic_graph": True,
        "seed_columns_define_network": False,
        "no_full_assignment_claim": True,
        "no_global_convergence_claim": True,
        "no_exact_flow_pattern_reproduction_claim": True,
        "workflow_provenance": provenance or {},
    }
    manifest_path = output_dir / "full_cg_v1_manifest.json"
    write_json(manifest_path, manifest)
    cg = run_full_cg_v1(make_namespace(manifest_path, run_dir, manifest))
    result = {
        "status": "PASS"
        if cg.get("run_status") == "PASS"
        and cg.get("final_solution_export_status") == "PASS"
        and cg.get("full_solution_and_duals_present") is True
        else "FAIL",
        "benchmark_id": benchmark_id,
        "model_signature": model["model_signature"],
        "seed_pool_signature": model["seed_pool_signature"],
        "reference_objective": reference["objective_value"],
        "cg_objective": cg.get("phase_ii_final_objective"),
        "cg_run_status": cg.get("run_status"),
        "final_solution_export_status": cg.get("final_solution_export_status"),
        "full_solution_and_duals_present": cg.get("full_solution_and_duals_present"),
        "stop_reason": cg.get("stop_reason"),
        "phase_i_needed": cg.get("phase_i_needed"),
        "phase_ii_candidates_added": cg.get("phase_ii_candidates_added"),
        "dynamic_dir": str(dynamic_dir),
        "run_dir": str(run_dir),
    }
    write_json(output_dir / "explicit_workflow_result.json", result)
    return {"model": model, "reference": reference, "manifest": manifest, "cg": cg, "result": result}
