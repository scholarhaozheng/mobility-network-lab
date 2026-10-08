"""Berkeley atlas: render explicit frozen plot tables; never import a solver."""
from pathlib import Path
import csv, json, hashlib, inspect, logging, math
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.collections import LineCollection, PatchCollection
from matplotlib.patches import Polygon
from matplotlib.colors import Normalize, PowerNorm
from matplotlib.ticker import MaxNLocator, ScalarFormatter
from shapely import wkt
from PIL import Image
from atlas_style import *
from embed_serif_fonts import embed_serif_fonts

HERE=Path(__file__).resolve().parent;INP=(HERE/'inputs') if (HERE/'inputs').exists() else HERE/'data';OUT=HERE/'figures'
logging.getLogger('fontTools.subset').setLevel(logging.ERROR)
RECORDS=[]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def csvread(n):
    with (INP/n).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def jread(n):return json.loads((INP/n).read_text(encoding='utf8'))
def vals(rs,k):return np.array([float(r[k]) if r.get(k) not in ('',None) else np.nan for r in rs])
def xy(coords):
    a=np.asarray(coords,float).copy();a[:,0]=(a[:,0]+122.27)*111.320*np.cos(np.deg2rad(37.87));a[:,1]=(a[:,1]-37.87)*110.574;return a
ROADS=csvread('physical_geometry.csv');SEGS=[xy(wkt.loads(r['geometry_wkt']).coords) for r in ROADS]
ZONES=csvread('zones.csv');ZIDS=[r['zone_id'] for r in ZONES];ZN=np.arange(1,14)
POLYS=[wkt.loads(r['geometry_wkt']) for r in ZONES]
ATTR={r['link_id']:r for r in csvread('static_link_attributes.csv')}
NODEXY={}
for r,s in zip(ROADS,SEGS):
    a=ATTR[r['link_id']];NODEXY[a['from_node_id']]=s[0];NODEXY[a['to_node_id']]=s[-1]
VERT=np.vstack(SEGS)
def title(ax,t):format_axes(ax);ax.set_title(t,loc='left',fontsize=10,fontweight='bold',pad=10)
def labels(ax,x,y):ax.set_xlabel(x);ax.set_ylabel(y)
def polygons(ax,values=None):
    patches=[];colors=[]
    for i,g in enumerate(POLYS):
        for p in ([g] if g.geom_type=='Polygon' else g.geoms):
            patches.append(Polygon(xy(p.exterior.coords),closed=True));colors.append(0 if values is None else values[i])
    pc=PatchCollection(patches,facecolor='#f2f7f8',edgecolor='#93a7b3',linewidth=.6,zorder=0)
    if values is not None:pc.set_array(np.array(colors));pc.set_cmap(FLOW_CMAP);pc.set_norm(Normalize(0,max(values)))
    ax.add_collection(pc);return pc
def basemap(ax,fill=True,roadwidth=.36):
    if fill:polygons(ax)
    ax.add_collection(LineCollection(SEGS,colors=ROAD,linewidths=roadwidth,zorder=1))
    ax.set_xlim(VERT[:,0].min()-.07,VERT[:,0].max()+.07);ax.set_ylim(VERT[:,1].min()-.07,VERT[:,1].max()+.07)
    format_axes(ax,map_axis=True);labels(ax,'East of display origin (km)','North of display origin (km)')
    ax.xaxis.set_major_locator(MaxNLocator(5));ax.yaxis.set_major_locator(MaxNLocator(5))
def zonelabels(ax):
    for i,g in enumerate(POLYS):
        p=g.representative_point();x,y=xy([[p.x,p.y]])[0];ax.text(x,y,str(i+1),fontsize=7,ha='center',va='center',color=INK,bbox={'facecolor':'white','edgecolor':'none','alpha':.72,'pad':.4},zorder=5)
def finish(fig,stem,heading,stage,caption,panels,sources,data):
    compact_header(fig)
    OUT.mkdir(exist_ok=True)
    for ext in ['svg','png','pdf']:
        metadata={'Date':None} if ext=='svg' else ({'CreationDate':None,'ModDate':None} if ext=='pdf' else None)
        fig.savefig(OUT/(stem+'.'+ext),dpi=240,bbox_inches='tight',pad_inches=.055,metadata=metadata)
    font=embed_serif_fonts(OUT/(stem+'.svg'))
    with Image.open(OUT/(stem+'.png')) as im:dim=list(im.size)
    plt.close(fig)
    caller=inspect.currentframe().f_back
    rec={'id':'BERKELEY-R3-'+stem.upper().replace('_','-'),'stem':stem,'title':heading,'city':'Berkeley','stage':stage,'caption':caption,'panels':panels,'dimensions':dim,
      'renderer':{'file':'render_figures.py','function':caller.f_code.co_name,'line':caller.f_code.co_firstlineno},
      'source_data':[{'path':'data/'+n,'sha256':sha(INP/n)} for n in sources],
      'style':{'layout':'C','font':'DejaVu Serif','palette':PALETTE,'functions':['new_figure','format_axes','compact_header']},
      'solver_calls':0,'scope':'Saved engineering scenario, not observed traffic or a local empirical calibration.',
      'coordinate_transform':{'origin_lon_lat':[-122.27,37.87],'x_km':'(lon+122.27)*111.320*cos(37.87 deg)','y_km':'(lat-37.87)*110.574','scientific_geometry_changed':False},
      'font':font,'exports':{e:{'path':stem+'.'+e,'sha256':sha(OUT/(stem+'.'+e))} for e in ['svg','png','pdf']}}
    (OUT/(stem+'.source.json')).write_text(json.dumps(rec,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    (OUT/(stem+'.plot_data.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf8')
    (OUT/(stem+'.caption.md')).write_text(caption+'\n',encoding='utf8');RECORDS.append(rec);print(stem,flush=True)

def source_geography():
    fig=new_figure('berkeley','Source geography and accepted model support','13 zones / 2,150 physical links',figsize=(9.8,6.5))
    ax=fig.add_axes([.09,.13,.82,.66]);title(ax,'Actual model polygons, retained roads and auto access');basemap(ax);zonelabels(ax)
    points=np.array([NODEXY[z['auto_access_node']] for z in ZONES if z['auto_access_node']])
    ax.scatter(points[:,0],points[:,1],s=22,color=TEAL,edgecolor='white',lw=.7,zorder=4,label='11 available auto access nodes')
    ax.legend(loc='lower left',fontsize=8)
    caption='All 13 model-zone polygons and all 2,150 accepted directed physical road links are shown. Number labels follow the complete generation/OD zone order. Teal points are the 11 saved auto access nodes; the two zones without an auto node remain in the geographic context. Road color is contextual and encodes no flow. This screened model differs from the inherited 8,991-link preflight source map. Display coordinates use the same local kilometre convention as Boston. © OpenStreetMap contributors, ODbL 1.0; zone geometry is derived from 2020 Census geography.'
    finish(fig,'source_geography','Source geography and accepted model support','sources',caption,{'a':'Actual zones, roads, access nodes; no quantitative road-flow encoding'},['zones.csv','physical_geometry.csv','static_link_attributes.csv'],{'zones':ZONES,'physical_link_count':2150,'auto_access_nodes':11})

def population_jobs():
    fig=new_figure('berkeley','Population and jobs in the 13 model zones','Discrete source-block allocation / different source years',figsize=(11.2,6.1))
    for pos,key,heading,unit in [(.07,'population_2020','a  Census population, 2020','Residents'),(.56,'primary_jobs_2023','b  Primary workplace jobs, 2023','Primary jobs')]:
        ax=fig.add_axes([pos,.17,.345,.62]);title(ax,heading);basemap(ax,False);v=vals(ZONES,key);c=polygons(ax,v);zonelabels(ax)
        box=ax.get_position();cb=fig.colorbar(c,cax=fig.add_axes([box.x1+.01,box.y0,.012,box.height]));cb.set_label(unit)
        ax.text(.03,.02,f'Total {sum(v):,.0f}',transform=ax.transAxes,fontsize=9,weight='bold',bbox={'facecolor':'white','edgecolor':'none','pad':2},zorder=8)
    caption='The two maps retain all 13 model zones, with independent linear count color scales. Population sums to 31,821 residents (2020 Census); attraction weights sum to 16,583 primary workplace jobs (2023 LODES WAC). Counts follow the saved discrete rule: a source block contributes when its official internal point lies inside the model zone. Values are not whole-tract totals, density, or household counts. Different years and concepts must not be treated as synchronous population and employment observations. The numbered zones match the full OD matrix. Roads are only context. Census/LODES source counts; © OpenStreetMap contributors for the road context.'
    finish(fig,'population_jobs','Population and jobs in the 13 model zones','population',caption,{'a':'2020 resident count by model zone','b':'2023 primary job count by model zone'},['zones.csv','physical_geometry.csv'],{'zone_rows':ZONES,'population_total':31821,'jobs_total':16583})

def transit_network():
    stops=csvread('transit_stops.csv');direct=csvread('transit_direct.csv');mat=np.zeros((13,13))
    for r in direct:mat[ZIDS.index(r['o_zone_id']),ZIDS.index(r['d_zone_id'])]=1
    assert mat.sum()==38
    fig=new_figure('berkeley','Scheduled transit geography and model availability','AC Transit / 5 October 2026',figsize=(11.2,6.3))
    a=fig.add_axes([.07,.15,.39,.62]);title(a,'a  Source-envelope stops');basemap(a)
    p=xy([[r['longitude'],r['latitude']] for r in stops]);a.scatter(p[:,0],p[:,1],s=10,color=TEAL,edgecolor='white',lw=.3,zorder=3)
    # Source-envelope stops can lie beyond the auto model; retain their actual coordinates.
    a.set_xlim(min(p[:,0].min(),VERT[:,0].min())-.08,max(p[:,0].max(),VERT[:,0].max())+.08);a.set_ylim(min(p[:,1].min(),VERT[:,1].min())-.08,max(p[:,1].max(),VERT[:,1].max())+.08)
    a.text(.03,.03,f'{len(stops)} scheduled stops',transform=a.transAxes,fontsize=9,bbox={'facecolor':'white','edgecolor':'none','pad':2})
    a=fig.add_axes([.60,.15,.30,.62]);title(a,'b  Saved direct OD alternatives')
    im=a.imshow(mat,cmap=FLOW_CMAP,vmin=0,vmax=1,origin='upper',interpolation='none');a.set_xticks(range(13),ZN,fontsize=7);a.set_yticks(range(13),ZN,fontsize=7);labels(a,'Destination model zone','Origin model zone');a.grid(False)
    cb=fig.colorbar(im,cax=fig.add_axes([.915,.23,.012,.43]),ticks=[0,1]);cb.ax.set_yticklabels(['Absent','Available'])
    caption='Left: all 168 AC Transit stops in the frozen source envelope, shown at their supplied coordinates against the 2,150-link model road context. Equal symbol size identifies stops, not ridership or frequency. Right: the saved direct-service option exists on 38 of 156 directed interzonal pairs in the complete 13-zone system. A stop on the map does not by itself guarantee an OD alternative, legal crossing, accessible entrance, or transfer. BART from a different service date and documentary Bear Transit maps are excluded from this selected-day calculation. Service date 5 October 2026; feed S1000256; no observed-operations inference. © OpenStreetMap contributors for road context; AC Transit scheduled source.'
    finish(fig,'transit_network','Scheduled transit geography and model availability','transit',caption,{'a':'All 168 source-envelope stop coordinates','b':'Binary direct-transit OD availability, all 13 × 13 cells'},['transit_stops.csv','transit_direct.csv','zones.csv','physical_geometry.csv'],{'stops':stops,'direct_options':direct,'availability_matrix':mat.tolist()})

def transit_service():
    hrs=csvread('transit_service_hours.csv');direct=csvread('transit_direct.csv')
    fig=new_figure('berkeley','Scheduled service and direct-option time components','Source timetable / engineering mode-choice inputs',figsize=(11.0,5.1))
    a=fig.add_axes([.08,.19,.37,.54]);title(a,'a  Selected-date stop departures');a.bar(vals(hrs,'hour'),vals(hrs,'stop_events'),color=TEAL,width=.82);labels(a,'Timetable clock hour (24+ retained)','Scheduled stop events');a.set_xticks([0,4,8,12,16,20,24]);a.set_xlim(-.7,27.7)
    a.axvspan(7.5,8.5,color=BLUE,alpha=.14);a.text(.03,.96,'Shaded: 08:00–09:00',transform=a.transAxes,va='top',fontsize=8)
    a=fig.add_axes([.59,.19,.35,.54]);title(a,'b  Saved direct-option components')
    names=['In-vehicle','Access','Assumed wait'];fields=['travel_time_min','access_min','wait_min']
    for i,(name,key) in enumerate(zip(names,fields)):
        y=np.sort(vals(direct,key));x=np.linspace(i-.19,i+.19,len(y));a.scatter(x,y,s=12,color=[TEAL,BLUE,INK][i],alpha=.8,zorder=3)
        a.plot([i-.25,i+.25],[np.median(y)]*2,color=INK,lw=1.3)
    a.set_xticks(range(3),names);a.set_xlim(-.5,2.5);labels(a,'38 saved direct OD alternatives','Minutes');a.text(.98,.95,'Ticks: median',transform=a.transAxes,ha='right',va='top',fontsize=8)
    caption='Panel a counts all 14,649 scheduled stop-departure events in the frozen source-envelope table for 5 October 2026, preserving timetable hours beyond midnight. These are stop events: one trip contributes at multiple stops, so this is not a count of vehicles, unique trips or observed service. The highlighted 08:00–09:00 interval matches the engineering demand hour. Panel b shows every one of the 38 saved direct OD options, with deterministic sorted offsets to reveal overlapping values. In-vehicle and access times are saved option values; the identical ten-minute waits are an explicit assumption. Transfers are zero and fare is USD 2.50 in this case. No ridership or wait-time observations are inferred.'
    finish(fig,'transit_service','Scheduled service and direct-option time components','transit',caption,{'a':'Selected-day stop-event count by timetable hour','b':'All 38 option times; sorted point offsets, median ticks'},['transit_service_hours.csv','transit_direct.csv'],{'hourly_stop_events':hrs,'direct_options':direct})

def static_source_margins():
    demand=csvread('static_demand.csv');gen=csvread('generation_complete.csv');origin=np.zeros(13);dest=np.zeros(13)
    for r in demand:origin[ZIDS.index(r['o_zone_id'])]+=float(r['volume']);dest[ZIDS.index(r['d_zone_id'])]+=float(r['volume'])
    assert np.isclose(origin.sum(),953.049842713612)
    fig=new_figure('berkeley','Demand ledger and vehicle assignment margins','S72 / one declared morning hour',figsize=(11.0,5.4))
    a=fig.add_axes([.10,.22,.33,.53]);title(a,'a  Person-trip boundary ledger')
    keys=['external_or_uncaptured_person_trips','intrazonal_person_trips','interzonal_production_person_trips'];total=[sum(float(r[k]) for r in gen) for k in keys]
    bars=a.barh([0,1,2],total,color=[ROAD,BLUE,TEAL],height=.56);a.set_yticks([0,1,2],['External / uncaptured','Intrazonal','Internal interzonal']);a.invert_yaxis();a.set_xlim(0,5600);a.grid(False,axis='y');a.grid(axis='x',color=GRID,lw=.5);a.set_xlabel('Person trips in the declared hour')
    for i,v in enumerate(total):a.text(v+55,i,f'{v:,.2f}',va='center',fontsize=8)
    a=fig.add_axes([.58,.22,.36,.53]);title(a,'b  Positive-drive OD margins');a.bar(ZN-.19,origin,width=.38,color=TEAL,label='Origins');a.bar(ZN+.19,dest,width=.38,color=BLUE,label='Destinations');a.set_xticks(ZN,ZN,fontsize=7);labels(a,'Model zone, complete order','Vehicle demand (PCE/h)');a.legend(fontsize=8)
    caption='The first panel retains the complete one-hour person ledger: 4,705.530375 external/uncaptured, 152.0248275 intrazonal and 2,381.7222975 internal-interzonal person trips. The second panel aggregates all 72 positive vehicle OD pairs by all 13 possible origin/destination zones. Each side sums to 953.049842713612 PCE/h, after the single person-to-vehicle conversion; absence of positive vehicle demand remains zero. This separates the boundary/capture ledger from the actual assignment margins. The assumptions are 0.65 HBW movements/resident/day, 35% morning allocation, 35% capture, 6% intrazonal share, and 1.30 occupancy; these are engineering values, not locally fitted rates.'
    finish(fig,'static_source_margins','Demand ledger and vehicle assignment margins','static',caption,{'a':'Person-trip generation boundary ledger','b':'Complete 13-zone vehicle origin and destination margins'},['generation_complete.csv','static_demand.csv','zones.csv'],{'person_ledger':dict(zip(keys,total)),'zone_ids':ZIDS,'origin_pce_h':origin.tolist(),'destination_pce_h':dest.tolist(),'od_rows':demand})

def static_endpoints():
    demand=csvread('static_demand.csv');margins=[np.zeros(13),np.zeros(13)]
    for r in demand:
        margins[0][ZIDS.index(r['o_zone_id'])]+=float(r['volume']);margins[1][ZIDS.index(r['d_zone_id'])]+=float(r['volume'])
    vmax=max(np.max(v) for v in margins)
    fig=new_figure('berkeley','Where the vehicle demand enters and leaves','S72 / actual access-node geometry',figsize=(11.2,6.1))
    for pos,val,label in zip([.07,.56],margins,['a  Origin PCE/h','b  Destination PCE/h']):
        a=fig.add_axes([pos,.17,.34,.61]);title(a,label);basemap(a);zonelabels(a)
        for z,q in zip(ZONES,val):
            if z['auto_access_node'] and q>0:
                x,y=NODEXY[z['auto_access_node']];a.scatter(x,y,s=380*q/vmax,c=[q],cmap=FLOW_CMAP,vmin=0,vmax=vmax,edgecolors=INK,lw=.4,zorder=4)
        box=a.get_position();cb=fig.colorbar(plt.cm.ScalarMappable(norm=Normalize(0,vmax),cmap=FLOW_CMAP),cax=fig.add_axes([box.x1+.01,box.y0,.012,box.height]));cb.set_label('PCE/h')
    caption='Origin and destination margins from all 72 positive vehicle OD rows are placed at the actual saved auto access nodes. Both panels share the same color and symbol-area scale, with area proportional to PCE/h and zero-demand symbols omitted. All 13 polygons and all 2,150 retained road links remain as context; zone numbering is consistent with the OD matrix. Source and sink are engineering access nodes, not surveyed parcel entrances or observed trip endpoints. Each side sums to 953.049842713612 PCE/h. © OpenStreetMap contributors; Census-derived zone geography.'
    finish(fig,'static_endpoints','Where the vehicle demand enters and leaves','static',caption,{'a':'Origin demand at actual access nodes','b':'Destination demand at actual access nodes'},['static_demand.csv','zones.csv','physical_geometry.csv','static_link_attributes.csv'],{'zone_ids':ZIDS,'origin_pce_h':margins[0].tolist(),'destination_pce_h':margins[1].tolist(),'common_symbol_area_max':380,'common_color_max_pce_h':float(vmax)})

def fw_saved_check():
    hist=csvread('static_fw_history.csv');assert len(hist)==1 and int(hist[0]['iteration'])==0
    gate=jread('static_policy.json')['fw']['full_relative_gap_abs'];assert gate==1e-5
    q=float(hist[0]['objective']);gap=float(hist[0]['relative_gap']);signed=float(hist[0]['signed_gap']);guard=-1e-8
    assert 0<gap<=gate and signed>=guard and hist[0]['step']==''
    fig=new_figure('berkeley','Frank–Wolfe: initial stopping check','S72 / 72 OD / one-hour static assignment',figsize=(9.8,4.4))
    a=fig.add_axes([.065,.25,.30,.49]);a.set_axis_off();a.set_title('a  Saved state',loc='left',fontsize=10,fontweight='bold',pad=10)
    for y,label,value in [(.82,'Saved iteration','0'),(.61,'FW updates','0')]:
        a.text(0,y,label,fontsize=9,va='center');a.text(.91,y,value,fontsize=12,weight='bold',ha='right',va='center',color=TEAL)
    a.axhline(.46,color=GRID,lw=.8);a.text(0,.33,'Beckmann objective',fontsize=9)
    a.text(0,.12,f'{q:,.6f}',fontsize=16,color=INK,weight='bold');a.text(.99,.12,'PCE·min',fontsize=8,ha='right')
    a=fig.add_axes([.48,.31,.46,.43]);title(a,'b  Initial gap versus stopping gate');a.set_xscale('log');a.set(xlim=(1e-16,1e-4),ylim=(0,1),yticks=[])
    a.grid(False);a.spines['left'].set_visible(False);a.tick_params(axis='x',which='minor',bottom=False)
    a.set_xticks([1e-16,1e-12,1e-8,1e-4]);a.set_xlabel('Relative gap (dimensionless, log scale)')
    a.scatter([gap],[.40],s=58,color=TEAL,zorder=4);a.vlines(gate,.12,.68,color=BLUE,linestyles='--',lw=1.3)
    a.annotate('Saved gap\n9.93068 × 10⁻¹⁶',xy=(gap,.40),xytext=(0,20),textcoords='offset points',ha='left',va='bottom',color=TEAL,fontsize=9)
    a.annotate('Frozen gate\n10⁻⁵',xy=(gate,.68),xytext=(0,4),textcoords='offset points',ha='center',va='bottom',color=BLUE,fontsize=9)
    fig.text(.065,.155,'Initial stopping check passed — no update was taken.',fontsize=10,weight='bold',color=TEAL)
    fig.text(.065,.095,'Signed gap: 2.72848 × 10⁻¹² PCE·min; lower guard: −10⁻⁸ PCE·min (passed).',fontsize=8,color=INK)
    caption='The accepted S72 algorithm-transfer FW run stops at initialization: its complete history has one row (iteration 0), no step length and zero updates. Panel a reports the saved Beckmann objective, 2746.0944149794555 PCE·min, as a value rather than a point on an arbitrarily magnified objective axis. Panel b places the saved dimensionless relative gap 9.930680236469416e−16 and the frozen 1e−5 gate on a horizontal log axis; these are a measurement and its threshold, not two iterations. The solver also requires signed gap >= −1e−8 PCE·min; the saved signed gap is 2.7284841053187847e−12 PCE·min, so both stopping conditions pass before an update. Relative gap is signed gap divided by max(total travel cost, 1e−12), not by the Beckmann objective. Values near floating-point precision are not evidence of a meaningful precision advantage. The independent same-instance evaluator reports 4.96534011823471e−16 relative gap; the upstream four-stage initial assignment reports 1.6551133727449009e−15 under its distinct 1e−4 gate. Those separate checks remain separate, and no convergence trajectory is invented.'
    finish(fig,'fw_saved_check','Frank–Wolfe: initial stopping check','static',caption,{'a':'Saved iteration 0, zero updates and raw Beckmann objective as direct values','b':'One saved relative gap on a horizontal logarithmic metric axis versus its frozen gate; separate signed-gap guard'},['static_fw_history.csv','static_policy.json'],{'history':hist,'gate':gate,'updates':0,'signed_gap_lower_guard_pce_minutes':guard,'relative_gap_definition':'signed_gap / max(total_travel_cost, 1e-12)','stopping_rule':'abs(relative_gap) <= gate and signed_gap >= -1e-8','initial_stopping_check_passed':True,'gap_axis':'horizontal logarithmic; no iteration axis','objective_display':'direct value; no objective axis'})

def time_layers():
    arcs=csvread('time_layer_arcs.csv');nodes=csvread('time_layer_nodes.csv');path=csvread('t01_selected_path.csv')[:6]
    coords={r['physical_node_id']:xy([[r['longitude'],r['latitude']]])[0] for r in nodes};order={r['physical_node_id']:i for i,r in enumerate(nodes)}
    pathkeys={(r['link_id'],int(r['from_time_step']),int(r['to_time_step'])) for r in path}
    states={(r['from_physical_node_id'],int(r['from_time'])) for r in arcs}|{(r['to_physical_node_id'],int(r['to_time'])) for r in arcs}
    fig=new_figure('berkeley','Road states across selected time layers','Actual T4 fragment / time indices 5–11',figsize=(11.5,6.0))
    a=fig.add_axes([.025,.11,.55,.64],projection='3d');a.set_title('a  Actual local node-time graph',loc='left',fontsize=10,weight='bold')
    for r in arcs:
        p=coords[r['from_physical_node_id']];q=coords[r['to_physical_node_id']];t,u=int(r['from_time']),int(r['to_time']);highlight=(r['physical_link_id'],t,u) in pathkeys
        a.plot([p[0],q[0]],[p[1],q[1]],[t,u],color=TEAL if highlight else (BLUE if r['arc_type']=='waiting' else ROAD),lw=2 if highlight else .6,alpha=1 if highlight else .7)
    for t in range(5,12):
        p=np.array([coords[n] for n,u in states if u==t]);a.scatter(p[:,0],p[:,1],np.full(len(p),t),s=6,color=INK,alpha=.7)
    a.set(xlabel='',ylabel='',zlabel='Time index / 30 s');a.set_zticks([5,7,9,11]);a.view_init(elev=21,azim=-55);a.tick_params(labelsize=7);a.set_box_aspect((1,.7,1.2));a.xaxis.set_major_locator(MaxNLocator(4));a.yaxis.set_major_locator(MaxNLocator(4))
    a.text2D(.17,-.14,'East and north of display origin (km)',transform=a.transAxes,fontsize=8)
    b=fig.add_axes([.69,.18,.25,.52]);title(b,'b  Same fragment, discrete states')
    for r in arcs:
        t,u=int(r['from_time']),int(r['to_time']);j,k=order[r['from_physical_node_id']],order[r['to_physical_node_id']];highlight=(r['physical_link_id'],t,u) in pathkeys
        b.plot([t,u],[j,k],color=TEAL if highlight else (BLUE if r['arc_type']=='waiting' else ROAD),lw=2 if highlight else .7,zorder=4 if highlight else 1)
    for t in range(5,12):
        js=[order[n] for n,u in states if u==t];b.scatter(np.full(len(js),t),js,s=9,color=INK,zorder=2)
    b.set_yticks(range(7),[r['physical_node_id'] for r in nodes]);b.set_xticks(range(5,12));labels(b,'Time index, 30 s per step','Physical node ID')
    caption='A declared local fragment of the accepted T4 graph shows seven real road nodes across time indices 5–11 (08:02:30–08:05:30). Every drawn edge is a saved dynamic arc with both endpoints in this node/time window. Teal marks the first six actual movement arcs of positive computed column 1; blue marks waiting arcs, and gray marks other retained movements. Both panels display the same 57-arc fragment, first in actual local geographic coordinates and then as a discrete node/time graph. Only node-time states present as endpoints in the saved arc subset are marked. This is a construction view, not a whole-city dynamic simulation or the complete 89-movement route. Arc costs and rounded 30-second time increments are different quantities; the following route figure retains that distinction.'
    finish(fig,'time_layers','Road states across selected time layers','construction',caption,{'a':'Actual geographic 3D local graph at seven time layers','b':'Same saved arc subset in a node-ID/time-index graph'},['time_layer_arcs.csv','time_layer_nodes.csv','t01_selected_path.csv'],{'arcs':arcs,'nodes':nodes,'highlighted_path_arcs':path,'selected_time_indices':list(range(5,12))})

def cg_phase_one():
    data=jread('t02_cg_phases.plot_data.json');rs=data['phase_i'];x=vals(rs,'round')
    fig=new_figure('berkeley','Column generation: Phase I feasibility','T4 / all five saved rounds',figsize=(10.5,4.8))
    a=fig.add_axes([.09,.22,.35,.51]);title(a,'a  Total artificial flow');a.step(x,vals(rs,'artificial_flow'),where='post',color=TEAL,lw=1.7);a.scatter(x,vals(rs,'artificial_flow'),s=27,color=TEAL,zorder=3);a.axhline(0,color=INK,lw=.6);a.set_xticks(range(5));a.set_ylim(-.07,1.4);labels(a,'Phase I saved round','Artificial flow (PCE)')
    a=fig.add_axes([.59,.22,.35,.51]);title(a,'b  Available path columns');a.step(x,vals(rs,'pool_columns'),where='post',color=BLUE,lw=1.7);a.scatter(x,vals(rs,'pool_columns'),s=27,color=BLUE,zorder=3);a.set_xticks(range(5));a.set_yticks(range(4,9));labels(a,'Phase I saved round','Columns in restricted master')
    caption='All five saved Phase-I records are retained. Total artificial flow stays at 1.2003774460867707 PCE through rounds 0–3 and reaches zero at round 4; the available pool grows from four to eight columns. The frozen artificial-flow tolerance is 1e−8 PCE. The saved records contain aggregate artificial flow, not its OD-by-round allocation, so the second panel shows real saved pool growth rather than an invented per-OD artificial-flow heatmap. Phase-I reduced costs are dimensionless and appear in the separate closure figure.'
    finish(fig,'cg_phase_one','Column generation: Phase I feasibility','finite',caption,{'a':'Aggregate artificial flow at each saved phase-I round','b':'Saved Phase-I pool size'},['t02_cg_phases.plot_data.json','t02_frozen_pricing_gates.json'],{'phase_i':rs,'artificial_flow_gate_pce':1e-8})

def cg_phase_two():
    rs=jread('t02_cg_phases.plot_data.json')['phase_ii'];lp=jread('accuracy_objective_vs_lp.plot_data.json')['same_T4_LP_objective_pce_minutes'];x=vals(rs,'round')
    y=vals(rs,'master_objective');delta=np.diff(y)
    assert list(x)==[0,1,2] and delta[0]<0 and delta[1]==0
    fig=new_figure('berkeley','Phase II objective','T4 / four OD / three saved states',figsize=(9,5.4))
    a=fig.add_axes([.13,.22,.80,.54]);format_axes(a)
    a.step(x,y,where='post',color=TEAL,lw=1.6)
    a.axhline(lp,ls='--',color=BLUE,lw=1.2,label='Same-graph arc-flow LP')
    a.scatter(x[:1],y[:1],s=27,marker='o',facecolor='white',edgecolor=INK,label='Initial Phase II state',zorder=4)
    a.scatter(x[1:][delta<0],y[1:][delta<0],s=30,marker='o',facecolor=TEAL,edgecolor=TEAL,label='Objective decrease',zorder=5)
    a.scatter(x[1:][delta==0],y[1:][delta==0],s=30,marker='s',facecolor='white',edgecolor=TEAL,label='Objective unchanged',zorder=5)
    a.set(xlim=(-.10,2.16),ylim=(43.35,47.25),xticks=[0,1,2]);a.ticklabel_format(axis='y',style='plain',useOffset=False)
    labels(a,'Phase II round','Objective (PCE·min)');a.legend(fontsize=8,loc='upper right')
    a.annotate('LP cost reached;\npricing still open',xy=(1,y[1]),xytext=(.43,44.35),fontsize=8,color=INK,arrowprops={'arrowstyle':'->','lw':.7,'color':INK})
    a.annotate('Pricing closes',xy=(2,y[2]),xytext=(1.57,44.35),fontsize=8,color=INK,arrowprops={'arrowstyle':'->','lw':.7,'color':INK})
    caption='Boston-matched raw-objective post-step view of all three saved Phase-II states (rounds 0–2), not a normalized or logarithmic error plot. The hollow initial circle, filled decrease circle and hollow unchanged square classify adjacent recorded objective values; the Berkeley trace does not store Boston commit-classification labels, so no degenerate-commit claim is made. Objective decreases from 46.81717881521473 to 43.667424408006426 PCE·min at round 1 and is unchanged at round 2. The same-T4 independent LP is 43.66742440800644 PCE·min. Round 1 agrees with LP within floating-point precision but still has minimum full-graph reduced cost −0.06717 min; pricing closes only at round 2 (−4.44e−16 min). Only saved states are drawn. This is the four-OD finite T4 instance, not S72.'
    finish(fig,'cg_phase_two','Phase II objective','finite',caption,{'a':'Raw objective post-step, recorded initial/decreased/unchanged states, same-graph LP and distinct pricing-closure round'},['t02_cg_phases.plot_data.json','accuracy_objective_vs_lp.plot_data.json'],{'phase_ii':rs,'same_T4_LP_objective_pce_minutes':lp,'objective_delta_from_previous':[None,*delta.tolist()],'display_classification':['initial','objective_decrease','objective_unchanged'],'classification_source':'Derived from adjacent saved objective values; not a solver commit category.','matching_reference':'Boston cg_figures / G-F079; raw linear objective with post-step and point classes'})

def cg_pricing_closure():
    data=jread('t02_cg_phases.plot_data.json');fig=new_figure('berkeley','Complete-graph pricing closure','Different phase objectives imply different units',figsize=(10.8,4.9))
    for x0,key,label,unit in [(.10,'phase_i','a  Phase I','dimensionless'),(.60,'phase_ii','b  Phase II','min')]:
        rs=data[key];a=fig.add_axes([x0,.24,.34,.50]);title(a,label);a.plot(vals(rs,'round'),vals(rs,'min_full_graph_reduced_cost'),'o-',color=TEAL if key=='phase_i' else BLUE,ms=4,lw=1.4);a.axhline(0,color=INK,lw=.7);a.set_xticks(vals(rs,'round'));labels(a,'Saved round',f'Minimum reduced cost ({unit})');a.text(.40,.14,'Gate: −10⁻⁸' if key=='phase_i' else 'Gate: −10⁻⁷ min',transform=a.transAxes,fontsize=8)
    caption='Every saved minimum complete-graph reduced cost is shown on its own phase axis. Phase I uses dimensionless costs; Phase II uses minutes. The frozen negative-reduced-cost tolerances are 1e−8 and 1e−7 minutes respectively. Zero is drawn as a reference; the distinct tolerances are annotated because they are indistinguishable from zero at this scale. Final Phase-I pricing is zero; final Phase-II pricing is −4.4408920985e−16 minutes, with ten available columns. No exhaustion label or extra curve is inferred from these saved fields.'
    finish(fig,'cg_pricing_closure','Complete-graph pricing closure','finite',caption,{'a':'Phase-I full-graph minimum reduced cost, unitless','b':'Phase-II full-graph minimum reduced cost, minutes'},['t02_cg_phases.plot_data.json','t02_frozen_pricing_gates.json'],data)

def lr_bounds():
    data=jread('t03_lr_bounds_physical.plot_data.json');rs=data['LR_history'];x=vals(rs,'iteration');lp=jread('accuracy_objective_vs_lp.plot_data.json')['same_T4_LP_objective_pce_minutes']
    low=vals(rs,'best_dual');high=vals(rs,'best_primal');gap=vals(rs,'gap')*100
    assert np.isnan(high[:9]).all() and np.isnan(gap[:9]).all() and np.isfinite(high[9]) and np.ptp(low)==0
    assert np.isclose(gap[-1],100*(high[-1]-low[-1])/max(1,abs(high[-1])),rtol=1e-12)
    fig=new_figure('berkeley','Lagrangian bounds and certified gap','T4 / ten iterations / first feasible recovery at 10',figsize=(9,4.5))
    a=fig.add_axes([.09,.18,.38,.60]);title(a,'a  Best saved bounds')
    a.step(x,low,where='post',color=TEAL,lw=1.7,label='Best dual lower bound')
    a.step(x,high,where='post',color=BLUE,lw=1.7,marker='o',ms=4.5,label='Recovered primal upper bound')
    a.scatter([x[-1]],[low[-1]],color=TEAL,s=22,zorder=3)
    a.set(xlim=(.7,10.6),ylim=(43.56,43.735),xticks=[1,4,7,10]);a.ticklabel_format(axis='y',style='plain',useOffset=False)
    labels(a,'Lagrangian iteration','Objective (PCE·min)');a.legend(loc='upper left',fontsize=7.5)
    a.annotate('First feasible upper\nat iteration 10',xy=(10,high[-1]),xytext=(-7,9),textcoords='offset points',ha='right',va='bottom',fontsize=7.5,color=BLUE)
    a.text(1.4,43.595,'Best lower bound unchanged',fontsize=7.5,color=TEAL)
    a=fig.add_axes([.61,.18,.34,.60]);title(a,'b  Certified relative gap')
    a.step(x,gap,where='post',color=TEAL,lw=1.7);a.scatter([10],[gap[-1]],color=TEAL,s=25,zorder=3)
    a.axhline(1,color=BLUE,ls='--',lw=1.2,label='Frozen 1% gate')
    a.set(xlim=(.7,10.6),ylim=(0,1.15),xticks=[1,4,7,10]);labels(a,'Lagrangian iteration','Certified primal–dual gap (%)')
    a.text(1.4,.59,'No feasible upper bound\nat iterations 1–9',fontsize=8,color=INK)
    a.annotate(f'{gap[-1]:.4f}% at iteration 10',xy=(10,gap[-1]),xytext=(-7,9),textcoords='offset points',ha='right',va='bottom',fontsize=8,color=TEAL)
    a.legend(loc='upper right',fontsize=8)
    caption='The Hong Kong/Boston bound-and-gap design is applied to the actual Berkeley trace: teal is the saved best dual lower bound, blue the separately recovered feasible primal upper, and the right panel is the certified relative gap in percent on a linear axis. All ten best lower bounds equal 43.58459836422644 PCE·min; the flat line is real. The first and only saved feasible upper is 43.667424408006426 PCE·min at iteration 10, so it appears as a blue point, with a single gap point of 0.18967467145784354%, below the frozen 1% gate. The gap is 100×(best_primal−best_dual)/max(1,|best_primal|). Missing primal/gap values at iterations 1–9 remain missing; no curve is extrapolated. The independent same-T4 LP 43.66742440800644 remains in the source record but is not drawn as an LR upper-bound trajectory. Current relaxed dual iterates are not substituted for the best bound.'
    finish(fig,'lr_bounds','Lagrangian bounds and certified gap','finite',caption,{'a':'Saved best dual lower (teal) and feasible recovered upper (blue), preserving nine missing upper bounds','b':'Saved gap percent and frozen 1% gate; only iteration 10 has a certificate'},['t03_lr_bounds_physical.plot_data.json','accuracy_objective_vs_lp.plot_data.json'],{'history':rs,'same_T4_LP_objective_pce_minutes':lp,'independent_LP_drawn':False,'gate_percent':1,'gap_definition':'100 * (best_primal - best_dual) / max(1, abs(best_primal))','matching_reference':'Hong Kong bounds / C-HK-LAGRANGIAN-BOUNDS and Boston admm_lagrangian / G-F147; raw linear bounds and gap percent'})

def lr_prices():
    rs=jread('t03_lr_bounds_physical.plot_data.json')['LR_history'];x=vals(rs,'iteration')
    fig=new_figure('berkeley','Lagrangian prices and relaxed capacity violations','T4 / current iterates, not the best-dual state',figsize=(11.1,5.0))
    for x0,k,t,y,color in [(.075,'max_multiplier','a  Maximum capacity multiplier','Price (min)',TEAL),(.395,'multiplier_positive_count','b  Positive-price arc count','Priced dynamic arcs',BLUE),(.715,'max_current_capacity_violation','c  Current relaxed capacity excess','Maximum excess (PCE)',INK)]:
        a=fig.add_axes([x0,.24,.23,.50]);title(a,t);a.plot(x,vals(rs,k),'o-',ms=3.5,lw=1.3,color=color);a.set_xticks([1,4,7,10]);labels(a,'Saved LR iteration',y);a.set_ylim(bottom=0)
    caption='All ten saved current-iterate summaries are retained: maximum capacity multiplier in minutes (PCE·min objective divided by PCE capacity), number of strictly positive-price dynamic arcs, and maximum current relaxed capacity excess in PCE. These current price iterates are not the best-dual multiplier state, which is an independent saved vector; large swings do not change the flat best-valid-bound sequence. Relaxed capacity violation does not describe the final separately recovered feasible flow. Only these recorded summaries are plotted, without inventing per-arc history or interpolated recovery outcomes.'
    finish(fig,'lr_prices','Lagrangian prices and relaxed capacity violations','finite',caption,{'a':'Current maximum multiplier, min','b':'Current positive multiplier count','c':'Current relaxed maximum capacity excess, PCE'},['t03_lr_bounds_physical.plot_data.json'],{'history':rs})

def lr_recovery():
    rs=jread('t03_lr_bounds_physical.plot_data.json')['LR_history'];rec=jread('t03_recovery_history.json');fig=new_figure('berkeley','Path-pool growth and separate primal recovery','T4 / two saved recovery calls',figsize=(10.8,4.9))
    a=fig.add_axes([.10,.23,.34,.51]);title(a,'a  Saved path pool');a.step(vals(rs,'iteration'),vals(rs,'path_pool_size'),where='post',color=TEAL,lw=1.5);a.scatter(vals(rs,'iteration'),vals(rs,'path_pool_size'),s=23,color=TEAL);a.set_yticks([4,5,6]);labels(a,'Saved LR iteration','Available paths')
    a=fig.add_axes([.60,.23,.34,.51]);title(a,'b  Actual recovery LP calls')
    for r in rec:a.scatter(r['iteration'],r['path_count'],s=65,facecolors=TEAL if r['feasible'] else 'white',edgecolors=TEAL if r['feasible'] else BLUE,lw=1.3,label='Feasible' if r['feasible'] else 'Infeasible',zorder=3)
    a.set_xlim(.3,10.7);a.set_ylim(3.5,7);a.set_xticks([1,10]);a.set_yticks([4,5,6,7]);labels(a,'LR iteration at recovery call','Paths supplied to recovery LP');a.legend(fontsize=8,loc='upper left')
    a.annotate('Null objective',xy=(1,4),xytext=(2.3,4.1),fontsize=8);a.annotate('43.66742441\nPCE·min',xy=(10,6),xytext=(6.2,5),fontsize=8,arrowprops={'arrowstyle':'-','color':INK,'lw':.6})
    caption='All ten path-pool sizes and exactly two saved recovery attempts are shown. The call at iteration 1 uses four paths and is infeasible, so its objective remains null. The call at iteration 10 uses six paths and is feasible, with objective 43.667424408006426 PCE·min. The curve in panel a is path-pool growth, not a sequence of solved feasible upper bounds. A separate physical-link projection figure compares the actual recovered LR flow against independent LP and CG, rather than substituting their flow as LR output.'
    finish(fig,'lr_recovery','Path-pool growth and separate primal recovery','finite',caption,{'a':'All saved path-pool sizes','b':'Exactly two recovery calls and their feasibility'},['t03_lr_bounds_physical.plot_data.json','t03_recovery_history.json'],{'history':rs,'recovery':rec})

if __name__=='__main__':
    for f in [source_geography,population_jobs,transit_network,transit_service,static_source_margins,static_endpoints,fw_saved_check,time_layers,cg_phase_one,cg_phase_two,cg_pricing_closure,lr_bounds,lr_prices,lr_recovery]:f()
    (HERE/'NEW_FIGURES.json').write_text(json.dumps({'status':'PENDING_VISUAL_QA','solver_calls':0,'figures':RECORDS},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
