"""Guard browser preview fidelity, performance budgets and README layout."""
from pathlib import Path
import sys, unittest
from bs4 import BeautifulSoup
from urllib.parse import urljoin
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from optimize_site_images import restore_preview_markup, verify
from build_readme_from_homepage import image_cell

class PreviewTests(unittest.TestCase):
    def test_released_sources_and_preview_hashes_match(self):
        result=verify()
        self.assertEqual(result['status'],'PASS',result['errors'])
        home=next(p for p in result['pages'] if p['page']=='docs/index.html')
        self.assertEqual(result['renderMode'],'original')
        self.assertEqual(home['servedImageBytes'],home['originalBytes'])

    def test_added_browser_attributes_restore_original_scientific_markup(self):
        original='<section><a href="figure.svg"><img alt="A flow figure" src="figure.svg"/></a></section>'
        wrapped='<section><a href="figure.svg"><picture class="perf-preview" data-perf-added="width height loading decoding"><source srcset="figure.webp" type="image/webp"/><img alt="A flow figure" src="figure.svg" width="960" height="600" loading="lazy" decoding="async"/></picture></a></section>'
        restored=restore_preview_markup(BeautifulSoup(wrapped,'html.parser'))
        self.assertEqual(str(restored),str(BeautifulSoup(original,'html.parser')))
        original_wrapper=wrapped.replace('perf-preview','perf-original').replace('<source srcset="figure.webp" type="image/webp"/>','')
        self.assertEqual(str(restore_preview_markup(BeautifulSoup(original_wrapper,'html.parser'))),str(restored))
        tampered=BeautifulSoup(wrapped.replace('A flow figure','An observed flow'),'html.parser')
        self.assertNotEqual(str(restore_preview_markup(tampered)),str(restored))
        tampered=BeautifulSoup(wrapped.replace('src="figure.svg"','src="wrong.svg"'),'html.parser')
        self.assertNotEqual(str(restore_preview_markup(tampered)),str(restored))

    def test_original_dimensions_restore_earlier_layout_attributes(self):
        original=BeautifulSoup('<img src="figure.svg" width="400" height="220" alt="Flow"/>','html.parser')
        wrapped=BeautifulSoup('<picture class="perf-original" data-perf-added="loading decoding"><img src="figure.svg" width="1600" height="900" alt="Flow" loading="lazy" decoding="async"/></picture>','html.parser')
        wrapped.picture['data-perf-original-attrs']='{"width":"400","height":"220"}'
        self.assertEqual(str(restore_preview_markup(wrapped)),str(original))
        tampered=BeautifulSoup('<picture class="perf-original"><img src="wrong.svg"/></picture>','html.parser')
        tampered.picture['data-perf-original-attrs']='{"src":"figure.svg"}'
        with self.assertRaises(ValueError): restore_preview_markup(tampered)

    def test_normalization_cannot_erase_scientific_attributes(self):
        tampered=BeautifulSoup('<picture class="perf-preview" data-perf-added="src alt"><source type="image/webp" srcset="preview.webp"/><img src="wrong.svg" alt="wrong"/></picture>','html.parser')
        with self.assertRaises(ValueError): restore_preview_markup(tampered)

    def test_readme_multifigure_panels_are_bounded_and_link_originals(self):
        home=BeautifulSoup((ROOT/'docs/index.html').read_text(encoding='utf8'),'html.parser')
        card=next(c for c in home.select('.atlas-card') if c.select_one('.r11-figure-series,.r12-figure-series'))
        output=BeautifulSoup(image_cell(card,3),'html.parser')
        self.assertTrue(output.find_all('img'))
        for image in output.find_all('img'):
            self.assertLessEqual(int(image['width']),265)
            self.assertLessEqual(int(image['height']),280)
            self.assertNotIn('/performance/previews/',image['src'])
            self.assertTrue((ROOT/image['src']).is_file())
        self.assertEqual([a.get('href') for a in output.find_all('a')],[urljoin('https://scholarhaozheng.github.io/mobility-network-lab/',a.get('href')) for a in card.select_one('.r11-figure-series,.r12-figure-series').find_all('a')])

    def test_original_fonts_preload_before_stylesheets(self):
        home=BeautifulSoup((ROOT/'docs/index.html').read_text(encoding='utf8'),'html.parser')
        links=home.head.find_all('link')
        fonts=[link for link in links if link.get('as')=='font']
        self.assertEqual(len(fonts),2)
        first_css=next(i for i,l in enumerate(links) if 'stylesheet' in l.get('rel',[]))
        for font in fonts:
            self.assertLess(links.index(font),first_css)
            self.assertIn('crossorigin',font.attrs)
            self.assertTrue((ROOT/'docs'/font['href']).is_file())

    def test_dynamic_views_load_original_layout_helper_before_the_atlas(self):
        home=BeautifulSoup((ROOT/'docs/index.html').read_text(encoding='utf8'),'html.parser')
        scripts=[s.get('src','') for s in home.find_all('script')]
        helper=scripts.index('assets/performance/original-map.js')
        atlas=next(i for i,s in enumerate(scripts) if '/atlas.js' in s)
        self.assertLess(helper,atlas)
        self.assertIn('window.MCLPreviewImage(img', (ROOT/'docs/assets/reading/atlas.js').read_text(encoding='utf8'))

if __name__=='__main__':unittest.main()
