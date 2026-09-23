"""Render Boston public visuals from frozen, explicitly supplied saved inputs.

Requires Python 3.10+ and Pillow. No model, matcher, network, or data download runs.
The coordinates are transformed from EPSG:4326 to WGS84 / UTM zone 19N
(EPSG:32619) for display and metric scale bars. SVG paths contain display
pixels only; no source coordinates, identifiers, or local paths are embedded.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

NAVY = "#102c3e"
INK = "#18394a"
TEAL = "#087e83"
MINT = "#b1ebe0"
PAPER = "#f5f8fa"
MUTED = "#58717d"
LINE = "#d8e4e8"
WHITE = "#ffffff"
GMNS_CREDIT = "Roads: GMNS Plus 21_Boston; zones: MCL H3"
MASSGIS_CREDIT = "Parcels: MassGIS (Bureau of Geographic Information), Commonwealth of Massachusetts EOTSS"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def features(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))["features"]


def wkt_coords(wkt: str) -> list[tuple[float, float]]:
    # All physical links are LINESTRING, and selected parcel exteriors are POLYGON.
    # For rare MULTIPOLYGON parcels this returns the first exterior only.
    if not wkt:
        return []
    if wkt.startswith("LINESTRING"):
        body = wkt[wkt.index("(") + 1 : wkt.rindex(")")]
    elif wkt.startswith("POLYGON") or wkt.startswith("MULTIPOLYGON"):
        start = wkt.index("((") + 2
        end = wkt.index(")", start)
        body = wkt[start:end]
    else:
        return []
    out = []
    for part in body.split(","):
        xy = part.strip().strip("() ").split()
        if len(xy) >= 2:
            out.append((float(xy[0]), float(xy[1])))
    return out


def utm19(lon: float, lat: float) -> tuple[float, float]:
    """WGS84 transverse Mercator, EPSG:32619, metre coordinates."""
    a = 6378137.0
    ecc2 = 0.0066943799901413165
    ep2 = ecc2 / (1 - ecc2)
    p = math.radians(lat)
    lam = math.radians(lon)
    lam0 = math.radians(-69.0)
    n = a / math.sqrt(1 - ecc2 * math.sin(p) ** 2)
    t = math.tan(p) ** 2
    c = ep2 * math.cos(p) ** 2
    aa = math.cos(p) * (lam - lam0)
    m = a * (
        (1 - ecc2 / 4 - 3 * ecc2**2 / 64 - 5 * ecc2**3 / 256) * p
        - (3 * ecc2 / 8 + 3 * ecc2**2 / 32 + 45 * ecc2**3 / 1024) * math.sin(2 * p)
        + (15 * ecc2**2 / 256 + 45 * ecc2**3 / 1024) * math.sin(4 * p)
        - (35 * ecc2**3 / 3072) * math.sin(6 * p)
    )
    k = 0.9996
    e = 500000 + k * n * (
        aa + (1 - t + c) * aa**3 / 6 + (5 - 18 * t + t**2 + 72 * c - 58 * ep2) * aa**5 / 120
    )
    north = k * (
        m + n * math.tan(p) * (
            aa**2 / 2 + (5 - t + 9 * c + 4 * c**2) * aa**4 / 24
            + (61 - 58 * t + t**2 + 600 * c - 330 * ep2) * aa**6 / 720
        )
    )
    return e, north


def project_line(coords: list[tuple[float, float]]) -> list[tuple[float, float]]:
    return [utm19(lon, lat) for lon, lat in coords]


@dataclass
class View:
    xmin: float
    ymin: float
    xmax: float
    ymax: float
    left: float
    top: float
    width: float
    height: float

    @classmethod
    def from_bounds(cls, bounds, box, margin=0.0):
        xmin, ymin, xmax, ymax = bounds
        dx, dy = xmax - xmin, ymax - ymin
        xmin -= dx * margin
        xmax += dx * margin
        ymin -= dy * margin
        ymax += dy * margin
        left, top, width, height = box
        # Fixed isotropic scale in UTM metres, with the geographic centre kept.
        scale = min(width / (xmax - xmin), height / (ymax - ymin))
        cx, cy = (xmin + xmax) / 2, (ymin + ymax) / 2
        full_w, full_h = width / scale, height / scale
        return cls(cx - full_w / 2, cy - full_h / 2, cx + full_w / 2, cy + full_h / 2,
                   left, top, width, height)

    def xy(self, p):
        return (self.left + (p[0] - self.xmin) * self.width / (self.xmax - self.xmin),
                self.top + (self.ymax - p[1]) * self.height / (self.ymax - self.ymin))

    @property
    def pixels_per_metre(self):
        return self.width / (self.xmax - self.xmin)


def bounds_for(poly):
    allp = [p for ring in poly for p in ring]
    return min(p[0] for p in allp), min(p[1] for p in allp), max(p[0] for p in allp), max(p[1] for p in allp)


class Canvas:
    def __init__(self, width: int, height: int, background=WHITE):
        self.width, self.height = width, height
        self.im = Image.new("RGB", (width, height), background)
        self.draw = ImageDraw.Draw(self.im)
        self.svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
                    f'<rect width="{width}" height="{height}" fill="{background}"/>']
        self.font_dir = Path("C:/Windows/Fonts")
        self._clip_parent = None

    def font(self, size, bold=False):
        name = "segoeuib.ttf" if bold else "segoeui.ttf"
        path = self.font_dir / name
        try:
            return ImageFont.truetype(str(path), int(size))
        except OSError:
            return ImageFont.load_default()

    def rect(self, box, fill, outline=None, width=1):
        x0, y0, x1, y1 = box
        self.draw.rectangle(tuple(round(v) for v in box), fill=fill, outline=outline, width=round(width))
        extra = f' stroke="{outline}" stroke-width="{width}"' if outline else ""
        self.svg.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{x1-x0:.1f}" height="{y1-y0:.1f}" fill="{fill}"{extra}/>')

    def line(self, a, b, color, width=1):
        self.polyline([a, b], color, width)

    def polyline(self, points, color, width=1, opacity=1.0, dash=None):
        if len(points) < 2:
            return
        coords = [(round(x), round(y)) for x, y in points]
        if dash:
            for a, b in zip(coords, coords[1:]):
                length = math.dist(a, b)
                if length < 0.1:
                    continue
                n = max(1, math.ceil(length / (dash[0] + dash[1])))
                for j in range(n):
                    start = (j * (dash[0] + dash[1])) / length
                    end = min(1, (j * (dash[0] + dash[1]) + dash[0]) / length)
                    if start >= 1:
                        break
                    p0 = (round(a[0] + (b[0]-a[0])*start), round(a[1]+(b[1]-a[1])*start))
                    p1 = (round(a[0] + (b[0]-a[0])*end), round(a[1]+(b[1]-a[1])*end))
                    self.draw.line([p0, p1], fill=color, width=max(1, round(width)))
        else:
            self.draw.line(coords, fill=color, width=max(1, round(width)), joint="curve")
        val = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
        dd = f' stroke-dasharray="{dash[0]},{dash[1]}"' if dash else ""
        self.svg.append(f'<polyline points="{val}" fill="none" stroke="{color}" stroke-width="{width:.1f}" stroke-linecap="round" stroke-linejoin="round" opacity="{opacity:.2f}"{dd}/>')

    def polygon(self, points, fill, outline=None, width=1):
        if len(points) < 3:
            return
        coords = [(round(x), round(y)) for x, y in points]
        self.draw.polygon(coords, fill=fill)
        if outline:
            self.draw.line(coords + [coords[0]], fill=outline, width=max(1, round(width)), joint="curve")
        val = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
        edge = f' stroke="{outline}" stroke-width="{width:.1f}"' if outline else ""
        self.svg.append(f'<polygon points="{val}" fill="{fill}"{edge}/>')

    def circle(self, centre, radius, fill, outline=None, width=1):
        x, y = centre
        box = (round(x-radius), round(y-radius), round(x+radius), round(y+radius))
        self.draw.ellipse(box, fill=fill, outline=outline, width=max(1, round(width)))
        edge = f' stroke="{outline}" stroke-width="{width:.1f}"' if outline else ""
        self.svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius:.1f}" fill="{fill}"{edge}/>')

    def text(self, pos, value, size, color=INK, bold=False):
        x, y = pos
        self.draw.text((round(x), round(y)), value, fill=color, font=self.font(size, bold), anchor="lt")
        weight = "700" if bold else "400"
        self.svg.append(f'<text x="{x:.1f}" y="{y + size*0.91:.1f}" font-size="{size}" font-weight="{weight}" font-family="Segoe UI,Arial,sans-serif" fill="{color}">{html.escape(value)}</text>')

    def save(self, png: Path, svg: Path | None = None, *, max_colors=None):
        if self._clip_parent is not None:
            raise RuntimeError("Unclosed map clipping group")
        png.parent.mkdir(parents=True, exist_ok=True)
        if max_colors:
            self.im.quantize(colors=max_colors, method=Image.Quantize.FASTOCTREE).save(png, optimize=True)
        else:
            self.im.save(png, optimize=True)
        if svg:
            svg.parent.mkdir(parents=True, exist_ok=True)
            svg.write_text("\n".join(self.svg + ["</svg>"]) + "\n", encoding="utf-8")

    def begin_clip(self, box):
        if self._clip_parent is not None:
            raise RuntimeError("Nested clipping is unsupported")
        self._clip_parent = self.im
        self._clip_box = tuple(round(v) for v in box)
        self.im = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        self.draw = ImageDraw.Draw(self.im)
        x0, y0, x1, y1 = box
        self.svg.append(f'<defs><clipPath id="mapClip"><rect x="{x0:.1f}" y="{y0:.1f}" width="{x1-x0:.1f}" height="{y1-y0:.1f}"/></clipPath></defs><g clip-path="url(#mapClip)">')

    def end_clip(self):
        if self._clip_parent is None:
            raise RuntimeError("No map clipping group")
        crop = self.im.crop(self._clip_box)
        self._clip_parent.paste(crop, self._clip_box[:2], crop)
        self.im = self._clip_parent
        self.draw = ImageDraw.Draw(self.im)
        self._clip_parent = None
        self.svg.append("</g>")


def display_line(view, coords):
    return [view.xy(p) for p in coords]


def bbox_visible(view, line):
    if not line:
        return False
    xs, ys = zip(*line)
    return not (max(xs) < view.xmin or min(xs) > view.xmax or max(ys) < view.ymin or min(ys) > view.ymax)


def offset_right(points, amount):
    if len(points) < 2:
        return points
    out = []
    for i, p in enumerate(points):
        a = points[max(0, i-1)]
        b = points[min(len(points)-1, i+1)]
        dx, dy = b[0]-a[0], b[1]-a[1]
        length = math.hypot(dx, dy)
        out.append((p[0] - dy / length * amount, p[1] + dx / length * amount) if length else p)
    return out


def arrow(c, points, color, size=9):
    if len(points) < 2:
        return
    mid = len(points) // 2
    p0, p1 = points[max(0, mid-1)], points[min(len(points)-1, mid)]
    dx, dy = p1[0]-p0[0], p1[1]-p0[1]
    length = math.hypot(dx, dy)
    if length < 5:
        return
    ux, uy = dx/length, dy/length
    tip = ((p0[0]+p1[0])/2, (p0[1]+p1[1])/2)
    base = (tip[0]-ux*size, tip[1]-uy*size)
    c.polygon([tip, (base[0]-uy*size*.45, base[1]+ux*size*.45),
               (base[0]+uy*size*.45, base[1]-ux*size*.45)], color)


def draw_geo_line(c, view, coords, color, width=1, **kwargs):
    if bbox_visible(view, coords):
        c.polyline(display_line(view, coords), color, width, **kwargs)


def draw_geo_poly(c, view, coords, fill, outline=None, width=1):
    if bbox_visible(view, coords):
        c.polygon(display_line(view, coords), fill, outline, width)


def scale_bar(c, view, x, y, metres=1000, color=INK):
    length = metres * view.pixels_per_metre
    if length > 270:
        metres = 500
        length = metres * view.pixels_per_metre
    c.line((x, y), (x+length, y), color, 5)
    c.line((x, y-7), (x, y+7), color, 3)
    c.line((x+length, y-7), (x+length, y+7), color, 3)
    c.text((x, y+10), f"{metres/1000:g} km", 22, color, True)


def map_frame(c, view, title, subtitle, source, footer):
    c.rect((0, 0, c.width, 128), WHITE)
    c.text((72, 26), title, 46, NAVY, True)
    c.text((74, 83), subtitle, 24, MUTED)
    c.rect((view.left, view.top, view.left+view.width, view.top+view.height), PAPER, LINE, 2)
    c.rect((0, 1012, c.width, c.height), WHITE)
    c.line((72, 1008), (c.width-72, 1008), LINE, 2)
    c.text((72, 1020), source, 19, MUTED)
    c.text((72, 1051), footer, 19, MUTED)


def sidebar(c, heading):
    c.rect((1352, 148, 1740, 978), WHITE, LINE, 2)
    c.text((1380, 180), heading, 32, NAVY, True)


def legend_line(c, y, color, title, sub="", width=6, dashed=False):
    c.polyline([(1384, y+12), (1450, y+12)], color, width, dash=(12,8) if dashed else None)
    c.text((1470, y), title, 25, INK, True)
    if sub:
        c.text((1470, y+29), sub, 20, MUTED)


def label_lines(c, x, y, strings, size=22, spacing=30, color=MUTED):
    for line in strings:
        c.text((x, y), line, size, color)
        y += spacing
    return y


def color_mix(a, b, t):
    aa = tuple(int(a[i:i+2],16) for i in (1,3,5))
    bb = tuple(int(b[i:i+2],16) for i in (1,3,5))
    return "#"+"".join(f"{round(aa[i]*(1-t)+bb[i]*t):02x}" for i in range(3))


class Data:
    def __init__(self, root: Path):
        self.root = root
        self.links = []
        for r in rows(root / "gmns_links.csv"):
            if r["is_physical"] != "True":
                continue
            self.links.append({"id": r["link_id"], "version": r["network_version"],
                               "geometry": project_line(wkt_coords(r["geometry"])),
                               "status": r["boundary_status"]})
        self.link_by_id = {r["id"]: r for r in self.links}
        self.zones = []
        for f in features(root / "zones.geojson"):
            geom = f["geometry"]
            if geom["type"] != "Polygon":
                continue
            self.zones.append({"id": f["properties"]["zone_id"],
                               "level": f["properties"]["zone_level"],
                               "geometry": project_line(geom["coordinates"][0])})
        self.core = [project_line(f["geometry"]["coordinates"][0]) for f in features(root / "core.geojson")]
        self.analysis = [project_line(f["geometry"]["coordinates"][0]) for f in features(root / "analysis.geojson")]
        self.parcels = []
        for r in rows(root / "parcel_geometries.csv"):
            geom = wkt_coords(r["geometry_wkt_epsg4326"])
            if len(geom) >= 3:
                self.parcels.append(project_line(geom))
        self.network_version = self.links[0]["version"]
        if {r["version"] for r in self.links} != {self.network_version}:
            raise ValueError("Mixed physical network versions")
        self.core_bounds = bounds_for(self.core)
        self.analysis_bounds = bounds_for(self.analysis)
        self.r9 = [z for z in self.zones if z["level"] == "fine"]
        self.r7 = [z for z in self.zones if z["level"] == "parent"]
        self.activity = {r["zone_id"]: r for r in rows(root / "zone_activity_r9.csv")}
        if set(self.activity) != {z["id"] for z in self.r9}:
            raise ValueError("Activity zones differ from r9 map zones")
        if {r["network_version"] for r in self.activity.values()} != {self.network_version}:
            raise ValueError("Activity network version mismatch")
        self.corridor = rows(root / "corridor_link.csv")
        self.s1 = {r["link_id"]: r for r in rows(root / "s1_solution.csv")}
        self.s2 = {r["link_id"]: r for r in rows(root / "s2_solution.csv")}
        if set(self.s1) != set(self.s2) or set(self.s1) != set(self.link_by_id):
            raise ValueError("S1/S2 physical link IDs or network geometry differ")
        if {r["network_version"] for r in self.s1.values()} != {self.network_version}:
            raise ValueError("S1 network version mismatch")
        if {r["network_version"] for r in self.s2.values()} != {self.network_version}:
            raise ValueError("S2 network version mismatch")
        for name, scenario in [("s1", self.s1), ("s2", self.s2)]:
            summary = json.loads((root / f"{name}_run_summary.json").read_text(encoding="utf-8"))
            if summary["status"] != "executed" or not summary["solver_converged"]:
                raise ValueError(f"Saved {name} run is not accepted")
        self.gps_quality = rows(root / "gps_segment_quality.csv")
        self.gps_points = rows(root / "gps_point_progress.csv")
        self.gps_path = rows(root / "gps_path_links.csv")
        if {r["network_version"] for r in self.gps_points} != {self.network_version}:
            raise ValueError("GPS point network version mismatch")
        if {r["network_version"] for r in self.gps_path} != {self.network_version}:
            raise ValueError("GPS path network version mismatch")
        counts = Counter(p["segment_id"] for p in self.gps_points)
        eligible = sorted(r["segment_id"] for r in self.gps_quality
                          if r["observation_eligible"] == "True" and counts[r["segment_id"]] >= 6)
        if not eligible:
            raise ValueError("No eligible GPS segment with >=6 saved points")
        self.gps_segment = eligible[0]
        self.selected_quality = next(r for r in self.gps_quality if r["segment_id"] == self.gps_segment)
        self.selected_points = sorted((r for r in self.gps_points if r["segment_id"] == self.gps_segment),
                                      key=lambda r: int(r["point_seq"]))
        self.selected_path = sorted((r for r in self.gps_path if r["segment_id"] == self.gps_segment),
                                    key=lambda r: int(r["path_order"]))
        self.metrics = self.compute_metrics()

    def compute_metrics(self):
        delta = {lid: float(self.s2[lid]["volume"]) - float(self.s1[lid]["volume"])
                 for lid in self.s1}
        nonzero = {lid: d for lid, d in delta.items() if abs(d) > 1e-10}
        area = [float(r["official_res_area_sqft_weighted"]) for r in self.activity.values()
                if r["official_res_area_sqft_weighted"]]
        return {
            "network_version": self.network_version,
            "physical_link_count": len(self.links),
            "r9_zone_count": len(self.r9),
            "r7_zone_count": len(self.r7),
            "parcel_count": len(self.parcels),
            "activity_nonmissing": len(area),
            "activity_missing": len(self.r9)-len(area),
            "activity_zero": sum(v == 0 for v in area),
            "activity_min_sqft": min(area),
            "activity_max_sqft": max(area),
            "s1_nonzero_links": sum(float(r["volume"]) > 0 for r in self.s1.values()),
            "s1_max_volume": max(float(r["volume"]) for r in self.s1.values()),
            "delta_min": min(delta.values()),
            "delta_max": max(delta.values()),
            "delta_nonzero_count": len(nonzero),
            "delta_negative_count": sum(d < 0 for d in nonzero.values()),
            "delta_positive_count": sum(d > 0 for d in nonzero.values()),
            "gps_selection_rule": "lexicographically first quality-eligible segment with at least six saved public derived points",
            "gps_selected_segment_internal": self.gps_segment,
            "gps_selected_point_count": len(self.selected_points),
            "gps_selected_path_links": len(self.selected_path),
            "gps_lateral_error_min_m": min(float(r["lateral_error_m"]) for r in self.selected_points),
            "gps_lateral_error_max_m": max(float(r["lateral_error_m"]) for r in self.selected_points),
        }


def draw_parcels(c, data, view, *, color="#e1e9eb", max_count=None):
    count = 0
    for poly in data.parcels:
        if not bbox_visible(view, poly):
            continue
        pts = display_line(view, poly)
        c.polyline(pts, color, 1)
        count += 1
        if max_count and count >= max_count:
            break


def draw_roads(c, data, view, color="#b7cbd0", width=2):
    for road in data.links:
        draw_geo_line(c, view, road["geometry"], color, width)


def draw_zones(c, zones, view, color, width=2):
    for zone in zones:
        if bbox_visible(view, zone["geometry"]):
            pts = display_line(view, zone["geometry"])
            c.polyline(pts, color, width)


def draw_core(c, data, view, color=TEAL, width=4):
    for ring in data.core:
        draw_geo_line(c, view, ring, color, width)


def hero(data, out: Path, social=False):
    w, h = (1280, 640) if social else (1800, 600)
    c = Canvas(w, h, NAVY)
    left = 650 if social else 735
    view = View.from_bounds(data.core_bounds, (left, 12, w-left+80, h-24), .30)
    draw_zones(c, data.r9, view, "#2e5867", 1)
    draw_zones(c, data.r7, view, "#477680", 2)
    for road in data.links:
        draw_geo_line(c, view, road["geometry"], "#59818c", 2)
    # One verified ordered corridor; its geometry is sourced from 23 member links.
    for member in data.corridor:
        line = data.link_by_id[member["link_id"]]["geometry"]
        draw_geo_line(c, view, line, "#8bcac3", 4)
    draw_core(c, data, view, "#77a5a9", 2)
    for x in range(left-110, left+60, 5):
        t = max(0, min(1, (x-(left-110))/170))
        shade = color_mix(NAVY, "#254858", t*.52)
        c.rect((x, 0, x+5, h), shade)
    c.rect((0, 0, left-110, h), NAVY)
    if social:
        c.text((68, 70), "MOBILITY COMPUTATION LAB", 23, MINT, True)
        c.text((68, 158), "City networks.", 59, WHITE, True)
        c.text((68, 235), "Travel demand.", 59, WHITE, True)
        c.text((68, 312), "Inspectable computation.", 43, WHITE, True)
        c.text((70, 434), "GMNS  /  Spatial zones  /  Mobility observations", 20, "#b8d4d9")
        c.text((70, 480), "Central Boston example", 21, MINT, True)
        c.text((70, 592), GMNS_CREDIT, 16, "#9ebcc5")
    else:
        c.text((90, 78), "MOBILITY COMPUTATION LAB", 28, MINT, True)
        c.text((90, 160), "City networks.", 70, WHITE, True)
        c.text((90, 248), "Travel demand.", 70, WHITE, True)
        c.text((90, 336), "Inspectable computation.", 56, WHITE, True)
        c.text((90, 460), "GMNS  /  Spatial zones  /  Mobility observations  /  Assignment", 24, "#b8d4d9")
        c.text((90, 510), "Central Boston example", 24, MINT, True)
        c.text((1120, 568), GMNS_CREDIT, 16, "#c4dfe1")
    name = "mcl_social_preview.png" if social else "mcl_boston_hero.png"
    c.save(out / name, None if social else out / "mcl_boston_hero.svg", max_colors=192 if social else None)


def network_map(data, out):
    c = Canvas(1800, 1100)
    view = View.from_bounds(data.analysis_bounds, (70, 150, 1240, 830), .035)
    map_frame(c, view, "Central Boston: GMNS Network and Spatial Zones",
              "Physical directed roads  /  H3 r9 zones and r7 parents  /  one ordered model corridor",
              GMNS_CREDIT + "; " + MASSGIS_CREDIT,
              "EPSG:32619 display  |  Source network: " + data.network_version)
    c.begin_clip((view.left, view.top, view.left+view.width, view.top+view.height))
    draw_parcels(c, data, view)
    draw_roads(c, data, view, "#b7cbd0", 2)
    draw_zones(c, data.r9, view, "#d5e1df", 2)
    draw_zones(c, data.r7, view, "#6ba2a3", 3)
    for ring in data.analysis:
        draw_geo_line(c, view, ring, "#7d949e", 4, dash=(15, 11))
    draw_core(c, data, view, TEAL, 5)
    for member in data.corridor:
        geom = data.link_by_id[member["link_id"]]["geometry"]
        draw_geo_line(c, view, geom, "#e7a65a", 6)
    c.end_clip()
    scale_bar(c, view, 105, 905, 2000)
    sidebar(c, "Map layers")
    legend_line(c, 260, "#b7cbd0", "Physical roads", "5,091 directed links", 5)
    legend_line(c, 340, "#d5e1df", "H3 r9", "177 clipped fine zones", 4)
    legend_line(c, 420, "#6ba2a3", "H3 r7", "9 parent zones", 5)
    legend_line(c, 500, TEAL, "Core boundary", "Fixed analysis core", 5)
    legend_line(c, 580, "#7d949e", "Analysis extent", "2.5 km buffer", 4, True)
    legend_line(c, 660, "#e7a65a", "One corridor", "23 ordered member links", 6)
    label_lines(c, 1380, 766, ["Access connectors omitted:", "they are model relations,", "not mapped streets.", "Parcel outlines are context,", "not building footprints."], 21, 31)
    c.save(out / "boston_network_zones.png", out / "boston_network_zones.svg")


def quantile(sorted_values, q):
    ix = (len(sorted_values)-1)*q
    lo = math.floor(ix)
    hi = math.ceil(ix)
    return sorted_values[lo]*(hi-ix)+sorted_values[hi]*(ix-lo) if lo != hi else sorted_values[lo]


def activity_map(data, out):
    c = Canvas(1800, 1100)
    view = View.from_bounds(data.core_bounds, (70, 150, 1240, 830), .08)
    map_frame(c, view, "Residential Assessment Area by Zone",
              "MassGIS assessment RES_AREA  /  area-allocated to clipped H3 r9 zones  /  square feet",
              GMNS_CREDIT + "; " + MASSGIS_CREDIT,
              "Boston FY2023 and Cambridge FY2026 parcels  |  Activity run: boston_activity_prior_r1_20260922")
    c.begin_clip((view.left, view.top, view.left+view.width, view.top+view.height))
    values = sorted(float(r["official_res_area_sqft_weighted"]) for r in data.activity.values()
                    if r["official_res_area_sqft_weighted"])
    cuts = [quantile(values, q) for q in (.2, .4, .6, .8)]
    colors = ["#e6f2f0", "#b9dfd7", "#79bdb6", "#338f92", "#155767"]
    for z in data.r9:
        record = data.activity[z["id"]]
        raw = record["official_res_area_sqft_weighted"]
        if raw == "":
            fill = "#e1e5e7"  # missing, including no assessment feature intersections
        else:
            val = float(raw)
            fill = "#ffffff" if val == 0 else colors[sum(val > cut for cut in cuts)]
        draw_geo_poly(c, view, z["geometry"], fill, "#c9d8da", 2)
    draw_roads(c, data, view, "#d4dedf", 1)
    draw_zones(c, data.r7, view, "#598e96", 4)
    draw_core(c, data, view, TEAL, 4)
    c.end_clip()
    scale_bar(c, view, 105, 905, 1000)
    sidebar(c, "RES_AREA / zone")
    labels = [f"≤ {cuts[0]/1e6:.2f}M", f"{cuts[0]/1e6:.2f}–{cuts[1]/1e6:.2f}M",
              f"{cuts[1]/1e6:.2f}–{cuts[2]/1e6:.2f}M", f"{cuts[2]/1e6:.2f}–{cuts[3]/1e6:.2f}M",
              f"> {cuts[3]/1e6:.2f}M"]
    for i, (color, label) in enumerate(zip(colors, labels)):
        y = 275+i*75
        c.rect((1382, y, 1428, y+42), color, "#a9c7cb", 1)
        c.text((1450, y+5), label+" sq ft", 24, INK, True)
    c.rect((1382, 664, 1428, 706), "#e1e5e7", "#a9c7cb", 1)
    c.text((1450, 669), f"Missing ({data.metrics['activity_missing']})", 23, INK, True)
    c.rect((1382, 728, 1428, 770), WHITE, "#a9c7cb", 1)
    c.text((1450, 733), f"Zero ({data.metrics['activity_zero']})", 23, INK, True)
    label_lines(c, 1382, 817, ["145 zones have RES_AREA.", "Missing is not treated as 0.", "Parcel areas are spatial priors,", "not trip counts."], 20, 31)
    c.save(out / "boston_activity_prior.png", out / "boston_activity_prior.svg")


def gps_map(data, out):
    c = Canvas(1800, 1100)
    original = [utm19(float(r["original_lon"]), float(r["original_lat"])) for r in data.selected_points]
    projected = [utm19(float(r["projected_lon"]), float(r["projected_lat"])) for r in data.selected_points]
    allp = original+projected
    b = (min(x for x,y in allp), min(y for x,y in allp), max(x for x,y in allp), max(y for x,y in allp))
    view = View.from_bounds(b, (70, 150, 1240, 830), .25)
    map_frame(c, view, "Transit Positions and Matched Road Geometry",
              "One prequalified public transit vehicle segment  /  saved projections, no rematching",
              GMNS_CREDIT + "; " + MASSGIS_CREDIT,
              "EPSG:32619  |  Position data: MassDOT / MBTA V3  |  MCL quality run boston_quality_r1_20260922")
    c.begin_clip((view.left, view.top, view.left+view.width, view.top+view.height))
    draw_parcels(c, data, view, color="#e4eaeb")
    draw_roads(c, data, view, "#c8d5d8", 2)
    ordered_geom = []
    for r in data.selected_path:
        geom = data.link_by_id[r["link_id"]]["geometry"]
        if bbox_visible(view, geom):
            points = display_line(view, geom)
            c.polyline(points, TEAL, 7)
            ordered_geom.append(points)
    for pts in ordered_geom[::max(1,len(ordered_geom)//6)]:
        arrow(c, pts, TEAL, 13)
    for a, bpt in zip(original, projected):
        c.line(view.xy(a), view.xy(bpt), "#d79c5f", 3)
    for i, (a, bpt) in enumerate(zip(original, projected)):
        c.circle(view.xy(bpt), 8, WHITE, TEAL, 3)
        c.circle(view.xy(a), 7, "#e7a65a", NAVY, 1)
        if i in (0, len(original)-1):
            x,y=view.xy(a)
            c.text((x+13, y-23), "START" if i==0 else "END", 21, NAVY, True)
    c.end_clip()
    scale_bar(c, view, 105, 905, 500)
    sidebar(c, "Saved evidence")
    legend_line(c, 274, TEAL, "Matched road", "Ordered path links", 7)
    c.circle((1404, 372), 9, "#e7a65a", NAVY, 2)
    c.text((1440, 356), "Vehicle position", 24, INK, True)
    c.circle((1404, 450), 9, WHITE, TEAL, 3)
    c.text((1440, 434), "Projected point", 24, INK, True)
    legend_line(c, 530, "#d79c5f", "Lateral offset", "actual scale in metres", 3)
    label_lines(c, 1382, 635, [f"{len(original)} saved points",
                                 f"{data.metrics['gps_lateral_error_min_m']:.1f}–{data.metrics['gps_lateral_error_max_m']:.1f} m offset",
                                 "Quality class: qualified", "Selected by stable ID order", "among eligible segments.",
                                 "9/28 returned paths eligible", "overall; no lane accuracy."], 20, 34)
    c.save(out / "boston_gps_projection.png", out / "boston_gps_projection.svg")


def flow_base(data, title, subtitle, footer):
    c = Canvas(1800, 1100)
    view = View.from_bounds(data.core_bounds, (70, 150, 1240, 830), .08)
    map_frame(c, view, title, subtitle, GMNS_CREDIT + "; flows: saved MCL S1/S2 assignment",
              footer)
    c.begin_clip((view.left, view.top, view.left+view.width, view.top+view.height))
    draw_roads(c, data, view, "#d5e0e2", 2)
    draw_zones(c, data.r9, view, "#e3ecec", 1)
    draw_core(c, data, view, "#73a1a6", 3)
    return c, view


def flow_map(data, out, delta=False):
    if delta:
        title = "Change in Modeled Panel Flow: Exploratory Transit Adjustment"
        subtitle = "S2 − S1 on identical directed links  /  fixed HBW panel  /  modeled vehicle trips"
        footer = "No regional background traffic  |  Exploratory observation adjustment  |  Not a causal or citywide estimate"
    else:
        title = "Modeled Road Flow in the Fixed HBW Panel"
        subtitle = "S1 planned service  /  directed physical links  /  modeled vehicle trips"
        footer = "No regional background traffic  |  Fixed HBW panel  |  Scenario S1 planned service"
    c, view = flow_base(data, title, subtitle, footer)
    vmax = data.metrics["s1_max_volume"]
    dlim = max(abs(data.metrics["delta_min"]), abs(data.metrics["delta_max"]))
    plotted = []
    for lid, link in data.link_by_id.items():
        v1 = float(data.s1[lid]["volume"])
        v2 = float(data.s2[lid]["volume"])
        value = v2-v1 if delta else v1
        if (abs(value) <= 1e-10 if delta else value <= 0):
            continue
        geom = link["geometry"]
        if not bbox_visible(view, geom):
            continue
        pts = offset_right(display_line(view, geom), 2.7)
        if delta:
            frac = min(1, abs(value)/dlim)
            color = color_mix("#a8c9d3", "#206b9a", max(.22, frac)) if value < 0 else color_mix("#edbfad", "#b64f49", max(.22, frac))
            width = 3.5 + 3*math.sqrt(frac)
        else:
            frac = value/vmax
            color = color_mix("#87c7c2", "#095867", math.sqrt(frac))
            width = 3 + 6*math.sqrt(frac)
        c.polyline(pts, color, width)
        plotted.append((pts, color))
    for pts, color in plotted:
        arrow(c, pts, color, 8)
    c.end_clip()
    scale_bar(c, view, 105, 905, 1000)
    sidebar(c, "S2 − S1" if delta else "S1 road flow")
    if delta:
        for i, (value, color) in enumerate([(-dlim,"#206b9a"),(-dlim/2,"#72a7bf"),(0,"#e7ecee"),(dlim/2,"#d99586"),(dlim,"#b64f49")]):
            y = 275+i*77
            c.rect((1382,y,1433,y+43),color)
            c.text((1450,y+4),f"{value:+.6f}",25,INK,True)
        label_lines(c, 1382, 706, [f"{data.metrics['delta_nonzero_count']} changed directed links",
                                     f"{data.metrics['delta_negative_count']} decreases; {data.metrics['delta_positive_count']} increases",
                                     "Symmetric scale around zero.",
                                     "Visible line width is a key,", "not an effect-size claim."], 20, 33)
    else:
        for i, frac in enumerate((0, .25, .5, .75, 1)):
            y = 275+i*77
            color = color_mix("#87c7c2", "#095867", math.sqrt(frac))
            c.rect((1382,y,1433,y+43),color)
            c.text((1450,y+4),f"{vmax*frac:.1f}",25,INK,True)
        label_lines(c, 1382, 706, [f"{data.metrics['s1_nonzero_links']} nonzero directed links",
                                     f"Maximum: {vmax:.3f} trips",
                                     "Opposing directions offset", "2.7 px for legibility.",
                                     "Not observed road traffic."], 20, 33)
    name = "boston_panel_flow_delta" if delta else "boston_panel_flow_s1"
    c.save(out / f"{name}.png", out / f"{name}.svg")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", type=Path, help="JSON containing input_dir and output_dir")
    p.add_argument("--input-dir", type=Path, help="Frozen input directory")
    p.add_argument("--output-dir", type=Path, help="Directory for PNG/SVG assets")
    p.add_argument("--asset", choices=["all","hero","social","network","activity","gps","flow_s1","flow_delta"], default="all")
    args = p.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8")) if args.config else {}
    input_dir = args.input_dir or (Path(config["input_dir"]) if "input_dir" in config else None)
    output_dir = args.output_dir or (Path(config["output_dir"]) if "output_dir" in config else None)
    if input_dir is None or output_dir is None:
        p.error("Supply --input-dir and --output-dir, or --config with both paths")
    data = Data(input_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    actions = {"hero": lambda: hero(data, output_dir), "social": lambda: hero(data, output_dir, True),
               "network": lambda: network_map(data, output_dir), "activity": lambda: activity_map(data, output_dir),
               "gps": lambda: gps_map(data, output_dir), "flow_s1": lambda: flow_map(data, output_dir),
               "flow_delta": lambda: flow_map(data, output_dir, True)}
    for key, action in actions.items():
        if args.asset in ("all", key):
            action()
            print("rendered", key, flush=True)


if __name__ == "__main__":
    main()
