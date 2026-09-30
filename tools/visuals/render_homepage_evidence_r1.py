#!/usr/bin/env python3
"""Render source-grounded homepage thumbnails and three-city case entry assets.

Presentation-only: reads already-public figure/graph records and never invokes a
scientific solver, demand pipeline, map matcher, or provider API.
"""
from __future__ import annotations

import csv
import hashlib
import html
import json
import math
import re
from collections import defaultdict
from pathlib import Path

import networkx as nx
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
ASSET = ROOT / "docs/assets/homepage_evidence_r1"
MAP = Path(__file__).with_name("homepage_evidence_r1_map.csv")
FONT = Path("C:/Windows/Fonts/segoeui.ttf")
BOLD = Path("C:/Windows/Fonts/segoeuib.ttf")
NAVY, MINT, PALE = "#102c3e", "#b1ebe0", "#d6e9eb"

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = BOLD if bold else FONT
    return ImageFont.truetype(str(path), size) if path.is_file() else ImageFont.load_default()

def save_png(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG", optimize=True)

def thumbnail(source: Path, target: Path, size: tuple[int,int] = (500,290)) -> dict:
    with Image.open(source) as loaded:
        original_size = loaded.size
        im = loaded.convert("RGB")
        im.thumbnail(size, Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", size, "#ffffff")
        canvas.paste(im, ((size[0]-im.width)//2, (size[1]-im.height)//2))
        save_png(canvas, target)
    return {"source_size": original_size, "display_pixels": list(size), "image_box_pixels": [im.width, im.height], "transform": "full image, aspect-preserving fit; no crop, no relabeling"}

def wkt_points(wkt: str) -> list[tuple[float, float]]:
    if not wkt.startswith("LINESTRING("):
        return []
    return [tuple(map(float, pair.strip().split()[:2])) for pair in wkt[11:-1].split(",")]

def cover_graph(city: str) -> tuple[list[list[tuple[float,float]]], str, str]:
    if city == "sioux_falls":
        source = "examples/sioux-falls/native_l3_r1/inputs_snapshot/SiouxFalls/link.csv"
        with (ROOT/source).open(newline="", encoding="utf-8-sig") as f:
            edges = [(r["from_node_id"], r["to_node_id"]) for r in csv.DictReader(f)]
        graph = nx.Graph()
        graph.add_edges_from(edges)
        pos = nx.spring_layout(graph, seed=24, iterations=140)
        lines = [[tuple(pos[a]), tuple(pos[b])] for a,b in edges]
        return lines, source, "Frozen classic Sioux directed-link topology; deterministic schematic layout, not geographic coordinates."
    source = "docs/assets/hong_kong/full_stack_r5/r2r4_baseline/phase_a/instance/link.csv"
    with (ROOT/source).open(newline="", encoding="utf-8-sig") as f:
        lines = [wkt_points(r["geometry"]) for r in csv.DictReader(f) if r["mcl_link_class"] == "physical"]
    return [line for line in lines if len(line) > 1], source, "Official-derived physical-road WKT only; nonphysical zone-access links omitted."

def cover(city: str) -> dict:
    config = {
        "sioux_falls": ("Sioux Falls", "Supplied demand.", "Static benchmark  /  Selected finite cases", "Frozen classic 24-node / 76-link topology; schematic layout"),
        "hong_kong": ("Hong Kong", "Modeled demand.", "Turn-aware GMNS  /  Four-stage scenario  /  Assignment", "Official-derived physical roads; not observed traffic"),
    }
    title, middle, scopes, note = config[city]
    lines, source, description = cover_graph(city)
    coords = [p for line in lines for p in line]
    minx, maxx = min(p[0] for p in coords), max(p[0] for p in coords)
    miny, maxy = min(p[1] for p in coords), max(p[1] for p in coords)
    def tx(p):
        x = 850 + (p[0]-minx)/max(maxx-minx,1e-9)*820
        y = 525 - (p[1]-miny)/max(maxy-miny,1e-9)*445
        return (round(x,2), round(y,2))
    geom = [[tx(p) for p in line] for line in lines]
    svg_lines = "\n".join('<polyline points="'+" ".join(f"{x},{y}" for x,y in line)+'" fill="none" stroke="#4d8990" stroke-width="1.3" opacity="0.65" stroke-linecap="round"/>' for line in geom)
    texts = [
      (90,104,"MOBILITY COMPUTATION LAB",28,MINT,True),
      (90,224,"City networks.",70,"#ffffff",True),
      (90,312,middle,70,"#ffffff",True),
      (90,388,"Inspectable computation.",56,"#ffffff",True),
      (90,482,scopes,23,PALE,False),
      (90,532,f"{title} case",25,MINT,True),
      (860,582,note,16,PALE,False),
    ]
    text_svg = "\n".join(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{700 if bold else 400}" font-family="Segoe UI,Arial,sans-serif" fill="{color}">{html.escape(value)}</text>' for x,y,value,size,color,bold in texts)
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="1800" height="600" viewBox="0 0 1800 600"><rect width="1800" height="600" fill="{NAVY}"/><rect x="790" width="1010" height="600" fill="#193b4d"/>{svg_lines}<rect width="770" height="600" fill="{NAVY}"/>{text_svg}</svg>\n'
    svg_path = ASSET/f"{city}_case_cover.svg"
    svg_path.write_text(svg, encoding="utf-8", newline="\n")
    im = Image.new("RGB", (1800,600), NAVY)
    draw = ImageDraw.Draw(im)
    draw.rectangle((790,0,1800,600),fill="#193b4d")
    for line in geom:
        draw.line(line,fill="#4d8990",width=2)
    draw.rectangle((0,0,770,600),fill=NAVY)
    for x,y,value,size,color,bold in texts:
        draw.text((x,y-size),value,font=font(size,bold),fill=color)
    png_path = ASSET/f"{city}_case_cover.png"
    save_png(im,png_path)
    record = {"city": title, "svg_sha256": sha(svg_path), "png_sha256": sha(png_path), "source_graph": source, "source_graph_sha256": sha(ROOT/source), "graph_description": description, "style_reference": "docs/assets/boston/visual_release_r1/mcl_boston_hero.svg", "style_reference_sha256": sha(ROOT/"docs/assets/boston/visual_release_r1/mcl_boston_hero.svg"), "renderer": "tools/visuals/render_homepage_evidence_r1.py", "no_scientific_rerun": True}
    (ASSET/f"{city}_case_cover.source.json").write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8",newline="\n")
    return record

def sioux_topology() -> dict:
    source="examples/sioux-falls/native_l3_r1/inputs_snapshot/SiouxFalls/link.csv"
    with (ROOT/source).open(newline='',encoding='utf-8-sig') as f:
        records=list(csv.DictReader(f))
    graph=nx.Graph()
    graph.add_edges_from((r['from_node_id'],r['to_node_id']) for r in records)
    pos=nx.spring_layout(graph,seed=24,iterations=140)
    xs=[v[0] for v in pos.values()]; ys=[v[1] for v in pos.values()]
    def pt(node):
        x,y=pos[node]
        return (round(105+(x-min(xs))/max(max(xs)-min(xs),1e-9)*990,2),round(570-(y-min(ys))/max(max(ys)-min(ys),1e-9)*420,2))
    im=Image.new('RGB',(1200,650),'#f6f9fa');d=ImageDraw.Draw(im)
    d.rectangle((0,0,1200,105),fill=NAVY)
    d.text((37,22),'Sioux Falls | frozen classic network',font=font(42,True),fill='#ffffff')
    for a,b in graph.edges():d.line((pt(a),pt(b)),fill='#42909a',width=5)
    for node in graph.nodes():
        x,y=pt(node);d.ellipse((x-11,y-11,x+11,y+11),fill='#102c3e',outline='#ffffff',width=2)
        d.text((x+15,y-14),str(node),font=font(19,True),fill='#193b4d')
    display_note=f'24 nodes | {len(records)} directed arcs ({graph.number_of_edges()} paired strokes) | supplied OD | schematic'
    d.text((37,612),display_note,font=font(21),fill='#536b78')
    png=ASSET/'sioux_falls_classic_topology.png';save_png(im,png)
    lines='\n'.join(f'<line x1="{pt(a)[0]}" y1="{pt(a)[1]}" x2="{pt(b)[0]}" y2="{pt(b)[1]}" stroke="#42909a" stroke-width="5"/>' for a,b in graph.edges())
    nodes='\n'.join(f'<circle cx="{pt(n)[0]}" cy="{pt(n)[1]}" r="11" fill="#102c3e" stroke="#fff" stroke-width="2"/><text x="{pt(n)[0]+15}" y="{pt(n)[1]+5}" font-size="19" font-weight="700" fill="#193b4d">{n}</text>' for n in graph.nodes())
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="650" viewBox="0 0 1200 650"><rect width="1200" height="650" fill="#f6f9fa"/><rect width="1200" height="105" fill="{NAVY}"/><text x="37" y="69" font-size="42" font-weight="700" font-family="Segoe UI,Arial,sans-serif" fill="#fff">Sioux Falls | frozen classic network</text>{lines}{nodes}<text x="37" y="634" font-size="21" font-family="Segoe UI,Arial,sans-serif" fill="#536b78">{display_note}</text></svg>\n'
    svg_path=ASSET/'sioux_falls_classic_topology.svg';svg_path.write_text(svg,encoding='utf-8',newline='\n')
    record={'source_link_table':source,'source_link_table_sha256':sha(ROOT/source),'directed_links':len(records),'displayed_undirected_segments':graph.number_of_edges(),'nodes':graph.number_of_nodes(),'layout':'networkx spring seed 24, 140 iterations; reciprocal directed arcs share one schematic display segment; not geographic','png_sha256':sha(png),'svg_sha256':sha(svg_path),'scientific_solver_rerun':False}
    (ASSET/'sioux_falls_classic_topology.source.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')
    return record

def summary_card(city: str) -> dict:
    # Metrics are transcribed from the linked accepted case pages; no model is run.
    data = {
      "boston": ("Boston | saved outputs", [("177 H3 r9 zones", "spatial demand representation"), ("Four-stage example", "saved generation, distribution and mode response"), ("17,522 loaded ODs", "largest accepted expanded static FW tier")], "docs/cases/boston.md"),
      "sioux_falls": ("Sioux Falls | benchmark outputs", [("528 static ODs", "supplied vehicle demand; 24 nodes / 76 links"), ("200 / 250 finite ODs", "distinct historical selected instances"), ("CG · Lagrangian · ADMM", "accepted bounded algorithm evidence")], "docs/cases/sioux-falls.md"),
    }
    title, fields, source = data[city]
    im=Image.new("RGB",(1200,650),"#f5f8fa")
    d=ImageDraw.Draw(im)
    d.rectangle((0,0,1200,95),fill=NAVY)
    d.text((42,23),title,font=font(42,True),fill="#ffffff")
    y=132
    for value,description in fields:
        d.rounded_rectangle((40,y,1160,y+140),radius=14,fill="#ffffff",outline="#c9dce2",width=2)
        d.text((68,y+20),value,font=font(34,True),fill="#087f8c")
        d.text((68,y+75),description,font=font(24),fill="#324e61")
        y+=158
    d.text((43,616),"Saved-result overview preview; see the case for scope and units.",font=font(19),fill="#587080")
    path=ASSET/f"{city}_core_outputs_preview.png"
    save_png(im,path)
    record={"city":city,"source_page":source,"source_page_sha256":sha(ROOT/source),"png_sha256":sha(path),"fields":[{"value":a,"meaning":b} for a,b in fields],"type":"authored saved-result preview; not a scientific figure","renderer":"tools/visuals/render_homepage_evidence_r1.py"}
    (ASSET/f"{city}_core_outputs_preview.source.json").write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8",newline="\n")
    return record

def relative_root_link(path: str) -> str:
    return path.replace("\\","/")

def evidence_cell(row: dict) -> str:
    page=relative_root_link(row["evidence_page"])
    summary=html.escape(row["result_summary"])
    status=html.escape(row["scope / status"])
    label=f'<span class="home-city-label">{html.escape(row["city"])}</span>'
    if not row["source_figure_or_data"]:
        return f'<td>{label}<span class="evidence-status">{status}</span><br>{summary} <a href="{html.escape(page)}">Scope and evidence</a></td>'
    thumb=relative_root_link(row["thumbnail"])
    source=relative_root_link(row["source_figure_or_data"])
    alt=html.escape(f'{row["city"]}: {row["subitem"]} saved-result preview; {row["result_summary"]}',quote=True)
    return f'<td>{label}<span class="evidence-status">{status}</span><br>{summary}<div class="evidence-thumbs"><a href="{html.escape(page)}"><img src="{html.escape(thumb)}" width="250" alt="{alt}"></a></div><small><a href="{html.escape(source)}">Original figure</a> · <a href="{html.escape(page)}">Specific evidence</a></small></td>'

def section_03(rows: list[dict]) -> str:
    grouped=defaultdict(dict)
    for row in rows:
        grouped[(row["module"],row["subitem"])][row["city"]]=row
    out=['<a id="coverage"></a>','## 03 / Case coverage and selected evidence','',
         'The cells show saved results and their actual instance scope. A thumbnail is a navigational preview; full units, numerical values and source records remain in the linked evidence. City-data, static BPR/Beckmann and finite fixed-cost hard-capacity results are separate branches. [Complete statistics](docs/capabilities.md#comparable-statistics).','']
    last=None
    for (module,subitem),cities in grouped.items():
        if module!=last:
            if last:out.append('</tbody></table>\n')
            out += [f'### {module}','', '<table class="home-coverage"><thead><tr><th>Component / output</th><th>Boston</th><th>Sioux Falls</th><th>Hong Kong</th></tr></thead><tbody>']
            last=module
        out.append('<tr><th scope="row">'+html.escape(subitem)+'</th>'+''.join(evidence_cell(cities[city]) for city in ("Boston","Sioux Falls","Hong Kong"))+'</tr>')
    out.append('</tbody></table>\n')
    out += ['<a id="cg-experiments"></a><a id="admm-r2"></a><a id="algorithm-b"></a><a id="distributed-assignment"></a>',
            'The [cross-case CG evidence](docs/methods/space-time-cg.md#cg-experiments), [ADMM](docs/methods/admm-space-time.md), [official tap-b Algorithm B method](docs/methods/origin-based-algorithm-b.md) and [adapter distinction](docs/integrations/taplab-tapb.md), and [Lagrangian records](docs/methods/distributed-assignment.md) retain their full figure families. Boston and Hong Kong have independent 10/10 pricing closure on **different** ten-demand graphs; this is not imputed to the historical Sioux runs.','']
    return '\n'.join(out)

CASES={
 "Boston": {"stem":"boston","cover":"docs/assets/boston/visual_release_r1/mcl_boston_hero.png","gmns":"docs/assets/boston/visual_release_r1/boston_network_zones.png","core":"docs/assets/homepage_evidence_r1/boston_core_outputs_preview.png","assignment":"docs/assets/boston/scalable_tool_r1/fw_all_flow.png","page":"docs/cases/boston.md","gmns_page":"docs/cases/boston.md#gmns-zones-and-source-evidence","core_page":"docs/cases/boston.md#demand-transit-and-observations","assignment_page":"docs/cases/boston-assignment.md#primary-scale-result-versus-controlled-method-comparison","role":"Real-city GMNS/demand/observation workflow; scalable static assignment and a distinct bounded finite holdout.","assignment_caption":"Expanded static FW all tier: 17,522 loaded node ODs; modeled PCE trips."},
 "Sioux Falls": {"stem":"sioux_falls","cover":"docs/assets/homepage_evidence_r1/sioux_falls_case_cover.png","gmns":"docs/assets/homepage_evidence_r1/sioux_falls_classic_topology.png","core":"docs/assets/homepage_evidence_r1/sioux_falls_core_outputs_preview.png","assignment":"docs/assets/algorithm_b_r21/presentation/sioux_fw_flow_compact.png","page":"docs/cases/sioux-falls.md","gmns_page":"docs/cases/sioux-falls.md#gmns-zones-and-source-evidence","core_page":"docs/cases/sioux-falls.md#scope-and-statistics","assignment_page":"docs/cases/sioux-algorithm-b.md","role":"Supplied 528-OD static benchmark and separate historical 200/250-OD finite cases; not a four-stage city compiler.","assignment_caption":"Classic static FW versus official tap-b Algorithm B: ID-matched 76-link flow parity, log10(1 + flow); supplied OD."},
 "Hong Kong": {"stem":"hong_kong","cover":"docs/assets/homepage_evidence_r1/hong_kong_case_cover.png","gmns":"docs/assets/hong_kong/full_stack_r5/r2r4_baseline/figures/hk_assignment_ready_network.png","core":"docs/assets/hong_kong/full_stack_r5/r2r4_baseline/figures/hk_full_stack_overview.png","assignment":"docs/assets/hong_kong/full_stack_r5/r2r4_baseline/figures/hk_static_fw_flow.png","page":"docs/cases/hong-kong.md","gmns_page":"docs/cases/hong-kong.md#gmns-zones-and-source-evidence","core_page":"docs/cases/hong-kong.md#scope-and-statistics","assignment_page":"docs/cases/hong-kong-static-assignment.md","role":"Bounded turn-aware GMNS/four-stage engineering scenario and separate accepted ten-OD finite CG case.","assignment_caption":"Turn-aware one-hour static FW, 723.191 modeled PCE; not observed traffic."},
}

def case_slot(title: str, path: str, page: str, caption: str, thumb: str) -> str:
    return f'<div class="case-slot"><h4>{html.escape(title)}</h4><a href="{html.escape(page)}"><img src="{html.escape(thumb)}" width="350" alt="{html.escape(caption,quote=True)}"></a><p>{html.escape(caption)} <a href="{html.escape(path)}">Original image</a> · <a href="{html.escape(page)}">Evidence</a></p></div>'

def section_04() -> str:
    out=['## 04 / Explore the three cases','', 'The same four positions organize each entrance; source scope and units remain city-specific. Covers are presentation assets, not scientific validation.','', '<div class="case-parity-grid">']
    for city,c in CASES.items():
        out.append(f'<article class="case-parity-card"><h3>{html.escape(city)}</h3><p>{html.escape(c["role"])} <a href="{c["page"]}">Open case</a></p>')
        slots=[('0 / Case cover',c['cover'],c['page'],f'{city} case cover; see case for the model and evidence scope.'),('1 / GMNS and model representation',c['gmns'],c['gmns_page'],f'{city} network and model representation; source geometry or schematic scope is documented in the case.'),('2 / Core outputs',c['core'],c['core_page'],f'{city} saved core-output overview; not interchangeable with the assignment-flow figure.'),('3 / Traffic assignment results',c['assignment'],c['assignment_page'],c['assignment_caption'])]
        for title,path,page,caption in slots:
            # Cover and core preview are purpose-built for the entry; other slots use
            # the same source-grounded full-image derivatives as Section 03.
            thumb='docs/assets/homepage_evidence_r1/case_'+c['stem']+'_'+re.sub(r'[^a-z0-9]+','_',title.lower()).strip('_')+'.png'
            out.append(case_slot(title,path,page,caption,thumb))
        out.append('</article>')
    out += ['</div>','',
      '<p><strong>Retained city-specific evidence.</strong> These original figures remain directly visible in addition to the common four-slot entrances; their scientific scope is not interchangeable.</p>',
      '<div class="case-specific-strip">',
      '<a href="docs/cases/boston.md#gmns-zones-and-source-evidence"><img src="docs/assets/boston/visual_release_r1/boston_network_zones.png" width="350" alt="Original Central Boston GMNS network and special zones"></a>',
      '<a href="docs/cases/sioux-space-time.md#from-time-expanded-flows-back-to-final-physical-link-movement-flow"><img src="docs/assets/benchmarks/sioux_200od_final_physical_link_flow.png" width="350" alt="Original Sioux historical 200-OD final physical-link movement flow"></a>',
      '<a href="docs/cases/hong-kong-space-time.md#from-the-physical-network-to-the-finite-time-expanded-graph"><img src="docs/assets/cg_layered_companions_r1/hong_kong_layered_space_time_construction.png" width="350" alt="Original Hong Kong model-generated approved HK10 77-arc layered construction"></a>',
      '</div>','',
      '<a id="boston"></a><a id="sioux-falls"></a><a id="hong-kong"></a><a id="hong-kong-cg-r5"></a>', '[All retained scientific figure families](docs/visualizations.md) · [Full technical walkthrough](docs/full-walkthrough.md).','']
    return '\n'.join(out)

def update_readme(rows: list[dict]) -> None:
    path=ROOT/'README.md'
    content=path.read_text(encoding='utf-8')
    start=content.index('<a id="coverage"></a>')
    end=content.index('<a id="run-your-input"></a>')
    rewritten=content[:start]+section_03(rows)+'\n'+section_04()+'\n'+content[end:]
    path.write_text(rewritten,encoding='utf-8',newline='\n')

def update_case_pages() -> None:
    for city,c in CASES.items():
        p=ROOT/c['page']
        content=p.read_text(encoding='utf-8')
        img=Path(c['cover']).name
        if c['cover'].startswith('docs/assets/'):
            link='../assets/'+c['cover'].removeprefix('docs/assets/')
        else: raise ValueError(c['cover'])
        block=f'<!-- CASE COVER R1 START -->\n![{city} case cover]({link})\n\n*Case-entry cover; saved results, scope and sources are detailed below.*\n<!-- CASE COVER R1 END -->\n\n'
        if '<!-- CASE COVER R1 START -->' in content:
            content=re.sub(r'<!-- CASE COVER R1 START -->.*?<!-- CASE COVER R1 END -->\n\n',block,content,count=1,flags=re.S)
        else:
            paragraph_end=content.find('\n\n',content.find('\n\n')+2)
            content=content[:paragraph_end+2]+block+content[paragraph_end+2:]
        p.write_text(content,encoding='utf-8',newline='\n')

def render() -> None:
    ASSET.mkdir(parents=True,exist_ok=True)
    topology=sioux_topology()
    with MAP.open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
    thumbs={}
    for row in rows:
        source=row['source_figure_or_data']
        if not source: continue
        if sha(ROOT/source)!=row['source_sha256']:raise RuntimeError(f'Source changed: {source}')
        target=row['thumbnail']
        if target not in thumbs:
            info=thumbnail(ROOT/source,ROOT/target)
            thumbs[target]={"source":source,"source_sha256":row['source_sha256'],"thumbnail_sha256":sha(ROOT/target),**info,"cities":[row['city']],"subitems":[row['subitem']],"evidence_pages":[row['evidence_page']]}
        else:
            for key,value in [('cities',row['city']),('subitems',row['subitem']),('evidence_pages',row['evidence_page'])]:
                if value not in thumbs[target][key]:thumbs[target][key].append(value)
    covers={city:cover(city) for city in ('sioux_falls','hong_kong')}
    cards={city:summary_card(city) for city in ('boston','sioux_falls')}
    for city,c in CASES.items():
        for title,path,page in [('0 / Case cover',c['cover'],c['page']),('1 / GMNS and model representation',c['gmns'],c['gmns_page']),('2 / Core outputs',c['core'],c['core_page']),('3 / Traffic assignment results',c['assignment'],c['assignment_page'])]:
            target='docs/assets/homepage_evidence_r1/case_'+c['stem']+'_'+re.sub(r'[^a-z0-9]+','_',title.lower()).strip('_')+'.png'
            info=thumbnail(ROOT/path,ROOT/target,(500,167) if title.startswith('0 /') else (500,290))
            thumbs[target]={"source":path,"source_sha256":sha(ROOT/path),"thumbnail_sha256":sha(ROOT/target),**info,"cities":[city],"subitems":[title],"evidence_pages":[page]}
    manifest={"version":"homepage-evidence-r1","renderer":"tools/visuals/render_homepage_evidence_r1.py","map":"tools/visuals/homepage_evidence_r1_map.csv","thumbnails":thumbs,"covers":covers,"core_cards":cards,"sioux_classic_topology":topology,"scientific_solver_rerun":False}
    (ASSET/'THUMBNAIL_SOURCE_MANIFEST.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
    update_readme(rows)
    update_case_pages()
    print(f'Rendered {len(thumbs)} unique thumbnails, 2 covers and 2 saved-result cards')

if __name__=='__main__':render()
