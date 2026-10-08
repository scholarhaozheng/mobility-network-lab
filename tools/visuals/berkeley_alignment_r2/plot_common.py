"""Saved-data plot exports using the website's existing atlas style functions."""
from pathlib import Path
import csv, hashlib, json, logging, inspect
import matplotlib.pyplot as plt
from matplotlib.text import Text
from PIL import Image
from atlas_style import *
from embed_serif_fonts import embed_serif_fonts

HERE=Path(__file__).resolve().parent
INPUTS=HERE/'inputs'
if not INPUTS.exists():
    INPUTS=(HERE.parent/'data') if (HERE.parent/'data').exists() else HERE.parents[2]/'docs/assets/berkeley-atlas-r2/data'
OUT=HERE/'figures' if (HERE/'inputs').exists() else HERE/'regenerated'
logging.getLogger('fontTools.subset').setLevel(logging.ERROR)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read_json(name):return json.loads((INPUTS/name).read_text(encoding='utf8'))
def read_csv(name):
    with (INPUTS/name).open(encoding='utf-8-sig',newline='') as handle:return list(csv.DictReader(handle))
def save(fig,stem,title,stage,caption,panels,sources,plot_data=None):
    OUT.mkdir(parents=True,exist_ok=True)
    layout=compact_header(fig)
    for text in fig.findobj(Text):
        text.set_fontfamily('serif')
        if hasattr(text,'set_math_fontfamily'):text.set_math_fontfamily('dejavuserif')
    for extension in ['png','svg','pdf']:
        metadata={'Date':None} if extension=='svg' else ({'CreationDate':None,'ModDate':None} if extension=='pdf' else None)
        fig.savefig(OUT/(stem+'.'+extension),dpi=300,bbox_inches='tight',pad_inches=.055,metadata=metadata)
    font=embed_serif_fonts(OUT/(stem+'.svg'))
    with Image.open(OUT/(stem+'.png')) as im:dimensions=list(im.size)
    plt.close(fig)
    (OUT/(stem+'.caption.md')).write_text(caption+'\n',encoding='utf8')
    if plot_data is not None:(OUT/(stem+'.plot_data.json')).write_text(json.dumps(plot_data,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf8')
    caller=inspect.currentframe().f_back
    renderer={'file':'tools/visuals/berkeley_alignment_r2/'+Path(caller.f_code.co_filename).name,'function':caller.f_code.co_name,'line':caller.f_code.co_firstlineno}
    record={'id':stem,'title':title,'city':'Berkeley','stage':stage,'caption':caption,'panels':panels,'renderer':renderer,
      'status':'LOCAL_SAVED_RESULT_DERIVATIVE_PENDING_RELEASE_REVIEW','scientific_solver_rerun':False,
      'sources':[{'path':'data/'+name,'sha256':sha(INPUTS/name)} for name in sources],
      'plot_style':{'layout':'C','palette':'A/B blue–teal/navy','font':'DejaVu Serif','shared_functions':['configure','new_figure','format_axes','compact_header'],'style_hash':sha(HERE/'selected-style.json')},
      'font':font,'dimensions':dimensions,'layout_adjustment':layout,
      'exports':{ext:{'path':stem+'.'+ext,'sha256':sha(OUT/(stem+'.'+ext))} for ext in ['png','svg','pdf']},
      'integrity':'Saved values only; no optimizer, smoothing or fabricated iterations. Original accepted figures are retained separately.'}
    (OUT/(stem+'.source.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(stem,flush=True)
    return record
