#!/usr/bin/env python3
"""Build the English static site from Markdown and the machine-readable catalog.

Run without a repository URL for local previews. Set --repository-url before
publishing GitHub Pages so source-file links resolve outside the /docs site.
"""
from __future__ import annotations
import argparse
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
:root{--ink:#152b39;--muted:#536b78;--navy:#102c3e;--teal:#087e83;--mint:#b1ebe0;--paper:#f5f8fa;--line:#dce5eb;--white:#fff}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#fff;color:var(--ink);font:16px/1.7 -apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif}a{color:var(--teal);text-decoration:none}a:hover{text-decoration:underline}h1,h2,h3{line-height:1.16;letter-spacing:-.035em}h1{font-size:clamp(36px,4vw,56px)}h2{font-size:30px;margin:0 0 22px}h3{font-size:20px}p{margin:0 0 18px}code,pre{font-family:ui-monospace,SFMono-Regular,Consolas,monospace}code{font-size:.86em;background:#edf3f5;padding:.13em .3em;border-radius:4px}pre{background:#102c3e;color:#e4f2f5;padding:22px;overflow-x:auto;border-radius:12px;font-size:13px;line-height:1.8}pre code{background:none;padding:0;color:inherit}table{width:100%;border-collapse:collapse;font-size:14px}th,td{padding:16px 12px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}th{font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}.wrap{max-width:1160px;margin:auto;padding:0 38px}.nav{height:82px;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;gap:20px}.brand{display:flex;align-items:center;gap:12px;color:var(--ink);font-weight:750;font-size:17px;letter-spacing:-.035em}.monogram{width:34px;height:34px;display:grid;place-items:center;border-radius:9px;background:var(--navy);color:var(--mint);font-size:12px;letter-spacing:.02em}.navlinks{display:flex;gap:25px;font-size:13px;font-weight:600}.navlinks a{color:var(--muted)}.hero{padding:70px 0 58px;display:grid;grid-template-columns:1.28fr 1fr;gap:55px;align-items:center}.eyebrow{font-size:11px;letter-spacing:.16em;text-transform:uppercase;font-weight:750;color:var(--teal);margin-bottom:22px}.hero h1{margin:0 0 22px;font-size:clamp(40px,4.5vw,64px);letter-spacing:-.055em}.hero h1 em{font-style:normal;color:var(--teal)}.lede{max-width:550px;color:var(--muted);font-size:17px;line-height:1.75}.actions{display:flex;gap:12px;flex-wrap:wrap;margin-top:28px}.button{display:inline-flex;align-items:center;justify-content:center;min-height:44px;padding:10px 18px;border-radius:7px;border:1px solid var(--line);font-size:13px;font-weight:650;color:var(--ink);background:white}.button.primary{background:var(--navy);color:white;border-color:var(--navy)}.button:hover{text-decoration:none;filter:brightness(.95)}.pipeline{background:var(--navy);border-radius:18px;padding:30px;color:#c6dbe5;box-shadow:0 18px 50px #102c3e12}.pipeline .eyebrow{color:var(--mint);font-size:10px;margin-bottom:24px}.step{display:flex;gap:15px;align-items:center;padding:16px 0;border-bottom:1px solid #ffffff18}.step:last-child{border:0}.step b{font-size:16px;letter-spacing:-.01em;color:#fff;display:block}.step span{font-size:12px;color:#a9c5d2}.step small{font:11px ui-monospace,monospace;color:var(--mint);background:#ffffff10;border:1px solid #ffffff20;min-width:30px;height:30px;border-radius:50%;display:grid;place-items:center}.strip{border-block:1px solid var(--line);background:var(--paper)}.stripin{display:grid;grid-template-columns:repeat(3,1fr);gap:25px;padding:24px 0}.stripin b{display:block;font-size:14px;margin-bottom:3px}.stripin span{display:block;font-size:12px;color:var(--muted)}section{padding:58px 0}.sectionhead{display:flex;justify-content:space-between;align-items:flex-end;gap:22px;margin-bottom:26px}.sectionhead h2{margin:0}.sectionhead p{max-width:520px;color:var(--muted);font-size:14px;margin:0}.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}.card{padding:26px;border:1px solid var(--line);border-radius:12px;background:white;display:flex;flex-direction:column}.card h3{margin:11px 0 14px}.card p{font-size:13px;color:var(--muted);flex:1}.card a{font-weight:650;font-size:13px}.tag{font:10px ui-monospace,monospace;text-transform:uppercase;letter-spacing:.09em;color:var(--teal)}.meta{border-top:1px solid var(--line);padding-top:15px;margin:8px 0 20px;font-size:12px;color:var(--muted)}.soft{background:var(--paper)}.split{display:grid;grid-template-columns:.85fr 1.4fr;gap:48px;align-items:start}.split>div{min-width:0}.split p{color:var(--muted);font-size:14px}.note{font-size:12px;color:var(--muted);margin:16px 0 0}.benchmark-feature{display:block;margin:0 0 26px;border:1px solid var(--line);border-radius:14px;overflow:hidden;background:#fff;color:var(--muted)}.benchmark-feature img{display:block;width:100%;height:auto}.benchmark-feature span{display:block;padding:11px 16px;font-size:12px}.benchmark-feature:hover{text-decoration:none}.tiles{display:grid;grid-template-columns:repeat(3,1fr);gap:22px}.tile{border-top:2px solid var(--teal);padding:18px 0}.tile h3{margin:4px 0 14px}.tile p{font-size:14px;color:var(--muted)}.cta{background:var(--navy);color:white;border-radius:16px;padding:32px 36px;display:flex;justify-content:space-between;gap:24px;align-items:center}.cta h2{font-size:27px;margin-bottom:10px}.cta p{font-size:14px;color:#bdd1da;margin:0}.footer{margin-top:25px;border-top:1px solid var(--line);padding:28px 0;color:var(--muted);font-size:12px;display:flex;justify-content:space-between;gap:20px}.article{max-width:850px;margin:55px auto 75px;padding:0 32px}.article h1{font-size:42px;margin:10px 0 30px}.article h2{font-size:26px;margin:35px 0 16px}.article p,.article li{line-height:1.85}.article table{display:block;overflow:auto;margin:26px 0}.article table code{font-size:12px}.article .crumb{font-size:12px;color:var(--muted)}.article img{max-width:100%}.tablewrap{overflow:auto}.site-hint{padding:10px 14px;background:#edf5f4;border-left:3px solid var(--teal);font-size:13px}@media(max-width:800px){.wrap{padding:0 22px}.nav{height:auto;min-height:72px;flex-wrap:wrap;padding:16px 0;gap:12px}.navlinks{gap:16px;font-size:12px}.hero{grid-template-columns:1fr;padding:38px 0;gap:30px}.hero h1{font-size:46px}.pipeline{padding:24px}.stripin,.cards,.tiles,.split{grid-template-columns:1fr}.stripin{gap:14px}.sectionhead{display:block}.sectionhead p{margin-top:16px}.cards{gap:14px}.cta,.footer{flex-direction:column;align-items:flex-start}.article{padding:0 22px;margin:36px auto}.article h1{font-size:34px}section{padding:40px 0}.split{gap:12px}}
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
    nav = f'<header class="wrap"><nav class="nav"><a class="brand" href="{up}index.html"><span class="monogram">MCL</span>Mobility Computation Lab</a><div class="navlinks"><a href="{up}data-tools.html">Data tools</a><a href="{up}open-data.html">Evidence</a><a href="{up}datasets.html">Catalog</a><a href="{up}methods.html">Methods</a><a href="{up}getting-started.html">Documentation</a>{source}</div></nav></header>'
    foot = f'<div class="wrap"><footer class="footer"><span>Mobility Computation Lab · open evidence to verified network results</span><span><a href="{up}data-access.html">Data access</a> · <a href="{up}citation.html">Cite</a> · <a href="{up}roadmap.html">Roadmap</a></span></footer></div>'
    return f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="Open mobility data, model-ready network interfaces, reproducible assignment, and inspectable network optimization.">{site_target}<title>{html.escape(title)} | Mobility Computation Lab</title><link rel="stylesheet" href="{up}assets/site.css"></head><body>{nav}{body}{foot}</body></html>'


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
    return re.sub(r'((?:href|src)=")([^"]+)(")', lambda m: rewrite_link(m,path,repo_url), content)


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
<div class="wrap"><section class="hero"><div><p class="eyebrow">Local data tools · evidence · computation</p><h1>Open city data<br>to <em>verified<br>results.</em></h1><p class="lede">Normalize local mobility metadata, preserve matching uncertainty, inspect bounded evidence, and move compatible networks through reproducible assignment and independently checked optimization.</p><div class="actions"><a class="button primary" href="data-tools.html">Run the data tools →</a><a class="button" href="getting-started.html">Run a network</a></div></div><div class="pipeline"><p class="eyebrow">Four layers. No hidden claims.</p><div class="step"><small>01</small><div><b>Data tools & evidence</b><span>Catalog normalization · exact city matching · bounded summaries</span></div></div><div class="step"><small>02</small><div><b>Model-ready interface</b><span>Stable IDs · explicit units · zone access</span></div></div><div class="step"><small>03</small><div><b>Assignment & optimization</b><span>Static FW · reference LP · column generation</span></div></div><div class="step"><small>04</small><div><b>Verified outputs</b><span>Complete path pool · objectives · independent checks</span></div></div></div></section></div>
<div class="strip"><div class="wrap"><div class="stripin"><div><b>11,422 urban centres</b><span>A common GHSL frame, not transport coverage</span></div><div><b>4,425 unique GTFS contents</b><span>All-retained parseable view; 2,959 stop-evidence cities</span></div><div><b>2,465 realtime endpoints</b><span>Metadata representatives, not live health</span></div></div></div></div>
<div class="wrap"><section><div class="sectionhead"><h2>Open mobility data</h2><p>Compact accepted evidence with source hashes and explicit limits. Layers remain separate and are never summed into a false coverage count.</p></div><div class="tiles"><div class="tile"><span class="tag">Global frame</span><h3>City and transit evidence</h3><p>GHSL denominator, GTFS static content and bounded realtime classifications.</p><a href="open-data.html">Read the evidence guide →</a></div><div class="tile"><span class="tag">Map and shared mobility</span><h3>OSM and GBFS</h3><p>Bounded map-feature and registry summaries that do not claim service coverage.</p><a href="open-data.html#osm">Inspect the boundaries →</a></div><div class="tile"><span class="tag">Interfaces</span><h3>Model interoperability</h3><p>Standards and tools are catalogued as reuse pathways, not city availability.</p><a href="interoperability.html">Open the source catalog →</a></div></div></section></div>
<div class="soft"><div class="wrap"><section class="split"><div><p class="eyebrow">Executable data tools</p><h2>Normalize.<br>Match. Audit.</h2><p>Selected OMDV implementations process your local feed-catalog and city CSVs. Exact city/country matches, unmatched rows, and ambiguous keys remain inspectable.</p><a class="button" href="data-tools.html">Input and output guide →</a></div><div><pre><code>python -B tools/mcl_data.py catalog-city-match \\
  --catalog examples/data-tools/feeds_sample.csv \\
  --cities examples/data-tools/external_city_universe_sample.csv \\
  --output results/data-tools-demo</code></pre><p class="note">No network request, source checkout, GTFS ZIP parsing, realtime probing, GPS matching, or city-network compilation.</p></div></section></div></div>
<div class="wrap"><section><div class="sectionhead"><h2>Road benchmark records</h2><p>Documented numerical results, with source and access boundaries. These are historical benchmark records, not newly collected city datasets.</p></div><a class="benchmark-feature" href="datasets/sioux-250od.html"><img src="assets/benchmarks/sioux_250od_final_physical_link_flow.png" alt="Final physical-link movement flow for the selected 250-OD Sioux Falls benchmark subset"><span>Selected 250-OD Sioux Falls subset · line width is total final movement flow aggregated across modeled time, not static V/C or observed traffic.</span></a><div class="cards">
<article class="card"><span class="tag">Finite space–time CG</span><h3>Sioux Falls<br>200 OD</h3><p>Recovered final path flows with independent demand, capacity and objective checks.</p><div class="meta">24 nodes · 64 links · 446 final columns</div><a href="datasets/sioux-200od.html">Explore the result record →</a></article>
<article class="card"><span class="tag">Finite space–time CG</span><h3>Sioux Falls<br>250 OD</h3><p>A larger path pool, with saved records supporting final-flow reconstruction and verification.</p><div class="meta">24 nodes · 69 links · 567 final columns</div><a href="datasets/sioux-250od.html">Explore the result record →</a></article>
<article class="card"><span class="tag">Static assignment</span><h3>Sioux Falls<br>Frank–Wolfe</h3><p>An approximate static baseline with recomputed costs, objective and aggregate flow balance.</p><div class="meta">76 links · 528 OD records · 100 iterations</div><a href="datasets/sioux-static-fw.html">Explore the result record →</a></article></div><p class="note">Road input tables are not bundled with these records. Self-contained synthetic reference inputs are available for the source quick start.</p></section></div>
<div class="soft"><div class="wrap"><section class="split"><div><p class="eyebrow">Start with a runnable example</p><h2>Install. Run.<br>Check the result.</h2><p>The bundled capacity example starts with raw CSV inputs. Automatic initialization and the existing two-phase solver produce complete path-flow outputs.</p><a class="button" href="getting-started.html">Read the installation guide →</a></div><div><pre><code>python -m pip install -r requirements.txt

python tools/mnl.py run \\
  --input app/cases/capacity_zone_probe/input \\
  --config app/cases/capacity_zone_probe/case.json \\
  --seed-mode auto --seed-k 1 \\
  --output results/capacity-demo

python tools/mnl.py verify --run results/capacity-demo</code></pre><p class="note">Shell line continuation is shown for readability. The documentation includes single-line commands for Windows, macOS and Linux.</p></div></section></div></div>
<div class="wrap"><section><div class="sectionhead"><h2>Build on a shared contract</h2><p>Use the same network identifiers across configuration, solver outputs and result records.</p></div><div class="tiles"><div class="tile"><span class="tag">01 / Data</span><h3>Prepare compatible inputs</h3><p>Declare file mappings, units, departure times and zone access. Preserve the distinction between observed and synthetic demand.</p><a href="data-contract.html">Input specification →</a></div><div class="tile"><span class="tag">02 / Computation</span><h3>Choose a defined model</h3><p>Keep finite hard-capacitated path-flow optimization separate from static equilibrium and other future solver adapters.</p><a href="methods.html">Models and methods →</a></div><div class="tile"><span class="tag">03 / Extension</span><h3>Contribute an instance</h3><p>Add a data card, executable profile and repeatable checks. Promote available data, not an unimplemented roadmap item.</p><a href="add-a-network.html">Instance contribution guide →</a></div></div></section><section style="padding-top:0"><div class="cta"><div><h2>Your network. The same workflow.</h2><p>Bring a compatible instance, keep its provenance, and make the results reproducible.</p></div><a class="button" href="add-a-network.html">Add a network →</a></div></section></div></main>'''
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
        access = 'Inputs included' if item.get('access') == 'bundled-input' else 'Result record' if item.get('access') == 'results-only' else 'External source'
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
