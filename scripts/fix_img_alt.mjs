import fs from 'node:fs';
import path from 'node:path';

const GP = 'D:/lumicorepro-core/generated-projects';

// 26 projects share a feature-grid Home.jsx whose four card images carry alt="".
// An empty alt is only correct for purely decorative art; these cards sit next to
// a heading and a description, so the image carries meaning and needs a name.
const targets = [
  'apex', 'apex-002', 'build-020', 'build-021', 'build-022', 'build-023', 'build-024', 'build-025',
  'build-026', 'build-027', 'build-028', 'build-029', 'build-030', 'build-031', 'build-032',
  'build-033', 'build-034', 'build-035', 'build-036', 'build-037', 'build-038', 'build-039',
  'build-040', 'build-041', 'claimflow-ai-002', 'create',
];

let done = 0;
const skipped = [];

for (const name of targets) {
  const f = path.join(GP, name, 'frontend', 'src', 'pages', 'Home.jsx');
  if (!fs.existsSync(f)) { skipped.push(`${name}: no Home.jsx`); continue; }
  const src = fs.readFileSync(f, 'utf8');

  // For each empty-alt image, name it after the nearest preceding card heading.
  const headingRe = /<h3[^>]*>([\s\S]*?)<\/h3>/g;
  const headings = [];
  let m;
  while ((m = headingRe.exec(src)) !== null) {
    headings.push({ index: m.index, text: m[1].replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim() });
  }

  const imgRe = /<img\b[^>]*\salt=""[^>]*>/g;
  const out = src.replace(imgRe, (tag, offset) => {
    let text = '';
    for (let i = headings.length - 1; i >= 0; i -= 1) {
      if (headings[i].index < offset) { text = headings[i].text; break; }
    }
    const alt = text ? `${text} — feature preview` : 'Feature preview';
    // Keep attribute order: swap alt="" for the generated name.
    return tag.replace(/\salt=""/, ` alt="${alt.replace(/"/g, '&quot;')}"`);
  });

  const before = (src.match(/alt=""/g) || []).length;
  const after = (out.match(/alt=""/g) || []).length;
  if (before === 0) { skipped.push(`${name}: no empty alts`); continue; }
  if (after !== 0) { skipped.push(`${name}: ${after} empty alt(s) remain`); continue; }

  fs.writeFileSync(f, out, 'utf8');
  done += 1;
  console.log(`${name.padEnd(20)} alt="" x${before} -> named`);
}

console.log(`\nimg alt fix: ${done}/${targets.length} written`);
if (skipped.length) { console.log('skipped:'); skipped.forEach((s) => console.log('  ' + s)); }
