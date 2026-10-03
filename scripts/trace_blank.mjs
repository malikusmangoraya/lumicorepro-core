import { chromium } from 'playwright';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

const GP = 'D:/lumicorepro-core/generated-projects';
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.svg': 'image/svg+xml' };
const serve = (dir) => new Promise((res) => {
  const s = http.createServer((rq, rs) => {
    let p = decodeURIComponent(rq.url.split('?')[0]);
    if (p.endsWith('/')) p += 'index.html';
    const f = path.join(dir, p);
    if (!fs.existsSync(f) || fs.statSync(f).isDirectory()) { rs.writeHead(200, { 'Content-Type': 'text/html' }); return rs.end(fs.readFileSync(path.join(dir, 'index.html'))); }
    rs.writeHead(200, { 'Content-Type': TYPES[path.extname(f)] || 'application/octet-stream' });
    rs.end(fs.readFileSync(f));
  });
  s.listen(0, '127.0.0.1', () => res({ server: s, port: s.address().port }));
});

for (const name of process.argv.slice(2)) {
  const dist = path.join(GP, name, 'frontend', 'dist');
  const { server, port } = await serve(dist);
  const page = await b_page();
  async function b_page() {
    const b = await chromium.launch();
    const p = await b.newPage();
    p.__b = b;
    return p;
  }
  const out = [];
  page.on('pageerror', (e) => out.push({ msg: e.message, stack: (e.stack || '').split('\n').slice(0, 12) }));
  page.on('console', (m) => { if (m.type() === 'error') out.push({ console: m.text().slice(0, 300) }); });
  await page.goto(`http://127.0.0.1:${port}/`, { waitUntil: 'load', timeout: 30000 });
  await page.waitForTimeout(2000);
  const info = await page.evaluate(() => ({
    nodes: document.getElementById('root')?.children.length,
    scripts: Array.from(document.scripts).map((s) => s.src.split('/').pop()),
    bodyStart: document.body.innerHTML.slice(0, 200),
  }));
  console.log(`\n########## ${name}`);
  console.log(JSON.stringify(info, null, 2));
  out.forEach((o) => console.log(JSON.stringify(o, null, 2)));
  await page.__b.close();
  await new Promise((r) => server.close(r));
}
