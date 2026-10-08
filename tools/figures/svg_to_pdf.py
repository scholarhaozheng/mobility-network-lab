"""Convert a native SVG to vector PDF with embedded DejaVu Serif.
Requires svglib and reportlab; source paths and geometry remain vector objects.
"""
import sys,argparse,re,xml.etree.ElementTree as ET,io,copy
from pathlib import Path
ET.register_namespace('','http://www.w3.org/2000/svg')
ET.register_namespace('xlink','http://www.w3.org/1999/xlink')
p=argparse.ArgumentParser();p.add_argument('input');p.add_argument('output');p.add_argument('--package-dir');p.add_argument('--font-dir',required=True);a=p.parse_args()
if a.package_dir:sys.path.insert(0,a.package_dir)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics import renderPDF
from svglib.svglib import svg2rlg
from svglib.fonts import register_font
fd=Path(a.font_dir)
for name,file in [('DejaVu Serif','DejaVuSerif.ttf'),('DejaVu Serif-Bold','DejaVuSerif-Bold.ttf'),('DejaVu Serif-Italic','DejaVuSerif-Italic.ttf'),('DejaVu Serif-BoldItalic','DejaVuSerif-BoldItalic.ttf')]:pdfmetrics.registerFont(TTFont(name,str(fd/file)))
pdfmetrics.registerFontFamily('DejaVu Serif',normal='DejaVu Serif',bold='DejaVu Serif-Bold',italic='DejaVu Serif-Italic',boldItalic='DejaVu Serif-BoldItalic')
for family in ['DejaVu Serif','serif']:
 for weight,style,name in [('normal','normal','DejaVu Serif'),('bold','normal','DejaVu Serif-Bold'),('normal','italic','DejaVu Serif-Italic'),('bold','italic','DejaVu Serif-BoldItalic')]:
  register_font(family,font_path=str(fd / (name.replace(' ','')+'.ttf')),weight=weight,style=style,rlgFontName=name)
root=ET.fromstring(Path(a.input).read_bytes())
for text in root.iter():
 if not text.tag.endswith(('}text','}tspan')):continue
 st=text.get('style','');m=re.search(r'font:\s*((?:(?:700|400|bold|normal|italic)\s+)*)([\d.]+)px\s+([^;]+)',st)
 if m:
  st=st[:m.start()]+st[m.end():];text.set('font-size',m[2]);text.set('font-family','DejaVu Serif');text.set('font-weight','bold'if ('700'in m[1]or'bold'in m[1])else'normal');text.set('font-style','italic'if'italic'in m[1]else'normal')
  text.set('style',st)
  if not text.text and list(text):pass
# Inline SVG use references for svglib, preserving exact glyph/marker path geometry.
idmap={x.get('id'):x for x in root.iter()if x.get('id')}
def expand(parent):
 for child in list(parent):
  if child.tag.endswith('}use'):
   href=child.get('{http://www.w3.org/1999/xlink}href',child.get('href',''))
   if href.startswith('#')and href[1:]in idmap:
    target=copy.deepcopy(idmap[href[1:]]);target.attrib.pop('id',None)
    group=ET.Element('{http://www.w3.org/2000/svg}g')
    for key,value in child.attrib.items():
     if key not in ['x','y','transform','href','{http://www.w3.org/1999/xlink}href']:group.set(key,value)
    group.set('transform',child.get('transform','')+' translate('+child.get('x','0')+' '+child.get('y','0')+')');group.append(target);index=list(parent).index(child);parent.remove(child);parent.insert(index,group);expand(group)
  else:expand(child)
expand(root)
s=ET.tostring(root,encoding='utf-8');drawing=svg2rlg(io.BytesIO(s))
renderPDF.drawToFile(drawing,a.output,initialFontName='DejaVu Serif')
