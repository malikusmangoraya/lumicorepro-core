import { chromium } from 'playwright';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

const GP = 'D:/lumicorepro-core/generated-projects';
const OUT = 'D:/lumicorepro-core/logs/rebuild';
const TYPES = {
  '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css',
  '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png',
  '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp', '.ico': 'image/x-icon',
  '.woff2': 'font/woff2', '.woff': 'font/woff', '.txt': 'text/plain',
  '.xml': 'application/xml', '.map': 'application/json', '.mp4': 'video/mp4',
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
const GLOBAL_RE = 'https?://';

for (const name of targets) {
  const dist = path.join(GP, name, 'frontend', 'dist');
  if (!fs.existsSync(dist)) { results.push({ name, status: 'NO_DIST' }); continue; }
  const { server, port } = await serve(dist);
  const rec = { name };

  // --- SEO / metadata gate (no network needed: parse dist/index.html) ---
  const html = fs.readFileSync(path.join(dist, 'index.html'), 'utf8');
  const meta = (attr, key) => {
    const re = new RegExp(`<meta[^>]*${attr}=["']${key}["'][^>]*content=["']([^"']*)["']`, 'i');
    const alt = new RegExp(`<meta[^>]*content=["']([^"']*)["'][^>]*${attr}=["']${key}["']`, 'i');
    const m = html.match(re) || html.match(alt);
    return m ? m[1].trim() : '';
  };
  const linkHref = (rel) => {
    const m = html.match(new RegExp(`<link[^>]*rel=["']${rel}["'][^>]*href=["']([^"']*)["']`, 'i'));
    return m ? m[1] : '';
  };
  const jsonLd = (html.match(/application\/ld\+json/gi) || []).length;
  rec.seo = {
    title: (html.match(/<title[^>]*>([\s\S]*?)<\/title>/i) || [, ''])[1].trim(),
    description: meta('name', 'description'),
    ogTitle: meta('property', 'og:title'),
    ogDescription: meta('property', 'og:description'),
    ogImage: meta('property', 'og:image'),
    ogUrl: meta('property', 'og:url'),
    twitterCard: meta('name', 'twitter:card'),
    canonical: (html.match(/<link[^>]*rel=["']canonical["'][^>]*href=["']([^"']*)["']/i) || [, ''])[1],
    jsonLdBlocks: jsonLd,
    favicon: linkHref('icon') || linkHref('shortcut icon') || (/favicon\.svg/i.test(html) ? 'favicon.svg' : ''),
  };

  // --- Page + resource audit ---
  const page = await b.newPage({ viewport: { width: 1280, height: 800 } });
  const errors = [];
  const external = [];
  const allReq = [];
  page.on('pageerror', (e) => errors.push(String(e.message).slice(0, 140)));
  page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text().slice(0, 140)); });
  page.on('request', (r) => {
    allReq.push(r.url());
    if (r.url().startsWith(GLOBAL_RE) && !r.url().startsWith(`http://127.0.0.1:${port}`)) external.push(r.url().slice(0, 110));
  });
  const http4xx = [];
  page.on('response', (r) => { if (r.status() >= 400) http4xx.push(`${r.status()} ${r.url().slice(0, 90)}`); });

  try {
    await page.goto(`http://127.0.0.1:${port}/`, { waitUntil: 'load', timeout: 30000 });
    await page.waitForTimeout(1600);
    rec.perf = await page.evaluate(() => {
      const nav = performance.getEntriesByType('navigation')[0] || {};
      const paints = {};
      for (const p of performance.getEntriesByType('paint')) paints[p.name] = Math.round(p.startTime);
      const res = performance.getEntriesByType('resource');
      const byType = { js: 0, css: 0, img: 0, font: 0, other: 0 };
      let transfer = 0;
      for (const r of res) {
        const t = r.initiatorType || 'other';
        if (t === 'script') byType.js += 1;
        else if (t === 'link' || t === 'css') byType.css += 1;
        else if (t === 'img') byType.img += 1;
        else if (t === 'font' || t === 'other') byType.font += 1;
        else byType.other += 1;
        transfer += r.transferSize || 0;
      }
      return {
        domContentLoaded: Math.round(nav.domContentLoadedEventEnd || 0),
        loadEvent: Math.round(nav.loadEventEnd || 0),
        FCP: paints['first-contentful-paint'] ?? null,
        resourceCount: res.length,
        transferKB: Math.round(transfer / 1024),
        byType,
        domNodes: document.querySelectorAll('*').length,
        title: document.title,
        lang: document.documentElement.lang,
      };
    });
    rec.errors = errors;
    rec.http4xx = http4xx;
    rec.externalRequests = [...new Set(external)];
    rec.externalCount = rec.externalRequests.length;
  } catch (e) {
    rec.errors = [...errors, 'GOTO: ' + String(e.message).slice(0, 140)];
  }
  await page.close();
  await new Promise((r) => server.close(r));

  rec.ok =
    rec.errors.length === 0 &&
    rec.http4xx.length === 0 &&
    rec.seo.title.length > 0 &&
    rec.seo.description.length > 0 &&
    rec.seo.ogTitle.length > 0 &&
    rec.seo.ogImage.length > 0 &&
    rec.seo.jsonLdBlocks > 0 &&
    rec.seo.canonical.length > 0 &&
    rec.seo.favicon.length > 0;
  results.push(rec);
  console.log(
    `${rec.ok ? 'PASS' : 'FAIL'}  ${name.padEnd(30)} title=${String(rec.seo.title.length).padStart(3)} desc=${String(rec.seo.description.length).padStart(3)} ` +
    `ogImg=${rec.seo.ogImage ? 'y' : 'n'} jsonLd=${rec.seo.jsonLdBlocks} canon=${rec.seo.canonical ? 'y' : 'n'} fav=${rec.seo.favicon ? 'y' : 'n'} ` +
    `ext=${rec.externalCount} err=${rec.errors.length} 4xx=${rec.http4xx.length} load=${rec.perf?.loadEvent}ms`
  );
  if (rec.errors.length) rec.errors.slice(0, 2).forEach((e) => console.log(`        ! ${e}`));
}

await b.close();
const pass = results.filter((r) => r.ok).length;
fs.mkdirSync(OUT, { recursive: true });
fs.writeFileSync(path.join(OUT, 'seo-perf-verify.json'), JSON.stringify(results, null, 2));

const agg = {
  total: results.length,
  pass,
  hasTitle: results.filter((r) => r.seo.title).length,
  titleLenOk: results.filter((r) => r.seo.title.length >= 15 && r.seo.title.length <= 70).length,
  hasDescription: results.filter((r) => r.seo.description.length >= 50).length,
  hasOgImage: results.filter((r) => r.seo.ogImage).length,
  hasJsonLd: results.filter((r) => r.seo.jsonLdBlocks > 0).length,
  hasCanonical: results.filter((r) => r.seo.canonical).length,
  hasFavicon: results.filter((r) => r.seo.favicon).length,
  noErrors: results.filter((r) => r.errors.length === 0).length,
  noExternalRequests: results.filter((r) => r.externalCount === 0).length,
  loadUnder3s: results.filter((r) => (r.perf?.loadEvent ?? 9999) < 3000).length,
  fcpUnder1800: results.filter((r) => (r.perf?.FCP ?? 9999) < 1800).length,
  transferUnder1500KB: results.filter((r) => (r.perf?.transferKB ?? 99999) < 1500).length,
};
fs.writeFileSync(path.join(OUT, 'seo-perf-summary.json'), JSON.stringify(agg, null, 2));
console.log('\n--- AGGREGATE ---');
Object.entries(agg).forEach(([k, v]) => console.log(`${k.padEnd(24)} ${v}/${results.length}`));
console.log(`\nSEO/PERF PASS: ${pass}/${results.length}`);
