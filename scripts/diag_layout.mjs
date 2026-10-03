import { chromium } from 'playwright';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

const GP = 'D:/lumicorepro-core/generated-projects';
const TYPES = {
  '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css',
  '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png',
  '.jpg': 'image/jpeg', '.webp': 'image/webp', '.ico': 'image/x-icon',
  '.woff2': 'font/woff2', '.txt': 'text/plain', '.xml': 'application/xml',
};

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

const name = process.argv[2];
const width = Number(process.argv[3] || 1024);
const dist = path.join(GP, name, 'frontend', 'dist');
const { server, port } = await serve(dist);
const b = await chromium.launch();
const page = await b.newPage({ viewport: { width, height: 900 } });
await page.goto(`http://127.0.0.1:${port}/`, { waitUntil: 'load' });
await page.waitForTimeout(1600);

const out = await page.evaluate(() => {
  const vw = document.documentElement.clientWidth;
  const offenders = [];
  for (const el of document.querySelectorAll('*')) {
    const r = el.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) continue;
    if (r.right > vw + 1 || r.left < -1) {
      const cs = getComputedStyle(el);
      offenders.push({
        tag: el.tagName.toLowerCase(),
        cls: (el.className || '').toString().slice(0, 90),
        left: Math.round(r.left), right: Math.round(r.right), w: Math.round(r.width),
        pos: cs.position, ov: cs.overflowX, ws: cs.whiteSpace,
        txt: (el.textContent || '').trim().slice(0, 40),
      });
    }
  }
  const unlabeled = [];
  for (const b2 of document.querySelectorAll('button,[role="button"],a')) {
    if ((b2.textContent || '').trim()) continue;
    if (b2.getAttribute('aria-label') || b2.getAttribute('aria-labelledby') || b2.getAttribute('title')) continue;
    const r = b2.getBoundingClientRect();
    unlabeled.push({ tag: b2.tagName.toLowerCase(), cls: (b2.className || '').toString().slice(0, 80), w: Math.round(r.width), h: Math.round(r.height) });
  }
  return { vw, scrollW: document.documentElement.scrollWidth, offenders: offenders.slice(0, 20), offenderCount: offenders.length, unlabeled };
});
console.log(JSON.stringify(out, null, 2));
await b.close();
server.close();
