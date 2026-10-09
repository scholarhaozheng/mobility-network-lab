"""Apply stable image layout to the current homepage and reading volumes.

Run with NODE_PATH exposing sharp, then rebuild README with
python tools/build_readme_from_homepage.py. --check verifies source/preview
hashes, markup and the selected rendering policy without changing files.
The default original mode preserves the released SVG/PNG/JPEG bytes and quality.
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, subprocess, tempfile
from pathlib import Path
from urllib.parse import urlsplit, unquote
from bs4 import BeautifulSoup
ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
ASSETS = DOCS / 'assets/performance'
MANIFEST = ASSETS / 'manifest.json'
ADDED = {'loading', 'decoding', 'width', 'height'}


def pages():
    return [DOCS / n for n in ('index.html', 'index-coverage-city.html', 'index-coverage-stage.html')] + sorted((DOCS / 'volumes').glob('*.html'))


def source_key(page, src):
    parsed = urlsplit(src)
    if parsed.scheme or parsed.netloc or not parsed.path:
        return None
    target = (page.parent / unquote(parsed.path)).resolve()
    try:
        return target.relative_to(DOCS).as_posix()
    except ValueError:
        return None


def relative(page, path):
    return os.path.relpath(DOCS / path, page.parent).replace('\\', '/')


def restore_preview_markup(soup):
    """Restore original img attributes and wrappers for a rebuild or DOM proof."""
    for picture in list(soup.select('picture.perf-preview, picture.perf-original')):
        images = picture.find_all('img', recursive=False)
        sources = picture.find_all('source', recursive=False)
        original = 'perf-original' in picture.get('class', [])
        valid_sources = not sources if original else len(sources) == 1 and sources[0].get('type') == 'image/webp'
        if len(images) != 1 or not valid_sources:
            raise ValueError('Invalid performance picture')
        image = images[0]
        added = set(picture.get('data-perf-added', '').split())
        if not added <= ADDED:
            raise ValueError('Preview may normalize only added image layout attributes')
        for attribute in added:
            image.attrs.pop(attribute, None)
        restored = json.loads(picture.get('data-perf-original-attrs', '{}'))
        if not isinstance(restored, dict) or not restored.keys() <= ADDED:
            raise ValueError('Only original layout attributes may be restored')
        image.attrs.update(restored)
        picture.replace_with(image)
    return soup


def eligible(page, image):
    key = source_key(page, image.get('src', ''))
    if not key:
        return None
    path = DOCS / key
    if not path.is_file() or path.suffix.lower() not in ('.svg', '.png', '.jpg', '.jpeg'):
        return None
    if path.stat().st_size > 40000 or image.find_parent(class_='atlas-image'):
        return key
    return None


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify():
    errors = []
    data = json.loads(MANIFEST.read_text(encoding='utf8'))
    entries = data['entries']
    mode = data.get('renderMode', 'preview')
    if mode not in ('original', 'preview'):
        errors.append('Unknown rendering mode')
    for key, entry in entries.items():
        if digest(DOCS / key) != entry['sourceSha256']:
            errors.append('Original figure changed: ' + key)
        if mode == 'preview':
            if digest(DOCS / entry['rasterSource']) != entry['rasterSourceSha256']:
                errors.append('Released raster changed: ' + key)
            for variant, limit in [('thumb', 960), ('reading', 1600)]:
                item = entry[variant]
                if digest(DOCS / item['src']) != item['sha256']:
                    errors.append('Preview changed: ' + item['src'])
                if max(item['width'], item['height']) > limit or item['bytes'] > 800000:
                    errors.append('Preview budget exceeded: ' + item['src'])
                if abs(item['width']/item['height'] - entry['width']/entry['height']) > .015:
                    errors.append('Preview aspect ratio changed: ' + key)
    stats = []
    for page in pages():
        soup = BeautifulSoup(page.read_text(encoding='utf8'), 'html.parser')
        variant = 'reading' if page.parent.name == 'volumes' else 'thumb'
        keys = set()
        for image in soup.find_all('img'):
            key = source_key(page, image.get('src', ''))
            if key not in entries:
                continue
            keys.add(key)
            picture = image.find_parent('picture', class_='perf-original' if mode == 'original' else 'perf-preview')
            source = picture.find('source', recursive=False) if picture else None
            if mode == 'original':
                if not picture or source or image.get('srcset'):
                    errors.append('Original figure is being substituted: ' + page.name + ' ' + key)
                w, h = native_dimensions(DOCS / key)
                if abs(float(image.get('width', 1))/float(image.get('height', 1)) - w/h) > .001:
                    errors.append('Original aspect ratio differs from reserved box: ' + key)
            elif not source or source.get('srcset') != relative(page, entries[key][variant]['src']):
                errors.append('Missing or incorrect preview: ' + page.name + ' ' + key)
            if not all(image.get(a) for a in ('width', 'height', 'loading', 'decoding')):
                errors.append('Missing layout/loading attributes: ' + key)
        total = sum(entries[k][variant]['bytes'] for k in keys)
        if mode == 'preview' and page.name == 'index.html' and total > 25000000:
            errors.append('Homepage previews exceed 25 MB')
        stats.append({'page': page.relative_to(ROOT).as_posix(), 'figures': len(keys), 'originalBytes': sum(entries[k]['originalBytes'] for k in keys), 'previewBytes': total, 'servedImageBytes': sum(entries[k]['originalBytes'] for k in keys) if mode == 'original' else total})
    return {'status': 'FAIL' if errors else 'PASS', 'renderMode': mode, 'figures': len(entries), 'pages': stats, 'errors': errors}


def native_dimensions(path):
    # SVG viewBox preserves vector detail; no rasterization or resizing occurs.
    if path.suffix.lower() == '.svg':
        import xml.etree.ElementTree as ET
        with path.open('rb') as stream:
            element = next(ET.iterparse(stream, events=('start',)))[1]
        viewbox = element.get('viewBox', '').replace(',', ' ').split()
        if len(viewbox) == 4:
            return float(viewbox[2]), float(viewbox[3])
        values = [re.match(r'[0-9.]+', element.get(k, '')) for k in ('width', 'height')]
        if all(values):
            return tuple(float(v.group()) for v in values)
        raise ValueError('SVG has no explicit aspect ratio: ' + str(path))
    from PIL import Image
    with Image.open(path) as image:
        return image.size


def build(mode='original'):
    sources = set()
    originals = {}
    for page in pages():
        soup = restore_preview_markup(BeautifulSoup(page.read_text(encoding='utf8'), 'html.parser'))
        originals[page] = (soup, '\r\n' if b'\r\n' in page.read_bytes() else '\n')
        sources.update(key for im in soup.find_all('img') if (key := eligible(page, im)))
    ASSETS.mkdir(parents=True, exist_ok=True)
    if mode == 'preview' or not MANIFEST.is_file():
        with tempfile.TemporaryDirectory() as temporary:
            tasks = Path(temporary) / 'tasks.json'
            tasks.write_text(json.dumps(sorted(sources)), encoding='utf8')
            subprocess.run(['node', str(ROOT/'tools/visuals/build_figure_previews.cjs'), str(tasks)], check=True)
    data = json.loads(MANIFEST.read_text(encoding='utf8'))
    entries = data['entries']
    if not sources <= entries.keys():
        raise ValueError('Image inventory is stale; rebuild the preview inventory first')
    data['renderMode'] = mode
    data['renderPolicy'] = 'Render exact released SVG/PNG/JPEG sources; no substitution, rasterization, resizing or transcoding of displayed assets.' if mode == 'original' else 'Render bounded preview derivatives; originals remain linked.'
    MANIFEST.write_text(json.dumps(data, indent=2) + '\n', encoding='utf8')
    helper = 'original-map.js' if mode == 'original' else 'preview-map.js'
    picture_class = 'perf-original' if mode == 'original' else 'perf-preview'
    dimensions = {key: native_dimensions(DOCS/key) for key in sources}
    runtime = """// Generated by tools/optimize_site_images.py. Layout metadata only; original mode keeps the source URL.
(() => {
 const base = new URL('../../', document.currentScript.src);
 const entries = ENTRIES;
 window.MCLPreviewImage = (image, source) => {
  const url = new URL(source, document.baseURI);
  const key = url.origin === base.origin && url.pathname.startsWith(base.pathname) ? decodeURIComponent(url.pathname.slice(base.pathname.length)) : '';
  const item = entries[key];
  image.loading = 'lazy'; image.decoding = 'async';
  if (item) { image.width = Math.round(item.width); image.height = Math.round(item.height); image.style.aspectRatio = item.width + ' / ' + item.height; image.style.width = '100%'; image.src = item.src ? new URL(item.src, base).href : source; }
  else image.src = source;
 };
})();
""".replace('ENTRIES', json.dumps({k: {'src': e['thumb']['src'] if mode == 'preview' else None, 'width': dimensions[k][0], 'height': dimensions[k][1]} for k,e in entries.items() if k in sources}, separators=(',',':')))
    (ASSETS/helper).write_text(runtime, encoding='utf8')
    (ASSETS/'previews.css').write_text('/* Preserve the original image flex/grid placement. */\npicture.perf-preview,picture.perf-original{display:contents}\n/* Declared aspect ratios reserve the same box before and after decoding. */\npicture.perf-preview>img,picture.perf-original>img{width:100%!important;height:auto}\n/* An opaque sticky header avoids full-width GPU blur during scrolling. */\nbody>header{background:#fff;backdrop-filter:none;-webkit-backdrop-filter:none}\n@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}\n', encoding='utf8')
    for page, (soup, eol) in originals.items():
        for script in list(soup.find_all('script', src=re.compile(r'assets/performance/(preview|original)-map\.js$'))):
            script.decompose()
        variant = 'reading' if page.parent.name == 'volumes' else 'thumb'
        for preload in list(soup.select('link[data-perf-font]')):
            preload.decompose()
        if mode == 'original':
            for font in ('DejaVuSerif.ttf', 'DejaVuSerif-Bold.ttf'):
                preload = soup.new_tag('link', attrs={'rel':'preload', 'href':relative(page,'assets/fonts/'+font), 'as':'font', 'type':'font/ttf', 'crossorigin':'', 'data-perf-font':''})
                soup.head.insert(0, preload)
        for image in list(soup.find_all('img')):
            key = source_key(page, image.get('src', ''))
            if key not in entries:
                continue
            entry = entries[key]
            picture = soup.new_tag('picture', attrs={'class':picture_class})
            saved = {a: image[a] for a in ('width', 'height') if a in image.attrs}
            added = []
            for attribute, value in [('width',dimensions[key][0]),('height',dimensions[key][1]),('loading','lazy'),('decoding','async')]:
                if not image.get(attribute):
                    image[attribute] = str(value); added.append(attribute)
            if mode == 'original':
                w, h = dimensions[key]
                scale = 1000 if w != int(w) or h != int(h) else 1
                image['width'], image['height'] = str(round(w*scale)), str(round(h*scale))
                if saved:
                    picture['data-perf-original-attrs'] = json.dumps(saved, separators=(',', ':'))
            if added:
                picture['data-perf-added'] = ' '.join(added)
            if mode == 'preview':
                picture.append(soup.new_tag('source', attrs={'type':'image/webp','srcset':relative(page,entry[variant]['src'])}))
            image.replace_with(picture);picture.append(image)
        css = relative(page, 'assets/performance/previews.css')
        if not soup.find('link', href=css):
            soup.head.append(soup.new_tag('link', attrs={'rel':'stylesheet','href':css}))
        if variant == 'thumb':
            js = relative(page, 'assets/performance/' + helper)
            if not soup.find('script', src=js):
                script = soup.new_tag('script', attrs={'src':js,'defer':''})
                atlas = soup.find('script', src=re.compile(r'/atlas\.js'))
                if atlas: atlas['src'] = atlas['src'].split('?')[0] + ('?v=20261009-original-quality' if mode == 'original' else '?v=20261009-performance')
                if atlas: atlas.insert_before(script)
                else: soup.head.append(script)
        if variant == 'thumb':
            atlas = soup.find('script', src=re.compile(r'/atlas\.js'))
            if atlas: atlas['src'] = atlas['src'].split('?')[0] + ('?v=20261009-original-quality' if mode == 'original' else '?v=20261009-performance')
        page.write_bytes(str(soup).replace('\r\n', '\n').replace('\n', eol).encode('utf8'))
    return verify()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--mode', choices=('original', 'preview'), default='original')
    args = ap.parse_args()
    result = verify() if args.check else build(args.mode)
    print(json.dumps(result, indent=2))
    return bool(result['errors'])


if __name__ == '__main__':
    raise SystemExit(main())
