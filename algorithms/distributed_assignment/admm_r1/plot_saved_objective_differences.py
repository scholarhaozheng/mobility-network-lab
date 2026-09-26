"""Render paired scalar ADMM figures from the accepted saved-result summary only.

No optimizer, scientific model, or research archive is read by this script.
"""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent


def main() -> None:
    with (HERE / "ADMM_ACCEPTED_RESULT_SUMMARY.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if {row["case"] for row in rows} != {"Sioux_200OD", "Sioux_250OD"}:
        raise ValueError("Expected exactly the two accepted Sioux cases")
    output = HERE / "figures"
    output.mkdir(exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "svg.fonttype": "none"})
    for row in rows:
        if row["status"] != "PASS" or row["capacity_and_conservation_gate"] != "PASS":
            raise ValueError(f"Unaccepted case: {row['case']}")
        admm = float(row["admm_objective_vehicle_min"])
        lp = float(row["arc_lp_objective_vehicle_min"])
        percent = 100.0 * (admm - lp) / lp
        stated = 100.0 * float(row["relative_difference_fraction"])
        if abs(percent - stated) > 1e-10:
            raise ValueError(f"Summary mismatch: {row['case']}")
        fig, ax = plt.subplots(figsize=(3.94, 1.70), layout="constrained")
        fig.patch.set_facecolor("white")
        ax.plot([0, percent], [0, 0], color="#9ab8ba", linewidth=1.3, zorder=1)
        ax.scatter([0], [0], marker="|", s=250, color="#3e545d", zorder=3)
        ax.scatter([percent], [0], marker="o", s=42, color="#087e83", zorder=4)
        ax.set_xlim(-0.000035, 0.00072)
        ax.set_ylim(-0.24, 0.24)
        ax.set_yticks([])
        ax.set_xticks([0, 0.0002, 0.0004, 0.0006])
        ax.set_xlabel("Objective difference from same-graph LP (%)", labelpad=5)
        ax.spines[["left", "right", "top"]].set_visible(False)
        ax.spines["bottom"].set_color("#768990")
        ax.tick_params(axis="x", colors="#3e545d", length=3)
        stem = row["case"].lower() + "_objective_difference"
        fig.savefig(output / f"{stem}.svg", facecolor="white")
        fig.savefig(output / f"{stem}.png", dpi=300, facecolor="white")
        plt.close(fig)


if __name__ == "__main__":
    main()
