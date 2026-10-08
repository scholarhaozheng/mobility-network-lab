"""Exact current atlas style functions, extracted for saved-result Berkeley plots."""
from pathlib import Path
import json, textwrap
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.text import Text
ROOT=Path(__file__).resolve().parent
STYLE=json.loads((ROOT/'selected-style.json').read_text(encoding='utf8'))
PALETTE=STYLE['selection']['palette']
INK=PALETTE['ink'];TEAL=PALETTE['accent'];BLUE=PALETTE['second'];ROAD=PALETTE['road'];GRID=PALETTE['grid']
FLOW_CMAP=SEQUENTIAL_CMAP=LinearSegmentedColormap.from_list('selected_blue_teal',PALETTE['seq'])
DIFF_CMAP=DIVERGING_CMAP=LinearSegmentedColormap.from_list('selected_signed',PALETTE['div'])
CATEGORIES=[TEAL,BLUE,'#14355a','#80c3bd','#527f92','#bb6749','#a7cbd1','#6d729a']
CITY_LABELS={'boston':'Boston','hong-kong':'Hong Kong','berkeley':'Berkeley'}
def configure():
    plt.rcParams.update({'font.family':'serif','font.serif':['DejaVu Serif'],'mathtext.fontset':'dejavuserif',
      'svg.fonttype':'none','pdf.fonttype':42,'font.size':9,'axes.titlesize':11,'axes.labelsize':9,
      'axes.linewidth':.55,'axes.edgecolor':'#819097','text.color':INK,'axes.labelcolor':INK,
      'xtick.color':INK,'ytick.color':INK,'xtick.labelsize':8,'ytick.labelsize':8,
      'axes.spines.top':False,'axes.spines.right':False,'legend.frameon':False,
      'figure.facecolor':'white','savefig.facecolor':'white','svg.hashsalt':'mcl-selected-c-serif-v1'})
    return PALETTE

def new_figure(city,title,scope='',figsize=(9,6)):
    configure()
    fig=plt.figure(figsize=figsize)
    city=CITY_LABELS.get(city,city)
    label=city.upper()+(('  /  '+scope) if scope else '')
    label_artist=fig.text(.065,.963,label,fontsize=8.7,color=TEAL,weight='bold',va='top')
    line_length=max(35,int(figsize[0]*7.2))
    title_artist=fig.text(.065,.908,textwrap.fill(title,line_length),fontsize=15,color=INK,weight='bold',va='top',linespacing=1.12)
    fig._mcl_header_artists=(label_artist,title_artist)
    fig._mcl_header={'city':city,'title':title,'scope':scope}
    return fig

def format_axes(ax,map_axis=False):
    for spine in ax.spines.values():
        spine.set_linewidth(.45); spine.set_color('#9ba4a8')
    ax.tick_params(labelsize=8,length=3,pad=3)
    if map_axis:
        for spine in ax.spines.values(): spine.set_visible(True)
        ax.set_aspect('equal'); ax.grid(color=GRID,linewidth=.4,zorder=0)
    else: ax.grid(axis='y',color=GRID,linewidth=.5,zorder=0)
    return ax

def compact_header(fig, gap_pt=8.0, label_gap_pt=5.0):
    """Place the two figure headings next to actual panel bounds before export.

    Only heading positions change. Data axes, aspect ratios, labels and scientific
    geometry are kept intact. Vector-tight export then removes unused outer space.
    """
    headers=getattr(fig,'_mcl_header_artists',tuple(fig.texts[:2]))
    if len(headers)!=2:return {}
    label,title=headers
    fig.canvas.draw(); renderer=fig.canvas.get_renderer()
    body=[]
    for ax in fig.axes:
        if ax.get_visible():
            b=ax.get_tightbbox(renderer)
            if b is not None and b.width>0 and b.height>0:body.append(b)
    for artist in [*fig.texts,*fig.legends,*fig.artists]:
        if artist in headers or not artist.get_visible():continue
        try:
            b=artist.get_window_extent(renderer)
            if b is not None and b.width>0 and b.height>0:body.append(b)
        except (AttributeError,ValueError):pass
    if not body:return {}
    body_top=max(b.y1 for b in body)
    px_per_pt=fig.dpi/72.0
    prior_title_box=title.get_window_extent(renderer)
    original_gap=(prior_title_box.y0-body_top)/px_per_pt
    title_x,title_y=title.get_position()
    title.set_position((title_x,title_y+(body_top+gap_pt*px_per_pt-prior_title_box.y0)/fig.bbox.height))
    fig.canvas.draw(); renderer=fig.canvas.get_renderer()
    title_box=title.get_window_extent(renderer);label_box=label.get_window_extent(renderer)
    label_x,label_y=label.get_position()
    label.set_position((label_x,label_y+(title_box.y1+label_gap_pt*px_per_pt-label_box.y0)/fig.bbox.height))
    fig.canvas.draw();renderer=fig.canvas.get_renderer()
    return {'policy':'Heading positions use actual rendered panel bounds; scientific axes are unchanged.',
      'original_title_to_panels_pt':round(original_gap,3),
      'title_to_panels_pt':round((title.get_window_extent(renderer).y0-body_top)/px_per_pt,3),
      'label_to_title_pt':round((label.get_window_extent(renderer).y0-title.get_window_extent(renderer).y1)/px_per_pt,3),
      'outer_padding_in':0.055}

configure()
