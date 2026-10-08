"""Embed subsetted serif webfonts while retaining editable SVG text."""
import base64, io, re
import xml.etree.ElementTree as ET
from pathlib import Path
from fontTools import subset
from matplotlib import font_manager

def embed_serif_fonts(path):
    path=Path(path)
    markup=path.read_text(encoding='utf-8')
    tree=ET.fromstring(markup)
    characters=''.join(''.join(node.itertext()) for node in tree.iter() if node.tag.endswith('}text'))
    rules=[]
    for weight,variant,slant in [(400,'normal','normal'),(700,'bold','normal'),(400,'normal','italic'),(700,'bold','italic')]:
        filename=font_manager.findfont(font_manager.FontProperties(family='DejaVu Serif', weight=variant, style=slant),fallback_to_default=False)
        options=subset.Options()
        options.name_IDs=['*']
        font=subset.load_font(filename, options)
        cutter=subset.Subsetter(options=options)
        cutter.populate(text=characters)
        cutter.subset(font)
        font.flavor='woff'
        stream=io.BytesIO()
        font.save(stream)
        encoded=base64.b64encode(stream.getvalue()).decode('ascii')
        rules.append("@font-face{font-family:'DejaVu Serif';font-style:"+slant+";font-weight:"+str(weight)+";src:url(data:font/woff;base64,"+encoded+") format('woff');}")
    style='<style type="text/css" id="embedded-serif-fonts">'+''.join(rules)+'</style>'
    assert 'embedded-serif-fonts' not in markup
    markup=markup.replace('<defs>','<defs>'+style,1)
    path.write_text(markup,encoding='utf-8')
    return {'font_family':'DejaVu Serif','format':'embedded WOFF subsets','editable_text':True,'fonts':[400,700],'copyright_and_license_names_preserved':True}
