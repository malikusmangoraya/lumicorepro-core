import fs from 'node:fs';
import path from 'node:path';

const GP = 'D:/lumicorepro-core/generated-projects';

// The theme studio's close button is icon-only with no accessible name.
const projs = [
  'electronics-portfolio-001', 'electronics-portfolio-001-002', 'food-restaurant-001',
  'generated-website-003', 'generated-website-004', 'generated-website-005', 'generated-website-006',
  'generated-website-007', 'personal-creative-001', 'tourism-travel-001', 'tourism-travel-001-002',
];

let done = 0;
const skipped = [];

for (const name of projs) {
  const f = path.join(GP, name, 'frontend', 'src', 'components', 'common', 'ThemeCustomizer.jsx');
  if (!fs.existsSync(f)) { skipped.push(`${name}: no ThemeCustomizer`); continue; }
  const src = fs.readFileSync(f, 'utf8');

  const NEEDLE = /onClick=\{\(\) => setIsOpen\(false\)\}(\s*)className="p-1\.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-900"/;
  if (src.includes('aria-label="Close theme studio"')) { skipped.push(`${name}: already labeled`); continue; }
  if (!NEEDLE.test(src)) { skipped.push(`${name}: close button shape not matched`); continue; }

  const out = src.replace(
    NEEDLE,
    (m, ws) => `onClick={() => setIsOpen(false)}${ws}aria-label="Close theme studio"${ws}className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-900"`
  );
  fs.writeFileSync(f, out, 'utf8');
  done += 1;
}

console.log(`theme studio close-button label: ${done}/${projs.length}`);
if (skipped.length) { console.log('skipped:'); skipped.forEach((s) => console.log('  ' + s)); }
