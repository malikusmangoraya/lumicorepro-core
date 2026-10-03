import fs from 'node:fs';
import path from 'node:path';

const GP = 'D:/lumicorepro-core/generated-projects';
const SKIP = new Set(['node_modules', 'dist', '.git', 'build', '.vite']);
let fixed = 0;
const changed = [];

const strip = (f) => {
  const raw = fs.readFileSync(f, 'utf8');
  // U+FEFF anywhere, and a UTF-8 BOM byte sequence decoded as chars.
  const clean = raw.replace(/^\uFEFF+/, '').replace(/\uFEFF/g, '');
  if (clean !== raw) { fs.writeFileSync(f, clean, 'utf8'); return true; }
  return false;
};

const walk = (dir) => {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    if (SKIP.has(e.name)) continue;
    const p = path.join(dir, e.name);
    if (e.isDirectory()) { walk(p); continue; }
    if (!/\.(json|jsonc|jsx?|mjs|cjs|css|html|md|txt|ya?ml)$/i.test(e.name)) continue;
    if (strip(p)) { fixed += 1; changed.push(path.relative(GP, p)); }
  }
};

for (const name of fs.readdirSync(GP, { withFileTypes: true }).filter((d) => d.isDirectory()).map((d) => d.name)) {
  const root = path.join(GP, name, 'frontend');
  if (fs.existsSync(root)) walk(root);
}
console.log(`stripped BOM from ${fixed} file(s)`);
changed.forEach((c) => console.log('  ' + c));
