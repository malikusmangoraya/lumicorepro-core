import fs from 'node:fs';
import path from 'node:path';

const GP = 'D:/lumicorepro-core/generated-projects';

const targets = [
  'apex', 'apex-002', 'build-020', 'build-021', 'build-022', 'build-023', 'build-024', 'build-025',
  'build-026', 'build-027', 'build-028', 'build-029', 'build-030', 'build-031', 'build-032',
  'build-033', 'build-034', 'build-035', 'build-036', 'build-037', 'build-038', 'build-039',
  'build-040', 'build-041', 'claimflow-ai-002', 'create',
];

// The 26 projects share one navbar shape: the sticky site bar itself is a <nav>,
// so the document exposes no <header> banner landmark. Convert the bar to
// <header> and demote the link list to a labelled <nav> inside it.
const BAR_OPEN = '<nav className="sticky top-0 z-50 border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md px-6 py-4">';
const BAR_OPEN_ALT = "<nav className=\"sticky top-0 z-50 border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md px-6 py-4\">";
const LINK_ROW = '<div className="flex items-center gap-6">';
const LINK_ROW_ALT = "<div className=\"flex items-center gap-6\">";

let done = 0;
const skipped = [];

for (const name of targets) {
  const f = path.join(GP, name, 'frontend', 'src', 'components', 'navigation', 'GlassNavbar.jsx');
  if (!fs.existsSync(f)) { skipped.push(`${name}: missing file`); continue; }
  const src = fs.readFileSync(f, 'utf8');
  if (src.includes('<header')) { skipped.push(`${name}: already has header`); continue; }

  let out = src;
  if (out.includes(BAR_OPEN)) out = out.replace(BAR_OPEN, BAR_OPEN.replace('<nav ', '<header '));
  else if (out.includes(BAR_OPEN_ALT)) out = out.replace(BAR_OPEN_ALT, BAR_OPEN_ALT.replace('<nav ', '<header '));
  else { skipped.push(`${name}: bar <nav> not matched`); continue; }

  // Close tag of the bar is the final </nav> in the file.
  const lastClose = out.lastIndexOf('</nav>');
  if (lastClose === -1) { skipped.push(`${name}: no closing nav`); continue; }
  out = out.slice(0, lastClose) + '</header>' + out.slice(lastClose + '</nav>'.length);

  const rowTag = out.includes(LINK_ROW) ? LINK_ROW : (out.includes(LINK_ROW_ALT) ? LINK_ROW_ALT : null);
  if (!rowTag) { skipped.push(`${name}: link row not matched`); continue; }

  // The link row holds only {links.map(...)} entries, so its matching </div>
  // is the first one after the opening tag.
  const rowOpen = out.indexOf(rowTag);
  const rowClose = out.indexOf('</div>', rowOpen);
  if (rowClose === -1) { skipped.push(`${name}: link row close not found`); continue; }
  out =
    out.slice(0, rowOpen) +
    '<nav aria-label="Primary" className="flex items-center gap-6">' +
    out.slice(rowOpen + rowTag.length, rowClose) +
    '</nav>' +
    out.slice(rowClose);

  const openHeaders = (out.match(/<header/g) || []).length;
  const closeHeaders = (out.match(/<\/header>/g) || []).length;
  const openNavs = (out.match(/<nav/g) || []).length;
  const closeNavs = (out.match(/<\/nav>/g) || []).length;
  if (openHeaders !== closeHeaders || openNavs !== closeNavs) {
    skipped.push(`${name}: unbalanced (header ${openHeaders}/${closeHeaders}, nav ${openNavs}/${closeNavs})`);
    continue;
  }

  fs.writeFileSync(f, out, 'utf8');
  done += 1;
  console.log(`${name.padEnd(20)} header=${openHeaders} nav=${openNavs}`);
}

console.log(`\nnavbar landmark fix: ${done}/${targets.length} written`);
if (skipped.length) { console.log('skipped:'); skipped.forEach((s) => console.log('  ' + s)); }
