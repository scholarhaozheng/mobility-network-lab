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
    body='''<main>
<div class="wrap"><section class="hero"><div><p class="eyebrow">GMNS-compatible city network computing</p><h1>City networks.<br>Travel demand.<br><em>Computation.</em></h1><p class="lede">Connect prepared road networks and OD demand to routes, flows and independently checked optimization results. Reuse the same interfaces as city data and methods evolve.</p><div class="actions"><a class="button primary" href="datasets.html">Explore the networks →</a><a class="button" href="datasets/boston-behavior-feedback.html">Explore Boston feedback →</a><a class="button" href="getting-started.html">Run a model →</a></div><p class="note">Prepared-table tools remain the common interface. Central Boston connects source-backed zones, activity and household demand, transit observations, a bounded mode response and static FW.</p></div><div class="pipeline"><p class="eyebrow">One city model. Connected components.</p><div class="step"><small>01</small><div><b>Networks &amp; zone access</b><span>Directed roads · stable IDs · explicit access mappings</span></div></div><div class="step"><small>02</small><div><b>OD demand</b><span>Origins · destinations · volumes · time · provenance</span></div></div><div class="step"><small>03</small><div><b>Assignment &amp; optimization</b><span>Space–time CG · separate static FW baseline</span></div></div><div class="step"><small>04</small><div><b>Flows &amp; verification</b><span>Paths · arc loads · objectives · saved-output checks</span></div></div><p class="note" style="color:#bdd1da">Mobility observations support the model. Metadata matches are not GPS trajectories or inferred OD.</p></div></section></div>
<div class="strip"><div class="wrap"><div class="stripin"><div><b>A shared network contract</b><span>Nodes, links, zone access, demand and units</span></div><div><b>Reusable computational methods</b><span>Automatic routes, CG and a separate static baseline</span></div><div><b>Inspect the actual result</b><span>Complete flow exports, figures and verification</span></div></div></div></div>
<div class="wrap"><section><div class="sectionhead"><h2>Networks and visual results</h2><p>Open the source-backed Central Boston component or inspect retained Sioux Falls selected-OD benchmarks and their optimization traces.</p></div><div class="visual-grid"><figure class="figure-tile"><a href="datasets/sioux-200od.html"><img src="assets/benchmarks/sioux_200od_final_physical_link_flow.png" alt="200-OD Sioux Falls physical-link movement flow"></a><figcaption><b>Sioux Falls · 200 OD</b>24 nodes · 64 selected links · 446 final columns</figcaption></figure><figure class="figure-tile"><a href="datasets/sioux-250od.html"><img src="assets/benchmarks/sioux_250od_final_physical_link_flow.png" alt="250-OD Sioux Falls physical-link movement flow"></a><figcaption><b>Sioux Falls · 250 OD</b>24 nodes · 69 selected links · 567 final columns</figcaption></figure></div><p class="note">Schematic horizon-total movement-flow views, not observed traffic or static V/C. Opposite directions may overlap. These are different subsets, not a full 528-OD assignment.</p><div class="actions"><a class="button" href="visualizations.html">Open all six figures →</a><a class="button" href="outputs.html">Read the verification →</a></div><div class="cards"></div><p class="note">Consult each data card for source and redistribution boundaries. Synthetic reference inputs remain separate from city data.</p></section></div>
<div class="soft"><div class="wrap"><section><div class="sectionhead"><h2>Build around one city</h2><p>Road networks, zones, demand and evidence belong to the same modelling context—not to disconnected software demonstrations.</p></div><div class="workflow-strip"><a href="data-contract.html">Road network</a><span>→</span><a href="city-workflow.html">Zones &amp; hierarchy</a><span>→</span><a href="data-contract.html">OD demand</a><span>→</span><a href="city-workflow.html">Mobility evidence</a><span>→</span><a href="methods.html">Assignment</a></div><p class="focus-note">The current executable network workflow starts from prepared node, link and demand tables, with supplied zone access. Automated acquisition, hierarchical zone creation, OD estimation and GPS matching are described as extensions, not advertised as completed functions.</p><div class="tiles"><div class="tile"><span class="tag">Data and model</span><h3>Preserve the connection</h3><p>Declare the study area, IDs, modes, units and provenance. Keep observation, estimation and synthetic demand distinct.</p><a href="city-workflow.html">City workflow →</a></div><div class="tile"><span class="tag">Methods</span><h3>Keep models explicit</h3><p>Finite capacity-constrained CG and static Beckmann/FW are separate formulations. Future Bush and coupled methods need their own model and validation.</p><a href="methods.html">Computational methods →</a></div><div class="tile"><span class="tag">Reusable interface</span><h3>Add a network, not a solver</h3><p>Reuse compatible inputs and configurations. Retain physical-link mappings so results return to the source network.</p><a href="add-a-network.html">Contribute an instance →</a></div></div></section></div></div>
<div class="wrap"><section class="split"><div><p class="eyebrow">Run the computational core</p><h2>Prepare. Solve.<br>Inspect.</h2><p>The bundled capacity regression starts from raw CSVs. The existing two-phase solver exports complete path flows and supports solver-free output verification.</p><a class="button" href="getting-started.html">Installation and quick start →</a></div><div><pre><code>python -m pip install -r requirements.txt
python tools/mnl.py run \\
  --input app/cases/capacity_zone_probe/input \\
  --config app/cases/capacity_zone_probe/case.json \\
  --seed-mode auto --seed-k 1 \\
  --output results/capacity-demo
python tools/mnl.py verify --run results/capacity-demo</code></pre><p class="note">This self-contained input is a synthetic regression, not a city data product. Expected route flows: 3 and 7; objective: 27. Single-line cross-platform commands are in the documentation.</p></div></section></div>
<div class="soft"><div class="wrap"><section class="evidence-support"><div class="sectionhead"><h2>Supporting mobility data</h2><p>Open transit, map-feature and shared-mobility evidence helps select and document sources for a city study. Browse the retained city rows, then use the local tools with your own files.</p></div><!-- EVIDENCE_OVERVIEW --><p class="note">Source-qualified research snapshots, not live coverage. These layers use different units and must not be added together. Public projections exclude raw feeds, provider URLs and geometries. <a href="omdv-provenance.html">Trace the metrics →</a></p><div class="actions"><a class="button primary" href="open-data-explorer.html">Browse 11,422 city rows →</a><a class="button" href="open-data.html">Definitions and limits →</a><a class="button" href="city-workflow.html">Place evidence in a city model →</a></div><div class="split"><div><p class="eyebrow">Executable data tools</p><h3>Query evidence or inspect a local GTFS ZIP</h3><p>Stable IDs, explicit duplicate handling and an OMDV-derived offline parser preserve source state without claiming GPS matching or OD estimation.</p><a href="data-tools.html">Data tools →</a></div><div><pre><code>python -m pip install -r requirements-data-tools.txt
python -B tools/mcl_data.py catalog-city-match \\
  --catalog examples/data-tools/feeds_sample.csv \\
  --cities examples/data-tools/external_city_universe_sample.csv \\
  --output results/data-tools-demo</code></pre><p class="note">Open mobility data: <a href="open-data.html">retained study summaries</a> · <a href="omdv-provenance.html">source provenance</a> · <a href="interoperability.html">upstream tools</a>. Catalog counts do not measure runnable city models.</p></div></div></section></div></div>
<div class="wrap"><section><div class="cta"><div><h2>Your city. An explicit network model.</h2><p>Start with compatible inputs. Add evidence and methods without losing provenance or the working computational core.</p></div><a class="button" href="city-workflow.html">Explore the city workflow →</a></div></section></div></main>'''
    home_marker = '<main>\n<div class="wrap"><section class="hero">'
    if body.count(home_marker) != 1 or body.count('<div class="visual-grid">') != 1:
        raise RuntimeError('Homepage integration markers changed; inspect the site template.')
    site_cover = '''<div class="wrap"><figure class="site-cover"><img src="assets/boston/visual_release_r1/mcl_boston_hero.png" alt="Dark navy Mobility Computation Lab cover with real Central Boston street and zone geometry on the right."><figcaption>Central Boston geography, not traffic values. Roads: GMNS Plus 21_Boston (Apache-2.0), commit 116447ab641cca1ed34797d019c8e704063393c3; H3 zones and composition: Mobility Computation Lab.</figcaption></figure></div>'''
    boston_feature = '''<figure class="figure-tile boston-feature"><a href="datasets/boston-central.html#boston-visual-gallery"><img src="assets/boston/visual_release_r1/boston_network_zones.png" alt="Map of Central Boston roads, H3 zones, analysis and core boundaries, with one orange ordered corridor."></a><figcaption><b>Central Boston · network and spatial zones</b>5,091 directed physical GMNS links, 177 clipped H3 r9 zones and one ordered corridor. Parcel outlines are context, not building footprints. Roads: GMNS Plus 21_Boston (Apache-2.0); parcels: MassGIS (Bureau of Geographic Information), Commonwealth of Massachusetts EOTSS. <a href="datasets/boston-central.html#boston-visual-gallery">See all five source-qualified maps →</a></figcaption></figure>'''
    body = body.replace(home_marker, '<main>\n' + site_cover + '\n<div class="wrap"><section class="hero">', 1)
    body = body.replace('<div class="visual-grid">', boston_feature + '<div class="visual-grid">', 1)
    body = body.replace('<!-- EVIDENCE_OVERVIEW -->', evidence_overview())
    # The homepage cards are derived from the catalog, not from an assumed city list.
    catalog = json.loads((ROOT / 'catalog/datasets.json').read_text(encoding='utf-8'))
    visible = [item for item in catalog['datasets'] if item['kind'] in {'road-benchmark', 'city-network'}]
    cards = []
    for item in visible:
        tag = 'Static assignment' if item.get('profile') == 'static-beckmann-fw' else 'Finite space–time CG' if 'cg' in item.get('profile', '') else 'Network instance'
        title = html.escape(item['title']).replace(' | ', '<br>')
        pieces = [f"{item[key]:,} {label}" for key,label in [('nodes','nodes'),('links','links'),('od_pairs','OD pairs')]] if all(k in item for k in ('nodes','links','od_pairs')) else []
        if 'final_columns' in item:
            pieces.append(f"{item['final_columns']:,} final columns")
        card_path = Path(item['data_page']).relative_to('docs').with_suffix('.html').as_posix()
        description = html.escape(item.get('verification', 'See the data card for its source, access policy and verification.'))
        access = 'Inputs included' if item.get('access') == 'bundled-input' else 'Component included' if item.get('access') == 'bundled-example' else 'Result record' if item.get('access') == 'results-only' else 'External source'
        cards.append(f'<article class="card"><span class="tag">{html.escape(tag)}</span><h3>{title}</h3><p>{description}</p><div class="meta">{html.escape(" · ".join(pieces))}</div><a href="{html.escape(card_path)}">{access} →</a></article>')
    start = body.index('<div class="cards">') + len('<div class="cards">')
    end = body.index('</div><p class="note">', start)
    body = body[:start] + ''.join(cards) + body[end:]
    if any(item['kind'] == 'city-network' for item in visible):
        body = body.replace('Road benchmark records', 'Network catalog').replace('Documented numerical results, with source and access boundaries. These are historical benchmark records, not newly collected city datasets.', 'Runnable instances and documented benchmark results. Each data card declares its provenance, input access and verification scope.').replace('Road input tables are not bundled with these records. Self-contained synthetic reference inputs are available for the source quick start.', 'Consult each data card for input availability. Synthetic reference inputs remain separate from city datasets.')
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
