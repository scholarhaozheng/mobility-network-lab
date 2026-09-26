#!/usr/bin/env python3
"""Compose the eight accepted Algorithm B SVGs without recomputing results.

Pillow rasterization is display-only; no scientific solver is called.
"""
from __future__ import annotations

import base64
import csv
import hashlib
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "algorithms" / "origin_based_algorithm_b" / "figures"
DEST = ROOT / "docs" / "assets" / "algorithm_b_r21"
PANELS = (
    ("sioux_convergence.svg", "652f43dcadad359cc7d3eaf0c14b862676e15560ea5df66f4574ec98acc566d2"),
    ("boston_b1_convergence.svg", "9e433e4622120ca4e3523b44e1a90030afb7f541d7f6e629b273178f0e53c953"),
    ("sioux_fw_flow.svg", "c2c2ded314299dfd552faed76f377870c70f2163d94f46cca500fd3a89c2aec1"),
    ("boston_b1_fw_flow.svg", "87ead4c0f3439823a6829e4a0708795212f5a171775ad0f8d846ddaa0581beb7"),
    ("sioux_origin_flow.svg", "da73a25ef6a2c253f8f7ddb9f355a987b45dadb845bfe1d86cda5fbaec0de006"),
    ("boston_b1_origin_flow.svg", "22e3e773a522f18ec45561c87936d4ddb8f91745bf8d0efc12833a6b3e10ac46"),
    ("sioux_verification.svg", "fd2e52ee8cbc4afe5655920f16f6c9bfbf4f50a78e2ad713fc3464881e4e753c"),
    ("boston_b1_verification.svg", "ff933f8ea0fae9bf73ee9e0545abd3fe9ae4b5a83f93802dafda805abfcfeb9c"),
)
PANEL_W, SOURCE_H, PANEL_H, GAP = 1000, 620, 460, 16
CROPS = ((105, 520), (100, 550), (115, 520), (105, 530))
WIDTH, HEIGHT = 2 * PANEL_W + 3 * GAP, 4 * PANEL_H + 5 * GAP


def compose() -> Path:
    DEST.mkdir(parents=True, exist_ok=True)
    images = []
    manifest = []
    for i, (name, expected) in enumerate(PANELS):
        raw = (SOURCE / name).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != expected:
            raise ValueError(f"frozen source hash differs: {name}")
        if b'<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="620"' not in raw[:200]:
            raise ValueError(f"unexpected source canvas: {name}")
        x = GAP + (i % 2) * (PANEL_W + GAP)
        y = GAP + (i // 2) * (PANEL_H + GAP)
        top, bottom = CROPS[i // 2]
        crop_h = bottom - top
        y += (PANEL_H - crop_h) // 2
        payload = base64.b64encode(raw).decode("ascii")
        images.append(
            f'<svg x="{x}" y="{y}" width="{PANEL_W}" height="{crop_h}" '
            f'viewBox="0 {top} {PANEL_W} {crop_h}">'
            f'<image x="0" y="0" width="{PANEL_W}" height="{SOURCE_H}" '
            f'href="data:image/svg+xml;base64,{payload}"/></svg>'
        )
        manifest.append((i // 2 + 1, "Sioux Falls" if i % 2 == 0 else "Boston B1", name, len(raw), digest))
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
           f'width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">'
           '<rect width="100%" height="100%" fill="white"/>'
           + "".join(images) + '</svg>\n')
    out = DEST / "algorithm_b_cross_city_overview.svg"
    out.write_text(svg, encoding="utf-8")
    with (DEST / "SOURCE_SVG_SHA256.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(("row", "case", "source_svg", "bytes", "sha256"))
        writer.writerows(manifest)
    return out


def render_source_svg(path: Path) -> Image.Image:
    """Rasterize only the simple SVG element set present in the frozen panels."""
    root = ET.parse(path).getroot()
    image = Image.new("RGBA", (PANEL_W, SOURCE_H), "white")
    draw = ImageDraw.Draw(image, "RGBA")
    font_root = Path("C:/Windows/Fonts")
    fonts = {
        "title": ImageFont.truetype(str(font_root / "arialbd.ttf"), 26),
        "sub": ImageFont.truetype(str(font_root / "arial.ttf"), 14),
        "label": ImageFont.truetype(str(font_root / "arial.ttf"), 12),
        "tick": ImageFont.truetype(str(font_root / "arial.ttf"), 11),
    }
    text_colors = {"title": "#243042", "sub": "#596779",
                   "label": "#596779", "tick": "#66758a"}
    for item in root:
        tag = item.tag.rsplit("}", 1)[-1]
        a = item.attrib
        if tag == "style":
            continue
        if tag == "rect":
            x, y = float(a.get("x", 0)), float(a.get("y", 0))
            width = PANEL_W if a["width"] == "100%" else float(a["width"])
            height = SOURCE_H if a["height"] == "100%" else float(a["height"])
            box = (x, y, x + width, y + height)
            fill, outline = a.get("fill"), a.get("stroke")
            if "rx" in a:
                draw.rounded_rectangle(box, radius=float(a["rx"]), fill=fill, outline=outline)
            else:
                draw.rectangle(box, fill=fill, outline=outline)
        elif tag == "line":
            draw.line((float(a["x1"]), float(a["y1"]), float(a["x2"]), float(a["y2"])),
                      fill=a["stroke"], width=max(1, round(float(a.get("stroke-width", 1)))))
        elif tag == "polyline":
            points = [tuple(map(float, pair.split(","))) for pair in a["points"].split()]
            draw.line(points, fill=a["stroke"], width=max(1, round(float(a.get("stroke-width", 1)))))
        elif tag == "circle":
            cx, cy, r = float(a["cx"]), float(a["cy"]), float(a["r"])
            opacity = float(a.get("fill-opacity", 1))
            fill = (*bytes.fromhex(a["fill"].lstrip("#")), round(255 * opacity))
            draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=fill)
        elif tag == "text":
            style = a.get("class", "label")
            anchor = {"start": "ls", "middle": "ms", "end": "rs"}[a.get("text-anchor", "start")]
            draw.text((float(a["x"]), float(a["y"])), item.text or "",
                      font=fonts[style], fill=text_colors[style], anchor=anchor)
        else:
            raise ValueError(f"unhandled source SVG element {tag} in {path.name}")
    return image.convert("RGB")


def rasterize(svg: Path) -> Path:
    canvas = Image.new("RGB", (WIDTH, HEIGHT), "white")
    for i, (name, _) in enumerate(PANELS):
        x = GAP + (i % 2) * (PANEL_W + GAP)
        y = GAP + (i // 2) * (PANEL_H + GAP)
        top, bottom = CROPS[i // 2]
        y += (PANEL_H - (bottom - top)) // 2
        canvas.paste(render_source_svg(SOURCE / name).crop((0, top, PANEL_W, bottom)), (x, y))
    out = svg.with_suffix(".png")
    canvas.save(out, optimize=True)
    return out


def main() -> None:
    svg = compose()
    print(svg)
    print(rasterize(svg))


if __name__ == "__main__":
    main()
