"""Pure-render current project structure; no numerical solver or network access.
Run from the repository root: python tools/figures/project_structure.py
"""
from pathlib import Path
import json,re,sys,xml.etree.ElementTree as ET
import matplotlib.patches as patches
try:
    from .style import new_figure,export_figure,sha256,INK,TEAL,BLUE,REPO
except ImportError:
    from style import new_figure,export_figure,sha256,INK,TEAL,BLUE,REPO

OUT=REPO/'docs/assets/figure-contract-r11/project-structure'
ORDER=['boston','hong-kong','ann-arbor','urbana-champaign','ithaca','berkeley','chicago','pittsburgh','sioux-falls']
NAMES=['Boston','Hong Kong','Ann Arbor','Urbana–Champaign','Ithaca','Berkeley','Chicago','Pittsburgh','Sioux Falls']
W,H=880,1108
BASE='volumes/overview.html#'
STAGES=lambda n:BASE+'coverage-stage-'+str(n).zfill(2)

def render():
    fig=new_figure('shared','Complete project structure',figsize=(12.6,16.0))
    ax=fig.add_axes([.065,.035,.9,.865]);ax.set_xlim(0,W);ax.set_ylim(H,0);ax.set_axis_off()
    rects=[];text_checks=[]
    def label(text,x,y,size=9,weight='normal',color=INK,ha='left'):
        return ax.text(x,y,text,fontsize=size,fontweight=weight,color=color,ha=ha,va='top',linespacing=1.35)
    def section(text,y):label(text.upper(),0,y,10.4,'bold',TEAL)
    def card(key,title,lines,x,y,w,h,href,size=9.7,body=8.7):
        p=patches.FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0,rounding_size=4',facecolor='#f4f8f9',edgecolor='#c9dbe0',linewidth=.65)
        p.set_gid('hotspot-'+key);ax.add_patch(p)
        ax.plot([x+11,x+w-11],[y+7,y+7],color=TEAL,lw=1.05)
        ts=[label(title,x+11,y+14,size,'bold')]
        if lines:ts.append(label('\n'.join(lines),x+11,y+33,body))
        rects.append({'id':key,'label':title,'href':href,'model_box':[x,y,w,h],'patch':p})
        text_checks.append((key,p,ts))
        return p
    cols4=[0,224,448,672];cw=208
    section('Source evidence',0)
    for i,(key,title,line,url)in enumerate([
      ('roads','Roads, boundaries, zones','Network geography records',STAGES(1)),
      ('people','People and activity','Households, population, proxies',STAGES(3)),
      ('transit','Transit and walking','GTFS, fares, service and access',STAGES(4)),
      ('observations','Observation records','GPS, trajectories, detectors',STAGES(5))]):
        card(key,title,[line],cols4[i],18,cw,58,url)
    section('Model representation and upstream preparation',94)
    for i,(key,title,lines,url)in enumerate([
      ('gmns','GMNS representation',['Directed physical links','Hierarchy, centroids, access','Source IDs, units and turns'],BASE+'src-docs-data-contract-document'),
      ('demand','City demand preparation',['Statistics and boundaries','Separate activity attributes','Version / geography checks'],STAGES(6)),
      ('declared-od','Declared vehicle OD',['Supplied demand may enter','static assignment directly','No demographic compiler'],'volumes/sioux-falls.html#coverage-row-01'),
      ('association','Observation association',['Match/associate links and service','Optional input or diagnostics','Not automatic OD or calibration'],STAGES(5))]):
        card(key,title,lines,cols4[i],112,cw,83,url)
    section('Four-stage travel-demand workflow',213)
    for i,(key,title,lines,url)in enumerate([
      ('generation','01 / Trip generation',['Activities → productions and attractions'],STAGES(6)),
      ('distribution','02 / Trip distribution',['Margins + impedance','→ person origin–destination'],STAGES(7)),
      ('mode','03 / Mode choice',['Costs + declared choice model','→ mode-specific demand'],STAGES(8))]):
        card(key,title,lines,i*299,231,282,74,url,size=10.4,body=9)
    for x in [282,581]:ax.annotate('',xy=(x+15,268),xytext=(x+2,268),arrowprops={'arrowstyle':'-|>','color':TEAL,'lw':.8})
    ax.annotate('',xy=(739,327),xytext=(739,309),arrowprops={'arrowstyle':'-|>','color':TEAL,'lw':.8})
    outer=patches.FancyBboxPatch((0,330),880,283,boxstyle='round,pad=0,rounding_size=5',facecolor='white',edgecolor=BLUE,lw=1.05);outer.set_gid('hotspot-assignment');ax.add_patch(outer)
    rects.append({'id':'assignment','label':'04 / Traffic assignment','href':STAGES(9),'model_box':[0,330,880,30],'patch':outer,'overlay_header_only':True})
    label('04 / Traffic assignment',14,341,11.4,'bold');label('Vehicle demand → network flows',866,344,9,ha='right')
    label('FOUR INTERNAL ASSIGNMENT LAYERS',14,377,9.5,'bold',TEAL)
    for i,(key,title,lines)in enumerate([
      ('a','A / Native assignment',['Reference solvers','and reconstruction']),
      ('b','B / Decomposition',['Distributed methods','and subproblems']),
      ('c','C / Spatial hierarchy',['Representation','and access / turn states']),
      ('d','D / Coordination',['Shared capacities','and verification'])]):
        card('layer-'+key,title,lines,14+i*218,396,198,69,'#assignment-layer-'+key,size=9.6,body=8.7)
    label('TWO INDEPENDENT MATHEMATICAL CONTRACTS',14,484,9.5,'bold',TEAL)
    card('static','Static road assignment',[
      'BPR / Beckmann; period-specific vehicle OD',
      'Frank–Wolfe · official tap-b Algorithm B; adapters vary',
      'Finite-path reference · native L3 diagnostics',
      'Physical-link flows and original-space checks'],14,502,420,95,BASE+'src-docs-methods-document-static-frankwolfe-reference-implementation',size=10.4,body=8.8)
    card('finite','Finite time-expanded optimization',[
      'Separately selected graph, OD, time and capacities',
      'Fixed arc costs · shared hard capacity',
      'Arc-flow LP · two-phase CG · Lagrangian · ADMM',
      'Movement-flow reconstruction and feasibility checks'],446,502,420,95,BASE+'src-docs-methods-space-time-cg-document',size=10.4,body=8.8)
    section('Saved outputs and independent checks',635)
    card('outputs','Saved outputs and independent checks',[
      'Zonal / mode demand · generated columns · physical-link flows · CSV / SQLite · figures',
      'Units, conservation, objective / gap and provenance checks are specific to each instance.'],0,653,880,62,BASE+'src-docs-outputs-document',size=10.2,body=9)
    section('Real-city cases / one comparison framework',738)
    summaries=[
      ['City demand and static scales','Separate bounded finite cases'],
      ['Turn-aware city demand','Separate static and finite cases'],
      ['25-zone morning city model','S600 static; finite unsolved'],
      ['21-zone morning city model','S72 static; separate T4'],
      ['11-zone midday activity model','S110 static; separate T4'],
      ['13-zone morning city model','S72 static; separate T4'],
      ['5-zone morning city model','S20 static; separate T4'],
      ['41-group morning city model','S72 static; separate T4']]
    for i,(slug,name,lines)in enumerate(zip(ORDER[:8],NAMES[:8],summaries)):
        card('city-'+slug,name,lines,cols4[i%4],758+(i//4)*80,cw,67,'volumes/'+slug+'.html',size=10.1,body=8.7)
    section('Demonstration benchmark',927)
    card('city-sioux-falls','Sioux Falls',['Supplied-OD static benchmark · separate historical selected 200 / 250-OD finite cases','City-demographic and mode-choice preparation are outside this benchmark.'],0,947,880,63,'volumes/sioux-falls.html',size=10.1,body=9)
    section('Tools and documentation',1030)
    for i,(key,title,lines,url)in enumerate([
      ('tools','Data and GMNS tools',['Catalog · exports · queries'],BASE+'src-docs-data-tools-document'),
      ('rc5','Generic RC5 engine',['0.3.0-rc5 scope only'],BASE+'src-docs-getting-started-document-run-from-raw-input'),
      ('code','Versioned method code',['Algorithms · case adapters'],'reproduce.html'),
      ('examples','Examples and checks',['Saved results · validation','Independent validators'],'reproduce.html')]):
        card(key,title,lines,cols4[i],1048,cw,60,url,size=9.7,body=8.7)
    fig.canvas.draw();r=fig.canvas.get_renderer();overflow=[]
    for key,p,labels in text_checks:
        b=p.get_window_extent(r)
        for text in labels:
            q=text.get_window_extent(r)
            if q.x0<b.x0-1 or q.x1>b.x1+1 or q.y0<b.y0-1 or q.y1>b.y1+1:overflow.append({'card':key,'text':text.get_text(),'text_bbox':list(q.bounds),'card_bbox':list(b.bounds)})
    if overflow:raise ValueError('Text outside card: '+repr(overflow))
    caption=('Source evidence and model preparation connect the four travel-demand stages to separate static BPR/Beckmann and fixed-cost, hard-capacity finite-network contracts. A–D are internal assignment reading layers. Eight real-city cases share equal card sizes and one reading order; Sioux Falls follows them as a supplied-OD demonstration benchmark. S600, S110, S72 and S20 identify distinct saved static instances; T4 identifies separate bounded finite instances. A card does not imply that every method is accepted. Follow its case page and the current nineteen-row coverage table for method-level results, failures and limits. All module links remain available. This architecture rendering reuses documented scope and does not rerun any numerical computation.')
    sources=[{'public_path':'docs/assets/atlas/figures/g-f001.svg','sha256':sha256(REPO/'docs/assets/atlas/figures/g-f001.svg'),'role':'Preserved prior structure and module targets'}, {'public_path':'tools/figures/project_structure.py','sha256':sha256(__file__),'role':'Current declarative architecture and pure renderer'}]
    record={'figure_id':'G-F001-R11','city':'shared','instance':'Current eight-city reading scope plus independent Sioux Falls demonstration; 2026-10-08','role':'architecture','conclusion':'All real-city cases occupy the same conceptual layer; static and finite contracts and method-level acceptance remain distinct.','panels':['source evidence','model preparation','four-stage demand','assignment layers and contracts','saved outputs','eight real-city cases','demonstration benchmark','tools'],'quantity':'Qualitative model roles and reading links','unit':'Not quantitative','case_order':ORDER,'equal_real_city_card_model_dimensions':[cw,67],'data_limits':'No numerical result or new method acceptance is inferred by diagram membership.','text_overflow_checks':{'cards':len(text_checks),'failures':overflow}}
    record=export_figure(fig,OUT,record,caption,sources,close=False)
    # Bind browser hotspots to the actual exported SVG rectangle geometry.
    svg=OUT.with_suffix('.svg');ns='http://www.w3.org/2000/svg';root=ET.fromstring(svg.read_bytes());view=[float(x)for x in root.attrib['viewBox'].split()];vw,vh=view[2:]
    hotspots=[]
    for row in rects:
        g=root.find('.//{'+ns+'}g[@id="hotspot-'+row['id']+'"]');path=g.find('.//{'+ns+'}path');v=[float(x)for x in re.findall(r'[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?',path.attrib['d'])];xs=v[0::2];ys=v[1::2];x0,x1=min(xs),max(xs);y0,y1=min(ys),max(ys)
        if row.get('overlay_header_only'):y1=y0+(30/283)*(y1-y0)
        h={k:row[k]for k in ['id','label','href','model_box']};h['svg_box']=[x0,y0,x1-x0,y1-y0];h['percent']={'left':100*x0/vw,'top':100*y0/vh,'width':100*(x1-x0)/vw,'height':100*(y1-y0)/vh};hotspots.append(h)
        target='../../'+('index.html'+row['href']if row['href'].startswith('#')else row['href'])
        a=ET.SubElement(root,'{'+ns+'}a',{'href':target,'aria-label':row['label']});ET.SubElement(a,'{'+ns+'}rect',{'x':str(x0),'y':str(y0),'width':str(x1-x0),'height':str(y1-y0),'fill':'transparent','pointer-events':'all'})
    ET.register_namespace('',ns);ET.register_namespace('xlink','http://www.w3.org/1999/xlink');root.set('role','img');root.set('aria-labelledby','structure-title structure-description');title=ET.Element('{'+ns+'}title',{'id':'structure-title'});title.text='Complete project structure: eight real-city cases and a separate Sioux Falls demonstration benchmark';root.insert(0,title);desc=ET.Element('{'+ns+'}desc',{'id':'structure-description'});desc.text=caption;root.insert(1,desc);svg.write_bytes(ET.tostring(root,encoding='utf-8',xml_declaration=True))
    record['exports']['svg']=sha256(svg);record['hotspots']=hotspots;record['svg_viewbox']=view;record['status']='RENDERED_PENDING_VISUAL_QA';OUT.with_suffix('.source.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'output':str(OUT),'dimensions':record['dimensions'],'viewbox':view,'hotspots':len(hotspots),'overflow':overflow}))
    return record
if __name__=='__main__':render()
