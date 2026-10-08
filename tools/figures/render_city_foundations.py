"""Render four-city foundation and demand figures from frozen saved tables.

No optimization, matching, acquisition, or webpage mutation is performed.
Example:
  python tools/figures/render_city_foundations.py --project-root /path/to/lab --output-dir /path/to/staged
The input hash contracts are existing city-alignment-r3 source sidecars. Paths in
those historical records are remapped to the explicit project and current repo.
"""
from pathlib import Path
import argparse, json, hashlib, sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import PowerNorm, Normalize
from shapely import wkt
from shapely.geometry import shape, LineString
from shapely.ops import substring
from pyproj import Transformer
try:
    from . import style as fs
except ImportError:
    import style as fs

ROOT=None; SRC=None; DOC=fs.REPO/'docs'; OUTPUT=None
T=fs.TEAL; B=fs.BLUE; INK=fs.INK
EXPECTED={}; OLD={}; MANIFEST=[]; VERIFIED_INPUTS={}
CITIES={
 'chicago':dict(name='Chicago',folder='chicago',run='runs/chicago_core_hbw_am_v1',crs=26916,period='08:00–09:00 HBW',input='zones.csv'),
 'pittsburgh':dict(name='Pittsburgh',folder='pittsburgh',run='run_001',crs=26917,period='08:00–09:00 HBW',input='zones.csv'),
 'ithaca':dict(name='Ithaca',folder='ithaca',run='run_20261005',crs=26918,period='11:00–12:00 local activity',input='zones.csv'),
 'urbana-champaign':dict(name='Urbana–Champaign',folder='urbana_champaign',run='run_v1',crs=26916,period='08:00–09:00 HBW',input='zones_activity.csv')}

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind_path(raw):
    raw=str(raw).replace('\\','/')
    if '/candidate_repo/' in raw:return fs.REPO/raw.split('/candidate_repo/',1)[1]
    if '/work/' in raw:return ROOT/'work'/raw.split('/work/',1)[1]
    raise ValueError('Input is outside known explicit roots: '+raw)
def checked(p):
    p=Path(p).resolve(); k=str(p)
    if k not in EXPECTED:raise ValueError('Input lacks frozen hash binding: '+p.name)
    got=sha(p)
    if got!=EXPECTED[k]:raise ValueError('Frozen input changed: '+p.name)
    VERIFIED_INPUTS[k]=got
    return p
def read(p):return pd.read_csv(checked(p),dtype=str).fillna('')
def num(s):return pd.to_numeric(s,errors='coerce').fillna(0).to_numpy(float)
def js(p):return json.loads(checked(p).read_text(encoding='utf-8-sig'))
def new(city,title,scope,size=(10,5.6)):
    return fs.new_figure(CITIES[city]['name'],title,scope,figsize=size)
def note(fig,text):
    fig._external_notes=getattr(fig,'_external_notes',[])+[text]
def public_source(p,city,key):
    p=checked(p); record={'sha256':sha(p)}
    try:record['public_path']=p.relative_to(fs.REPO).as_posix()
    except ValueError:record['source_id']=city+'/'+key+'/'+p.name
    return record

def save(fig,city,key,title,caption,inputs,panels):
    c=CITIES[city];old=OLD[(city,key)]; oldpath=DOC/'assets/city-alignment-r3'/city/(key+'.svg')
    notes=' '.join(getattr(fig,'_external_notes',[])).replace('\n',' ')
    additions={
      'sources':'Reciprocal directed arcs can share geometry; no assigned flow is encoded.',
      'population':'Missing household fields are unknown, not zero. Census/ACS allocation is an input, not a simulated traffic quantity.',
      'transit':'Source stops and route shapes do not establish legal pedestrian access, operating service, or observed ridership.',
      'generation':'Scenario assumptions, not measured trip counts. External and intrazonal components do not enter interzonal assignment; attractions are normalized to productions.',
      'distribution':'Zero rows and columns remain visible; intrazonal cells are structural zeros. Labels use the final six digits of long zone IDs.',
      'mode':'Generalized cost includes model time and money terms. Person totals precede the separate occupancy-to-PCE conversion.',
      'trace':'An accepted numerical gap concerns this scenario and demand set; it does not certify real traffic conditions.'}
    caption=' '.join([caption,additions[key]]).strip()
    caption+=' This drawing uses the frozen '+c['run']+' evidence. Later supplementary datasets are separate and are not implied to have entered this scenario.'
    # Verify all reconstructed scientific quantities against the frozen figure ledger.
    expected_panels=old['panels']
    if key=='transit' and city in ('chicago','pittsburgh'):
        expected_panels=[p for p in expected_panels if p.get('metric')!='evidence boundary']
    if panels!=expected_panels:raise ValueError('Reconstructed evidence differs from frozen record: '+city+'/'+key)
    numeric_evidence=json.loads(json.dumps(panels))
    # Preserve all scalar accounting values from the original figure record.
    if key=='population':
        panels=[p for p in panels if p.get('available') is not False]
    quantities={
      'sources':('physical road geography','projected km'),
      'population':('resident population; occupied housing proxy','persons; occupied units'),
      'transit':('saved stop coordinates; source service/route records','projected km; records'),
      'generation':('interzonal production and attraction; generation ledger','person trips per declared period'),
      'distribution':('directed OD person trips; origin and destination margins','person trips per declared period; log(1 + person trips) colour'),
      'mode':('person demand; person-weighted generalized cost; available positive OD pairs','person trips per declared period; generalized minutes; OD pairs'),
      'trace':('Beckmann objective; relative gap','PCE-min; dimensionless')}
    if key=='mode':
        specs=[('a','person_trips','person demand','person trips per declared period'),('b','person_weighted_generalized_minutes','person-weighted generalized cost','generalized minutes'),('c','available_positive_od','available positive OD pairs','OD pairs')]
        panels=[{'panel':label,'metric':metric,'unit':unit,'modes':[r['mode'] for r in numeric_evidence],'values':[r[field] for r in numeric_evidence]} for label,field,metric,unit in specs]
    if key=='distribution':
        for panel in panels:panel['unit']='person trips per declared period'
    if key=='transit':
        for panel in panels:
            if panel.get('metric')=='archived route shapes':panel['unit']='projected km; route-shape records (not unique routes)'
    for panel in panels:
        panel.setdefault('unit',quantities[key][1]);panel.setdefault('instance',c['run']+' / '+c['period'])
    rec={'figure_id':'R11-'+city.upper()+'-'+key.upper(),'city':city,'title':fig._mcl_header['title'],
      'instance':{'saved_run':c['run'],'declared_period':c['period'],'revision':'frozen four-stage scenario used by R3 source figures'},
      'role':'iteration' if key=='trace' else ('geography' if key in ('sources','transit') else 'demand'),
      'conclusion':caption.split('. ')[0]+'.','panels':panels,'quantity':quantities[key][0],'unit':quantities[key][1],
      'renderer':{'script':'tools/figures/render_city_foundations.py','function':key,'sha256':sha(__file__)},
      'original_asset':{'public_path':oldpath.relative_to(fs.REPO).as_posix(),'sha256':sha(oldpath)},
      'original_source_record':{'public_path':old['_record_path'].relative_to(fs.REPO).as_posix(),'sha256':sha(old['_record_path'])},
      'original_evidence_panels':old['panels'],'moved_canvas_notes':notes,'numeric_evidence_preserved':numeric_evidence,'numerical_equivalence':'EXACT_MATCH_TO_FROZEN_FIGURE_RECORD',
      'preserved_limits':['No later supplementary field is asserted to be used in the frozen demand model.','Copyright and explanatory prose are retained in the external caption.']}
    if key=='trace':rec['saved_states']=len(panels[0]['iteration'])
    sources=list({str(Path(p).resolve()):p for p in inputs}.values())
    stem=OUTPUT/city/key
    result=fs.export_figure(fig,stem,rec,caption=caption,sources=[public_source(p,city,key) for p in sources])
    MANIFEST.append({'city':city,'family':key,'id':rec['figure_id'],'old_asset':rec['original_asset'],
      'old_source':rec['original_source_record'],'new_files':{ext:str(stem.with_suffix('.'+ext)) for ext in ['svg','png','pdf','source.json','caption.md']},
      'source_count':len(sources),'exports':result['exports'],'status':result['status'],'solver_calls':0,'matcher_calls':0})
    return result

def lab(z):return str(z).replace('tract2020_','')[-6:] if len(str(z))>7 else str(z)

def ordered(d):return d.sort_values('zone_id',key=lambda s:s.str.extract(r'(\d+)$')[0].astype('int64'))

def axes(fig,n=2,ratios=None,bottom=.18,top=.75):
    return fig.subplots(1,n,gridspec_kw={'width_ratios':ratios or [1]*n}) if False else [fig.add_subplot(g) for g in fig.add_gridspec(1,n,left=.07,right=.96,bottom=bottom,top=top,wspace=.35,width_ratios=ratios or [1]*n)]

def format_ax(ax,title,x=None,y=None):
    ax.set_title(title,loc='left',fontweight='bold',pad=10)
    if x:ax.set_xlabel(x)
    if y:ax.set_ylabel(y)
    fs.format_axes(ax)

def load_geography(city):
    c=CITIES[city]; base=SRC/c['folder']; four=base/'four_stage';run=four/c['run']
    solpath=run/'assignment/link_solution.csv'; sol=read(solpath) if city!='pittsburgh' else None; inputs=[solpath]
    if city=='chicago':
        p=four/'inputs/network_source_crosswalk.csv'; g=read(p);g=g.rename(columns={'geometry_wgs84':'geometry_wkt'}); inputs+=[p]
        data=sol.merge(g[['link_id','geometry_wkt']],on='link_id',validate='one_to_one')
    elif city=='pittsburgh':
        p=DOC/f'assets/six-city-r3-1/{city}/plot_data/FS_A01/physical_flow.csv';g=read(p);inputs=[p]
        data=g.rename(columns={'physical_link_id':'link_id'})
    elif city=='ithaca':
        p=DOC/f'assets/six-city-r3-1/{city}/plot_data/FS_A04/FS_A04_plot_data.csv';g=read(p).rename(columns={'model_link_id':'link_id'});inputs+=[p]
        data=sol.merge(g[['link_id','geometry_wkt']],on='link_id',validate='one_to_one')
    else:
        p=base/'processed/gmns/link.csv';mp=four/'inputs/physical_link_map.csv';g=read(p).rename(columns={'link_id':'gmns_link_id','geometry':'geometry_wkt'});m=read(mp).rename(columns={'model_link_id':'link_id'});inputs += [p,mp]
        data=sol.merge(m[['link_id','gmns_link_id']],on='link_id',validate='one_to_one').merge(g[['gmns_link_id','geometry_wkt']],on='gmns_link_id',validate='many_to_one')
    trans=Transformer.from_crs(4326,c['crs'],always_xy=True)
    seg=[]
    for (_,row) in data.iterrows():
        a=np.asarray(wkt.loads(row.geometry_wkt).coords); xx,yy=trans.transform(a[:,0],a[:,1]); points=np.column_stack([xx,yy])/1000
        if city=='urbana-champaign' and row.link_id.endswith((':A',':B')):
            # Source builder: A is I -> M and B is M -> O, preserving directed source order.
            ln=LineString(points); part=substring(ln,0,.5,normalized=True) if row.link_id.endswith(':A') else substring(ln,.5,1,normalized=True)
            points=np.asarray(part.coords)
        seg.append(points)
    allpts=np.vstack(seg);origin=allpts.min(axis=0);seg=[x-origin for x in seg]
    return data,seg,origin,trans,inputs

def map_base(ax,seg,city,origin):
    ax.add_collection(LineCollection(seg,colors=fs.ROAD,linewidths=.28,zorder=1))
    ax.autoscale();fs.format_axes(ax,map_axis=True);ax.set_anchor('NW')
    ax.set_xlabel('Easting from local origin (km)');ax.set_ylabel('Northing from local origin (km)')
    ax.ticklabel_format(useOffset=False,style='plain')

def sources(city,geo):
    data,seg,origin,trans,inputs=geo;c=CITIES[city]
    fig=new(city,'Retained physical road graph','GEOGRAPHIC SUPPORT',(9.2,6.2))
    ax=fig.add_axes([.09,.16,.80,.61]);map_base(ax,seg,city,origin)
    ax.collections[0].set_color('#8195a5');ax.collections[0].set_linewidth(.35)
    note(fig,f'EPSG:{c["crs"]}; projected kilometres. Reciprocal arcs may share geometry.\nNo virtual turn/access arcs, no assigned flow encoded. © OpenStreetMap contributors / ODbL.')
    return save(fig,city,'sources','Physical source roads and retained graph',
       f'{len(data):,} retained physical directed traversals in the saved {c["period"]} model, shown in EPSG:{c["crs"]}. This is the retained model graph, not a claim to draw every road in the source archive. Virtual movements are excluded; colour has no traffic meaning. © OpenStreetMap contributors / ODbL.',inputs,
       [{'panel':'a','metric':'physical road geography','unit':'projected km','encoding':'gray lines; one per physical directed traversal','CRS':f'EPSG:{c["crs"]}','local_origin_metres':(origin*1000).tolist()}])

def population(city):
    c=CITIES[city];p=SRC/c['folder']/'four_stage/inputs'/c['input'];d=ordered(read(p));N=len(d);xx=np.arange(N)
    missing=all(x=='' for x in d.households)
    fig=new(city,'Resident population inputs' if missing else 'Population and household inputs','DEMAND INPUTS',(8.4,5.4) if missing else (11,5.8));aa=axes(fig,1 if missing else 2,bottom=.27)
    aa[0].bar(xx,num(d.population),color=T);format_ax(aa[0],'a  Resident population',y='Persons')
    missing=all(x=='' for x in d.households)
    if not missing:
        aa[1].bar(xx,num(d.households),color=B);format_ax(aa[1],'b  Household proxy',y='Occupied units')
    for ax in aa:
        if ax.axison:ax.set_xticks(xx);ax.set_xticklabels([lab(z) for z in d.zone_id],rotation=90,fontsize=6.3);ax.set_xlabel('Zone ID (last 6 digits for long Census IDs)')
    bounds={'chicago':'Clipped community-area allocation of ACS population; uniform-area assumption.',
       'pittsburgh':'Selected 2020 blocks grouped by tract ID; not whole-tract totals.',
       'ithaca':'Saved clipped-zone demographic allocation; not a campus census.',
       'urbana-champaign':'2020 blocks selected by internal point; not earlier whole-tract totals.'}[city]
    note(fig,bounds+'\nEvery model zone is shown in stable ID order; Census/ACS input, not simulated traffic.')
    return save(fig,city,'population','All-zone demographic denominator',bounds+f' All {N} zones are retained; population total {num(d.population).sum():,.6g}. '+('Households are unknown.' if missing else f'Occupied units total {num(d.households).sum():,.6g}.'),[p],
       [{'panel':'a','metric':'population','unit':'persons','total':float(num(d.population).sum())}, {'panel':'b','metric':'households proxy','unit':'occupied units','available':not missing,'total':None if missing else float(num(d.households).sum())}])

def transit(city,geo):
    c=CITIES[city];base=SRC/c['folder'];data,seg,origin,trans,_=geo
    opts={
      'chicago':('processed/source_tagged_stops.csv','lon','lat','OSM source-tagged stops; no service calendar'),
      'pittsburgh':('processed/stops.csv','lon','lat','Earlier bounded preflight stop tags; no timetable'),
      'ithaca':('processed/tcat_stops_aoi.csv','lon','lat','TCAT stops / 2026-10-05 service-day flags'),
      'urbana-champaign':('continuation_20261005/processed/ntm_mtd_stops_20260309.csv','longitude','latitude','BTS/NTM archive / 2026-03-09; timetable unknown')}
    path,xcol,ycol,label=opts[city];p=base/path;d=read(p);x,y=trans.transform(num(d[xcol]),num(d[ycol]));xy=np.column_stack([x,y])/1000-origin
    single=city in ('chicago','pittsburgh')
    fig=new(city,'Transit source geography','SOURCE CONTEXT',(8.4,6.1) if single else (11.2,6.3));aa=axes(fig,1 if single else 2,ratios=[1] if single else ([1,1] if city=='urbana-champaign' else [1.4,1]),bottom=.18)
    map_base(aa[0],seg,city,origin);aa[0].scatter(xy[:,0],xy[:,1],s=8,c=T,alpha=.65,zorder=3);aa[0].set_title('a  Saved stop coordinates',loc='left',weight='bold')
    inputs=[p]+list(geo[4]);panels=[{'panel':'a','metric':'stop coordinates','unit':'projected km','count':len(d),'source_scope':label}]
    if city=='ithaca':
        served=d.served_on_day.str.lower().eq('true').sum(); vals=[served,len(d)-served];aa[1].bar(['Flagged\nserved','Not flagged\nserved'],vals,color=[T,B]);format_ax(aa[1],'b  Calendar evidence',y='Saved stop records');
        for i,v in enumerate(vals):aa[1].text(i,v+max(vals)*.03,str(v),ha='center',fontsize=10)
        tail='Service-day flags do not certify pedestrian access or observed ridership.'
        panels.append({'panel':'b','metric':'stop service-day flags','unit':'records','served':int(served),'not_flagged':len(d)-int(served)})
    elif city=='urbana-champaign':
        rp=base/'continuation_20261005/processed/ntm_mtd_route_shapes_20260309.geojson';features=js(rp)['features'];routes=[]
        for f in features:
            g=shape(f['geometry']);lines=list(g.geoms) if g.geom_type=='MultiLineString' else [g]
            for ln in lines:
                a=np.asarray(ln.coords);rx,ry=trans.transform(a[:,0],a[:,1]);routes.append(np.column_stack([rx,ry])/1000-origin)
        map_base(aa[1],seg,city,origin);aa[1].add_collection(LineCollection(routes,colors=B,linewidths=.7,alpha=.4));aa[1].set_title('b  Archived route shapes',loc='left',weight='bold');inputs.append(rp);tail=f'{len(d)} stop records; {len(features)} route-shape records, not unique routes or scheduled trips.'
        panels.append({'panel':'b','metric':'archived route shapes','count':len(features),'unit':'records, not unique routes'})
    else:
        tail=f'{len(d):,} saved stop records. Stop tags and road proximity do not prove legal walk access or operating service. The frozen scenario has no accepted service-day transit paths; no zero-demand transit bar is implied.'
        # Evidence boundary is caption metadata, not a fabricated quantitative panel.
    note(fig,label+'.\n'+tail+' © OpenStreetMap contributors / ODbL; agency/BTS data as labelled.')
    return save(fig,city,'transit','Transit source geography and service boundary',label+'. '+tail+' The gray retained road graph is geographic context, not a transit route model.',inputs,panels)

def generation(city):
    c=CITIES[city];p=DOC/f'assets/six-city-r3-1/{city}/plot_data/generation_complete.csv';d=ordered(read(p));xx=np.arange(len(d));P=num(d.interzonal_production_person_trips);A=num(d.interzonal_attraction_person_trips)
    fig=new(city,'Trip generation and demand accounting',''+c['period'],(11.6,6.1));aa=axes(fig,2,ratios=[1.9,1],bottom=.29)
    aa[0].bar(xx-.18,P,width=.36,color=T,label='Production');aa[0].bar(xx+.18,A,width=.36,color=B,label='Attraction');format_ax(aa[0],f'a  All {len(d)} model zones',y='Interzonal person trips / period');aa[0].set_xticks(xx);aa[0].set_xticklabels([lab(z) for z in d.zone_id],rotation=90,fontsize=6.3);aa[0].set_xlabel('Zone ID (last 6 digits for long IDs)');aa[0].legend(fontsize=8)
    cols=['generated_person_trips','external_or_uncaptured_person_trips','intrazonal_person_trips','interzonal_production_person_trips'];totals=[float(num(d[k]).sum()) for k in cols]
    aa[1].barh(['Generated','External /\nuncaptured','Intrazonal','Interzonal'],totals,color=[INK,'#a7b7c7','#8ac3bd',T]);aa[1].invert_yaxis();format_ax(aa[1],'b  Demand accounting',x='Person trips / period');aa[1].set_xlim(0,max(totals)*1.32)
    for i,v in enumerate(totals):aa[1].text(v+max(totals)*.025,i,f'{v:,.1f}',va='center',fontsize=8)
    assert np.isclose(totals[0],sum(totals[1:]),atol=1e-6)
    note(fig,'Scenario assumptions, not measured trip counts. External and intrazonal components do not enter interzonal assignment.\nAttractions are normalized to productions; no zones are dropped or ranked out of view.')
    return save(fig,city,'generation','All-zone trip generation and demand ledger',f'All {len(d)} zones; {c["period"]}. The left panel shows saved interzonal productions/attractions. The right panel accounts for all generated persons, including excluded and intrazonal components. No top-12 truncation.',[p],
      [{'panel':'a','metric':'production and attraction','unit':'persons per declared period','zone_count':len(d),'P_total':float(P.sum()),'A_total':float(A.sum())},{'panel':'b','metric':'generation ledger','fields':dict(zip(cols,totals))}])

def distribution(city):
    c=CITIES[city];p=DOC/f'assets/six-city-r3-1/{city}/plot_data/FS_D01/distribution.csv';gp=DOC/f'assets/six-city-r3-1/{city}/plot_data/generation_complete.csv';d=read(p);ids=list(ordered(read(gp)).zone_id);idx={z:i for i,z in enumerate(ids)};M=np.zeros((len(ids),len(ids)))
    for _,r in d.iterrows():M[idx[r.o_zone_id],idx[r.d_zone_id]]+=float(r.person_trips)
    fig=new(city,'Trip distribution and directed OD margins',c['period'],(13.5,6.7));aa=axes(fig,3,ratios=[1.6,1,1],bottom=.24)
    im=aa[0].imshow(np.log1p(M),cmap=fs.FLOW_CMAP,origin='upper',interpolation='nearest');aa[0].set_title(f'a  Full {len(ids)} × {len(ids)} OD matrix',loc='left',weight='bold');aa[0].set_xlabel('Destination zone');aa[0].set_ylabel('Origin zone')
    step=1 if len(ids)<=22 else 2;ticks=np.arange(0,len(ids),step)
    for ax in aa[:1]:ax.set_xticks(ticks);ax.set_xticklabels([lab(ids[i]) for i in ticks],rotation=90,fontsize=6);ax.set_yticks(ticks);ax.set_yticklabels([lab(ids[i]) for i in ticks],fontsize=6)
    cb=fig.colorbar(im,ax=aa[0],fraction=.046,pad=.04);cb.set_label('log(1 + person trips)')
    for ax,v,title in [(aa[1],M.sum(1),'b  Origin totals'),(aa[2],M.sum(0),'c  Destination totals')]:
        ax.barh(np.arange(len(ids)),v,color=T if ax==aa[1] else B);ax.invert_yaxis();ax.set_yticks(ticks);ax.set_yticklabels([lab(ids[i]) for i in ticks],fontsize=6);format_ax(ax,title,x='Person trips / period')
    note(fig,f'Positive cells: {np.count_nonzero(M):,}; total: {M.sum():,.6f} persons. Zero rows/columns and intrazonal structural zeros remain visible.\nMargins shown are directed OD totals after the declared PA direction, not the original PA targets. Long labels use final 6 digits.')
    return save(fig,city,'distribution','Complete OD matrix with origin and destination margins',f'Full {len(ids)}×{len(ids)} model-zone matrix including zero cells; {np.count_nonzero(M)} positive OD pairs and {M.sum():,.9f} persons in {c["period"]}. Colours are log(1+persons); margins are untransformed directed OD totals after PA direction. Every model zone is retained.',[p,gp],
       [{'panel':'a','metric':'directed OD person trips','encoding':'log(1+persons)','shape':list(M.shape),'positive_cells':int(np.count_nonzero(M)),'total':float(M.sum())},{'panel':'b','metric':'origin margin','total':float(M.sum())},{'panel':'c','metric':'destination margin','total':float(M.sum())}])

def mode(city):
    c=CITIES[city];p=SRC/c['folder']/'four_stage'/c['run']/'mode_choice/mode_choice_by_od.csv';d=read(p);modes=[m for m in ['drive','walk','transit'] if m in set(d['mode'])]; rows=[]
    for m in modes:
        z=d[d['mode']==m];yes=z.available.str.lower().isin(['true','1']);pp=num(z.person_trips);mins=num(z.generalized_min);n=int(((num(z.od_person_trips)>0)&yes).sum())
        if n:rows.append((m,float(pp.sum()),float((pp*mins).sum()/max(pp.sum(),1e-100)),n))
    if not rows:raise ValueError(city+' no modeled mode rows')
    fig=new(city,'Mode choice: demand, cost and availability',c['period'],(11.5,5.8));aa=axes(fig,3,bottom=.22);labels=[x[0].title() for x in rows];colors=[T,B,'#7da4b4'][:len(rows)]
    for k,(title,unit) in enumerate([('a  Person demand','Person trips / period'),('b  Person-weighted cost','Generalized minutes'),('c  Available OD pairs','OD pairs')]):
        vals=[r[k+1] for r in rows];aa[k].bar(labels,vals,color=colors);format_ax(aa[k],title,y=unit);aa[k].set_ylim(0,max(vals)*1.25)
        for i,v in enumerate(vals):aa[k].text(i,v+max(vals)*.035,f'{v:,.0f}' if k==2 else f'{v:,.2f}',ha='center',fontsize=9)
    notransit='transit' not in [r[0] for r in rows]
    note(fig,('Transit is not modeled: no accepted service-day path costs. An omitted bar is not a prediction of zero transit.\n' if notransit else 'Transit uses the saved bounded timetable/path-cost assumptions; no observed ridership is inferred.\n')+'Generalized cost includes the model time and money terms. Person totals precede the separate occupancy-to-PCE conversion.')
    return save(fig,city,'mode','Mode choice: persons, costs and availability',f'Saved OD-specific choice in {c["period"]}; sums over every positive-demand OD. Persons, person-weighted generalized minutes, and available OD counts have separate axes. '+('Transit is not modeled; no zero bar is shown.' if notransit else 'Transit is included only where saved as available.'),[p],
       [{'mode':r[0],'person_trips':r[1],'person_weighted_generalized_minutes':r[2],'available_positive_od':r[3]} for r in rows])

def trace(city):
    c=CITIES[city];p=SRC/c['folder']/'four_stage'/c['run']/'assignment/fw_trace.csv';sp=p.with_name('assignment_summary.json');d=read(p);x=num(d.iteration);g=num(d.relative_gap);obj=num(d.beckmann_objective);summary=js(sp);threshold=float(summary.get('relative_gap_tolerance',1e-4));single=len(d)==1
    fig=new(city,'Frank–Wolfe objective and relative gap',''+('INITIAL ENDPOINT; ZERO UPDATES' if single else 'ACTUAL SAVED ITERATIONS'),(10.5,5.4));aa=axes(fig,2,bottom=.23)
    aa[0].plot(x,obj,'o' if single else '-o',color=T,markersize=5);format_ax(aa[0],'a  Beckmann objective',x='Saved iteration',y='PCE-minutes');aa[0].ticklabel_format(useOffset=False,style='plain',axis='y')
    aa[1].plot(x,g,'o' if single else '-o',color=B,markersize=5);aa[1].axhline(threshold,color=INK,linestyle='--',linewidth=1,label=f'Tolerance {threshold:g}');format_ax(aa[1],'b  Relative gap',x='Saved iteration',y='Dimensionless relative gap');aa[1].legend(fontsize=8)
    if np.all(g>0) and not single:aa[1].set_yscale('log')
    elif single:aa[1].set_ylim(-threshold*.1,max(threshold,g.max())*1.2)
    for ax in aa:ax.set_xticks(x.astype(int));ax.set_xlim(-.3,max(x)+.3)
    if single:
        aa[0].annotate(f'{obj[0]:,.6f}',(0,obj[0]),xytext=(0,12),textcoords='offset points',fontsize=9,ha='center');aa[1].annotate(f'Saved gap = {g[0]:.12g}',(0,g[0]),xytext=(0,12),textcoords='offset points',fontsize=9,ha='center')
    note(fig,('Only iteration 0 exists. No update curve, artificial log floor or interpolated points are added.' if single else f'{len(d)-1} actual updates; markers are saved iterations only. Gap uses a logarithmic y-axis.')+'\nAn accepted numerical gap concerns this scenario and demand set; it does not certify real traffic conditions.')
    return save(fig,city,'trace','Frank–Wolfe saved objective and gap',f'{len(d)} saved record(s), {len(d)-1} updates; final objective {obj[-1]:.12g} PCE-min, gap {g[-1]:.12g} against {threshold:g}. '+('The exact zero (where present) is plotted on a linear axis; no convergence history is fabricated.' if single else 'Original iteration samples and objective retained.'),[p,sp],
      [{'panel':'a','metric':'Beckmann objective','unit':'PCE-min','values':obj.tolist(),'iteration':x.tolist()},{'panel':'b','metric':'relative gap','unit':'dimensionless','values':g.tolist(),'threshold':threshold,'iteration':x.tolist(),'axis':'linear' if single else 'log'}])

def prepare(city,keys):
    # Geography is used as context by sources and transit, so include its exact
    # source binding even if an older transit sidecar omitted background inputs.
    for key in set(keys)|{'sources'}:
        p=DOC/'assets/city-alignment-r3'/city/(key+'.source.json')
        data=json.loads(p.read_text(encoding='utf-8-sig'));data['_record_path']=p;OLD[(city,key)]=data
        for item in data['source_inputs']:
            resolved=bind_path(item['path']).resolve();k=str(resolved)
            if k in EXPECTED and EXPECTED[k]!=item['sha256']:raise ValueError('Conflicting frozen hashes')
            EXPECTED[k]=item['sha256'];checked(resolved)

def main():
    global ROOT,SRC,OUTPUT
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root',required=True,type=Path)
    parser.add_argument('--output-dir',required=True,type=Path)
    parser.add_argument('--cities',nargs='+',choices=list(CITIES),default=list(CITIES))
    args=parser.parse_args();ROOT=args.project_root.resolve();SRC=ROOT/'work/six_city_preflight_r1/cities';OUTPUT=args.output_dir.resolve()
    if OUTPUT==DOC or DOC in OUTPUT.parents:raise ValueError('Use a staging directory outside the published docs tree.')
    original_hashes={str(p):sha(p) for city in args.cities for p in (DOC/'assets/city-alignment-r3'/city).glob('*') if p.is_file()}
    errors=[]
    for city in args.cities:
        keys=['sources','population','transit','generation','distribution','mode']+(['trace'] if city=='chicago' else [])
        try:
            prepare(city,keys);geo=load_geography(city)
            for key in keys:
                print('RENDER',city,key,flush=True)
                if key in ('sources','transit'):globals()[key](city,geo)
                else:globals()[key](city)
        except Exception as exc:
            import traceback
            traceback.print_exc();errors.append({'city':city,'reason':type(exc).__name__+': '+str(exc)})
    changed=[p for p,h in original_hashes.items() if sha(p)!=h]
    if changed:raise RuntimeError('Original figure bytes were changed: '+repr(changed))
    OUTPUT.mkdir(parents=True,exist_ok=True)
    report={'schema':'mcl_foundations_r11','figures':MANIFEST,'errors':errors,'count':len(MANIFEST),'original_bytes_preserved':not changed,
      'verified_input_count':len(VERIFIED_INPUTS),'input_hashes':VERIFIED_INPUTS,'solver_calls':0,'matcher_calls':0,'page_mutations':0,
      'visual_qa':'PENDING; every exported PNG must be inspected before integration.'}
    (OUTPUT/'FOUNDATIONS_RENDER_RESULT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print('COMPLETE',len(MANIFEST),'figures;',len(errors),'errors',flush=True)
    if errors:raise SystemExit(2)
if __name__=='__main__':main()

