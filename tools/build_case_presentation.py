#!/usr/bin/env python3
"""Render only the framework/case presentation pages from the root README and case sources.
No model, routing, pricing or network operation is called.
Run after the existing complete documentation build to keep this layout in sync.
"""
from pathlib import Path
import re,html,json,hashlib
from urllib.parse import urlsplit
from markdown_it import MarkdownIt
from bs4 import BeautifulSoup

def main(argv=None):
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    S=Path(__file__).resolve().parents[1]
    CSS='''
    :root{--ink:#142e43;--muted:#587080;--teal:#087f8c;--line:#d6e1e7;--soft:#f1f6f8;--navy:#142d43;--mint:#58c7b4}*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:84px}body{margin:0;background:#fff;color:var(--ink);font:16px/1.72 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}a{color:var(--teal);text-decoration:none}a:hover{text-decoration:underline}header{border-bottom:1px solid var(--line);background:#fff}.mast{max-width:1260px;margin:auto;padding:22px 34px;display:flex;align-items:center;justify-content:space-between;gap:25px}.brand{font-weight:800;letter-spacing:-.02em;font-size:22px;color:var(--ink)}.brand small{display:block;font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);font-weight:500}.nav{position:sticky;top:0;z-index:8;background:rgba(255,255,255,.97);border-bottom:1px solid var(--line)}.nav div{max-width:1260px;padding:12px 34px;margin:auto;display:flex;gap:25px;overflow-x:auto;white-space:nowrap;font-size:13px;font-weight:650}.mcl-page{max-width:1250px;margin:auto;padding:35px 34px 80px}.mcl-page>p:first-child{margin:0 0 25px}.mcl-page h1{font-size:44px;letter-spacing:-.05em;line-height:1.18;margin:28px 0 22px}.mcl-page h2{font-size:35px;letter-spacing:-.035em;line-height:1.25;margin:75px -22px 28px;padding:25px 22px;border-top:3px solid var(--teal);background:var(--soft)}.mcl-page h3{font-size:25px;line-height:1.35;letter-spacing:-.02em;margin-top:39px;margin-bottom:17px}.mcl-page h4{font-size:19px;margin-top:28px}.mcl-page p{margin:15px 0;color:#324e61}.mcl-page strong{color:var(--ink)}.mcl-page img{max-width:100%;height:auto;vertical-align:middle}.mcl-page p[align="center"]{margin:27px 0}.mcl-page p[align="center"] img{border:1px solid var(--line);border-radius:10px}.mcl-page table{border-collapse:separate;border-spacing:0;width:100%;margin:25px 0 29px;border:1px solid var(--line);border-radius:9px;overflow:hidden;font-size:14px}.mcl-page th{background:var(--navy);color:#fff;text-align:left;line-height:1.4;font-weight:650;padding:15px}.mcl-page th strong{color:white}.mcl-page td{padding:14px 15px;vertical-align:top;border-top:1px solid var(--line)}.mcl-page td+td,.mcl-page th+th{border-left:1px solid var(--line)}.mcl-page tr:nth-child(2n+1) td{background:#f8fafb}.mcl-page table.figure-grid td,.mcl-page table:has(img) td{padding:12px}.mcl-page table img{display:block;width:100%;height:auto}.mcl-page .table-scroll{overflow-x:auto}.mcl-page pre{background:#152d41;color:#e2edf4;padding:23px 25px;border-radius:10px;overflow:auto;font-size:13px;line-height:1.65;margin:22px 0}.mcl-page pre code{background:none;color:inherit;word-break:normal}.mcl-page code{font-family:Consolas,monospace;font-size:.88em;padding:2px 4px;background:#eef4f7;color:#2f576f;overflow-wrap:anywhere}.mcl-page small{font-size:12px;color:var(--muted)}.mcl-page blockquote{border-left:4px solid var(--teal);padding:2px 22px;margin:25px 0;background:var(--soft)}.mcl-page ul{padding-left:24px}.mcl-page li{margin-bottom:7px}.mcl-page a[id]{display:block;scroll-margin-top:80px}.mcl-page hr{border:0;border-top:1px solid var(--line);margin:40px 0}.mcl-page .section-label{font-size:12px;text-transform:uppercase;letter-spacing:.14em;color:var(--teal)}footer{max-width:1250px;margin:auto;padding:25px 34px 50px;font-size:12px;color:var(--muted);border-top:1px solid var(--line)}@media(max-width:760px){.mcl-page p:has(img[src*="population_allocation"]){overflow-x:auto}.mcl-page img[src*="population_allocation"]{max-width:none;width:900px}.mast{padding:17px 20px}.brand{font-size:18px}.mast>a{font-size:13px}.nav div{padding:10px 18px;gap:20px}.mcl-page{padding:22px 18px 50px}.mcl-page h1{font-size:34px}.mcl-page h2{font-size:28px;margin:50px -7px 25px;padding:20px 9px}.mcl-page h3{font-size:23px}.mcl-page p{font-size:15px}.mcl-page table{font-size:12px;min-width:560px}.mcl-page table:has(img){min-width:520px}.mcl-page th,.mcl-page td{padding:10px}.mcl-page .table-scroll{margin:0 -2px}.mcl-page pre{padding:18px;font-size:12px}.mcl-page p[align="center"] img{border-radius:5px}footer{padding:22px 20px}}
    '''
    CSS += '\n@media(max-width:760px){.boston-admm-page .mcl-page table:not(:has(img)){min-width:0;table-layout:fixed;font-size:11px}.boston-admm-page .mcl-page table:not(:has(img)) th:first-child,.boston-admm-page .mcl-page table:not(:has(img)) td:first-child{width:57%}.boston-admm-page .mcl-page table:not(:has(img)) th:last-child,.boston-admm-page .mcl-page table:not(:has(img)) td:last-child{white-space:nowrap}}\n'
    CSS='\n'.join(line.rstrip() for line in CSS.splitlines())+'\n'
    (S/'docs/assets/presentation-r3.css').write_text(CSS,encoding='utf-8')
    MD=MarkdownIt('commonmark',{'html':True}).enable('table')
    def slug(s):return re.sub(r'\s+','-',re.sub(r'[^\w\s-]','',s.strip().lower()))
    def content(path,isroot=False):
     text=path.read_text(encoding='utf-8');out=BeautifulSoup(MD.render(text),'html.parser')
     used={x.get('id') for x in out.find_all(id=True)}
     for h in out.find_all(re.compile('^h[1-6]$')):
      a=slug(h.get_text());key=a;i=1
      while key in used:key=f'{a}-{i}';i+=1
      h['id']=key;used.add(key)
     for tag in out.find_all(['img','a']):
      attr='src' if tag.name=='img' else 'href';raw=tag.get(attr,'')
      if not raw or raw.startswith(('#','http:','https:','mailto:','data:')):continue
      file,sep,frag=raw.partition('#')
      if isroot:
       file=file[5:] if file.startswith('docs/') else '../'+file
      if file.endswith('.md'):
       # Serve docs Markdown as generated HTML; source/example Markdown remains repository link.
       absfile=(S/'docs'/file).resolve() if isroot else (path.parent/file).resolve()
       if absfile.is_relative_to((S/'docs').resolve()):file=file[:-3]+'.html'
       else:
        try:rel=absfile.relative_to(S.resolve()).as_posix();file='https://github.com/scholarhaozheng/mobility-network-lab/blob/main/'+rel
        except ValueError:pass
      tag[attr]=file+(sep+frag if sep else '')
     for table in out.find_all('table'):
      div=out.new_tag('div',attrs={'class':'table-scroll'});table.wrap(div)
     return str(out)
    def shell(body,title,depth=0):
     prefix='../'*depth
     page_class=' class="boston-admm-page"' if title.startswith('Boston ADMM R2') else ''
     return '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(title)+' · Mobility Computation Lab</title><link rel="stylesheet" href="'+prefix+'assets/presentation-r3.css"></head><body'+page_class+'><header><div class="mast"><a class="brand" href="'+prefix+'index.html">Mobility Computation Lab<small>GMNS · demand · observation · computation</small></a><a href="https://github.com/scholarhaozheng/mobility-network-lab">Source repository ↗</a></div></header><nav class="nav"><div><a href="'+prefix+'index.html#framework">Shared framework</a><a href="'+prefix+'index.html#cg-experiments">CG experiments</a><a href="'+prefix+'index.html#admm-r2">ADMM R2</a><a href="'+prefix+'index.html#coverage">Case coverage</a><a href="'+prefix+'index.html#boston">Boston</a><a href="'+prefix+'index.html#sioux-falls">Sioux Falls</a><a href="'+prefix+'index.html#run-your-input">Use the tool</a><a href="'+prefix+'index.html#mobility-data-support">Open data</a></div></nav><main class="mcl-page">'+body+'</main><footer>Source-qualified computational examples. Numerical approximation, evidence linkage and empirical validation are distinct. See each case for its exact scope, units and provenance.</footer></body></html>'
    home=content(S/'README.md',True)
    # This is a deliberate source file: the existing complete site build can render it without a second narrative.
    (S/'docs/index.md').write_text('<!-- Homepage content derived from the root README by tools/build_case_presentation.py. -->\n'+home+'\n',encoding='utf-8')
    (S/'docs/index.html').write_text(shell(home,'Framework and cases'),encoding='utf-8')
    files=['docs/capabilities.md','docs/cases/boston.md','docs/cases/boston-assignment.md','docs/cases/boston-space-time.md','docs/cases/boston-admm.md','docs/cases/boston-algorithm-b.md','docs/cases/sioux-falls.md','docs/cases/sioux-space-time.md','docs/cases/sioux-admm.md','docs/cases/sioux-algorithm-b.md','docs/methods/space-time-cg.md','docs/methods/admm-space-time.md','docs/methods/origin-based-algorithm-b.md','docs/integrations/taplab-tapb.md','docs/RUN_YOUR_OWN_GMNS.md','docs/BOSTON_SCALE_RESULTS.md','docs/SCALABLE_TOOL_DATA_NOTICE.md','docs/datasets/boston-population-households.md','docs/datasets/boston-behavior-feedback.md','docs/datasets/boston-four-step-sources.md','docs/datasets/boston-visual-sources.md']
    for f in files:
     p=S/f; depth=len(p.relative_to(S/'docs').parts)-1
     body=content(p);title=next(x.content for x in MD.parse(p.read_text(encoding='utf-8')) if x.type=='inline')
     p.with_suffix('.html').write_text(shell(body,title,depth),encoding='utf-8')
    print('Generated',1+len(files),'pages')
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
