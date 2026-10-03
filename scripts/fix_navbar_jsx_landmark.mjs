import fs from 'node:fs';
import path from 'node:path';

const GP = 'D:/lumicorepro-core/generated-projects';

const targets = [
  'apex', 'apex-002', 'build-020', 'build-021', 'build-022', 'build-023', 'build-024', 'build-025',
  'build-026', 'build-027', 'build-028', 'build-029', 'build-030', 'build-031', 'build-032',
  'build-033', 'build-034', 'build-035', 'build-036', 'build-037', 'build-038', 'build-039',
  'build-040', 'build-041', 'claimflow-ai-002', 'create',
];

// Home.jsx imports components/Navbar (not components/navigation/GlassNavbar), and
// that bar is itself a <nav>, so these 26 sites ship no <header> banner landmark.
// Promote the bar to <header> and demote the desktop link row to a labelled <nav>.
const BAR = '<nav className="sticky top-0 z-50 border-b border-[var(--t-border)] bg-canvas/95 backdrop-blur supports-[backdrop-filter]:bg-canvas/80">';
const ROW = '<div className="hidden md:flex items-center gap-8">';

let done = 0;
const skipped = [];

for (const name of targets) {
  const f = path.join(GP, name, 'frontend', 'src', 'components', 'Navbar.jsx');
  if (!fs.existsSync(f)) { skipped.push(`${name}: missing Navbar.jsx`); continue; }
  const src = fs.readFileSync(f, 'utf8');
  if (src.includes('<header')) { skipped.push(`${name}: already has header`); continue; }
  if (!src.includes(BAR)) { skipped.push(`${name}: bar tag not matched`); continue; }
  if (!src.includes(ROW)) { skipped.push(`${name}: link row not matched`); continue; }

  let out = src.replace(BAR, BAR.replace('<nav ', '<header '));
  const lastClose = out.lastIndexOf('</nav>');
  if (lastClose === -1) { skipped.push(`${name}: no closing nav`); continue; }
  out = out.slice(0, lastClose) + '</header>' + out.slice(lastClose + 6);

  const rowOpen = out.indexOf(ROW);
  const rowClose = out.indexOf('</div>', rowOpen);
  if (rowClose === -1) { skipped.push(`${name}: row close not found`); continue; }
  out =
    out.slice(0, rowOpen) +
    '<nav aria-label="Primary" className="hidden md:flex items-center gap-8">' +
    out.slice(rowOpen + ROW.length, rowClose) +
    '</nav>' +
    out.slice(rowClose);

  const h = [(out.match(/<header/g) || []).length, (out.match(/<\/header>/g) || []).length];
  const n = [(out.match(/<nav/g) || []).length, (out.match(/<\/nav>/g) || []).length];
  if (h[0] !== h[1] || n[0] !== n[1]) { skipped.push(`${name}: unbalanced header ${h} nav ${n}`); continue; }

  fs.writeFileSync(f, out, 'utf8');
  done += 1;
}

console.log(`Navbar landmark fix: ${done}/${targets.length}`);
if (skipped.length) { console.log('skipped:'); skipped.forEach((s) => console.log('  ' + s)); }
