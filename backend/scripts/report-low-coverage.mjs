import { readFileSync } from 'fs';

const cov = JSON.parse(readFileSync(new URL('../coverage/coverage-final.json', import.meta.url), 'utf8'));

const rows = [];
for (const [key, value] of Object.entries(cov)) {
  const statements = Object.values(value.s || {});
  const hit = statements.filter((count) => count > 0).length;
  const file = key.split('lumicorepro-core')[1] || key;
  rows.push({
    file: file.replace(/\\/g, '/').replace(/^\//, ''),
    pct: statements.length ? Math.round((1000 * hit) / statements.length) / 10 : 0,
    total: statements.length,
    missed: statements.length - hit,
  });
}

const sizeable = rows.filter((r) => r.total >= 20).sort((a, b) => a.pct - b.pct);
console.log(`instrumented files with >=20 statements: ${sizeable.length}`);
for (const r of sizeable.slice(0, 50)) {
  console.log(`${String(r.pct).padStart(5)}%  ${String(r.missed).padStart(4)} missed  ${r.file}`);
}
