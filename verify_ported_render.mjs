import { chromium } from 'playwright';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

const DEL = 'D:/lumicorepro-core/delivery';
const TARGETS = ['kestrel-fleet', 'maison-noir', 'ledgerline', 'kinetiq-health'];
const ROUTES = ['/', '/about', '/services', '/pricing', '/contact', '/privacy',
  '/terms', '/login', '/register', '/admin', '/checkout', '/account'];

const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css',
  '.svg': 'image/svg+xml', '.json': 'application/json', '.png': 'image/png',
  '.jpg': 'image/jpeg', '.webp': 'image/webp', '.woff2': 'font/woff2', '.ico': 'image/x-icon' };

function serve(root, prefix) {
  return http.createServer((req, res) => {
    let p = decodeURIComponent(req.url.split('?')[0]);
    if (p.startsWith(prefix)) p = p.slice(prefix.length) || '/';
    let file = path.join(root, p);
    if (!fs.existsSync(file) || fs.statSync(file).isDirectory()) file = path.join(root, 'index.html');
    const ext = path.extname(file);
    res.writeHead(200, { 'Content-Type': MIME[ext] || 'application/octet-stream' });
    fs.createReadStream(file).pipe(res);
  });
}

const browser = await chromium.launch();
let pass = 0, fail = 0;
const fails = [];

for (const name of TARGETS) {
  const root = path.join(DEL, name, 'frontend', 'dist');
  if (!fs.existsSync(root)) { fails.push({ name, errs: ['no dist'] }); fail++; continue; }
  const srv = serve(root, '/' + name);
  await new Promise((r) => srv.listen(0, '127.0.0.1', r));
  const port = srv.address().port;
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await ctx.newPage();
  for (const route of ROUTES) {
    const errs = [];
    const onErr = (m) => { if (m.type() === 'error') errs.push(m.text()); };
    const onPe = (e) => errs.push(String(e.message || e));
    page.on('console', onErr); page.on('pageerror', onPe);
    let ok = true;
    try {
      await page.goto(`http://127.0.0.1:${port}/${name}${route}?cb=${Date.now()}`,
        { waitUntil: 'domcontentloaded', timeout: 30000 });
      await page.waitForFunction(() => {
        if (!document.body) return false;
        if (document.body.innerText.trim().length > 200) return true;
        // forms (checkout, login) carry most of their content in controls
        return document.querySelectorAll('form, input, button, [role="button"]').length > 3;
      }, { timeout: 15000 });
      const info = await page.evaluate(() => {
        const h1 = document.querySelector('h1');
        const anyHead = h1 || document.querySelector('h2, h3');
        return {
          txt: anyHead ? anyHead.textContent.trim() : '',
          hasMain: !!document.querySelector('main'),
          bodyLen: document.body.innerText.trim().length,
          controls: document.querySelectorAll('form, input, button').length,
        };
      });
      if (!info.hasMain || (info.bodyLen < 120 && info.controls < 4)) {
        ok = false; errs.push(`thin render ${JSON.stringify(info)}`);
      }
      if (/undefined|NaN|\[object/i.test(info.txt)) { ok = false; errs.push('bad text: ' + info.txt.slice(0, 60)); }
      const real = errs.filter((e) => !/favicon|404|net::ERR|analytics|sentry/i.test(e));
      if (real.length) { ok = false; errs.push(...real.slice(0, 2)); }
    } catch (e) { ok = false; errs.push(String(e.message || e).slice(0, 120)); }
    page.off('console', onErr); page.off('pageerror', onPe);
    if (ok) pass++; else { fail++; fails.push({ name, route, errs }); }
  }
  await ctx.close();
  srv.close();
}
await browser.close();
console.log(JSON.stringify({ pass, fail, fails }, null, 1).slice(0, 2600));
