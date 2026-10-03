import fs from 'node:fs';
import path from 'node:path';

const GP = 'D:/lumicorepro-core/generated-projects';

const targets = [
  'apex', 'apex-002', 'build-020', 'build-021', 'build-022', 'build-023', 'build-024', 'build-025',
  'build-026', 'build-027', 'build-028', 'build-029', 'build-030', 'build-031', 'build-032',
  'build-033', 'build-034', 'build-035', 'build-036', 'build-037', 'build-038', 'build-039',
  'build-040', 'build-041', 'claimflow-ai-002', 'create',
];

// The landmark pass replaced the link-row's opening <div> with <nav> but left the
// row's original </div> in place, so every touched file has one stray close tag.
// Drop the </div> that immediately follows the injected </nav>.
const files = [];
for (const name of targets) {
  files.push(path.join(GP, name, 'frontend', 'src', 'components', 'Navbar.jsx'));
  files.push(path.join(GP, name, 'frontend', 'src', 'components', 'navigation', 'GlassNavbar.jsx'));
}

let fixed = 0;
const skipped = [];

for (const f of files) {
  if (!fs.existsSync(f)) continue;
  const src = fs.readFileSync(f, 'utf8');
  if (!src.includes('<nav aria-label="Primary"')) { skipped.push(`${path.relative(GP, f)}: no injected nav`); continue; }

  const open = src.indexOf('<nav aria-label="Primary"');
  const close = src.indexOf('</nav>', open);
  if (close === -1) { skipped.push(`${path.relative(GP, f)}: injected nav not closed`); continue; }

  const after = src.slice(close + '</nav>'.length);
  const m = after.match(/^(\r?\n[ \t]*)<\/div>/);
  if (!m) { skipped.push(`${path.relative(GP, f)}: no stray </div> after injected nav`); continue; }

  const out = src.slice(0, close + '</nav>'.length) + after.slice(m[0].length);
  fs.writeFileSync(f, out, 'utf8');
  fixed += 1;
}

console.log(`stray </div> repair: ${fixed} file(s)`);
if (skipped.length) { console.log('skipped:'); skipped.forEach((s) => console.log('  ' + s)); }
