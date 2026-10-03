import { chromium } from 'playwright';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

const GP = 'D:/lumicorepro-core/generated-projects';
const TYPES = {
  '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css',
  '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png',
  '.jpg': 'image/jpeg', '.webp': 'image/webp', '.ico': 'image/x-icon',
  '.woff2': 'font/woff2', '.woff': 'font/woff', '.txt': 'text/plain',
  '.xml': 'application/xml', '.map': 'application/json',
};

const serve = (dir) => new Promise((res) => {
  const s = http.createServer((rq, rs) => {
    let p = decodeURIComponent(rq.url.split('?')[0]);
    if (p.endsWith('/')) p += 'index.html';
    const f = path.join(dir, p);
    if (!f.startsWith(path.resolve(dir)) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) {
      rs.writeHead(200, { 'Content-Type': 'text/html' });
      return rs.end(fs.readFileSync(path.join(dir, 'index.html')));
    }
    rs.writeHead(200, { 'Content-Type': TYPES[path.extname(f)] || 'application/octet-stream' });
    rs.end(fs.readFileSync(f));
  });
  s.listen(0, '127.0.0.1', () => res({ server: s, port: s.address().port }));
});

const only = process.argv[2] ? process.argv[2].split(',') : null;
const names = fs.readdirSync(GP, { withFileTypes: true }).filter((d) => d.isDirectory()).map((d) => d.name).sort();
const targets = only ? names.filter((n) => only.includes(n)) : names;

const b = await chromium.launch();
const results = [];
for (const name of targets) {
  const dist = path.join(GP, name, 'frontend', 'dist');
  if (!fs.existsSync(dist)) { results.push({ name, status: 'NO_DIST' }); continue; }
  const { server, port } = await serve(dist);
  const page = await b.newPage({ viewport: { width: 1280, height: 800 } });
  const errs = [];
  const failed = [];
  page.on('pageerror', (e) => errs.push(String(e.message).slice(0, 160)));
  page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text().slice(0, 160)); });
  page.on('requestfailed', (r) => failed.push(r.url().slice(0, 120)));
  const http404 = [];
  page.on('response', (r) => { if (r.status() >= 400) http404.push(`${r.status()} ${r.url().slice(0, 100)}`); });
  let rec = { name };
  try {
    const resp = await page.goto(`http://127.0.0.1:${port}/`, { waitUntil: 'load', timeout: 30000 });
    await page.waitForTimeout(1800);
    rec.status = resp.status();
    rec = { ...rec, ...(await page.evaluate(() => {
      const root = document.getElementById('root');
      return {
        mounted: !!root && root.children.length > 0,
        nodes: root ? root.querySelectorAll('*').length : 0,
        h1: Array.from(document.querySelectorAll('h1')).map((h) => h.textContent.trim().slice(0, 40)),
        title: (document.title || '').slice(0, 50),
        overflowX: document.documentElement.scrollWidth - document.documentElement.clientWidth,
        blankText: document.body.innerText.trim().length,
      };
    })) };
    rec.errors = errs;
    rec.failedReqs = failed;
    rec.http4xx = http404;
    rec.ok = rec.mounted && rec.nodes > 40 && errs.length === 0 && failed.length === 0 && http404.length === 0;
  } catch (e) {
    rec.ok = false;
    rec.errors = [...errs, 'GOTO: ' + String(e.message).slice(0, 140)];
  }
  await page.close();
  await new Promise((r) => server.close(r));
  results.push(rec);
  const flag = rec.ok ? 'PASS' : 'FAIL';
  console.log(`${flag}  ${name.padEnd(30)} nodes=${String(rec.nodes).padStart(4)} h1=${(rec.h1?.[0] || 'NONE').slice(0, 28).padEnd(28)} err=${rec.errors?.length || 0} 4xx=${rec.http4xx?.length || 0} ovf=${rec.overflowX}`);
  if (rec.errors?.length) rec.errors.slice(0, 3).forEach((e) => console.log(`        ! ${e}`));
}
await b.close();
const pass = results.filter((r) => r.ok).length;
fs.writeFileSync('D:/lumicorepro-core/logs/rebuild/runtime-verify.json', JSON.stringify(results, null, 2));
console.log(`\nRUNTIME VERIFY: ${pass}/${results.length} pass`);
