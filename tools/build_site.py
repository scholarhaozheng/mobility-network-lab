#!/usr/bin/env python3
"""Build the English static site from Markdown and the machine-readable catalog.

Run without a repository URL for local previews. Set --repository-url before
publishing GitHub Pages so source-file links resolve outside the /docs site.
"""
from __future__ import annotations
import argparse
import csv
import html
import json
import posixpath
from pathlib import Path
import re
from urllib.parse import urlsplit
from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
MD = MarkdownIt("commonmark", {"html": True}).enable("table")

CSS = """
:root{--ink:#152b39;--muted:#536b78;--navy:#102c3e;--teal:#087e83;--mint:#b1ebe0;--paper:#f5f8fa;--line:#dce5eb;--white:#fff}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#fff;color:var(--ink);font:16px/1.7 -apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif}a{color:var(--teal);text-decoration:none}a:hover{text-decoration:underline}h1,h2,h3{line-height:1.16;letter-spacing:-.035em}h1{font-size:clamp(36px,4vw,56px)}h2{font-size:30px;margin:0 0 22px}h3{font-size:20px}p{margin:0 0 18px}code,pre{font-family:ui-monospace,SFMono-Regular,Consolas,monospace}code{font-size:.86em;background:#edf3f5;padding:.13em .3em;border-radius:4px}pre{background:#102c3e;color:#e4f2f5;padding:22px;overflow-x:auto;border-radius:12px;font-size:13px;line-height:1.8}pre code{background:none;padding:0;color:inherit}table{width:100%;border-collapse:collapse;font-size:14px}th,td{padding:16px 12px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}th{font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}.wrap{max-width:1160px;margin:auto;padding:0 38px}.nav{min-height:82px;height:auto;padding:18px 0;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;gap:20px}.brand{display:flex;align-items:center;gap:12px;color:var(--ink);font-weight:750;font-size:17px;letter-spacing:-.035em}.monogram{width:34px;height:34px;display:grid;place-items:center;border-radius:9px;background:var(--navy);color:var(--mint);font-size:12px;letter-spacing:.02em}.navlinks{display:flex;gap:20px;font-size:13px;font-weight:600;flex-wrap:wrap;justify-content:flex-end;min-width:0}.navlinks a{color:var(--muted)}.hero{padding:70px 0 58px;display:grid;grid-template-columns:1.28fr 1fr;gap:55px;align-items:center}.eyebrow{font-size:11px;letter-spacing:.16em;text-transform:uppercase;font-weight:750;color:var(--teal);margin-bottom:22px}.hero h1{margin:0 0 22px;font-size:clamp(40px,4.5vw,64px);letter-spacing:-.055em}.hero h1 em{font-style:normal;color:var(--teal)}.lede{max-width:550px;color:var(--muted);font-size:17px;line-height:1.75}.actions{display:flex;gap:12px;flex-wrap:wrap;margin-top:28px}.button{display:inline-flex;align-items:center;justify-content:center;min-height:44px;padding:10px 18px;border-radius:7px;border:1px solid var(--line);font-size:13px;font-weight:650;color:var(--ink);background:white}.button.primary{background:var(--navy);color:white;border-color:var(--navy)}.button:hover{text-decoration:none;filter:brightness(.95)}.pipeline{background:var(--navy);border-radius:18px;padding:30px;color:#c6dbe5;box-shadow:0 18px 50px #102c3e12}.pipeline .eyebrow{color:var(--mint);font-size:10px;margin-bottom:24px}.step{display:flex;gap:15px;align-items:center;padding:16px 0;border-bottom:1px solid #ffffff18}.step:last-child{border:0}.step b{font-size:16px;letter-spacing:-.01em;color:#fff;display:block}.step span{font-size:12px;color:#a9c5d2}.step small{font:11px ui-monospace,monospace;color:var(--mint);background:#ffffff10;border:1px solid #ffffff20;min-width:30px;height:30px;border-radius:50%;display:grid;place-items:center}.strip{border-block:1px solid var(--line);background:var(--paper)}.stripin{display:grid;grid-template-columns:repeat(3,1fr);gap:25px;padding:24px 0}.stripin b{display:block;font-size:14px;margin-bottom:3px}.stripin span{display:block;font-size:12px;color:var(--muted)}section{padding:58px 0}.sectionhead{display:flex;justify-content:space-between;align-items:flex-end;gap:22px;margin-bottom:26px}.sectionhead h2{margin:0}.sectionhead p{max-width:520px;color:var(--muted);font-size:14px;margin:0}.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}.card{padding:26px;border:1px solid var(--line);border-radius:12px;background:white;display:flex;flex-direction:column}.card h3{margin:11px 0 14px}.card p{font-size:13px;color:var(--muted);flex:1}.card a{font-weight:650;font-size:13px}.tag{font:10px ui-monospace,monospace;text-transform:uppercase;letter-spacing:.09em;color:var(--teal)}.meta{border-top:1px solid var(--line);padding-top:15px;margin:8px 0 20px;font-size:12px;color:var(--muted)}.soft{background:var(--paper)}.split{display:grid;grid-template-columns:.85fr 1.4fr;gap:48px;align-items:start}.split>div{min-width:0}.split p{color:var(--muted);font-size:14px}.note{font-size:12px;color:var(--muted);margin:16px 0 0}.benchmark-feature{display:block;margin:0 0 26px;border:1px solid var(--line);border-radius:14px;overflow:hidden;background:#fff;color:var(--muted)}.benchmark-feature img{display:block;width:100%;height:auto}.benchmark-feature span{display:block;padding:11px 16px;font-size:12px}.benchmark-feature:hover{text-decoration:none}.tiles{display:grid;grid-template-columns:repeat(3,1fr);gap:22px}.tile{border-top:2px solid var(--teal);padding:18px 0}.tile h3{margin:4px 0 14px}.tile p{font-size:14px;color:var(--muted)}.cta{background:var(--navy);color:white;border-radius:16px;padding:32px 36px;display:flex;justify-content:space-between;gap:24px;align-items:center}.cta h2{font-size:27px;margin-bottom:10px}.cta p{font-size:14px;color:#bdd1da;margin:0}.footer{margin-top:25px;border-top:1px solid var(--line);padding:28px 0;color:var(--muted);font-size:12px;display:flex;justify-content:space-between;gap:20px}.article{max-width:850px;margin:55px auto 75px;padding:0 32px}.article h1{font-size:42px;margin:10px 0 30px}.article h2{font-size:26px;margin:35px 0 16px}.article p,.article li{line-height:1.85}.article table{display:block;overflow:auto;margin:26px 0}.article table code{font-size:12px}.article .crumb{font-size:12px;color:var(--muted)}.article img{max-width:100%}.tablewrap{overflow:auto}.site-hint{padding:10px 14px;background:#edf5f4;border-left:3px solid var(--teal);font-size:13px}@media(max-width:800px){.wrap{padding:0 22px}.nav{height:auto;min-height:72px;flex-wrap:wrap;padding:16px 0;gap:12px}.navlinks{gap:8px 16px;font-size:12px;justify-content:flex-start;width:100%}.hero{grid-template-columns:1fr;padding:38px 0;gap:30px}.hero h1{font-size:46px}.pipeline{padding:24px}.stripin,.cards,.tiles,.split{grid-template-columns:1fr}.stripin{gap:14px}.sectionhead{display:block}.sectionhead p{margin-top:16px}.cards{gap:14px}.cta,.footer{flex-direction:column;align-items:flex-start}.article{padding:0 22px;margin:36px auto}.article h1{font-size:34px}section{padding:40px 0}.split{gap:12px}}
.hero-visual{display:block;width:100%;border-radius:12px}.visual-grid{display:grid;grid-template-columns:1fr 1fr;gap:22px}.figure-tile{margin:0;border:1px solid var(--line);border-radius:12px;overflow:hidden;background:white}.figure-tile img{display:block;width:100%;height:auto}.figure-tile figcaption{padding:14px 18px;font-size:13px;color:var(--muted)}.figure-tile figcaption b{display:block;color:var(--ink);font-size:16px;margin-bottom:5px}.workflow-strip{display:flex;align-items:center;gap:10px;flex-wrap:wrap;padding:18px 0 8px}.workflow-strip a{padding:10px 13px;border:1px solid var(--line);border-radius:8px;background:white;font-size:13px;font-weight:650}.focus-note{padding:15px 18px;border-left:3px solid var(--teal);background:var(--paper);color:var(--muted);font-size:13px}.subtle-link{font-size:13px}.art-symbol{width:100%;display:block;border:1px solid #ffffff20;border-radius:9px;margin:8px 0 18px}.hero .pipeline{padding:24px}.hero .pipeline p:last-child{margin-bottom:0}.evidence-support{border-top:1px solid var(--line)}.card h3.evidence-metric{font-size:36px;margin:14px 0 8px}.evidence-support>.split{margin-top:34px}.explorer-controls{display:grid;grid-template-columns:2fr 1fr auto;gap:10px;margin:22px 0}.explorer-controls input,.explorer-controls select,.explorer-controls button{min-height:42px;border:1px solid var(--line);border-radius:7px;padding:8px 11px;background:white;color:var(--ink)}.explorer-controls button{background:var(--navy);color:white;font-weight:650}.explorer-status{font-size:13px;color:var(--muted)}.explorer-table td{font-size:12px}.state-yes{color:#06736f;font-weight:700}.state-no{color:#79543a;font-weight:700}
@media(max-width:800px){.visual-grid{grid-template-columns:1fr}.brand{font-size:16px}.navlinks a{white-space:nowrap}.hero h1{font-size:42px}.workflow-strip{gap:8px}.workflow-strip a{font-size:12px}.article img{height:auto} }

"""

CSS += """
.site-cover{margin:24px 0 0;border:1px solid var(--line);border-radius:14px;overflow:hidden;background:var(--navy)}
.site-cover img{display:block;width:100%;height:auto}
.site-cover figcaption{padding:9px 14px;color:#d6e9eb;font-size:12px}
.boston-feature{margin:0 0 24px}.boston-feature img{display:block;width:100%;height:auto}
@media(max-width:800px){.site-cover{margin-top:16px}.site-cover figcaption{font-size:11px}}
"""

CSS += '\n.story-intro{padding:40px 0 34px}.story-intro h1{margin:0 0 18px;font-size:clamp(38px,5vw,65px);letter-spacing:-.055em}.story-intro h1 em{font-style:normal;color:var(--teal)}.story-intro .lede{max-width:800px}.step-index{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin:34px 0 0}.step-index a{padding:18px;border:1px solid var(--line);border-radius:10px;display:grid;grid-template-columns:32px 1fr;gap:2px 10px;align-items:start;min-width:0;background:var(--paper)}.step-index span{grid-row:span 2;font-size:23px;font-weight:800;color:var(--teal)}.step-index b{font-size:14px;color:var(--ink);line-height:1.4}.step-index small{font-size:12px;color:var(--muted)}.four-step-cards{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}.stage-card{background:white;border:1px solid var(--line);border-radius:14px;overflow:hidden;display:flex;flex-direction:column;min-width:0}.stage-copy{padding:24px 24px 16px}.stage-copy .eyebrow{margin:0 0 12px}.stage-copy h3{margin:0 0 12px;font-size:25px}.stage-copy p{font-size:14px;color:var(--muted);margin:0 0 12px}.stage-copy .result-line{display:block;font-size:14px;color:var(--teal)}.stage-card>a{display:block;margin-top:auto}.stage-card img{width:100%;display:block;height:auto}.stage-footer{padding:16px 24px 22px;border-top:1px solid var(--line)}.stage-footer p{font-size:12px;color:var(--muted);margin-bottom:8px}.stage-footer a{font-size:13px;font-weight:650}.scope-bridge{margin-top:26px;padding:20px 24px;border-left:4px solid var(--teal);background:white}.scope-bridge p{font-size:14px;color:var(--muted);margin:8px 0 0}.feedback-chain{display:grid;grid-template-columns:1fr 22px 1fr 22px 1fr 22px 1fr;gap:10px;align-items:center;background:var(--navy);color:white;padding:26px;border-radius:14px;margin:28px 0}.feedback-chain small{color:var(--mint);display:block;font-size:11px;text-transform:uppercase;letter-spacing:.09em;margin-bottom:8px}.feedback-chain b{font-size:16px;line-height:1.5}.feedback-chain>span{font-size:24px;color:var(--mint)}.feedback-case{display:grid;grid-template-columns:1fr 1.2fr;gap:34px;align-items:start;margin:32px 0}.feedback-case>div{min-width:0}.feedback-case h3{font-size:24px}.feedback-case p{font-size:14px;color:var(--muted)}.feedback-case th,.feedback-case td{padding:12px 10px}.gps-story .focus-note{margin-top:22px}.stage-card,.gps-story,.story-intro{overflow-wrap:anywhere}.article code{overflow-wrap:anywhere}.article pre code{overflow-wrap:normal}.article h2[id],.article a[id],section[id],article[id]{scroll-margin-top:24px}\n@media(max-width:800px){.step-index{grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.step-index a{padding:14px 11px}.step-index b{font-size:13px}.step-index small{font-size:11px}.four-step-cards,.feedback-case{grid-template-columns:1fr}.stage-copy{padding:22px 20px 14px}.stage-footer{padding:14px 20px 20px}.story-intro{padding:30px 0}.feedback-chain{grid-template-columns:1fr;text-align:center;gap:10px;padding:22px}.feedback-chain>span{transform:rotate(90deg);font-size:20px}.feedback-case{gap:16px}.tablewrap table{font-size:13px}}\n'


CSS += """
.case-nav{display:flex;flex-wrap:wrap;gap:9px;margin:24px 0 7px}
.case-nav a{border:1px solid var(--line);background:var(--paper);border-radius:7px;padding:8px 11px;font-size:12px;font-weight:650;color:var(--ink)}
.case-section .tablewrap{margin:25px 0}.case-section .assignment-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin:25px 0 16px}
.case-section .assignment-grid .figure-tile{min-width:0}.case-section .assignment-grid .figure-tile:last-child{grid-column:1 / -1;max-width:800px;margin:auto}.case-section .assignment-diff{margin:16px 0 24px}
.case-section .figure-tile figcaption{font-size:12px}.case-section .figure-tile figcaption b{font-size:14px}
@media(max-width:800px){.case-section .assignment-grid{grid-template-columns:1fr}.case-section .assignment-grid .figure-tile:last-child{grid-column:auto;max-width:none}.case-nav{gap:6px}.case-nav a{font-size:11px;padding:7px 9px}}
"""

def shell(
    title: str,
    body: str,
    depth: int = 0,
    repo_url: str = "",
    site_url: str = "",
    article: bool = False,
) -> str:
    up = "../" * depth
    source = f'<a href="{html.escape(repo_url)}">GitHub ↗</a>' if repo_url else ""
    site_target = (
        f'<meta name="project-site-target" content="{html.escape(site_url, quote=True)}">'
        '<meta name="project-site-status" content="configured-target-not-deployment-confirmation">'
        if site_url
        else ""
    )
    nav = f'<header class="wrap"><nav class="nav"><a class="brand" href="{up}index.html"><span class="monogram">MCL</span>Mobility Computation Lab</a><div class="navlinks"><a href="{up}city-workflow.html">City workflow</a><a href="{up}datasets.html">Networks</a><a href="{up}visualizations.html">Visual results</a><a href="{up}open-data-explorer.html">City evidence</a><a href="{up}open-data.html">Open data</a><a href="{up}methods.html">Methods</a><a href="{up}getting-started.html">Documentation</a>{source}</div></nav></header>'
    foot = f'<div class="wrap"><footer class="footer"><span>Mobility Computation Lab · city networks, demand and reproducible computation</span><span><a href="{up}data-access.html">Data access</a> · <a href="{up}citation.html">Cite</a> · <a href="{up}roadmap.html">Roadmap</a></span></footer></div>'
    return f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="City networks, travel demand and reproducible network computation.">{site_target}<title>{html.escape(title)} | Mobility Computation Lab</title><link rel="stylesheet" href="{up}assets/site.css"></head><body>{nav}{body}{foot}</body></html>'


def rewrite_link(match: re.Match, source: Path, repo_url: str) -> str:
    raw = html.unescape(match.group(2))
    if raw.startswith(("http:", "https:", "mailto:", "#")):
        return match.group(0)
    filepart, marker, fragment = raw.partition("#")
    resolved = (source.parent / filepart).resolve()
    try:
        inside = resolved.relative_to(DOCS)
        target = str(Path(filepart).with_suffix('.html')).replace('\\', '/') if filepart.endswith('.md') else filepart
    except ValueError:
        if repo_url:
            try:
                rel = resolved.relative_to(ROOT).as_posix()
                target = repo_url.rstrip('/') + ('/tree/main/' if resolved.is_dir() else '/blob/main/') + rel
            except ValueError:
                target = filepart
        else:
            target = filepart
    if marker:
        target += '#' + fragment
    return match.group(1) + html.escape(target, quote=True) + match.group(3)


def render_markdown(path: Path, repo_url: str) -> str:
    tokens = MD.parse(path.read_text(encoding="utf-8"))
    for i, token in enumerate(tokens):
        if token.type == 'heading_open' and i + 1 < len(tokens):
            title = tokens[i+1].content
            slug = re.sub(r'[^a-z0-9 _-]', '', title.lower()).replace(' ', '-')
            token.attrSet('id', slug)
    content = MD.renderer.render(tokens, MD.options, {})
    if path.name == "open-data-explorer.md":
        source = DOCS / "data" / "open-mobility" / "city_evidence.csv"
        with source.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = [
                {
                    "id": row["city_id"],
                    "name": row["city_name"],
                    "iso2": row["country_iso2"],
                    "iso3": row["country_iso3"],
                    "catalog": row["catalog_strict_two_registry"],
                    "gtfs": row["gtfs_all_retained_stop_evidence"],
                    "hashes": row["gtfs_all_retained_unique_content_hash_count"],
                    "realtime": row["realtime_all_retained_city_class"],
                }
                for row in csv.DictReader(handle)
            ]
        payload = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
        content = content.replace("__MCL_CITY_INDEX__", payload.replace("<", "\\u003c"))
    return re.sub(r'((?:href|src)=")([^"]+)(")', lambda m: rewrite_link(m,path,repo_url), content)


def evidence_overview() -> str:
    """Render existing, non-additive research summaries; never contact a provider."""
    catalog = json.loads((ROOT / "catalog/open-data-evidence.json").read_text(encoding="utf-8"))
    metrics = {metric["id"]: metric for layer in catalog["layers"] for metric in layer["metrics"]}
    def n(metric_id: str) -> str:
        return f"{metrics[metric_id]['value']:,}"
    cards = [
        ("global_city_frame", "City frame", n("ghsl_urban_centres"), "GHSL urban centres", f"Common study frame; {n('strict_two_registry_catalog_cities')} cities in the separately defined strict catalog scenario.", "open-data.html#global-city-frame"),
        ("gtfs_static", "GTFS static", n("cities_with_inside_polygon_stop_evidence"), "cities with inside-polygon stop evidence", f"{n('all_retained_unique_content_hashes')} unique parseable content hashes in the all-retained view. Not service coverage.", "open-data.html#gtfs-static"),
        ("gtfs_realtime", "GTFS-Realtime", n("endpoint_representatives"), "metadata endpoint representatives", "Source inventory and retained parse snapshots, not a live endpoint-health monitor.", "open-data.html#gtfs-realtime"),
        ("osm_map_features", "OSM evidence", n("sample_extracts"), "regional extracts in the bounded sample", f"{n('ghsl_rows_with_point_features')} of {n('ghsl_rows_in_sample_countries')} sampled urban-centre rows have bbox-joined point features.", "open-data.html#osm"),
        ("gbfs_shared_mobility", "Shared mobility", n("system_rows"), "GBFS system registry rows", f"{n('countries_with_rows')} countries represented. Registry locations are not reviewed city matches or GPS traces.", "open-data.html#gbfs-and-shared-mobility"),
        ("model_interoperability", "Model interfaces", n("crosswalk_entries"), "standards and tools in the crosswalk", "GMNS, TNTP, GTFS and related ecosystems: documented reuse pathways, not bundled implementations.", "interoperability.html"),
    ]
    rendered = []
    for layer, title, value, unit, meaning, link in cards:
        rendered.append(f'<article class="card" data-evidence-layer="{html.escape(layer)}"><span class="tag">{html.escape(title)}</span><h3 class="evidence-metric">{html.escape(value)}</h3><p><strong>{html.escape(unit)}</strong><br>{html.escape(meaning)}</p><a href="{html.escape(link)}">Definitions and source scope →</a></article>')
    return '<div class="cards" id="open-evidence-overview">' + ''.join(rendered) + '</div>'


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository-url', default=None)
    args = parser.parse_args()
    project = ROOT/'catalog/project.json'
    config = json.loads(project.read_text(encoding='utf-8')) if project.exists() else {
        'title': 'Mobility Computation Lab',
        'repository_url': None,
        'site_url': None,
    }
    if args.repository_url is not None:
        if not re.fullmatch(r'https://github.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/?',args.repository_url):
            parser.error('Use the confirmed GitHub repository URL, without a branch or token.')
        config['repository_url']=args.repository_url.rstrip('/')
    repo_url=config.get('repository_url') or ''
    site_url=(config.get('site_url') or '').strip()
    if site_url and not re.fullmatch(
        r'https://[A-Za-z0-9_.-]+\.github\.io/[A-Za-z0-9_.-]+/',
        site_url,
    ):
        parser.error('Use a GitHub Pages project URL ending in a slash.')
    project.write_text(json.dumps(config,indent=2)+'\n', encoding='utf-8', newline='\n')
    (DOCS/'assets').mkdir(parents=True,exist_ok=True)
    (DOCS/'assets/site.css').write_text(CSS, encoding='utf-8', newline='\n')
    (DOCS/'.nojekyll').write_text('', encoding='utf-8', newline='\n')
    for path in DOCS.rglob('*.md'):
        if path.name=='index.md':continue
        title=path.read_text(encoding='utf-8').splitlines()[0].lstrip('# ').strip()
        depth=len(path.relative_to(DOCS).parents)-1
        article=f'<main class="article"><p class="crumb">Documentation / {html.escape(title)}</p>{render_markdown(path,repo_url)}</main>'
        path.with_suffix('.html').write_text(
            shell(
                title,
                article,
                depth=depth,
                repo_url=repo_url,
                site_url=site_url,
                article=True,
            ),
            encoding='utf-8',
            newline='\n',
        )
    # The framework-first homepage is generated from the root README after the
    # complete site build. Keep the established builder for unrelated pages.
    if (DOCS / 'index.md').read_text(encoding='utf-8').startswith(
        '<!-- Homepage content derived from the root README by tools/build_case_presentation.py. -->'
    ):
        from build_case_presentation import main as build_case_presentation
        build_case_presentation()
        print(f'Built complete documentation in {DOCS}; framework-first pages refreshed last')
        return 0
    # Legacy homepage source for trees that have not adopted the presentation.
    body = render_markdown(DOCS / "index.md", repo_url)
    for marker in ("<!-- EVIDENCE_OVERVIEW -->", "<!-- DATASET_CARDS -->"):
        if body.count(marker) != 1:
            raise RuntimeError(f"Homepage source must contain exactly one {marker}")
    body = body.replace("<!-- EVIDENCE_OVERVIEW -->", evidence_overview())
    catalog = json.loads((ROOT / "catalog/datasets.json").read_text(encoding="utf-8"))
    cards = []
    for item in catalog["datasets"]:
        if item["kind"] not in {"road-benchmark", "city-network"}:
            continue
        tag = "Static assignment" if item.get("profile") == "static-beckmann-fw" else "Finite space–time CG" if "cg" in item.get("profile", "") else "Network instance"
        title = html.escape(item["title"]).replace(" | ", "<br>")
        pieces = [f"{item[key]:,} {label}" for key, label in [("nodes", "nodes"), ("links", "links"), ("od_pairs", "OD pairs")] if key in item]
        if "final_columns" in item:
            pieces.append(f"{item['final_columns']:,} final columns")
        page = Path(item["data_page"]).relative_to("docs").with_suffix(".html").as_posix()
        description = html.escape(item.get("verification", "See the source and model scope in the data card."))
        cards.append(f'<article class="card"><span class="tag">{html.escape(tag)}</span><h3>{title}</h3><p>{description}</p><div class="meta">{html.escape(" · ".join(pieces))}</div><a href="{html.escape(page)}">Open data card →</a></article>')
    body = body.replace("<!-- DATASET_CARDS -->", "".join(cards))
    (DOCS/'index.html').write_text(
        shell('Home', body, repo_url=repo_url, site_url=site_url),
        encoding='utf-8',
        newline='\n',
    )
    print(
        f'Built static documentation in {DOCS}; '
        f'repository URL: {repo_url or "local preview"}; '
        f'Pages target: {site_url or "not configured"} '
        '(configuration only)'
    )
    return 0

if __name__=='__main__':raise SystemExit(main())
