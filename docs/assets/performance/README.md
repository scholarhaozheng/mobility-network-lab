# Original-quality browser performance

The homepage, city/stage views, ten reading volumes and repository README display the exact released SVG, PNG and JPEG assets. The active `renderMode` in `manifest.json` is `original`. No displayed image is resized, rasterized or transcoded. The 282 recorded original assets retain their SHA-256 hashes; the homepage's original figure set totals 262,218,386 bytes before lazy loading.

Image dimensions follow each original SVG viewBox or raster aspect ratio. Responsive width reserves the same box before and after decoding. Images use native lazy loading and asynchronous decoding. The original serif fonts are preloaded to prevent navigation wrapping during font substitution. Row alignment runs on layout, width, font and instance changes instead of every image load. Scroll updates reuse unchanged measurements and avoid repeated text writes. The reading header uses an opaque background to avoid full-width backdrop blur.

Build the original-quality layout and synchronize README from the repository root:

```powershell
python -B tools/optimize_site_images.py --mode original
python -B tools/build_readme_from_homepage.py
python -B tools/optimize_site_images.py --check
python -B tools/build_readme_from_homepage.py --check
```

Python requires Beautiful Soup and Pillow. Repeated builds restore the original layout attributes before applying the new wrappers, so they do not nest pictures. The manifest retains historical preview metadata for comparison; unused preview files are not shipped in this edition. The optional preview builder requires Node.js and Sharp, but the active original-quality layout does not select those derivatives.

`benchmark.json` contains three sequential trials per version in Chrome 154 headless, at 1440 by 900 pixels and 4x CPU throttling over local HTTP. Each trial opens the homepage and visits Boston, Hong Kong, Urbana-Champaign, Ithaca, Chicago and Pittsburgh. Mean cumulative long-task time decreased from 71.329 to 37.514 seconds; mean cumulative layout shift decreased from 6.315 to 0.012. Initial layout shift was zero in all three candidate trials. Candidate maximum individual long tasks ranged from 2.827 to 3.316 seconds: large SVGs still cause measurable stalls.

These totals cover the complete navigation sequence, not just initial loading. Native lazy-loading timing and requested image counts vary between trials. This CPU simulation does not measure the affected computers, their GPUs or physical mouse latency. Reproduce a trial with Playwright on `NODE_PATH` and the installed Chrome:

```powershell
node tools/visuals/browser_performance_audit.cjs before-recheck ./benchmark-output
node tools/visuals/browser_performance_audit.cjs original-quality-recheck ./benchmark-output
```

A label beginning with `before` serves HTML and renderers from Git HEAD; other labels serve current workspace bytes. After publication, use the recorded baseline commit to reconstruct the pre-change version when comparing releases.

The publication gate verifies original image identity, layout metadata and README synchronization. Hong Kong scientific DOM fingerprints are checked after restoring original image markup. Original URLs, alternative text, captions, scientific text and linked evidence remain protected.
