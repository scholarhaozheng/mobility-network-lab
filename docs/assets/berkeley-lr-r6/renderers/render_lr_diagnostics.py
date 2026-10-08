"""Plot saved Berkeley LR records; no solver imports or scientific computation.

Input schema ``mcl.berkeley.lr-diagnostic-plot.v1`` (JSON numbers or numeric
strings are accepted; missing upper/gap values must be null or empty strings)::

    {
      "schema": "mcl.berkeley.lr-diagnostic-plot.v1",
      "history": [{"iteration": 1, "best_dual": 43.5,
        "best_primal": null, "gap": null, "max_multiplier": 0,
        "multiplier_positive_count": 0, "max_current_capacity_violation": 1,
        "path_pool_size": 4}],
      "recovery_history": [{"iteration": 1, "path_count": 4,
        "feasible": false, "objective": null}],
      "run": {"id": "receiver-selected-run", "iterations": 300,
        "diagnostic": true, "kind": "cold_start", "fixture": false,
        "first_certified_iteration": 10, "validation_status": "PASS"},
      "relative_gap_gate": 0.01,
      "reference": {"lp_objective_pce_minutes": 43.6674},
      "original_accepted": {"run_id": "frozen-original", "iterations": 10,
        "best_dual": 43.5846, "best_primal": 43.6674, "gap": 0.0018967},
      "source_records": [{"path": "history.csv", "sha256": "..."}]
    }

The abbreviated example describes fields, not valid complete evidence. History
must contain every saved iteration in increasing order, and run.iterations is
the final iteration number. ``first_certified_iteration`` is the first saved
certificate at or below ``relative_gap_gate``; it is never an invented stop in
the diagnostic run. ``original_accepted`` identifies the separately preserved
accepted experiment. ``diagnostic: true`` does not confer acceptance.

Instead of inline lists, ``history_csv`` and ``recovery_json`` may name files
relative to the input JSON. ``recovery_history`` may also be a list of records
read directly by a caller. Extra saved history fields are retained in exports.

API: normalize_input(mapping_or_json_path), render_all(data, output_dir), and
emit(fig, stem, title, caption, panels, data, output_dir, plot_data=None,
     function=None). ``emit`` is reusable by the separate physical-flow plot.
All exports are confined to output_dir; importing this module writes nothing.

Figure contract: four quantitative grids expose saved best bounds/certificates,
current multiplier diagnostics, and actual recovery events. Every saved point
is retained; missing upper bounds stay missing. The original formal gate and
later diagnostic rounds are distinguished without asserting that more rounds
improve the endpoint. Backend: existing atlas Python/matplotlib, selected C
layout, blue/teal/navy and DejaVu Serif. Outputs: editable SVG, PDF, 300dpi PNG,
exact normalized plot data, caption, source identities and export hashes.
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import importlib.util
import inspect
import json
import logging
import math
from pathlib import Path
from typing import Any, Mapping

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator
from PIL import Image


HERE = Path(__file__).resolve().parent
# A self-contained exported renderer may place the unchanged style files beside it.
STYLE_DIR = HERE if (HERE / "atlas_style.py").exists() else HERE.parent / "city_alignment_r3" / "berkeley"
SCHEMA = "mcl.berkeley.lr-diagnostic-plot.v1"


def _module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_style = _module("berkeley_lr_r6_style", STYLE_DIR / "atlas_style.py")
_fonts = _module("berkeley_lr_r6_fonts", STYLE_DIR / "embed_serif_fonts.py")
TEAL, BLUE, INK, ROAD, GRID = (_style.TEAL, _style.BLUE, _style.INK,
                               _style.ROAD, _style.GRID)
FLOW_CMAP, DIFF_CMAP = _style.FLOW_CMAP, _style.DIFF_CMAP
new_figure, format_axes, compact_header = (_style.new_figure,
                                         _style.format_axes,
                                         _style.compact_header)
logging.getLogger("fontTools.subset").setLevel(logging.ERROR)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _number(value, name, nullable=False):
    if value is None or value == "":
        if nullable:
            return None
        raise ValueError(f"Missing required number: {name}")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"Non-finite number: {name}")
    return value


def _integer(value, name):
    value = _number(value, name)
    if value != int(value):
        raise ValueError(f"Not an integer: {name}")
    return int(value)


def _boolean(value, name):
    if value is True or value == "True" or value == "true":
        return True
    if value is False or value == "False" or value == "false":
        return False
    raise ValueError(f"Not a boolean: {name}")


def normalize_input(value: Mapping[str, Any] | str | Path) -> dict:
    """Normalize and verify display semantics, without substituting run values."""
    source_path = None
    if isinstance(value, (str, Path)):
        source_path = Path(value).resolve()
        data = json.loads(source_path.read_text(encoding="utf-8"))
        base = source_path.parent
    else:
        data = copy.deepcopy(dict(value))
        base = Path.cwd()
    if data.get("schema", SCHEMA) != SCHEMA:
        raise ValueError("Unsupported LR plotting schema")
    data["schema"] = SCHEMA
    sources = list(data.get("source_records", []))
    if "history" not in data:
        path = (base / data["history_csv"]).resolve()
        with path.open(encoding="utf-8-sig", newline="") as stream:
            data["history"] = list(csv.DictReader(stream))
        sources.append({"path": str(path), "sha256": sha(path)})
    if "recovery_history" not in data:
        path = (base / data["recovery_json"]).resolve()
        data["recovery_history"] = json.loads(path.read_text(encoding="utf-8"))
        sources.append({"path": str(path), "sha256": sha(path)})
    if source_path:
        sources.append({"path": str(source_path), "sha256": sha(source_path)})
    data["source_records"] = sources
    required = ("best_dual", "max_multiplier", "multiplier_positive_count",
                "max_current_capacity_violation", "path_pool_size")
    history = data["history"]
    if not history:
        raise ValueError("History is empty")
    for record in history:
        record["iteration"] = _integer(record["iteration"], "iteration")
        for key in required:
            record[key] = _number(record.get(key), key)
        for key in ("best_primal", "gap"):
            record[key] = _number(record.get(key), key, nullable=True)
        for key in ("multiplier_positive_count", "path_pool_size"):
            record[key] = _integer(record[key], key)
        for key in required[1:]:
            if record[key] < 0:
                raise ValueError(f"Negative saved {key}")
        if (record["best_primal"] is None) != (record["gap"] is None):
            raise ValueError("Upper bound and certificate gap must be jointly missing")
        if record["best_primal"] is not None:
            upper, lower = record["best_primal"], record["best_dual"]
            expected = max(0.0, (upper - lower) / max(1.0, abs(upper)))
            if lower > upper + max(1.0, abs(upper)) * 1e-9:
                raise ValueError("Best lower exceeds feasible upper")
            if not math.isclose(record["gap"], expected, rel_tol=1e-7, abs_tol=1e-11):
                raise ValueError("Saved gap differs from bound-derived certificate")
    iterations = [r["iteration"] for r in history]
    if iterations[0] < 0 or iterations != list(range(iterations[0], iterations[-1] + 1)):
        raise ValueError("History must preserve every iteration in increasing order")
    lower = np.array([r["best_dual"] for r in history])
    tolerance = max(1.0, float(np.max(np.abs(lower)))) * 1e-9
    if np.any(np.diff(lower) < -tolerance):
        raise ValueError("Saved best-dual sequence decreases")
    upper_rows = [r for r in history if r["best_primal"] is not None]
    if upper_rows:
        first_upper = upper_rows[0]["iteration"]
        if any(r["best_primal"] is None for r in history if r["iteration"] > first_upper):
            raise ValueError("A saved best feasible upper disappears after recovery")
        if np.any(np.diff([r["best_primal"] for r in upper_rows]) > tolerance):
            raise ValueError("Saved best-primal sequence increases")
    gate = _number(data.get("relative_gap_gate", 0.01), "relative_gap_gate")
    if gate <= 0:
        raise ValueError("Relative gap gate must be positive")
    data["relative_gap_gate"] = gate
    passing = [r["iteration"] for r in history
               if r["gap"] is not None and r["gap"] <= gate]
    first_gate = passing[0] if passing else None
    run = data["run"]
    if not run.get("id"):
        raise ValueError("run.id is required")
    if "iterations" in run and _integer(run["iterations"], "run.iterations") != iterations[-1]:
        raise ValueError("run.iterations must equal the actual final saved iteration")
    if "first_certified_iteration" in run and run["first_certified_iteration"] != first_gate:
        raise ValueError("Declared first certified iteration differs from history")
    run.update(iterations=iterations[-1], first_certified_iteration=first_gate)
    run["diagnostic"] = _boolean(run.get("diagnostic", True), "run.diagnostic")
    run["fixture"] = _boolean(run.get("fixture", False), "run.fixture")
    original = data["original_accepted"]
    original["iterations"] = _integer(original["iterations"], "original_accepted.iterations")
    for key in ("best_dual", "best_primal", "gap"):
        if key in original:
            original[key] = _number(original[key], "original_accepted." + key)
    for record in data["recovery_history"]:
        record["iteration"] = _integer(record["iteration"], "recovery.iteration")
        record["path_count"] = _integer(record["path_count"], "recovery.path_count")
        record["feasible"] = _boolean(record["feasible"], "recovery.feasible")
        record["objective"] = _number(record.get("objective"), "recovery.objective", nullable=True)
        if record["iteration"] not in iterations or record["path_count"] < 0:
            raise ValueError("Recovery call has invalid iteration/path count")
        if record["feasible"] != (record["objective"] is not None):
            raise ValueError("Infeasible recovery must have null objective; feasible needs a cost")
    recovery_iterations = [r["iteration"] for r in data["recovery_history"]]
    if recovery_iterations != sorted(recovery_iterations):
        raise ValueError("Recovery calls must retain saved chronological order")
    lp = data.setdefault("reference", {}).get("lp_objective_pce_minutes")
    if lp is not None:
        data["reference"]["lp_objective_pce_minutes"] = _number(lp, "reference LP")
    data["display_validation"] = {
        "status": "PASS", "history_rows": len(history),
        "first_iteration": iterations[0], "last_iteration": iterations[-1],
        "missing_upper_rows": sum(r["best_primal"] is None for r in history),
        "missing_gap_rows": sum(r["gap"] is None for r in history),
        "recovery_calls": len(data["recovery_history"]),
        "first_certified_iteration": first_gate,
        "best_bound_attained_iteration": iterations[int(np.argmax(lower))],
        "highest_saved_best_dual": float(np.max(lower)),
        "final_current_dual": _number(history[-1].get("dual"), "final current dual", nullable=True),
        "final_signed_upper_minus_lower": (history[-1]["best_primal"] - history[-1]["best_dual"]
                                           if history[-1]["best_primal"] is not None else None),
        "certificate_formula": "max(0,(best_primal-best_dual)/max(1,abs(best_primal)))",
        "zero_gap_interpretation": "Saved clipping at zero can indicate numerical agreement at floating-point precision; it is not an algebraic proof of exact equality.",
        "numerical_acceptance": "Receiver status is metadata; this checks plotting semantics only."
    }
    return data


def _series(data, key):
    return np.array([np.nan if r.get(key) is None else float(r[key])
                     for r in data["history"]])


def _scope(data):
    run, original = data["run"], data["original_accepted"]
    if run["fixture"]:
        return f"FIXTURE / {len(data['history'])} original saved rounds; no new run"
    status = "cold diagnostic" if run.get("kind") == "cold_start" else "diagnostic"
    return f"T4 / original accepted stop {original['iterations']} / {status}: {run['iterations']} rounds"


def _provenance_text(data):
    run, original = data["run"], data["original_accepted"]
    prefix = ("FIXTURE PREVIEW: only the original saved records are drawn; no extended run is claimed. "
              if run["fixture"] else "")
    text = (prefix + f"The original accepted run remains separately preserved at iteration {original['iterations']}. "
            f"This view uses {len(data['history'])} actual saved records from run {run['id']}, "
            f"through iteration {run['iterations']}. ")
    if run["diagnostic"]:
        text += "The extended trace is a diagnostic experiment and does not retroactively change the original stopping decision. "
    if run.get('validation_status') == 'PASS':
        text += 'Independent diagnostic audit passed. '
        if run.get('formal_evaluation_status') != 'PASS':
            text += 'The original formal-entry replay is pending at this figure export; the 300-round run is not labelled formally accepted. '
    first = run["first_certified_iteration"]
    if first is not None:
        text += f"The formal {100 * data['relative_gap_gate']:g}% certificate is first met at saved iteration {first}; later rounds, when present, are shaded as post-gate diagnostics. "
    else:
        text += "No saved iteration meets the declared certificate gate. "
    return text


def _panel(ax, title):
    format_axes(ax)
    ax.set_title(title, loc="left", fontsize=10, fontweight="bold", pad=10)


def _clock(ax, data, xlabel="Lagrangian iteration"):
    x = _series(data, "iteration")
    pad = max(0.3, (x[-1] - x[0]) * 0.035)
    ax.set_xlim(x[0] - pad, x[-1] + pad)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=4, steps=[1, 2, 2.5, 5, 10]))
    if len(x) == 1:
        ax.set_xticks(x)
    ax.set_xlabel(xlabel)
    first = data["run"]["first_certified_iteration"]
    if first is not None:
        if x[-1] > first:
            ax.axvspan(first, x[-1], color="#eef3f5", zorder=-2)
        ax.axvline(first, color="#7b8d98", linestyle=":", linewidth=0.9, zorder=1)


def _footer(fig, data):
    first = data["run"]["first_certified_iteration"]
    if first is None:
        text = "All saved records shown; no formal certificate gate has been met."
    elif data["run"]["iterations"] > first:
        text = f"Dotted line: first formal certificate at iteration {first}.  Shading: subsequent diagnostic rounds."
    else:
        text = f"Dotted line: first formal certificate at iteration {first}.  No later rounds are present in these records."
    fig.text(0.075, 0.025, text, fontsize=8, color=INK)


def _bounds_panel(ax, data, title="a  Best saved bounds"):
    _panel(ax, title)
    x, lower, upper = (_series(data, k) for k in ("iteration", "best_dual", "best_primal"))
    ax.step(x, lower, where="post", color=TEAL, linewidth=1.7, label="Best dual lower bound")
    ax.step(x, upper, where="post", color=BLUE, linewidth=1.7, label="Recovered primal upper")
    selected = {0, len(x) - 1}
    selected.add(int(np.argmax(lower)))
    first = data["run"]["first_certified_iteration"]
    if first is not None:
        selected.add(int(np.flatnonzero(x == first)[0]))
    available = np.flatnonzero(np.isfinite(upper))
    if len(available):
        selected.add(int(available[0]))
    selected = sorted(selected)
    ax.scatter(x[selected], lower[selected], s=16, color=TEAL, zorder=4)
    finite = [i for i in selected if np.isfinite(upper[i])]
    ax.scatter(x[finite], upper[finite], s=21, color=BLUE, zorder=4)
    values = np.r_[lower, upper[np.isfinite(upper)]]
    low, high = float(values.min()), float(values.max())
    span = max(high - low, max(abs(high), 1) * 0.001)
    ax.set_ylim(low - span * 0.20, high + span * 0.50)
    ax.set_ylabel("Objective (PCE·min)")
    ax.ticklabel_format(axis="y", style="plain", useOffset=False)
    ax.yaxis.set_major_locator(MaxNLocator(nbins=5))
    ax.legend(loc="upper left", fontsize=7.5)
    _clock(ax, data)


def _gap_panel(ax, data, title="b  Certified relative gap"):
    _panel(ax, title)
    x, gap = _series(data, "iteration"), _series(data, "gap") * 100
    gate = data["relative_gap_gate"] * 100
    ax.step(x, gap, where="post", color=TEAL, linewidth=1.7)
    finite = np.flatnonzero(np.isfinite(gap))
    if len(finite):
        indices = sorted({int(finite[0]), int(finite[-1])})
        ax.scatter(x[indices], gap[indices], s=25, color=TEAL, zorder=4)
        last = finite[-1]
        final_label = f"{gap[last]:.5g}% at {int(x[last])}"
        if gap[last] == 0:
            final_label += "\n(floating-point closure)"
        ax.annotate(final_label,
                    xy=(x[last], gap[last]), xytext=(-6, 9), textcoords="offset points",
                    ha="right", va="bottom", fontsize=8, color=TEAL)
        first_gate = data["run"]["first_certified_iteration"]
        if first_gate is not None and first_gate != int(x[last]):
            at_gate = int(np.flatnonzero(x == first_gate)[0])
            ax.scatter([x[at_gate]], [gap[at_gate]], s=25, color=TEAL, zorder=4)
            ax.annotate(f"{gap[at_gate]:.5g}% at {first_gate}",
                        xy=(x[at_gate], gap[at_gate]), xytext=(6, 9),
                        textcoords="offset points", ha="left", va="bottom",
                        fontsize=8, color=TEAL)
    ax.axhline(gate, color=BLUE, linestyle="--", linewidth=1, label=f"Frozen {gate:g}% gate")
    ymax = max(gate, float(np.nanmax(gap)) if len(finite) else 0)
    ax.set_ylim(-max(ymax, 1e-6) * .03, max(ymax, 1e-6) * 1.23)
    ax.set_ylabel("Gap (%)")
    ax.legend(loc="upper right", fontsize=8)
    _clock(ax, data)


def _pool_panel(ax, data, title="a  Saved path pool"):
    _panel(ax, title)
    x, values = _series(data, "iteration"), _series(data, "path_pool_size")
    ax.step(x, values, where="post", color=TEAL, linewidth=1.6)
    if len(x) <= 20:
        ax.scatter(x, values, s=18, color=TEAL, zorder=4)
    low, high = values.min(), values.max()
    pad = max(0.6, float(high - low) * 0.15)
    ax.set_ylim(max(0, low - pad), high + pad)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True, nbins=5))
    ax.set_ylabel("Available paths")
    _clock(ax, data)


def _recovery_panel(ax, data, title="b  Actual recovery LP calls"):
    _panel(ax, title)
    records = data["recovery_history"]
    for feasible, color, label in ((True, TEAL, "Feasible"), (False, BLUE, "Infeasible")):
        subset = [r for r in records if r["feasible"] == feasible]
        if subset:
            ax.scatter([r["iteration"] for r in subset], [r["path_count"] for r in subset],
                       s=38, facecolors=color if feasible else "white", edgecolors=color,
                       linewidths=1.1, marker="o" if feasible else "s", label=label, zorder=4)
    values = [r["path_count"] for r in records]
    if values:
        low, high = min(values), max(values)
        pad = max(0.8, (high - low) * 0.22)
        ax.set_ylim(max(0, low - pad), high + pad * 2.5)
        ax.legend(fontsize=7.5, loc="upper left", ncol=2)
    else:
        ax.set_ylim(0, 1)
        ax.text(.5, .5, "No recovery calls saved", transform=ax.transAxes, ha="center")
    feasible_records = [r for r in records if r["feasible"]]
    if feasible_records:
        best = min(r["objective"] for r in feasible_records)
        ax.text(.98, .04, f"Best feasible call: {best:.8f} PCE·min", transform=ax.transAxes,
                ha="right", va="bottom", fontsize=7.6, color=TEAL,
                bbox={"facecolor": "white", "edgecolor": "none", "alpha": .8, "pad": 1.5})
    ax.yaxis.set_major_locator(MaxNLocator(integer=True, nbins=5))
    ax.set_ylabel("Paths supplied to recovery LP")
    _clock(ax, data, "LR iteration at recovery call")


def emit(fig, stem, title, caption, panels, data, output_dir, *, plot_data=None, function=None):
    """Save one atlas figure and return its integration-ready metadata record."""
    data = normalize_input(data)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    layout = compact_header(fig)
    for ext in ("svg", "png", "pdf"):
        metadata = {"Date": None} if ext == "svg" else (
            {"CreationDate": None, "ModDate": None} if ext == "pdf" else None)
        fig.savefig(out / (stem + "." + ext), dpi=300, bbox_inches="tight",
                    pad_inches=.055, metadata=metadata)
    fonts = _fonts.embed_serif_fonts(out / (stem + ".svg"))
    with Image.open(out / (stem + ".png")) as im:
        dimensions = list(im.size)
    plt.close(fig)
    if function is None:
        caller = inspect.currentframe().f_back
        renderer_path = Path(caller.f_code.co_filename)
        renderer_function = caller.f_code.co_name
        line = caller.f_code.co_firstlineno
    else:
        renderer_path = Path(inspect.getsourcefile(function))
        renderer_function = function.__name__
        line = inspect.getsourcelines(function)[1]
    record = {
        "id": "BERKELEY-R6-" + stem.upper().replace("_", "-"), "stem": stem,
        "title": title, "city": "Berkeley", "stage": "finite", "caption": caption,
        "panels": panels, "dimensions": dimensions,
        "renderer": {"file": renderer_path.name, "function": renderer_function,
                     "line": line, "sha256": sha(renderer_path)},
        "source_records": data["source_records"], "run": data["run"],
        "original_accepted": data["original_accepted"],
        "reference": data["reference"], "display_validation": data["display_validation"],
        "style": {"layout": "C", "font": "DejaVu Serif", "palette": _style.PALETTE,
                  "functions": ["new_figure", "format_axes", "compact_header"],
                  "style_sha256": sha(STYLE_DIR / "atlas_style.py")},
        "layout_adjustment": layout, "font": fonts,
        "solver_calls_by_renderer": 0,
        "status": "FIXTURE_PREVIEW" if data["run"]["fixture"] else "SAVED_DIAGNOSTIC_PLOT",
        "exports": {ext: {"path": stem + "." + ext, "sha256": sha(out / (stem + "." + ext))}
                    for ext in ("svg", "png", "pdf")}
    }
    payload = copy.deepcopy(data)
    if plot_data is not None:
        payload["figure_data"] = plot_data
    for suffix, content in ((".source.json", record), (".plot_data.json", payload)):
        (out / (stem + suffix)).write_text(json.dumps(content, ensure_ascii=False,
                                                     indent=2, allow_nan=False) + "\n", encoding="utf8")
    (out / (stem + ".caption.md")).write_text(caption + "\n", encoding="utf8")
    return record


def lr_bounds(data, output_dir):
    data = normalize_input(data)
    title = "Lagrangian bounds and certified gap"
    fig = new_figure("berkeley", title, _scope(data), figsize=(9.5, 4.8))
    _bounds_panel(fig.add_axes([.095, .235, .36, .53]), data)
    _gap_panel(fig.add_axes([.61, .235, .34, .53]), data)
    _footer(fig, data)
    last = data["history"][-1]
    caption = _provenance_text(data) + (
        "Teal denotes the saved best dual lower bound and blue the separately recovered feasible upper. "
        "The right panel shows 100 times the saved dimensionless certificate on a linear percentage axis, "
        "against the unchanged gate. Missing upper/gap records remain unplotted. "
        f"Final best lower is {last['best_dual']:.16g} PCE·min; "
        + (f"best upper is {last['best_primal']:.16g} PCE·min and gap is {100*last['gap']:.16g}%. "
           if last["best_primal"] is not None else "no feasible upper is saved. ")
        + f"The highest saved best bound first appears at iteration {data['display_validation']['best_bound_attained_iteration']}. "
        + (f"The final current relaxed dual is separately {data['display_validation']['final_current_dual']:.16g} PCE·min; it is not substituted for the running best bound. "
           if data['display_validation']['final_current_dual'] is not None else "")
        + "The certificate is max(0, (U−L)/max(1,|U|)). "
        + (f"The final signed U−L is {data['display_validation']['final_signed_upper_minus_lower']:.6g} PCE·min. A saved zero gap here denotes numerical agreement at floating-point precision, not an algebraic proof of exact equality. "
           if last['gap'] == 0 else "")
        + "The independent LP scalar remains in metadata and is not substituted for an LR upper bound. "
          "No smoothing, invented points, or optimizer calls are used by this renderer.")
    return emit(fig, "lr_bounds", title, caption,
                {"a": "Saved best lower and recovered best upper; PCE·min",
                 "b": "Saved certified gap in percent; frozen gate"}, data, output_dir, function=lr_bounds)


def lr_prices(data, output_dir):
    data = normalize_input(data)
    title = "Lagrangian prices and relaxed capacity violations"
    fig = new_figure("berkeley", title, _scope(data), figsize=(11.3, 5.1))
    specs = [(.075, "max_multiplier", "a  Maximum capacity\nmultiplier", "Price (min)", TEAL),
             (.405, "multiplier_positive_count", "b  Positive-price\ndynamic arcs", "Priced dynamic arcs", BLUE),
             (.735, "max_current_capacity_violation", "c  Relaxed capacity\nexcess", "Maximum excess (PCE)", INK)]
    for left, field, heading, ylabel, color in specs:
        ax = fig.add_axes([left, .235, .215, .50])
        _panel(ax, heading)
        x, values = _series(data, "iteration"), _series(data, field)
        ax.plot(x, values, color=color, linewidth=1.2,
                marker="o" if len(x) <= 20 else None, markersize=3)
        ax.set_ylim(0, max(float(values.max()) * 1.16, 1 if "count" in field else .01))
        if "count" in field:
            ax.yaxis.set_major_locator(MaxNLocator(integer=True, nbins=5))
        ax.set_ylabel(ylabel)
        _clock(ax, data)
    _footer(fig, data)
    caption = _provenance_text(data) + (
        "Every saved current-iterate maximum capacity multiplier, strictly positive multiplier count "
        "and maximum relaxed capacity excess is shown. Multiplier units are minutes, from a PCE·min "
        "objective divided by a PCE capacity; relaxed excess is PCE. These current-iterate summaries "
        "are distinct from the saved best-dual multiplier state. Relaxed excess is not the feasibility "
        "residual of separately recovered primal flow. A closed best-bound certificate does not imply "
        "that subsequent current multipliers stop changing; the full diagnostic retains those changes. "
        "No smoothing or per-arc history is inferred.")
    return emit(fig, "lr_prices", title, caption,
                {"a": "Current max_multiplier, min", "b": "Current multiplier_positive_count",
                 "c": "Current max_current_capacity_violation, PCE"}, data, output_dir, function=lr_prices)


def lr_recovery(data, output_dir):
    data = normalize_input(data)
    title = "Path-pool growth and separate primal recovery"
    fig = new_figure("berkeley", title, _scope(data), figsize=(10.4, 4.9))
    _pool_panel(fig.add_axes([.09, .24, .35, .52]), data)
    _recovery_panel(fig.add_axes([.60, .24, .35, .52]), data)
    _footer(fig, data)
    records = data["recovery_history"]
    feasible = sum(r["feasible"] for r in records)
    caption = _provenance_text(data) + (
        f"Panel a retains all {len(data['history'])} saved path-pool sizes; panel b shows exactly "
        f"{len(records)} actual recovery calls ({feasible} feasible, {len(records)-feasible} infeasible). "
        "Filled circles are feasible calls and open squares are infeasible calls. Null objectives remain "
        "missing and are never zero-imputed. Pool growth is not a sequence of feasible upper bounds. "
        "The call records and own recovered physical flow retain their separate source identities.")
    return emit(fig, "lr_recovery", title, caption,
                {"a": "Every saved path_pool_size", "b": "Actual recovery calls and their feasibility"},
                data, output_dir, function=lr_recovery)


def t03_lr_bounds_physical(data, output_dir):
    data = normalize_input(data)
    title = "Lagrangian bounds and primal recovery"
    fig = new_figure("berkeley", title, _scope(data), figsize=(10.5, 7.7))
    _bounds_panel(fig.add_axes([.095, .575, .355, .24]), data)
    _gap_panel(fig.add_axes([.61, .575, .34, .24]), data)
    _pool_panel(fig.add_axes([.095, .185, .355, .24]), data, "c  Saved path pool")
    _recovery_panel(fig.add_axes([.61, .185, .34, .24]), data, "d  Actual recovery LP calls")
    _footer(fig, data)
    caption = _provenance_text(data) + (
        "The retained combined view separates best bounds, percentage certificate, saved path-pool "
        "growth and actual recovery LP calls. It uses the same complete normalized records as the three "
        "individual LR figures. Best-so-far bounds are not current relaxed dual costs. Missing primal "
        "certificates and infeasible recovery objectives remain missing. The certificate is "
        "max(0, (U−L)/max(1,|U|)); a saved zero from floating-point bound agreement is not an "
        "algebraic proof of exact equality. The separate physical-flow "
        "comparison must use this diagnostic run's own selected recovered flow; this panel does not "
        "assert equality with LP or CG. No physical flow or unseen recovery state is inferred here.")
    return emit(fig, "t03_lr_bounds_physical", title, caption,
                {"a": "Best saved lower and recovered upper", "b": "Available gap percent",
                 "c": "Saved path-pool size", "d": "Actual separate recovery calls"},
                data, output_dir, function=t03_lr_bounds_physical)


STYLES = ("lr_bounds", "lr_prices", "lr_recovery", "t03_lr_bounds_physical")


def render_all(data, output_dir, *, styles=STYLES):
    """Render only requested LR figures; return records without site mutation."""
    data = normalize_input(data)
    if not set(styles) <= set(STYLES):
        raise ValueError("Unknown LR figure style")
    return [globals()[name](data, output_dir) for name in styles]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input_json", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--styles", nargs="+", choices=STYLES, default=STYLES)
    args = parser.parse_args()
    records = render_all(args.input_json, args.output_dir, styles=args.styles)
    result = {"status": "RENDERED_PENDING_VISUAL_REVIEW", "solver_calls_by_renderer": 0,
              "input_sha256": sha(args.input_json), "figures": records}
    (args.output_dir / "LR_FIGURES.json").write_text(json.dumps(result, ensure_ascii=False,
                                                              indent=2) + "\n", encoding="utf8")
    print(json.dumps({"figures": len(records), "output_dir": str(args.output_dir)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
