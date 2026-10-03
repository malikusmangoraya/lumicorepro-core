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

const names = process.argv.slice(2);
const b = await chromium.launch();

for (const name of names) {
  const dist = path.join(GP, name, 'frontend', 'dist');
  if (!fs.existsSync(dist)) { console.log(`${name}: NO DIST`); continue; }
  const { server, port } = await serve(dist);
  const page = await b.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto(`http://127.0.0.1:${port}/`, { waitUntil: 'load' });
  await page.waitForTimeout(1500);
  const out = await page.evaluate(() => {
    const desc = (el) => {
      const p = [];
      for (let n = el; n && n !== document.body; n = n.parentElement) {
        p.push(n.tagName.toLowerCase() + (n.className ? '.' + String(n.className).trim().split(/\s+/).slice(0, 3).join('.') : ''));
        if (p.length === 4) break;
      }
      return p.join(' < ');
    };
    const imgsNoAlt = Array.from(document.querySelectorAll('img:not([alt])')).slice(0, 6).map((i) => ({
      src: (i.getAttribute('src') || '').slice(0, 70), chain: desc(i),
    }));
    const imgTotal = document.querySelectorAll('img').length;
    const unlab = Array.from(document.querySelectorAll('button,[role="button"],a')).filter((x) => {
      if ((x.textContent || '').trim()) return false;
      return !x.getAttribute('aria-label') && !x.getAttribute('aria-labelledby') && !x.getAttribute('title');
    }).slice(0, 6).map((x) => ({ tag: x.tagName.toLowerCase(), chain: desc(x), html: x.outerHTML.slice(0, 110) }));
    // top-level landmark-ish containers, to find what plays the header role
    const topKids = Array.from(document.querySelectorAll('#root > div > *, body > div > *')).slice(0, 4).map((n) => {
      const cs = getComputedStyle(n);
      return `${n.tagName.toLowerCase()}${n.className ? '.' + String(n.className).trim().split(/\s+/).slice(0, 3).join('.') : ''} pos=${cs.position}`;
    });
    return {
      headerCount: document.querySelectorAll('header').length,
      bannerRole: document.querySelectorAll('[role="banner"]').length,
      imgTotal, imgsNoAlt, unlabCount: unlab.length, unlab, topKids,
    };
  });
  console.log(`\n===== ${name}`);
  console.log(JSON.stringify(out, null, 2));
  await page.close();
  server.close();
}
await b.close();
