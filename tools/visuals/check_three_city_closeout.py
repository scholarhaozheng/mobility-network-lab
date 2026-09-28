#!/usr/bin/env python3
"""No-solve assertions for the bounded R2 presentation closeout."""
from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[2]
errors: list[str] = []
checks = 0


def check(condition: bool, message: str) -> None:
    global checks
    checks += 1
    if not condition:
        errors.append(message)


def content(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


class HtmlEvidence(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.hrefs: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = dict(attrs)
        if data.get("id"):
            self.ids.add(data["id"])
        if tag == "a" and data.get("href"):
            self.hrefs.add(data["href"])


readme = content("README.md")
for city in ("boston", "sioux", "hong_kong"):
    r2 = f"docs/assets/three_city_r2/{city}_finite_space_time_case_sequence.png"
    r1 = f"docs/assets/three_city_r1/{city}_finite_space_time_case_sequence.png"
    check(bool(re.search(r'<img\s+src="' + re.escape(r2) + r'"', readme)), f"README not embedding current {city} R2 D")
    check(not bool(re.search(r'<img\s+src="' + re.escape(r1) + r'"', readme)), f"README still embedding superseded {city} R1 D")
    check(r1 in readme, f"README lost historical {city} R1 D link")
    page = content(f"docs/cases/{'sioux' if city == 'sioux' else city.replace('_', '-')}-space-time.md")
    for family in ("finite_space_time_case_sequence", "generated_column_time_indexed_path", "time_expanded_to_physical_link_flow"):
        r1_fragment = f"../assets/three_city_r1/{city}_{family}.png"
        r2_fragment = f"../assets/three_city_r2/{city}_{family}.png"
        check(f"]({r1_fragment})" in page and f"]({r2_fragment})" in page,
              f"{city} {family}: historical/current links missing")
        check(not bool(re.search(r'!\[[^\]]*\]\(' + re.escape(r1_fragment) + r'\)', page)),
              f"{city} {family}: superseded R1 duplicate still embedded")
        check(bool(re.search(r'!\[[^\]]*\]\(' + re.escape(r2_fragment) + r'\)', page)),
              f"{city} {family}: R2 view not embedded")

check(readme.index("## 03 / Comparable statistics") < readme.index("<a id=\"boston\"></a>"),
      "statistics no longer precede case details")
check("Sioux_200OD_P07.svg" not in readme[:readme.index("## 03 / Comparable statistics")],
      "detailed Sioux experiment still interrupts coverage and statistics")
check(readme.count("### Distributed assignment algorithms / bounded accepted results") == 1,
      "distributed-assignment heading duplicated")
for title in ("Boston / A generated column as a time-indexed path",
              "Sioux Falls / From the physical network to the finite time-expanded graph",
              "Hong Kong / From the physical network to the finite time-expanded graph"):
    check(title in readme, f"canonical visible README title absent: {title}")

for city, cats, changes in (
    ("boston", ["B07", "B09", "B10"], [-0.36462212977800723, -1.083333333333333, 1.0833333333333333]),
    ("sioux", ["XS170", "XS169"], [-500.0, 500.0]),
):
    stem = f"docs/assets/three_city_r2/{city}_finite_space_time_case_sequence"
    side = json.loads(content(stem + ".source.json"))
    svg = content(stem + ".svg")
    check(side.get("capacity_bar_categories") == cats, f"{city}: missing exact bar categories")
    check(all(abs(a-b) < 1e-10 for a,b in zip(side.get("capacity_bar_changes", []), changes))
          and len(side.get("capacity_bar_changes", [])) == len(changes), f"{city}: capacity bar values changed")
    check(side.get("capacity_bar_unit") == "model vehicles", f"{city}: missing capacity bar unit")
    for cat in cats:
        check(f">{cat}<" in svg, f"{city}: category label not rendered in SVG: {cat}")
    for value in changes:
        label = f"{value:+.3f}" if city == "boston" else f"{value:+.0f}"
        check(f">{label}<" in svg, f"{city}: signed bar value not rendered in SVG: {label}")
    check("<path" in svg and "0" in svg, f"{city}: D vector is empty")
sioux_side = json.loads(content("docs/assets/three_city_r2/sioux_finite_space_time_case_sequence.source.json"))
check("c/e: 200-OD traces only" in sioux_side.get("panel_instance_scope", ""),
      "Sioux D does not scope c/e to 200 OD")
check("Positive-flow links: not reported in released summary" in content("docs/assets/three_city_r2/sioux_finite_space_time_case_sequence.svg"),
      "Sioux positive-flow placeholder remains malformed")

broken = [
    ("docs/index.html", "cases/boston.html#experiments--reproduction"),
    ("docs/index.html", "cases/sioux-falls.html#experiments--reproduction"),
    ("docs/index.html", "cases/sioux-space-time.html#6-independent-pricing-closure"),
    ("docs/cases/boston.html", "#experiments--reproduction"),
    ("docs/cases/sioux-falls.html", "#experiments--reproduction"),
]
for source, href in broken:
    source_html = HtmlEvidence(); source_html.feed(content(source))
    check(href in source_html.hrefs, f"historical fragment source href no longer resolves as specified: {source} {href}")
    parsed = urlsplit(href)
    target = (ROOT / source).parent / unquote(parsed.path) if parsed.path else ROOT / source
    check(target.is_file(), f"fragment target file missing: {target}")
    if target.is_file():
        target_html = HtmlEvidence(); target_html.feed(target.read_text(encoding="utf-8"))
        check(unquote(parsed.fragment) in target_html.ids, f"fragment target ID missing: {href}")

status = json.loads(content("docs/assets/three_city_r2/DISCLOSURE_STATUS_R2.json"))
pending = set(status["pending_paths"])
check(status["owner_artifact_level_publication_approval"] == "PENDING", "HK10 disclosure gate was lifted")
required = {"README.md", "docs/index.md", "docs/index.html", "docs/cases/hong-kong.md",
            "docs/cases/hong-kong.html", "docs/cases/hong-kong-space-time.md",
            "docs/cases/hong-kong-space-time.html", "tools/visuals/render_three_city_parallel.py",
            "tools/visuals/render_three_city_parallel_r2.py"}
required |= {f"docs/assets/three_city_r1/data/hong_kong_selected_generated_column.{ext}"
             for ext in ("csv", "source.json")}
for release in ("r1", "r2"):
    for family in ("generated_column_time_indexed_path", "finite_space_time_case_sequence"):
        required |= {f"docs/assets/three_city_{release}/hong_kong_{family}.{ext}"
                     for ext in ("png", "svg", "source.json", "caption.md", "caption.html")}
check(required <= pending, f"HK10 pending group omissions: {sorted(required - pending)}")
for rel in pending:
    check((ROOT / rel).is_file(), f"HK10 pending file absent: {rel}")
check(not any("full_pool" in rel or "dual_array" in rel or "trajectory" in rel for rel in pending),
      "HK10 pending path improperly includes expanded private disclosure")

print(json.dumps({"status": "PASS" if not errors else "FAIL", "checks": checks,
                  "errors": errors, "publication_status": "READY_FOR_FINAL_REVIEW; HK10 disclosure PENDING",
                  "scientific_solver_rerun": False}, indent=2, ensure_ascii=False))
raise SystemExit(bool(errors))
