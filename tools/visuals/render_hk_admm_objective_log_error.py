#!/usr/bin/env python3
"""Render the accepted Hong Kong ADMM objective error without rerunning a solver.

The two input files are restricted saved records supplied at invocation time.
Only a PNG, an SVG, a caption and a hash-only source sidecar are exported.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/assets/admm_r3/hong_kong"
STEM = "hk_admm_r3_objective_abs_error_log10"
EXPECTED_HISTORY_SHA256 = "2e951aeb2640bb45c04b47b843a7296e1f026a0b48eb37ece68b3b9801074ec9"
EXPECTED_LP_SHA256 = "e46cee03f7ed7758c74f5489d2a48dd0a1eb0afcf0258fd71bbd65763854fbd7"
EXPECTED_PHYSICAL_SHA256 = "7542d56e58db8e1f17e7839eecb678497dc66c1c106a4a8a73234090c0c26f3a"
ORIGINAL = OUT / "hk_admm_r3_objective_vs_lp.png"
SOURCE_PACKAGE_SHA256 = "7686cc138a4feb76316d2a63626b4634fd9e361120048792bd8afbcf973b7573"
TRIPTYCH_STEM = "hk_admm_r3_residual_objective_physical_flow_triptych"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_saved_history(history_path: Path, lp_path: Path):
    if sha(history_path) != EXPECTED_HISTORY_SHA256 or sha(lp_path) != EXPECTED_LP_SHA256:
        raise ValueError("The saved ADMM history or same-graph LP reference differs from the accepted R3 inputs")
    with history_path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    lp = float(json.loads(lp_path.read_text(encoding="utf-8"))["objective_value"])
    if len(rows) != 165 or [int(r["iteration"]) for r in rows] != list(range(1, 166)):
        raise ValueError("Expected exactly the accepted 165 recorded outer iterations")
    if not math.isclose(lp, 32.98334567386431, rel_tol=0, abs_tol=1e-12):
        raise ValueError("The LP reference does not match the accepted four-OD graph")
    iteration = np.array([int(r["iteration"]) for r in rows], dtype=int)
    objective = np.array([float(r["objective"]) for r in rows], dtype=float)
    difference = np.abs(objective - lp)
    if not np.isfinite(difference).all() or np.any(difference <= 0):
        raise ValueError("Exact zero or invalid difference requires a declared zero-display policy; no floor is applied")
    if not math.isclose(objective[-1], 32.98357085525667, rel_tol=0, abs_tol=1e-10):
        raise ValueError("Final accepted ADMM objective changed")
    return iteration, difference, lp


def render(history_path: Path, lp_path: Path, output_dir: Path = OUT) -> dict:
    iteration, difference, lp = read_saved_history(history_path, lp_path)
    log_error = np.log10(difference)
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
        "svg.fonttype": "none",
        "svg.hashsalt": "hk-admm-r3-log-error-v1",
        "pdf.fonttype": 42,
        "axes.spines.right": False,
        "axes.spines.top": False,
    })
    fig = plt.figure(figsize=(14, 7.9), dpi=100, facecolor="#f6f9fb")
    fig.text(.045, .94, "Hong Kong ADMM R3 | objective error against same-graph LP",
             fontsize=25, weight="bold", color="#153047")
    fig.text(.045, .875, "Saved 4-OD iterate sequence · log10 absolute difference in vehicle-minutes",
             fontsize=14, color="#547086")
    ax = fig.add_axes((.105, .19, .82, .60), facecolor="#f6f9fb")
    ax.plot(iteration, log_error, color="#087f8c", linewidth=2.6)
    ax.scatter([iteration[-1]], [log_error[-1]], s=48, color="#08775b", zorder=4)
    ax.set_xlim(1, 165)
    ax.set_ylim(math.floor(float(log_error.min()) * 2) / 2 - .2,
                math.ceil(float(log_error.max()) * 2) / 2 + .2)
    ax.set_xticks([1, 40, 80, 120, 165])
    ax.set_xlabel("outer iteration", fontsize=12, color="#547086", labelpad=8)
    ax.set_ylabel("log10 |ADMM objective − LP| (vehicle-minutes)", fontsize=12,
                  color="#547086", labelpad=10)
    ax.tick_params(labelsize=10, colors="#547086")
    ax.grid(axis="y", color="#dbe6ed", linewidth=.8)
    ax.spines["left"].set_color("#8299aa")
    ax.spines["bottom"].set_color("#8299aa")
    fig.text(.105, .09,
             f"Final absolute error: {difference[-1]:.6g} vehicle-minutes   ·   log10 error: {log_error[-1]:.4f}",
             fontsize=12, color="#153047")
    output_dir.mkdir(parents=True, exist_ok=True)
    png = output_dir / f"{STEM}.png"
    svg = output_dir / f"{STEM}.svg"
    fig.savefig(png, dpi=100, facecolor=fig.get_facecolor(), metadata={"Software": "MCL saved-result derivative"})
    fig.savefig(svg, facecolor=fig.get_facecolor(), metadata={"Date": None})
    plt.close(fig)
    record = {
        "figure": STEM,
        "status": "DERIVED_FROM_ACCEPTED_FRESH_SAVED_RESULT",
        "renderer": "tools/visuals/render_hk_admm_objective_log_error.py",
        "quantity": "log10(abs(saved ADMM objective - same-graph arc-flow LP objective))",
        "units_before_log": "vehicle-minutes",
        "outer_iterations": len(iteration),
        "iteration_range": [int(iteration[0]), int(iteration[-1])],
        "lp_reference_objective_vehicle_minutes": lp,
        "final_absolute_error_vehicle_minutes": float(difference[-1]),
        "final_log10_absolute_error": float(log_error[-1]),
        "zero_difference_count": 0,
        "zero_policy": "No recorded difference is zero; no epsilon floor, interpolation or smoothing was used.",
        "source_package_sha256": SOURCE_PACKAGE_SHA256,
        "restricted_inputs": [
            {"restricted_source_id": "fresh_admm_run/history.csv", "source_sha256": EXPECTED_HISTORY_SHA256, "distribution": "not included"},
            {"restricted_source_id": "fresh_lp_reference/ARC_FLOW_REFERENCE_SUMMARY.json", "source_sha256": EXPECTED_LP_SHA256, "distribution": "not included"},
        ],
        "preserved_raw_objective_figure": {"path": ORIGINAL.relative_to(ROOT).as_posix(), "sha256": sha(ORIGINAL)},
        "png_sha256": sha(png),
        "svg_sha256": sha(svg),
        "scientific_solver_rerun": False,
        "claim_boundary": "Accepted bounded four-OD graph only; numerical comparison to its own LP, not full-territory or empirical validation.",
    }
    (output_dir / f"{STEM}.source.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    (output_dir / f"{STEM}.caption.md").write_text(
        "**Caption.** Recorded-iteration log10 absolute difference between the saved Hong Kong ADMM R3 objective "
        "and the same-graph arc-flow LP objective (vehicle-minutes). The curve is not interpolated or smoothed; "
        "the final error is approximately 2.2518e-4 vehicle-minutes after 165 iterations.\n\n"
        "**Boundary.** Bounded four-OD modeled-demand graph only. The previously published raw-objective view is retained; "
        "the restricted iteration history and LP summary are not distributed.\n",
        encoding="utf-8", newline="\n")
    return record


def render_triptych(history_path: Path, lp_path: Path, physical_path: Path, output_dir: Path = OUT) -> dict:
    """Match Boston's residual / own-LP error / physical-link scatter objects."""
    iteration, difference, lp = read_saved_history(history_path, lp_path)
    if sha(physical_path) != EXPECTED_PHYSICAL_SHA256:
        raise ValueError("The physical-link comparison differs from the accepted R3 table")
    with history_path.open(newline="", encoding="utf-8-sig") as handle:
        history = list(csv.DictReader(handle))
    with physical_path.open(newline="", encoding="utf-8-sig") as handle:
        physical = list(csv.DictReader(handle))
    if len(physical) != 111 or len({r["physical_link_id"] for r in physical}) != 111:
        raise ValueError("Expected exactly 111 unique selected physical links")
    lp_flow = np.array([float(r["lp_flow_pce"]) for r in physical])
    admm_flow = np.array([float(r["admm_flow_pce"]) for r in physical])
    if not np.isfinite(lp_flow).all() or not np.isfinite(admm_flow).all() or np.any(lp_flow < 0) or np.any(admm_flow < 0):
        raise ValueError("Physical-link flows must be finite and nonnegative")
    positive_lp, positive_admm = int(np.count_nonzero(lp_flow > 0)), int(np.count_nonzero(admm_flow > 0))
    rmse = float(np.sqrt(np.mean((admm_flow - lp_flow)**2)))
    max_difference = float(np.max(np.abs(admm_flow - lp_flow)))
    if (positive_lp, positive_admm) != (58, 58) or not math.isclose(rmse, 1.2935472922076921e-08, rel_tol=1e-6) or not math.isclose(max_difference, 6.371185934384016e-08, rel_tol=1e-6):
        raise ValueError("The physical-flow support or independent-check metrics changed")
    residuals = {name: np.array([float(r[name]) for r in history]) for name in
                 ("primal_residual", "dual_residual", "primal_threshold", "dual_threshold")}
    if any(np.any(values <= 0) or not np.isfinite(values).all() for values in residuals.values()):
        raise ValueError("Nonpositive residual or threshold needs an explicit log-display policy")

    fig = plt.figure(figsize=(15, 5.6), dpi=100, facecolor="white")
    fig.text(.045, .94, "Hong Kong ADMM R3 | saved-result sequence", fontsize=21,
             weight="bold", color="#153047")
    fig.text(.045, .865, "Fresh bounded 4-OD graph · same-graph LP reference · original physical links",
             fontsize=11, color="#547086")
    axs = [fig.add_axes((x, .24, .27, .48)) for x in (.065, .385, .705)]
    teal, blue, coral, muted = "#087f8c", "#315ab5", "#d87553", "#9eb4be"
    ax = axs[0]
    for key, color, label, style in (
        ("primal_residual", teal, "primal", "-"),
        ("dual_residual", blue, "dual", "-"),
        ("primal_threshold", coral, "primal gate", "--"),
        ("dual_threshold", "#bd8a35", "dual gate", "--"),
    ):
        ax.plot(iteration, np.log10(residuals[key]), color=color, lw=1.5 if style=="-" else 1,
                linestyle=style, label=label)
    ax.set_title("A  Residual convergence", fontsize=11, color="#153047", loc="left")
    ax.set_ylabel("log10 residual / gate", fontsize=8)
    ax.legend(fontsize=6.5, ncol=2, loc="lower left", frameon=False)

    ax = axs[1]
    ax.plot(iteration, np.log10(difference), color=teal, lw=1.9)
    ax.scatter([iteration[-1]], [math.log10(float(difference[-1]))], s=22, color="#08775b", zorder=4)
    ax.set_title("B  Objective error against LP", fontsize=11, color="#153047", loc="left")
    ax.set_ylabel("log10 |ADMM objective − LP|", fontsize=8)

    ax = axs[2]
    maximum = max(float(lp_flow.max()), float(admm_flow.max())) * 1.05
    ax.plot([0, maximum], [0, maximum], color=muted, lw=1, ls="--", zorder=1)
    ax.scatter(lp_flow, admm_flow, s=27, color=teal, edgecolors="white", linewidths=.25, zorder=3)
    ax.set_xlim(0, maximum); ax.set_ylim(0, maximum)
    ax.set_aspect("equal", adjustable="box")
    ax.set_title("C  Physical-link flow", fontsize=11, color="#153047", loc="left")
    ax.set_xlabel("LP flow (PCE)", fontsize=8)
    ax.set_ylabel("ADMM flow (PCE)", fontsize=8)
    for ax in axs[:2]:
        ax.set_xlim(1, 165)
        ax.set_xlabel("outer iteration", fontsize=8)
    for ax in axs:
        ax.grid(color="#dce6eb", lw=.55)
        ax.tick_params(labelsize=7)
        for spine in ("top", "right"): ax.spines[spine].set_visible(False)
    fig.text(.065, .085,
             "165 saved iterations  ·  final own-LP relative difference 6.827e-6  ·  111 physical links (58 positive in each flow)",
             fontsize=10, color="#547086")
    output_dir.mkdir(parents=True, exist_ok=True)
    png = output_dir / f"{TRIPTYCH_STEM}.png"
    svg = output_dir / f"{TRIPTYCH_STEM}.svg"
    fig.savefig(png, dpi=100, facecolor="white", metadata={"Software": "MCL saved-result derivative"})
    fig.savefig(svg, facecolor="white", metadata={"Date": None})
    plt.close(fig)
    record = {
        "figure": TRIPTYCH_STEM,
        "status": "DERIVED_FROM_ACCEPTED_FRESH_SAVED_RESULT",
        "renderer": "tools/visuals/render_hk_admm_objective_log_error.py",
        "panel_contract": {
            "A": "recorded-iteration log10 primal and dual residuals with their saved thresholds",
            "B": "recorded-iteration log10 absolute ADMM objective difference against this graph's LP objective",
            "C": "all 111 original physical links: LP physical-link flow on x, ADMM physical-link flow on y, PCE; identity line",
        },
        "physical_link_count": len(physical),
        "positive_support_lp": positive_lp,
        "positive_support_admm": positive_admm,
        "physical_flow_rmse_pce": rmse,
        "physical_flow_max_abs_difference_pce": max_difference,
        "zero_objective_difference_count": 0,
        "smoothing_or_jitter": False,
        "source_package_sha256": SOURCE_PACKAGE_SHA256,
        "restricted_inputs": [
            {"restricted_source_id": "fresh_admm_run/history.csv", "source_sha256": EXPECTED_HISTORY_SHA256, "distribution": "not included"},
            {"restricted_source_id": "fresh_lp_reference/ARC_FLOW_REFERENCE_SUMMARY.json", "source_sha256": EXPECTED_LP_SHA256, "distribution": "not included"},
            {"restricted_source_id": "HK_ADMM_R3_PHYSICAL_FLOW_COMPARISON.csv", "source_sha256": EXPECTED_PHYSICAL_SHA256, "distribution": "not included"},
        ],
        "png_sha256": sha(png),
        "svg_sha256": sha(svg),
        "scientific_solver_rerun": False,
        "claim_boundary": "Accepted bounded four-OD graph only; no full-territory or observed-traffic validation.",
    }
    (output_dir / f"{TRIPTYCH_STEM}.source.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    (output_dir / f"{TRIPTYCH_STEM}.caption.md").write_text(
        "**Caption.** Saved Hong Kong ADMM R3 residuals, log10 absolute objective error against its own arc-flow LP, "
        "and all 111 physical-link ADMM-versus-LP flows (PCE). The third panel uses the same LP-x/ADMM-y "
        "physical-link comparison object as Boston; 58 links have positive flow in each solution. Overlapping "
        "markers are not jittered.\n\n**Boundary.** Fresh bounded four-OD graph only; private saved history and "
        "link-flow records are not distributed.\n", encoding="utf-8", newline="\n")
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--history", type=Path, required=True, help="Accepted restricted R3 history CSV")
    parser.add_argument("--lp-summary", type=Path, required=True, help="Accepted same-graph LP summary JSON")
    parser.add_argument("--physical-comparison", type=Path, required=True,
                        help="Accepted restricted per-physical-link ADMM/LP comparison CSV")
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    record = render(args.history, args.lp_summary, args.output_dir)
    composite = render_triptych(args.history, args.lp_summary, args.physical_comparison, args.output_dir)
    print(json.dumps({key: record[key] for key in ("figure", "outer_iterations", "final_absolute_error_vehicle_minutes", "final_log10_absolute_error", "png_sha256", "svg_sha256")}, indent=2))
    print(json.dumps({key: composite[key] for key in ("figure", "physical_link_count", "positive_support_lp", "positive_support_admm", "physical_flow_rmse_pce", "png_sha256", "svg_sha256")}, indent=2))


if __name__ == "__main__":
    main()
