"""Bounded negative and repeatability tests against declared Boston input asset."""
import argparse
import hashlib
import shutil
import tempfile
from pathlib import Path

from boston_exchange import export, fresh_output, read_csv, validate, write_csv


def expect_failure(label, action):
    try:
        action()
    except (ValueError, KeyError):
        return label
    raise AssertionError(f"Expected failure did not occur: {label}")


def mutate_csv(path, edit):
    fields, rows = read_csv(path)
    edit(rows)
    write_csv(path, fields, rows)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--inputs", type=Path, required=True)
    p.add_argument("--schema", type=Path, required=True)
    args = p.parse_args()
    passed = []
    with tempfile.TemporaryDirectory(prefix="mcl gmns 测试 ") as folder:
        root = Path(folder)
        a, b = root / "export A", root / "export B"
        ma = export(args.inputs, a)
        mb = export(args.inputs, b)
        assert ma["export_sha256"] == mb["export_sha256"]
        passed.append("deterministic_second_export")
        assert ma["semantic_counts"]["fine_zones"] == 177
        assert ma["semantic_counts"]["distinct_access_nodes"] == 139
        passed.append("many_zones_share_physical_access_without_merge")
        passed.append(expect_failure("input_output_overlap", lambda: fresh_output(args.inputs, args.inputs / "inside")))
        passed.append(expect_failure("nonempty_output_refused", lambda: export(args.inputs, a)))
        for name, filename, edit in (
            ("duplicate_zone_rejected", "zone.csv", lambda rows: rows.append(dict(rows[0]))),
            ("missing_parent_rejected", "zone_hierarchy.csv", lambda rows: rows.pop()),
            ("missing_access_rejected", "zone_access.csv", lambda rows: rows.pop()),
            ("wrong_scenario_branch_rejected", "crosswalk.csv", lambda rows: rows.__setitem__(slice(None), [r for r in rows if not (r["scenario_id"] == "S2_exploratory_gps_overlay" and float(r["mu_transit_sensitivity"]) == 1.0)])),
        ):
            src = root / name
            shutil.copytree(args.inputs, src)
            mutate_csv(src / filename, edit)
            passed.append(expect_failure(name, lambda src=src, name=name: export(src, root / (name + " out"))))
        checks = validate(a, args.schema)
        assert checks["pass"]
        # Mutate copies of the actual export; keep the real candidate untouched.
        for name, filename, edit, check in (
            ("parent_double_load_rejected", "demand_S1.csv", lambda rows: rows[0].__setitem__("o_zone_id", "1001"), "S1_demand_fine_only"),
            ("unknown_evidence_link_rejected", "gps_path_links.csv", lambda rows: rows[0].__setitem__("link_id", "99999999"), "gps_link_fks"),
            ("capacity_double_conversion_rejected", "link.csv", lambda rows: next(r for r in rows if r["mcl_link_class"] == "physical").__setitem__("capacity", "2600"), "physical_standard_capacity_source"),
            ("direction_confusion_rejected", "link.csv", lambda rows: next(r for r in rows if r["mcl_link_class"] == "physical").__setitem__("dir_flag", "-1"), "physical_travel_direction"),
        ):
            dst = root / name
            shutil.copytree(a, dst)
            mutate_csv(dst / filename, edit)
            assert validate(dst, args.schema)[check] is False
            passed.append(name)
    print("PASS " + ", ".join(passed))


if __name__ == "__main__":
    main()
