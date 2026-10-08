"""Render the 2026-10-09 mainline increment from saved public plot data only.

Ann Arbor panels reuse the existing make_figures.py geometry and calculations;
Chicago history follows render_followup.py, replacing the constant-rho and
runtime panels with original-unit objective/primal/dual diagnostics. No solver.
"""
from pathlib import Path
import csv,json,math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'docs/assets/mainline-publication-20261009'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def rows(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def render_ann():
    evidence=DATA/'ann-arbor';assert read(evidence/'FW_CHECK.json')['status']=='PASS'
    figs=evidence;figs.mkdir(exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Serif','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'white','axes.facecolor':'white','svg.fonttype':'none','axes.titleweight':'bold'})
    od=rows(evidence/'VEHICLE_DEMAND.csv');phys=rows(evidence/'PHYSICAL_ROAD_FLOW.csv');order=read(evidence/'ZONE_ORDER.json');zi={z:i for i,z in enumerate(order)};mat=np.zeros((25,25))
    for r in od:mat[zi[r['o_zone_id']],zi[r['d_zone_id']]]=float(r['vehicle_demand_pce_hour'])
    curves=[];flow=[]
    for r in phys:
        text=r['geometry_wkt'].removeprefix('LINESTRING (').removesuffix(')');curves.append(np.array([list(map(float,p.strip().split())) for p in text.split(',')]));flow.append(float(r['assigned_flow_pce_hour']))
    flow=np.array(flow);colors=plt.cm.YlGnBu;navy='#17364d';teal='#218b86'
    fig,ax=plt.subplots(1,2,figsize=(11.5,4.8),gridspec_kw={'width_ratios':[1,1.25]});fig.subplots_adjust(left=.08,right=.94,bottom=.23,top=.82,wspace=.32)
    im=ax[0].imshow(mat,origin='upper',cmap='Blues',vmin=0);ax[0].set_title('a  Vehicle demand');ax[0].set(xlabel='Destination zone',ylabel='Origin zone',xticks=[0,6,12,18,24],yticks=[0,6,12,18,24],xticklabels=[order[i][3:] for i in [0,6,12,18,24]],yticklabels=[order[i][3:] for i in [0,6,12,18,24]])
    fig.colorbar(im,ax=ax[0],fraction=.045,pad=.035,label='Vehicle demand (PCE/h per OD)')
    ax[1].add_collection(LineCollection(curves,colors='#d2d7dc',linewidths=.45,zorder=1))
    positive=flow>0;norm=matplotlib.colors.Normalize(vmin=0,vmax=float(max(flow)));lc=LineCollection([s for s,p in zip(curves,positive) if p],array=flow[positive],cmap=colors,norm=norm,linewidths=.6+1.6*np.sqrt(flow[positive]/max(flow)),zorder=2);ax[1].add_collection(lc);ax[1].autoscale();ax[1].set_aspect(1/math.cos(math.radians(42.28)));ax[1].set_title('b  Assigned flow');ax[1].set(xlabel='Longitude',ylabel='Latitude');ax[1].tick_params(labelsize=8);ax[1].ticklabel_format(axis='both',useOffset=False);ax[1].locator_params(axis='x',nbins=4);ax[1].locator_params(axis='y',nbins=4)
    fig.colorbar(lc,ax=ax[1],fraction=.035,pad=.035,label='Assigned flow (PCE/h per road arc)')
    fig.suptitle('Ann Arbor | timetable demand reaches the original road graph',x=.08,ha='left',fontsize=13)
    fig.text(.08,.115,f"600 positive vehicle OD • {sum(float(r['vehicle_demand_pce_hour']) for r in od):,.6f} PCE/h • 5,138 physical road arcs; {sum(flow==0):,} zero-flow arcs retained.",fontsize=8)
    fig.text(.08,.07,'2026-10-05 timetable scenario, 08:00–09:00 HBW. Engineering coefficients; not measured or locally calibrated traffic.',fontsize=8)
    fig.text(.08,.035,'Grey = zero flow; all directed roads retained. © OpenStreetMap contributors; ODbL 1.0. Database and source notice accompany this figure.',fontsize=8)
    for ext in ['png','svg','pdf']:fig.savefig(figs/('ANN_CHOICE_FW_NETWORK.'+ext),dpi=220)
    plt.close(fig)
    checkpoint=read(evidence/'CHECKPOINT_AUDIT.json')['states'];iterations=[r['iteration'] for r in checkpoint];objective=[r['objective'] for r in checkpoint];gaps=[r['full_relative_gap'] for r in checkpoint]
    fig,ax=plt.subplots(1,2,figsize=(10.5,3.8));fig.subplots_adjust(left=.11,right=.95,bottom=.27,top=.8,wspace=.44)
    ax[0].plot(iterations,np.array(objective)-objective[-1],'-o',color=navy,ms=5);ax[0].set(xlabel='Actual FW update count',ylabel='Objective above final (PCE·min)',title='a  New branch objective',xticks=iterations)
    ax[1].plot(iterations,gaps,'-o',color=teal,ms=5);ax[1].axhline(1e-5,color='#a88b42',ls='--',lw=.9,label='Fixed gate 1e−5');ax[1].set(xlabel='Actual FW update count',ylabel='Signed full-graph relative gap',title='b  Original-graph check',xticks=iterations);ax[1].legend(frameon=False,fontsize=8,loc='upper right');ax[1].ticklabel_format(axis='y',style='sci',scilimits=(0,0))
    for i,g in zip(iterations,gaps):ax[1].annotate(f'{g:.3e}',(i,g),xytext=((-5,-17) if i==iterations[-1] else (3,8)),ha=('right' if i==iterations[-1] else 'left'),textcoords='offset points',fontsize=8)
    ax[1].margins(y=.28)
    fig.suptitle('Ann Arbor | one actual FW update, no padded trajectory',x=.11,ha='left',fontsize=13)
    fig.text(.11,.12,'Only ANN_TRANSIT_CHOICE_FW_V002 is shown. The old S600 and separate S72 are different demand instances.',fontsize=8)
    fig.text(.11,.065,'Iteration 0 failed the original gap gate; iteration 1 passed. A short curve does not determine geographic adequacy.',fontsize=8)
    fig.text(.11,.025,'Saved engineering result, service date 2026-10-05. Signed floating-point gaps retained; historical scenario, not a current journey planner.',fontsize=8)
    for ext in ['png','svg','pdf']:fig.savefig(figs/('ANN_CHOICE_FW_CONVERGENCE.'+ext),dpi=220)
    plt.close(fig)

def render_chicago():
    out=DATA/'chicago'; rs=rows(out/'ADMM_HISTORY_33_116.csv'); audit=read(out/'ENDPOINT_AUDIT.json')
    assert [int(float(r['iteration'])) for r in rs]==list(range(33,117))
    get=lambda k: np.array([float(r[k]) for r in rs])
    it=get('iteration'); navy='#173b64'; teal='#147d83'; amber='#a87937'; gray='#6f7780'
    plt.rcParams.update({'font.family':'DejaVu Serif','font.size':9,'axes.titlesize':11,'axes.labelsize':9,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'white','axes.facecolor':'white','savefig.facecolor':'white','svg.fonttype':'none','pdf.fonttype':42})
    fig,axs=plt.subplots(2,2,figsize=(12,7.0));fig.subplots_adjust(left=.09,right=.975,top=.88,bottom=.19,wspace=.27,hspace=.44)
    a,b,c,d=axs.flat
    a.plot(it,get('objective'),'-o',ms=2,lw=1.25,color=navy)
    a.set(title='a  Objective of original x',ylabel='Linear objective (PCE·min)')
    a.text(.98,.97,'x is infeasible; no certified upper bound\nCG objective difference not evaluated',transform=a.transAxes,ha='right',va='top',fontsize=8)
    b.plot(it,get('capacity_residual'),'-o',ms=2,lw=1.25,color=navy,label='Original x excess')
    b.axhline(1e-5,color=amber,ls='--',lw=1,label='Original gate: 1e−5 PCE')
    b.set(title='b  Shared capacity',ylabel='Maximum excess (PCE)',yscale='symlog');b.set_yscale('log') if np.all(get('capacity_residual')>0) else b.set_yscale('symlog',linthresh=1e-6);b.set_ylim(bottom=(5e-6 if np.all(get('capacity_residual')>0) else 0),top=max(get('capacity_residual'))*1.4);b.legend(fontsize=8,loc='best',frameon=False)
    c.plot(it,get('primal_residual'),'-o',ms=2,lw=1.25,color=navy,label='Primal residual')
    c.plot(it,get('primal_threshold'),'--',lw=1.1,color=amber,label='Saved per-iteration threshold')
    c.set(title='c  Primal stopping test',ylabel='Primal residual (PCE)',yscale='log');c.legend(fontsize=8,frameon=False)
    d.plot(it,get('dual_residual'),'-o',ms=2,lw=1.25,color=teal,label='Rho-scaled dual residual')
    d.plot(it,get('dual_threshold'),'--',lw=1.1,color=amber,label='Saved per-iteration threshold')
    d.scatter([116],[audit['generalized_dual']],color=navy,marker='D',s=29,zorder=4,label='Stationarity: endpoint only')
    d.set(title='d  Dual and endpoint stationarity',ylabel='Dual / stationarity (min)',yscale='log');d.legend(fontsize=7.6,frameon=False)
    for ax in axs.flat:
        ax.axvline(36.5,color=gray,ls=':',lw=.9);ax.set_xlabel('Actual complete outer iteration');ax.set_xlim(32.5,117);ax.grid(axis='y',alpha=.16)
    fig.suptitle('Chicago frozen T4 | saved ADMM diagnostic, outer 33–116',x=.09,ha='left',fontsize=14)
    fig.text(.09,.11,'84 saved rows: outer 33 is the inherited boundary; 34–36 retain the original coordination; 37–116 use alpha = 1.6.',fontsize=8)
    fig.text(.09,.073,f"Rho = {get('rho')[0]:.12g} min/PCE throughout. Original x remains infeasible; primal, dual and stationarity gates fail at 116.",fontsize=8)
    fig.text(.09,.036,'All recorded points are shown. No smoothing or synthetic states. Stationarity has one verified endpoint; no history is inferred.',fontsize=8)
    for ext in ['png','svg','pdf']:fig.savefig(out/('ADMM_HISTORY_33_116.'+ext),dpi=220)
    plt.close(fig)
if __name__=='__main__':
    render_ann();render_chicago()
    print('Rendered three figure families from saved values; optimizer_calls=0')
