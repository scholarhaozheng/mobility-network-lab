"""Export the approved homepage as a GitHub-compatible, fully expanded README.

The website is the content source. This exporter changes presentation only:
HTML tables replace CSS galleries, both Sioux scales are visible, and JS-added
reproduction links are emitted explicitly. No scientific figure is copied.
"""
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from copy import deepcopy
import argparse, html, json, re
from bs4 import BeautifulSoup, NavigableString, Tag
ROOT=Path(__file__).resolve().parents[1]
SITE='https://scholarhaozheng.github.io/mobility-network-lab/'
SOURCE=ROOT/'docs/index.html'

def url(value, image=False):
    if not value:return value
    if value.startswith('#'):return value
    parsed=urlsplit(value)
    if parsed.scheme or parsed.netloc:return value
    if image:return 'docs/'+value
    return urljoin(SITE,value)

def esc(value):return html.escape(str(value),quote=True)
def anchor(value):return '<a id="'+esc(value)+'"></a>\n\n' if value else ''

def inline(node):
    if isinstance(node,NavigableString):return str(node)
    text=''.join(inline(c) for c in node.children)
    if node.name=='a':
        return ('['+text+']('+url(node['href'])+')') if node.get('href') else ('<a id="'+esc(node['id'])+'"></a>' if node.get('id') else text)
    if node.name in ('strong','b'):return '**'+text+'**'
    if node.name in ('em','i'):return '*'+text+'*'
    if node.name=='code':return chr(96)+node.get_text()+chr(96)
    if node.name=='br':return '  \n'
    if node.name=='img':return '!['+node.get('alt','')+']('+url(node['src'],True)+')'
    return text

def clean(node):
    node=deepcopy(node)
    for t in [node]+list(node.find_all(True)):
        if t.attrs is None:continue
        if t.name in ('script','button','colgroup','col'):
            t.decompose();continue
        attrs={k:v for k,v in t.attrs.items() if k in ('href','src','alt','title','id','colspan','rowspan','align','valign','width','height','open')}
        if 'href' in attrs:attrs['href']=url(attrs['href'])
        if 'src' in attrs:attrs['src']=url(attrs['src'],True)
        t.attrs=attrs
        if t.name in ('td','th'):t['valign']='top'
        if t.name=='figure':t.name='div'
        if t.name=='figcaption':t.name='p'
        if t.name=='small':t.name='span'
    return node

def table(node):
    node=deepcopy(node)
    if 'coverage-matrix' in node.get('class',[]):
        for label in node.select('th > span, th > small'):label.insert_after(' · ')
    t=clean(node);t['width']='100%'
    for row in t.find_all('tr'):
        cells=row.find_all(['th','td'],recursive=False)
        cols=sum(int(c.get('colspan',1)) for c in cells)
        for c in cells:c['width']=str(round(100*int(c.get('colspan',1))/max(cols,1)))+'%'
    return str(t)+'\n\n'

def image_cell(card,columns):
    images=card.select('.atlas-image img')
    # Give every figure its original aspect ratio. Table rows align their tops
    # and place all following descriptions at a common vertical position.
    maxw={1:850,2:405,3:265,4:193}[columns]
    if len(images)>1:maxw=maxw//len(images)-12
    result=[]
    for im in images:
        w=float(im.get('width',1000));h=float(im.get('height',600))
        scale=min(maxw/w,(360 if columns==1 else 280)/h,1)
        link=im.find_parent('a');image='<img src="'+esc(url(im['src'],True))+'" alt="'+esc(im.get('alt',''))+'" width="'+str(max(1,round(w*scale)))+'" height="'+str(max(1,round(h*scale)))+'"/>'
        if link:image='<a href="'+esc(url(link['href']))+'">'+image+'</a>'
        result.append(image)
    if len(result)==1:return result[0]
    return '<table><tr>'+''.join('<td valign="top" width="'+str(round(100/len(result)))+'%">'+x+'</td>' for x in result)+'</tr></table>'

class Exporter:
    def __init__(self,soup,labels):self.soup=soup;self.labels=labels;self.gallery_count=0;self.card_ids=[]
    def gallery(self,gallery,label=None):
        self.gallery_count+=1
        cards=gallery.find_all(class_='atlas-card',recursive=False)
        stage=gallery.find_parent(class_='atlas-stage')
        is_hk_transit=stage and stage.get('data-stage')=='hong-kong-transit'
        cols=4 if is_hk_transit else int(gallery.get('data-columns',min(3,len(cards))))
        out=['<table width="100%">']
        if label:out.append('<tr><th colspan="'+str(cols)+'" align="left">'+esc(label)+'</th></tr>')
        for start in range(0,len(cards),cols):
            row=cards[start:start+cols];rows=[[],[],[],[]]
            for card in row:
                cid=card['data-figure'];self.card_ids.append(cid)
                title=card.find('h5',recursive=False)
                ids=[card.get('id')]+[a.get('id') for a in card.find_all('a',recursive=False) if a.get('id')]
                rows[0].append(''.join('<a id="'+esc(x)+'"></a>' for x in ids if x)+'<strong>'+esc(title.get_text(' ',strip=True))+'</strong>')
                rows[1].append(image_cell(card,cols))
                description=[];links=[]
                for child in card.find_all(recursive=False):
                    if child is title or (child.name=='a' and not child.get('href')):continue
                    cl=child.get('class',[])
                    if 'atlas-image' in cl:
                        description.extend(str(clean(c)) for c in child.select('figcaption'))
                        continue
                    # A two-image companion uses a wrapper with figcaptions.
                    if child.select('.atlas-image'):
                        description.extend(str(clean(c)) for c in child.select('figcaption'))
                        continue
                    if 'atlas-final-links' in cl or 'atlas-source-records' in cl:links.append(deepcopy(child))
                    else:description.append(str(clean(child)))
                repro_found=any(x.select('[data-reproduction-entry]') for x in links)
                if cid in self.labels and not repro_found:
                    p=self.soup.new_tag('p');a=self.soup.new_tag('a',href='reproduce.html?figure='+cid);a.string=self.labels[cid];p.append(a);links.append(p)
                rows[2].append(''.join(description))
                # Compact the label, not the frozen target, of long source URLs.
                for part in links:
                    for a in part.select('details a'):
                        path=a.get_text(strip=True)
                        if '/' in path:a['title']=path;a.string=path.split('/')[-1]
                rows[3].append(''.join(str(clean(x)) for x in links))
            for ri,contents in enumerate(rows):
                tag='th' if ri==0 else 'td'
                cells=['<'+tag+' width="'+str(round(100/cols))+'%" valign="top" align="left">'+value+'</'+tag+'>' for value in contents]
                if len(row)<cols:cells.append('<td colspan="'+str(cols-len(row))+'" width="'+str(round(100*(cols-len(row))/cols))+'%"></td>')
                out.append('<tr>'+''.join(cells)+'</tr>')
        return '\n'.join(out+['</table>'])+'\n\n'
    def sioux_finite(self,stage):
        panels=stage.select('.sioux-instance-panel');out=[anchor(stage.get('id'))]
        for child in stage.find_all(recursive=False):
            if child.select('.sioux-instance-panel') or child in panels or 'sioux-instance' in ' '.join(child.get('class',[])):continue
            if child.name=='button':continue
            out.append(self.render(child))
        out.append('Both selected instances are shown below: each method has a separate **200-OD row** and **250-OD row**. Their inputs, results and reference LPs remain separate.\n\n')
        blocks=[]
        for panel in panels:
            groups=[];group=[]
            for child in panel.find_all(recursive=False):
                if child.name=='h5' and group:groups.append(group);group=[]
                group.append(child)
            if group:groups.append(group)
            blocks.append((panel['data-sioux-od'],groups))
        for i in range(3):
            heading=blocks[0][1][i][0]
            out.append('##### '+inline(heading)+'\n\n')
            for scale,groups in blocks:
                group=groups[i]
                out.append(anchor(group[0].get('id')))
                for child in group[1:]:
                    if 'atlas-gallery' in child.get('class',[]):out.append(self.gallery(child,scale+' ODs'))
                    else:out.append(self.render(child))
        return ''.join(out)
    def framework(self,node):
        """Keep the opening's linked diagram readable without website CSS."""
        def link(element,label):
            return '<a href="'+esc(url(element['href']))+'">'+esc(label)+'</a>'
        def item(element,number=None):
            title=element.find('strong').get_text(' ',strip=True)
            if number:title=number+' / '+title
            detail=element.find('small')
            return '<strong>'+link(element,title)+'</strong>'+('<br/>'+esc(detail.get_text(' ',strip=True)) if detail else '')
        foundation=node.select_one('.scope-flow-foundation')
        out=['<table width="100%">',
             '<tr><th colspan="3" align="left">'+esc(node.select_one('.scope-flow-kicker').get_text(' ',strip=True))+'</th></tr>',
             '<tr><td colspan="3">'+item(foundation)+'</td></tr>',
             '<tr><td colspan="3"><strong>'+esc(node.select_one('.scope-flow-label').get_text(' ',strip=True))+'</strong></td></tr>']
        out.append('<tr>'+''.join('<td width="33%" valign="top">'+item(a,a.find('b').get_text(strip=True))+'</td>' for a in node.select('.scope-flow-demand a'))+'</tr>')
        assignment=node.select_one('.scope-flow-assignment-head')
        heading=assignment.find('h3')
        out.append('<tr><th colspan="3" align="left">'+anchor(heading.get('id')).strip()+link(assignment,assignment.find('b').get_text(strip=True)+' / '+heading.get_text(' ',strip=True))+'</th></tr>')
        contracts=[]
        for a in node.select('.scope-flow-contracts > a'):
            contracts.append('<td width="50%" valign="top">'+esc(a.select_one('.scope-flow-mini').get_text(' ',strip=True))+'<br/>'+item(a)+'</td>')
        out.append('<tr><td colspan="3"><table width="100%"><tr>'+''.join(contracts)+'</tr></table></td></tr>')
        layers=node.select('.scope-flow-depth > a')
        rows=['<tr>'+''.join('<td width="50%" valign="top">'+item(a,a.find('b').get_text(strip=True))+'</td>' for a in layers[i:i+2])+'</tr>' for i in range(0,len(layers),2)]
        out.append('<tr><td colspan="3"><table width="100%">'+''.join(rows)+'</table></td></tr>')
        more=node.select_one('.scope-flow-more')
        out.append('<tr><td colspan="3">'+link(more,more.get_text(' ',strip=True))+'</td></tr>')
        return '\n'.join(out+['</table>'])+'\n\n'

    def render(self,node):
        if isinstance(node,NavigableString):return ''
        cls=node.get('class',[])
        if 'scope-flow' in cls:return self.framework(node)
        if node.name in ('script','button') or node.get('id') in ('atlas-view-controls','atlas-compact-panel'):return ''
        if 'atlas-stage-prose' in cls or 'atlas-evidence-note' in cls:return str(clean(node))+'\n\n'
        if 'case-atlas' in cls:return ''.join(self.render(c) for c in node.children)
        if 'atlas-gallery' in cls:return self.gallery(node)
        if 'atlas-stage' in cls and node.get('data-stage')=='sioux-falls-finite':return self.sioux_finite(node)
        if 'project-structure-map' in cls:
            im=node.find('img');out='[!['+im.get('alt','')+']('+url(im['src'],True)+')]('+SITE+'assets/atlas/project-map.svg)\n\n'
            out+='Open the [clickable project map]('+SITE+'assets/atlas/project-map.svg), or use the same module links below.\n\n<table width="100%">\n<tr><th colspan="4" align="left">Project modules and reading destinations</th></tr>\n'
            links=node.select('a.project-map-link')
            for i in range(0,len(links),4):
                row=links[i:i+4];out+='<tr>'+''.join('<td width="25%" valign="top"><a href="'+esc(url(a['href']))+'">'+esc(a.get('title') or a.get_text(' ',strip=True))+'</a></td>' for a in row)
                if len(row)<4:out+='<td colspan="'+str(4-len(row))+'"></td>'
                out+='</tr>\n'
            return out+'</table>\n\n'
        if node.get('id')=='project-map-help':return '[Full-size SVG]('+SITE+'assets/atlas/project-map.svg) · [PNG](docs/assets/atlas/figures/g-f001.png) · [Accessible module and source table]('+SITE+'volumes/overview.html#src-docs-architecture-document).\n\n'
        if node.name=='table':return table(node)
        if node.name in ('h1','h2','h3','h4','h5','h6'):
            return anchor(node.get('id'))+'#'*int(node.name[1])+' '+inline(node).strip()+'\n\n'
        if node.name=='p':return (anchor(node.get('id'))+inline(node).strip()+'\n\n') if inline(node).strip() else ''
        if node.name=='a' and node.get('id'):return anchor(node['id'])
        if node.name in ('ul','ol'):
            return ''.join(('- ' if node.name=='ul' else str(i+1)+'. ')+(('<a id="'+esc(x['id'])+'"></a>') if x.get('id') else '')+inline(x).strip()+'\n' for i,x in enumerate(node.find_all('li',recursive=False)))+'\n'
        if node.name=='pre':return '~~~bash\n'+node.get_text().strip()+'\n~~~\n\n'
        if node.name=='details':return str(clean(node))+'\n\n'
        return ''.join(self.render(c) for c in node.children)

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--check',action='store_true');a=ap.parse_args()
    soup=BeautifulSoup(SOURCE.read_text(encoding='utf8'),'html.parser')
    js=(ROOT/'docs/assets/reproduction/entries.js').read_text(encoding='utf8')
    labels=json.loads(re.search(r'labels=(\{.*?\});for',js).group(1))
    exporter=Exporter(soup,labels);parts=[]
    children=[]
    for child in soup.select_one('main').children:
        if isinstance(child,Tag) and 'homepage-opening' in child.get('class',[]):
            children.extend(child.select_one('.opening-head').children)
            children.extend(child.select_one('.opening-prose').children)
            children.append(child.select_one('.scope-flow'))
        else:children.append(child)
    for child in children:
        parts.append(exporter.render(child))
        if isinstance(child,Tag) and child.name=='h1':
            parts.append('**Project website: ['+SITE+']('+SITE+')**\n\n')
            parts.append('[Overview]('+SITE+'volumes/overview.html) · [Boston]('+SITE+'volumes/boston.html) · [Sioux Falls]('+SITE+'volumes/sioux-falls.html) · [Hong Kong]('+SITE+'volumes/hong-kong.html) · [Reproduction guide]('+SITE+'reproduction.html) · [Experiment catalog]('+SITE+'reproduce.html)\n\n')
            parts.append('[01 Contributions](#01-what-this-project-adds) · [02 Project structure](#02-complete-project-structure) · [03 Coverage](#03-case-coverage-and-selected-evidence) · [04 City atlas](#04-explore-the-three-cases) · [05 Run and inspect](#05-run-and-inspect) · [06 Attribution](#06-attribution-scope-and-further-reading)\n\n')
        if isinstance(child,Tag) and child.get('id')=='04-explore-the-three-cases':
            parts.append('This README shows the complete static atlas in the same city, stage and method groups as the website. The [website atlas]('+SITE+'#04-explore-the-three-cases) also offers city and stage views. Both Sioux Falls OD scales are expanded here.\n\n')
        if isinstance(child,Tag) and child.get('id')=='05-run-and-inspect':
            parts.append('[Computational quickstart](REPRODUCTION_QUICKSTART.md) · [Experiment registry](experiments/README.md) · [Download the computational checkout]('+SITE+'downloads/computational-checkout.zip)\n\n')
            parts.append('Boston S1/S2 recipes rerun the assignment stage only. Saved-output checks verify released files; prepared-input reruns cover their declared stages. Independent full-DAG pricing closure remains open for the historical Sioux CG result.\n\n')
            parts.append('Choose an exact instance in the [Experiment catalog]('+SITE+'reproduce.html), then follow its Download, Environment, Run and Verify steps. The page supplies the matching command and required environment. The [static catalog]('+SITE+'reproduction/experiment-catalog.html) remains available without JavaScript. Historical inspection and fresh computation have separate status labels and receipts.\n\n')
            parts.append('<details><summary>Advanced: command-line registry reference</summary>\n\nThe experiment page selects the matching command for you. To inspect the two preserved registries directly:\n\n~~~bash\npython -B tools/mcl_reproduce.py list\npython -B tools/mcl_recovered.py list\n~~~\n\n</details>\n\n')
    output=''.join(parts).replace('\r\n','\n')
    expected=[c['data-figure'] for c in soup.select('#atlas-full-panel .atlas-card')]
    if len(exporter.card_ids)!=len(expected) or set(exporter.card_ids)!=set(expected):raise ValueError('Card loss or duplication during README export')
    destination=ROOT/'README.md'
    if a.check:
        if destination.read_text(encoding='utf8')!=output:raise ValueError('README is not synchronized with the homepage exporter')
    else:destination.write_bytes(output.encode('utf8'))
    print(json.dumps({'status':'PASS','cards':len(expected),'mainImages':len(soup.select('.atlas-image img')),'galleries':exporter.gallery_count,'bytes':len(output.encode('utf8')),'bothSiouxScalesExpanded':True,'homepageModified':False}))
if __name__=='__main__':main()
