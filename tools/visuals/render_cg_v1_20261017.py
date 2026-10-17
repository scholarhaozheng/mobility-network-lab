"""Approved V1 CG cards from frozen records. No solver or pricing calls.

Use --output-root to reproduce figures separately from the maintained website.
The original nine approved assets can be promoted without re-rendering.
"""
from pathlib import Path
import json, shutil, hashlib, sys, argparse, math, subprocess, logging
logging.getLogger('fontTools.subset').setLevel(logging.ERROR)
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator, FuncFormatter

R=Path(__file__).resolve().parents[2];D=R/'docs';A=D/'assets/shared-cg-dev48-20261014'
W=R/'tools/visuals'
OUT=D/'assets/cg-v1-20261017'
sys.path.insert(0,str(R/'tools/visuals/berkeley_alignment_r2'))
from atlas_style import new_figure,format_axes,compact_header,TEAL,BLUE,INK,GRID
from embed_serif_fonts import embed_serif_fonts

ORDER=['hong_kong_10_H','boston_10_H','sioux_200_H','berkeley_T4_H','chicago_T4_H','ann_arbor_F_Q','ithaca_F_Q','pittsburgh_F_H','urbana_F_H','sioux_250_H','urbana_S2_H','pittsburgh_S2_H','pittsburgh_F_Q','urbana_F_Q','urbana_S2_Q','pittsburgh_S2_Q']
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def num(v):return f'{v:,.6g}'
def scope(c):return f"Dev48 / {c['OD']:,} OD / {c['case_id'].split('_')[-1]} / demand x{c['scale']:g}"
def gaplabel(v):return 'Numerical zero' if abs(v)<1e-10 else f'{v:.6g}%'
def physical_data_path(c):
    """Use the one published movement/geometry record for this selected run."""
    return D/next(f['data']for f in c['figures']if f['id'].endswith('physical-flow'))
def save(c,fig,stem,data,caption):
    folder=OUT/'figures'/c['case_id'];folder.mkdir(parents=True,exist_ok=True)
    compact_header(fig)
    for ext in ['svg','png']:
        fig.savefig(folder/f'{stem}.{ext}',dpi=300,bbox_inches=None if stem=='physical-flow'else'tight',pad_inches=.055,metadata={'Date':None}if ext=='svg'else None)
    embed_serif_fonts(folder/f'{stem}.svg');plt.close(fig)
    data.update(case_id=c['case_id'],run_id=c['run_id'],code_package=c['code_package'],new_solver_calls=0,new_pricing_calls=0)
    write(folder/f'{stem}.plot.json',data)
    (folder/f'{stem}.caption.txt').write_text(caption+'\n',encoding='utf8')
    inputs=[D/c['source_dir']/n for n in ['result.json','upper-certificate.json','lower-certificate.json','phase-i-combined.plot.json','phase-ii-pair.plot.json']if(D/c['source_dir']/n).exists()]
    if stem=='physical-flow':inputs.append(physical_data_path(c))
    write(folder/f'{stem}.source.json',{'source_dir':c['source_dir'],
      'inputs':[{'path':p.relative_to(D).as_posix(),'sha256':sha(p)}for p in inputs],
      'renderer_sha256':sha(Path(__file__)),'style_sha256':sha(R/'tools/visuals/berkeley_alignment_r2/atlas_style.py'),
      'retained_map_renderer':{'path':'tools/visuals/render_cg_dev48_20261014.py','sha256':sha(W/'render_cg_dev48_20261014.py')}if stem=='physical-flow'else None,
      'caption':caption,'outputs':{ext:sha(folder/f'{stem}.{ext}')for ext in ['png','svg','plot.json']}})
    return {'src':f'figures/{c["case_id"]}/{stem}.svg','png':f'figures/{c["case_id"]}/{stem}.png',
      'data':f'figures/{c["case_id"]}/{stem}.plot.json','source':f'figures/{c["case_id"]}/{stem}.source.json','caption':caption}

def pair(c,title):
    fig=new_figure(c['city_name'],title,scope(c),figsize=(9,5.4))
    axes=[fig.add_axes([.10,.23,.33,.47]),fig.add_axes([.60,.23,.32,.47])]
    for ax in axes:format_axes(ax)
    return fig,axes
def line(ax,x,y,color=TEAL):
    if len(x)>1:ax.step(x,y,where='post',color=color,lw=1.7,zorder=3)
    ax.scatter(x,y,s=18,color=color,zorder=4)
    ax.scatter(x[:1],y[:1],s=28,facecolors='white',edgecolors=color,zorder=5)
    ax.scatter(x[-1:],y[-1:],s=25,marker='D',color=color,zorder=6)
    ax.set_xlim(min(x)-.28,max(x)+.28)
    if len(x)<=4:ax.set_xticks(x)
    else:ax.xaxis.set_major_locator(MaxNLocator(5,integer=True))
def minimal_bar(ax,values,labels,colors,max_value=None):
    pos=np.arange(len(values))[::-1]
    ax.barh(pos,values,color=colors,height=.32,zorder=3)
    ax.set_yticks(pos,labels);ax.set_ylim(-.6,len(values)-.4)
    maximum=max_value if max_value is not None else max(values)*1.24
    ax.set_xlim(0,maximum);ax.grid(axis='y',visible=False);ax.grid(axis='x',color=GRID,lw=.5)
    ax.spines['left'].set_visible(False);ax.tick_params(axis='y',length=0)
    ax.xaxis.set_major_locator(MaxNLocator(4))
    for yy,v in zip(pos,values):ax.text(v+maximum*.018,yy,num(v),va='center',fontsize=8,color=INK)

def phase1(c,r,p,cert):
    h=[x for x in r.get('history',[])if x.get('phase')=='I']
    if h:
        x=np.array([a['round']for a in h]);y=np.array([a['artificial_mass']for a in h]);pool=np.array([a['column_count']for a in h])
        assert np.allclose(y,p['total_artificial_capacity_slack'],rtol=0,atol=0)
        fig,(left,right)=pair(c,'Phase I: establish capacity feasibility')
        left.set_title('a  Total capacity slack',loc='left',weight='bold',fontsize=10)
        line(left,x,y);left.set_xlabel('Saved Phase I state');left.set_ylabel('Capacity slack ('+p['unit']+')')
        left.set_ylim(-max(y.max()*.045,.01),max(y.max()*1.13,.1));left.yaxis.set_major_locator(MaxNLocator(5));left.ticklabel_format(axis='y',style='plain',useOffset=False)
        left.annotate('Feasible',xy=(x[-1],y[-1]),xytext=(-10,22),textcoords='offset points',ha='right',fontsize=8,color=TEAL)
        if len(x)>1:
            right.set_title('b  Paths available to the master',loc='left',weight='bold',fontsize=9.4)
            line(right,x,pool,BLUE);right.set_xlabel('Saved Phase I state');right.set_ylabel('Path columns')
            spread=max(float(np.ptp(pool)),float(pool.max())*.02,1)
            right.set_ylim(max(0,pool.min()-spread*.12),pool.max()+spread*.24);right.yaxis.set_major_locator(MaxNLocator(5,integer=True));right.ticklabel_format(axis='y',style='plain',useOffset=False)
            right.text(.98,.96,f'{pool[0]:,} → {pool[-1]:,}',ha='right',va='top',transform=right.transAxes,fontsize=8,color=BLUE)
        else:
            right.set_title('b  Initial pool is feasible',loc='left',weight='bold',fontsize=10)
            minimal_bar(right,[int(pool[0])],['Paths'],[BLUE]);right.set_xlabel('Available path columns')
        footer=f'{len(x)} saved states  |  slack {num(y[0])} → {num(y[-1])} {p["unit"]}  |  {int(pool[-1]-pool[0]):,} columns added before Phase II'
        if len(x)==1:footer='Initial pool already satisfies capacity constraints; no Phase I update was needed.'
        fig.text(.10,.105,footer,fontsize=8)
        fig.text(.10,.045,'Capacity-resource slack, not unmet OD demand. Open circle: first state; diamond: final state.',fontsize=7.8)
        cap=f"本次 Phase I 的 {len(x)} 个真实保存状态：容量资源松弛 {y[0]:.16g} → {y[-1]:.16g} {p['unit']}；路径池 {int(pool[0])} → {int(pool[-1])}。右图解释可行路径如何扩充，不冒充逐 OD 人工需求热图。"
        return save(c,fig,'phase-i',{'phase_i_executed':True,'round':x.tolist(),'capacity_slack':y.tolist(),'path_pool':pool.tolist(),'unit':p['unit'],'semantics':'Bx=q; Ax-s<=capacity; auxiliary slack is not unmet demand'},cap)
    if c['actual_adapter']!='uniform_release shortcut':
        fig,(left,right)=pair(c,'Feasibility: a verified starting construction')
        seed=r.get('feasible_seed_verification')
        if seed:
            n=seed['seed_path_columns'];events=seed['original_release_events']
            left.set_title('a  Feasible seed paths',loc='left',weight='bold',fontsize=10)
            minimal_bar(left,[n],['Paths'],[TEAL]);left.set_xlabel('Initial path columns')
            right.set_title('b  Original releases covered',loc='left',weight='bold',fontsize=10)
            minimal_bar(right,[events],['Events'],[BLUE]);right.set_xlabel('Original release events')
            note=f"Demand residual {seed['seed_max_event_demand_residual']:.4g} PCE; capacity excess {seed['seed_max_capacity_excess']:.4g} PCE."
            data={'phase_i_executed':False,'feasible_seed_verification':seed,'initial_path_columns':n,'original_release_events':events}
        else:
            assert c['solver_branch']=='new_joint_delta_cg'
            left.set_title('a  Full-demand base',loc='left',weight='bold',fontsize=10)
            minimal_bar(left,[c['OD']],['OD'],[TEAL]);left.set_xlabel('Original positive OD pairs')
            right.set_title('b  Generated path pool',loc='left',weight='bold',fontsize=10)
            xs=[a['round']for a in r['round_history']];xs=xs+[max(xs)+1];ys=[a['columns_before']for a in r['round_history']]+[r['total_columns']]
            line(right,np.array(xs),np.array(ys),BLUE);right.set_xticks(xs,['CG '+str(a['round'])for a in r['round_history']]+['Final'],fontsize=7);right.set_ylabel('Path columns');right.ticklabel_format(axis='y',style='plain',useOffset=False)
            note='Full-demand base + source-generated paths; final primal verified, full-graph optimality OPEN.'
            data={'phase_i_executed':False,'original_OD':c['OD'],'release_events':c['events'],'pool_state':xs,'pool_columns':ys,'final_max_capacity_excess':cert['max_original_capacity_excess']}
        fig.text(.10,.105,note,fontsize=8)
        fig.text(.10,.045,'Phase I was not executed. These are saved construction records, not artificial-flow iterations.',fontsize=7.7)
        return save(c,fig,'phase-i',data,note+' Phase I was not executed; the panels describe the actual seed/base and its represented demand or path pool.')
    ratio=cert['maximum_original_capacity_ratio'];q=cert['original_hourly_pce'];served=cert['all_original_release_events_served'];res=cert['max_original_OD_hourly_demand_residual']
    assert served and res==0
    fig,(left,right)=pair(c,'Feasibility: an exact feasible construction')
    left.set_title('a  Peak load within capacity',loc='left',weight='bold',fontsize=10)
    left.barh([0],[100],height=.32,color='#e6eeee',zorder=1);minimal_bar(left,[ratio*100],['Peak'],[TEAL],110)
    left.axvline(100,color=BLUE,ls='--',lw=1);left.text(100,.43,'Capacity',ha='right',fontsize=8,color=BLUE);left.set_xlabel('Maximum load / capacity (%)')
    right.set_title('b  All demand is served',loc='left',weight='bold',fontsize=10)
    minimal_bar(right,[q],['Served'],[BLUE]);right.set_xlabel('Hourly demand (PCE/h)')
    fig.text(.10,.105,f'{c["OD"]:,} OD  |  {c["events"]:,} release events  |  zero demand residual',fontsize=8)
    fig.text(.10,.045,'Exact uniform-release construction; Phase I was not executed. Capacity ratio is an entry-time peak.',fontsize=7.8)
    cap=f"精确构造无需 Phase I：最大时空入弧容量比 {ratio:.12g}，所有 {c['events']:,} 个释放事件需求均被服务，原 OD 残差为0。容量比来自同次独立证书，不用累计流量冒充峰值。"
    return save(c,fig,'phase-i',{'phase_i_executed':False,'branch':'exact_uniform_release','maximum_entry_capacity_ratio':ratio,'served_hourly_pce':q,'all_release_events_served':served,'demand_residual':res,'release_events':c['events']},cap)

def phase2(c,data):
    x=np.array(data['position'],float);y=np.array(data['objective'],float)
    if data['fixed_reference'] is None:
        fig,(left,right)=pair(c,'Phase II: saved objective; bound not established')
        left.set_title('a  Real objective',loc='left',weight='bold',fontsize=10);line(left,x,y)
        left.set_xticks(x,data['labels'],fontsize=7);left.set_ylabel('Cost ('+data['unit']+')');left.ticklabel_format(axis='y',style='plain',useOffset=False)
        span=max(float(np.ptp(y)),abs(y[-1])*.002);left.set_ylim(y.min()-.13*span,y.max()+.37*span)
        right.set_title('b  Final-bound reference unavailable',loc='left',weight='bold',fontsize=9);right.axis('off')
        right.text(.5,.55,'No verified same-run full-graph L\n\nReference difference is unavailable.\nOptimality remains OPEN.',ha='center',va='center',fontsize=9,transform=right.transAxes,color=INK)
        saved=data.get('saved_cg_rounds') or c.get('saved_cg_rounds')
        note=(f'{saved} saved CG rounds + the final solved RMP; final point is not an extra CG round.'if saved else'The saved objective states are shown; no verified same-run terminal bound is available.')
        if not c.get('new_run_plot_inputs'):saved=3;note='Three saved CG rounds + the final solved RMP; the diamond is not a fourth CG round.'
        fig.text(.10,.105,note,fontsize=8)
        fig.text(.10,.045,'No historical or other-run lower bound is substituted. Missing bounds are never replaced with zero.',fontsize=7.8)
        return save(c,fig,'phase-ii',{'position':x.tolist(),'labels':data['labels'],'objective':y.tolist(),'fixed_terminal_L':None,'signed_reference_difference_percent':None,'saved_states':len(x),'saved_CG_rounds':saved,'unit':data['unit']},note+' No verified same-run full-graph lower bound is available; the right reference panel remains unavailable, and optimality remains OPEN.')
    ref=float(data['fixed_reference']);rel=100*(y-ref)/abs(ref)
    assert len(x)==len(y)>0 and np.all(np.isfinite(y))
    exact=c['actual_adapter']=='uniform_release shortcut';single=len(x)==1
    fig,(left,right)=pair(c,'Phase II: real cost and final-bound reference' if not exact else 'Optimality: the construction meets its bound')
    if single:
        left.set_title('a  Feasible cost and verified bound',loc='left',weight='bold',fontsize=9.2)
        minimal_bar(left,[float(y[-1]),ref],['U','L'],[TEAL,BLUE]);left.set_xlabel('Cost ('+data['unit']+')');left.ticklabel_format(axis='x',style='plain',useOffset=False)
    else:
        left.set_title('a  Real objective',loc='left',weight='bold',fontsize=10)
        line(left,x,y);left.axhline(ref,color=BLUE,ls='--',lw=1,label='Final verified bound');left.legend(fontsize=7,loc='upper right')
        left.set_xlabel('Saved Phase II state');left.set_ylabel('Cost ('+data['unit']+')');left.ticklabel_format(axis='y',style='plain',useOffset=False)
        span=max(float(np.ptp(np.r_[y,ref])),abs(ref)*.002,1e-5)
        left.set_ylim(min(y.min(),ref)-span*.13,max(y.max(),ref)+span*.37);left.yaxis.set_major_locator(MaxNLocator(5))
        if np.ptp(y)<abs(ref)*1e-12:left.text(.03,.90,'Stable at numerical precision',transform=left.transAxes,fontsize=8,va='top',color=TEAL)
    right.set_title('b  Distance to the final bound',loc='left',weight='bold',fontsize=9.6)
    maximum=float(np.abs(rel).max());guide=.01
    if single:
        right.spines['left'].set_visible(False);right.set_yticks([]);right.set_ylim(-.65,.65);right.set_xlim(-.0015,.012)
        right.axvspan(0,.01,color='#edf5f4');right.axvline(0,color=TEAL,lw=.9);right.axvline(.01,color='#a17d4f',ls='--',lw=.9)
        right.scatter([rel[-1]],[0],s=38,marker='D',color=BLUE,zorder=4)
        right.text(.00035,.08,gaplabel(rel[-1]),fontsize=9,color=TEAL)
        right.text(.01,.45,'0.01% guide',ha='right',fontsize=7.5,color='#83623e');right.set_xticks([0,.005,.01]);right.set_xlabel('Signed difference / final bound (%)');right.grid(axis='x',color=GRID,lw=.5)
    else:
        line(right,x,rel,BLUE);right.set_xlabel('Saved Phase II state');right.set_ylabel('100 (J − final L) / |final L| (%)')
        right.axhline(0,color='#8c9da4',lw=.7);right.axhline(guide,color='#a17d4f',ls='--',lw=.9)
        right.annotate('0.01% guide',xy=(.03,guide),xycoords=('axes fraction','data'),xytext=(0,3),textcoords='offset points',fontsize=7,color='#83623e')
        if maximum>.05:
            right.set_yscale('symlog',linthresh=.001,linscale=.7)
            right.set_ylim(-.0014,max(maximum*1.7,.02));right.set_yticks([v for v in [0,.001,.01,.1,1,10,100]if v<=maximum*1.7]);right.yaxis.set_major_formatter(FuncFormatter(lambda v,p:f'{v:g}'))
        else:right.set_ylim(-.0015,max(.012,maximum*1.3));right.set_yticks([0,.005,.01])
        right.text(.97,.96,gaplabel(rel[-1]),ha='right',va='top',transform=right.transAxes,fontsize=8,color=BLUE)
    note='Exact construction: no CG iterations were required.'if exact else 'One solved Phase II state: full-graph pricing closed at the first check.'if single else f'{len(x)} saved Phase II states; every recorded state is retained.'
    if c['solver_branch']=='new_joint_delta_cg':
        rounds=data.get('saved_cg_rounds') or c.get('saved_cg_rounds') or len(x)-1
        note=f'{rounds} saved CG rounds + final solved RMP; final point is not an extra CG round. OPEN.'if c.get('new_run_plot_inputs')else'Three saved CG rounds + final solved RMP; final point is not a fourth CG round. OPEN.'
        for ax in [left,right]:ax.set_xticks(x,data['labels'],fontsize=7);ax.set_xlabel('Saved RMP state')
    fig.text(.10,.105,note,fontsize=8)
    fig.text(.10,.045,'Fixed same-run terminal bound, not a per-round pricing gap. Signed raw values remain in plot data.',fontsize=7.8)
    cap=f"左：同次真实成本{'及独立下界的终点对照'if single else'完整轨迹'}。右：100×(J−本次最终L)/|本次最终L|，固定参考L={ref:.16g}，末端有符号参考差 {rel[-1]:.16g}%。这不是逐轮定价gap；0.01%只是读图尺度参考。页面验收gap另按(U−L)/|U|列出。"+('精确构造未执行CG迭代。'if exact else'首次Phase II检查即已闭合，未虚构前后两个求解状态。'if single else'没有平滑、截取尾段或补造点。')
    return save(c,fig,'phase-ii',{'position':x.tolist(),'objective':y.tolist(),'fixed_terminal_L':ref,'signed_reference_difference_percent':rel.tolist(),'reference_formula':'100*(J-L_final)/abs(L_final)','true_certificate_gap':c['gap_raw'],'exact_presolve':exact,'saved_states':len(x),'single_state_certificate_view':single,'unit':data['unit'],'display_policy':'No amplification of floating residuals; exact signed data retained'},cap)

def diagnostic(c,result):
    h=[x for x in result.get('history',[])if x.get('phase')=='II']
    if not h:return None
    if any(a.get(k)is None for a in h for k in ['true_primal_objective','full_graph_lower_bound']):return None
    x=np.array([a['round']for a in h]);u=np.array([a['true_primal_objective']for a in h]);l=np.array([a['full_graph_lower_bound']for a in h]);g=100*(u-l)/abs(u);bestl=np.maximum.accumulate(l);bg=100*(u-bestl)/abs(u)
    fig,(left,right)=pair(c,'Pricing diagnostics: current and best saved bounds')
    left.set_title('a  Current saved bounds',loc='left',weight='bold',fontsize=10)
    line(left,x,u,TEAL);left.plot(x,l,color=BLUE,marker='s',markersize=3,lw=1,label='Current L');left.plot([],[],color=TEAL,label='Feasible U');left.legend(fontsize=7,loc='best');left.set_xlabel('Saved Phase II state');left.set_ylabel('Original cost units');left.ticklabel_format(axis='y',style='plain',useOffset=False)
    sp=max(np.ptp(np.r_[u,l]),abs(u[-1])*.002);left.set_ylim(min(u.min(),l.min())-.1*sp,max(u.max(),l.max())+.25*sp)
    right.set_title('b  Gap to current / best L',loc='left',weight='bold',fontsize=10)
    line(right,x,g,BLUE);right.plot(x,bg,color=TEAL,lw=1.1,ls='--',marker='.',markersize=3,label='Best saved L');right.plot([],[],color=BLUE,label='Current L');right.axhline(.01,color='#a17d4f',ls=':',lw=1)
    right.set_yscale('symlog',linthresh=.001,linscale=.7);right.set_xlabel('Saved Phase II state');right.set_ylabel('100 (U − L) / |U| (%)');right.legend(fontsize=7,loc='upper right');right.set_ylim(min(-.0015,float(g.min())*1.2),max(.015,float(g.max())*1.6))
    fig.text(.10,.105,f'Final raw min reduced cost: {c["raw_last_minimum_reduced_cost"]:.7g}  |  original gate: −1e−6',fontsize=8)
    foot='Saved solver bounds; only the endpoint certificate was independently checked. No envelope replaces raw data.'
    if c['case_id']=='pittsburgh_S2_H':foot='Raw saved bounds shown here; the separate verified terminal bound mixes stage 57/60 duals.'
    fig.text(.10,.045,foot,fontsize=7.7)
    cap='完整逐轮定价诊断。当前L与已保存最佳L分别标示；最佳界不是原始曲线替代品。逐轮数据是求解器保存值，不能称每轮均已独立核验。'
    return save(c,fig,'pricing-diagnostic',{'round':x.tolist(),'U':u.tolist(),'current_L':l.tolist(),'best_saved_L':bestl.tolist(),'current_gap_percent':g.tolist(),'best_saved_gap_percent':bg.tolist(),'raw_pricing_min_rc':c['raw_last_minimum_reduced_cost']},cap)

def main():
    global OUT,D,A
    parser=argparse.ArgumentParser();parser.add_argument('--cases',nargs='*');parser.add_argument('--output-root',type=Path);parser.add_argument('--input-root',type=Path,help='Fresh plot inputs exported by export_cg_run_plot_data.py; requires an external output root');parser.add_argument('--redraw-maps',action='store_true',help='Rebuild centered maps with the retained physical-flow function, from saved plot data only');parser.add_argument('--maps-only',action='store_true',help='Render only the centered maps; preserve existing Phase I/II assets');args=parser.parse_args()
    if args.input_root:
        if not args.output_root or args.output_root.resolve().is_relative_to(R):parser.error('New-run inputs require --output-root outside the repository.')
        D=args.input_root.resolve();A=D;args.redraw_maps=True
    if args.output_root:OUT=args.output_root
    OUT.mkdir(parents=True,exist_ok=True)
    cats={c['case_id']:c for c in read(A/'catalog.json')['cases']};items=[]
    for cid in ORDER:
        if cid not in cats:continue
        if args.cases and cid not in args.cases:continue
        c=cats[cid];p=D/c['source_dir'];r=read(p/'result.json');p1=read(p/'phase-i-combined.plot.json');p2=read(p/'phase-ii-pair.plot.json');cert=read(p/'upper-certificate.json')
        folder=OUT/'figures'/cid;folder.mkdir(parents=True,exist_ok=True)
        if args.maps_only:
            import render_cg_dev48_20261014 as original_map
            original_map.D=D
            original_map.save=lambda case,fig,stem,title,caption: save(case,fig,stem,read(physical_data_path(case)),caption)
            original_map.physical(c,centered=True)
            print(cid,'centered map rendered',flush=True)
            continue
        figures=[phase1(c,r,p1,cert),phase2(c,p2)];diag=diagnostic(c,r)
        # The selected map already has the correct movement-only target and projection.
        physical=next(f for f in c['figures']if f['id'].endswith('physical-flow'))
        for name in ['physical-flow.svg','physical-flow.png','physical-flow.plot.json','physical-flow.source.json']:
            key={'physical-flow.svg':'src','physical-flow.png':'png','physical-flow.plot.json':'data','physical-flow.source.json':'source'}.get(name)
            source=D/physical[key]if key else p/name
            if source.exists()and source.resolve()!=(folder/name).resolve():shutil.copyfile(source,folder/name)
        if args.redraw_maps:
            import render_cg_dev48_20261014 as original_map
            original_map.D=D
            original_map.save=lambda case,fig,stem,title,caption: save(case,fig,stem,read(physical_data_path(case)),caption)
            original_map.physical(c,centered=True)
        physical=next(f for f in c['figures']if f['id'].endswith('physical-flow'))
        figures.append({'src':f'figures/{cid}/physical-flow.svg','png':f'figures/{cid}/physical-flow.png','data':f'figures/{cid}/physical-flow.plot.json','source':f'figures/{cid}/physical-flow.source.json','caption':'同次最终物理道路移动流量图；计入完整释放与到达尾段，排除等待、虚拟连接和转向弧。'+('Sioux为示意拓扑。'if c['city']=='sioux-falls'else'这是模型情景，不是实测交通。'),'same_source_sha256':sha(D/physical['src'])if(D/physical['src']).exists()else None})
        typ='open'if not c['accepted_at_frozen_gate']else'exact'if c['actual_adapter']=='uniform_release shortcut'else'closed'if c['raw_pricing_status']=='MET'else'tolerance'
        items.append({k:c[k]for k in ['case_id','city','city_name','run_id','code_package','OD','events','dt_seconds','horizon_steps','scale','U','L','gap_raw','raw_last_minimum_reduced_cost','actual_adapter']}|{'type':typ,'figures':figures,'diagnostic':diag,'phase_i_states':len(p1['round']),'phase_ii_states':len(p2['objective'])if typ!='exact'else 0})
        print(cid,typ,'rendered',flush=True)
    if args.maps_only:return
    existing=read(OUT/'design-data.json')['cases']if(OUT/'design-data.json').exists()else[]
    merged={c['case_id']:c for c in existing};merged.update({c['case_id']:c for c in items})
    data={'version':'20261017-v1','purpose':'local design candidate only','cases':[merged[k]for k in ORDER if k in merged],'new_solver_calls':0,'new_pricing_calls':0,'website_modified':False,'renderer':Path(__file__).relative_to(R).as_posix()}
    write(OUT/'design-data.json',data)
if __name__=='__main__':main()
