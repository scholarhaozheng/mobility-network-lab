"""Render accepted Berkeley ADMM traces; reads saved plotting data only."""
import numpy as np
import plot_common as pc

OBJECTIVE='accuracy_objective_vs_lp.plot_data.json'
INTERNAL='accuracy_primal_dual_internal_gates.plot_data.json'
LOCAL='accuracy_local_and_capacity_gates.plot_data.json'

def load():
    obj=pc.read_json(OBJECTIVE);internal=pc.read_json(INTERNAL);local=pc.read_json(LOCAL)
    x=np.array(obj['outer']);assert list(x)==list(range(1,171))
    assert internal['outer']==local['outer']==obj['outer']
    lp=float(obj['same_T4_LP_objective_pce_minutes']);values=np.asarray(obj['ADMM_objective_pce_minutes'])
    absolute=np.abs(values-lp);relative=absolute/max(abs(lp),1.)
    assert np.allclose(relative,obj['relative_gap'],rtol=2e-12,atol=1e-14)
    assert np.all(absolute>0) and np.isclose(values[-1],43.66974694298355)
    assert np.isclose(relative[-1],5.31869009587e-5)
    return obj,internal,local,x,lp,absolute,relative

def clock_axis(ax,x):
    ax.set_xlim(1,170);ax.set_xticks([1,38,80,120,170]);ax.set_xlabel('Recorded outer iteration')
    ax.axvline(38.5,color='#929ea6',ls='--',lw=.7,zorder=0)
    pc.format_axes(ax)

def only_zero_floor(values):
    v=np.asarray(values,dtype=float)
    assert np.isfinite(v).all() and np.all(v>=0)
    return np.where(v==0,1e-16,v)

def feasibility(ax,local,x):
    ax.semilogy(x,only_zero_floor(local['local_balance_pce']),color=pc.TEAL,lw=1.5,label='Local balance')
    ax.semilogy(x,only_zero_floor(local['capacity_excess_pce']),color=pc.BLUE,lw=1.5,label='Capacity excess')
    assert local['local_gate_pce']==local['capacity_gate_pce']==1e-5
    ax.axhline(1e-5,color=pc.INK,lw=.85,ls=':',label='Scientific gate')
    ax.set_ylabel('Original-unit residual (PCE)');ax.legend(fontsize=7,loc='upper right')
    clock_axis(ax,x)

def internal_axis(ax,internal,x,kind):
    color=pc.TEAL if kind=='primal' else pc.BLUE
    v=np.asarray(internal[kind+'_residual']);t=np.asarray(internal['recorded_'+kind+'_threshold'])
    assert np.all(v>0) and np.all(t>0)
    ax.semilogy(x,v,color=color,lw=1.5,label=kind.capitalize()+' residual')
    ax.semilogy(x,t,color=pc.INK,lw=.85,ls=':',label='Saved stopping threshold')
    ax.set_ylabel('Primal residual (PCE)' if kind=='primal' else 'Dual residual (min)')
    ax.legend(fontsize=7,loc='upper right');clock_axis(ax,x)

def absolute_axis(ax,x,absolute,lp,gate):
    ax.plot(x,np.log10(absolute),color=pc.TEAL,lw=1.6)
    ax.scatter(x[-1],np.log10(absolute[-1]),s=15,color=pc.TEAL,zorder=4)
    ax.axhline(np.log10(gate*max(abs(lp),1.)),color=pc.INK,lw=.85,ls=':',label='Equivalent relative gate')
    ax.set_ylabel('$\\log_{10}$(absolute objective error\n/ (PCE·min))')
    ax.legend(fontsize=7,loc='upper right');clock_axis(ax,x)

def convergence():
    obj,internal,local,x,lp,absolute,relative=load()
    title='ADMM convergence and objective agreement'
    fig=pc.new_figure('berkeley',title,'T4 / four OD / C1 + C2a / accepted stop 170',figsize=(11.4,8.6))
    axes=fig.subplots(2,2);fig.subplots_adjust(left=.10,right=.96,top=.79,bottom=.095,wspace=.37,hspace=.54)
    feasibility(axes[0,0],local,x);axes[0,0].set_title('a  Original-unit feasibility',loc='left')
    internal_axis(axes[0,1],internal,x,'primal');axes[0,1].set_title('b  Primal consensus',loc='left')
    internal_axis(axes[1,0],internal,x,'dual');axes[1,0].set_title('c  Dual update',loc='left')
    absolute_axis(axes[1,1],x,absolute,lp,obj['required_gate']);axes[1,1].set_title('d  Objective error against same-graph LP',loc='left')
    caption=('Accepted Berkeley T4 ADMM saved history, all 170 recorded outer iterations. The four panels follow the current Boston/Hong Kong diagnostic objects: '
      'original-unit balance and capacity feasibility, primal consensus, dual update, and log10 absolute objective error against the independent LP on the same T4 graph. '
      'Balance/capacity and primal residuals are PCE. The dual residual is rho times the consensus change and is in minutes: rho has min/PCE units. '
      'The dotted scientific feasibility gate is 1e-5 PCE; the internal thresholds are the recorded values. The objective gate line is the unchanged 1e-4 relative criterion expressed on the absolute-error axis. '
      'Only exact-zero feasibility values use a display value of 1e-16 PCE; every positive value, including smaller positives, is retained unchanged. '
      'The vertical separator is after C1 outer 38; C2a contributes 132 further updates under its disclosed new wall budget. The actual trace ends at 170; the registered 300-outer ceiling is not an extrapolated trace. '
      'Final own-x objective is 43.66974694298355 PCE·min against LP 43.66742440800644 PCE·min, absolute difference 0.00232253497711 PCE·min and relative difference 0.00531869%. '
      'Objective agreement is separate from physical-link flow agreement. No smoothing, interpolation or solver call.')
    panels={'a':'local_balance_pce and capacity_excess_pce; semilog y, exact-zero-only 1e-16 PCE display floor',
      'b':'primal_residual and recorded_primal_threshold; PCE; semilog y',
      'c':'dual_residual and recorded_dual_threshold; min; semilog y',
      'd':'log10(abs(ADMM_objective_pce_minutes - same_T4_LP_objective_pce_minutes)/(1 PCE·min)); no zero floor needed'}
    return pc.save(fig,'admm_convergence',title,'finite',caption,panels,[OBJECTIVE,INTERNAL,LOCAL],
      {'outer':x.tolist(),'local_balance_pce':local['local_balance_pce'],'capacity_excess_pce':local['capacity_excess_pce'],
       'primal_residual_pce':internal['primal_residual'],'primal_threshold_pce':internal['recorded_primal_threshold'],
       'dual_residual_min':internal['dual_residual'],'dual_threshold_min':internal['recorded_dual_threshold'],
       'absolute_objective_error_pce_min':absolute.tolist(),'log10_absolute_objective_error':np.log10(absolute).tolist(),
       'lp_objective_pce_min':lp,'relative_objective_error':relative.tolist(),'gate':obj['required_gate'],'c1_final_outer':38})

def objective():
    obj,internal,local,x,lp,absolute,relative=load()
    title='ADMM objective: absolute and relative error'
    fig=pc.new_figure('berkeley',title,'Same T4 LP / unchanged 1e-4 relative gate',figsize=(11.4,5.3))
    axes=fig.subplots(1,2);fig.subplots_adjust(left=.09,right=.96,top=.75,bottom=.16,wspace=.36)
    absolute_axis(axes[0],x,absolute,lp,obj['required_gate']);axes[0].set_title('a  Absolute objective difference',loc='left')
    ax=axes[1];ax.semilogy(x,relative,color=pc.TEAL,lw=1.6);ax.axhline(obj['required_gate'],color=pc.INK,lw=.85,ls=':',label='Scientific gate 1e-4')
    ax.scatter(x[-1],relative[-1],s=16,color=pc.TEAL,zorder=4);ax.set_ylabel('LP-relative objective difference\n(dimensionless)');ax.set_title('b  Relative acceptance criterion',loc='left');ax.legend(fontsize=7);clock_axis(ax,x)
    caption=('Two views of the same 170 saved ADMM own-x objective values, with the independent same-T4 LP reference 43.66742440800644 PCE·min. '
      'Panel a is log10 absolute difference relative to one PCE·min, following the current Hong Kong absolute-objective-error representation; Boston uses raw objective against LP. Panel b is abs(ADMM−LP)/max(abs(LP),1), a dimensionless quantity on a logarithmic y axis. '
      'Its horizontal 1e-4 gate equals 0.01%; the final value 5.31869009587e-5 equals 0.00531869%. The equivalent gate is also marked on panel a. '
      'Every saved point is positive and is displayed without a floor, smoothing or interpolation. The separator follows outer 38; the actual selected run ends at outer 170, while the registered ceiling remains 300. '
      'Reaching the objective criterion earlier did not mean all stopping conditions had passed. This objective comparison does not establish identical physical-link flows.')
    return pc.save(fig,'accuracy_objective_vs_lp',title,'finite',caption,{'a':'log10(abs(objective-LP)/(1 PCE·min))','b':'abs(objective-LP)/max(abs(LP),1), semilog y'},[OBJECTIVE],obj)

def internal():
    obj,data,local,x,lp,absolute,relative=load();title='ADMM primal and dual stopping checks'
    fig=pc.new_figure('berkeley',title,'T4 / all 170 saved updates / recorded thresholds',figsize=(11.4,5.3))
    axes=fig.subplots(1,2);fig.subplots_adjust(left=.09,right=.96,top=.75,bottom=.16,wspace=.34)
    for ax,kind,label in zip(axes,['primal','dual'],['a  Primal consensus','b  Dual update']):
        internal_axis(ax,data,x,kind);ax.set_title(label,loc='left')
    caption=('All saved primal and dual residuals with their recorded stopping thresholds. Primal residuals have PCE units. '
      'The dual residual rho times the norm of the consensus update has minutes as its unit because frozen rho is min/PCE; it is not another PCE feasibility residual. '
      'The internal stop changes from C1 to the accepted C2a absolute/relative policy 1e-6/1e-5 after outer 38, while rho stays fixed. '
      'Neither that internal stopping policy nor this plot replaces the unchanged original-coordinate feasibility and same-LP scientific gates. '
      'All points are positive; no log floor, interpolation or smoothing is applied. The final primal and dual checks both pass at cumulative outer 170.')
    return pc.save(fig,'accuracy_primal_dual_internal_gates',title,'finite',caption,{'a':'primal_residual and recorded_primal_threshold (PCE)','b':'dual_residual and recorded_dual_threshold (min)'},[INTERNAL],data)

def local():
    obj,internal,data,x,lp,absolute,relative=load();title='ADMM original-coordinate feasibility'
    fig=pc.new_figure('berkeley',title,'Local conservation and physical-arc capacity / T4',figsize=(11.4,5.3))
    axes=fig.subplots(1,2);fig.subplots_adjust(left=.09,right=.96,top=.75,bottom=.16,wspace=.34)
    for ax,key,label,color in zip(axes,['local_balance_pce','capacity_excess_pce'],['a  Maximum local balance error','b  Maximum capacity excess'],[pc.TEAL,pc.BLUE]):
        ax.semilogy(x,only_zero_floor(data[key]),color=color,lw=1.5);ax.axhline(1e-5,color=pc.INK,lw=.85,ls=':',label='Scientific gate 1e-5 PCE')
        ax.set_ylabel('Original-unit residual (PCE)');ax.set_title(label,loc='left');ax.legend(fontsize=7,loc='upper right');clock_axis(ax,x)
    zeros={key:int(np.count_nonzero(np.asarray(data[key])==0)) for key in ['local_balance_pce','capacity_excess_pce']}
    caption=('Original-unit local balance error and capacity excess from all 170 saved ADMM updates, in PCE. Both are compared with their unchanged 1e-5 PCE scientific gate. '
      'Exact zeros alone are drawn at 1e-16 PCE for log display; this artificial display position is not a measured positive residual. Every positive value remains unchanged, including positive values below 1e-16. '
      f'Zero counts: local balance {zeros["local_balance_pce"]}; capacity excess {zeros["capacity_excess_pce"]}. '
      'The vertical separator follows the 38 C1 updates. These original-coordinate scientific checks are separate from primal consensus and the rho-scaled dual update. No smoothing, fabricated iterations or new solve.')
    return pc.save(fig,'accuracy_local_and_capacity_gates',title,'finite',caption,{'a':'local_balance_pce; exact-zero-only display floor 1e-16','b':'capacity_excess_pce; exact-zero-only display floor 1e-16'},[LOCAL],data)

if __name__=='__main__':
    convergence();objective();internal();local()
