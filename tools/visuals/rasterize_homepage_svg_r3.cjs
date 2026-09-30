// One-time deterministic raster of the two existing public SVG-only panels.
// Usage: NODE_PATH=<node_modules containing sharp> node rasterize_homepage_svg_r3.cjs
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const sharp = require('sharp');

const root = path.resolve(__dirname, '..', '..');
const out = path.join(root, 'docs', 'assets', 'homepage_alignment_r3', 'svg_rasters');
const sources = [
  'docs/assets/algorithm_b_r21/source_panels/boston_b1_fw_flow.svg',
  'docs/assets/algorithm_b_r21/source_panels/sioux_origin_flow.svg',
];
const sha = b => crypto.createHash('sha256').update(b).digest('hex');

(async () => {
  fs.mkdirSync(out, { recursive: true });
  for (const source of sources) {
    const bytes = fs.readFileSync(path.join(root, source));
    const key = sha(Buffer.from(source)).slice(0, 16);
    const output = path.join(out, `${key}.png`);
    await sharp(bytes, { density: 144 }).flatten({ background: '#ffffff' })
      .png({ compressionLevel: 9 }).toFile(output);
    const sidecar = {
      source_path: source,
      source_sha256: sha(bytes),
      raster_path: path.relative(root, output).replaceAll('\\', '/'),
      raster_sha256: sha(fs.readFileSync(output)),
      transform: 'Exact public SVG rasterized with Sharp at density 144; no crop or scientific change',
    };
    fs.writeFileSync(output.replace(/\.png$/, '.source.json'), JSON.stringify(sidecar, null, 2) + '\n');
  }
  process.stdout.write(`Rasterized ${sources.length} SVG-only atlas sources\n`);
})().catch(e => { process.stderr.write(String(e) + '\n'); process.exitCode = 1; });
