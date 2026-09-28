#!/usr/bin/env python3
"""Refresh renderer-code hashes in existing R2 figure sidecars without redrawing."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/assets/three_city_r2"
RENDERER = Path(__file__).with_name("render_three_city_parallel_r2.py")
code_hash = hashlib.sha256(RENDERER.read_bytes()).hexdigest()
changed = []
for city in ("boston", "sioux", "hong_kong"):
    for family in ("physical_to_time_expanded_graph", "generated_column_time_indexed_path",
                   "time_expanded_to_physical_link_flow", "finite_space_time_case_sequence"):
        stem = OUT / f"{city}_{family}"
        side_path = stem.with_suffix(".source.json")
        side = json.loads(side_path.read_text(encoding="utf-8"))
        for ext in ("png", "svg"):
            current = hashlib.sha256(stem.with_suffix("." + ext).read_bytes()).hexdigest()
            if side[f"{ext}_sha256"] != current:
                raise ValueError(f"figure/output hash mismatch before sidecar refresh: {stem}.{ext}")
        if side["renderer_sha256"] != code_hash:
            side["renderer_sha256"] = code_hash
            side_path.write_text(json.dumps(side, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            changed.append(side_path.relative_to(ROOT).as_posix())
print(json.dumps({"status": "PASS", "renderer_sha256": code_hash,
                  "sidecars_refreshed": changed, "scientific_solver_rerun": False}, indent=2))
