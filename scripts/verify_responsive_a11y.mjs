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

const VIEWPORTS = [
  { label: 'mobile-320', width: 320, height: 720 },
  { label: 'mobile-375', width: 375, height: 812 },
  { label: 'tablet-768', width: 768, height: 1024 },
  { label: 'laptop-1024', width: 1024, height: 768 },
  { label: 'desktop-1440', width: 1440, height: 900 },
  { label: 'wide-1920', width: 1920, height: 1080 },
];

const probe = () => {
  // WCAG AA relative-luminance contrast. Must live inside the browser-evaluated
  // function body: Playwright serializes this function, so outer scope is unavailable.
  const contrast = (fg, bg) => {
    const parse = (c) => (c.match(/[\\d.]+/g) || []).map(Number);
    const lin = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
    const lum = (rgb) => 0.2126 * lin(rgb[0]) + 0.7152 * lin(rgb[1]) + 0.0722 * lin(rgb[2]);
    const a = lum(parse(fg));
    const b = lum(parse(bg));
    return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
  };

  const eff = (el) => {
    let n = el;
    let acc = '';
    while (n && n !== document.documentElement) {
      const c = getComputedStyle(n);
      const own = (c.backgroundColor || '').match(/rgba?\([^)]*\)/g) || [];
      for (const v of own.reverse()) {
        const nums = v.match(/[\d.]+/g) || [];
        if (nums.length < 3) continue;
        if (nums.length < 4 || Number(nums[3]) > 0.85) { acc = v; break; }
      }
      if (acc) break;
      n = n.parentElement;
    }
    return acc || 'rgb(255, 255, 255)';
  };

  const contrastFails = [];
  const sel = 'p, a, li, span, h1, h2, h3, h4, h5, h6, button, label, td, th, small, strong, em, div';
  const seen = new Set();
  const nodes = Array.from(document.querySelectorAll(sel)).slice(0, 500);
  for (const el of nodes) {
    const txt = (el.textContent || '').trim();
    if (!txt || txt.length > 240) continue;
    const r = el.getBoundingClientRect();
    if (r.width < 4 || r.height < 4) continue;
    const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || cs.display === 'none' || Number(cs.opacity) < 0.1) continue;
    if (el.querySelector(sel)) continue; // only leaf-ish text nodes
    const fg = cs.color;
    const bg = eff(el);
    const ratio = contrast(fg, bg);
    const size = parseFloat(cs.fontSize);
    const weight = Number(cs.fontWeight) || 400;
    const large = size >= 24 || (size >= 18.66 && weight >= 700);
    const need = large ? 3 : 4.5;
    if (ratio < need) {
      const key = fg + '|' + bg + '|' + Math.round(size);
      if (seen.has(key)) continue;
      seen.add(key);
      contrastFails.push({ sample: txt.slice(0, 42), fg, bg, ratio: Math.round(ratio * 100) / 100, need, size });
    }
  }

  const imgs = Array.from(document.querySelectorAll('img'));
  const imgNoAlt = imgs.filter((i) => !i.getAttribute('alt')).length;

  const btns = Array.from(document.querySelectorAll('button, [role="button"], a'));
  const unlabeled = btns.filter((b) => {
    const t = (b.textContent || '').trim();
    return !t && !b.getAttribute('aria-label') && !b.getAttribute('aria-labelledby') && !b.getAttribute('title');
  }).length;

  const headings = Array.from(document.querySelectorAll('h1,h2,h3,h4,h5,h6')).map((h) => Number(h.tagName[1]));
  let headingJumps = 0;
  for (let i = 1; i < headings.length; i += 1) if (headings[i] - headings[i - 1] > 1) headingJumps += 1;

  const noAltFields = Array.from(document.querySelectorAll('input:not([type=hidden]), select, textarea')).filter((f) => {
    if (f.getAttribute('aria-label') || f.getAttribute('aria-labelledby')) return false;
    if (f.id && document.querySelector(`label[for="${CSS.escape(f.id)}"]`)) return false;
    return !f.closest('label');
  }).length;

  return {
    overflowX: document.documentElement.scrollWidth - document.documentElement.clientWidth,
    docWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
    h1Count: document.querySelectorAll('h1').length,
    landmarks: {
      header: document.querySelectorAll('header').length,
      main: document.querySelectorAll('main').length,
      footer: document.querySelectorAll('footer').length,
      nav: document.querySelectorAll('nav').length,
    },
    contrastFails: contrastFails.slice(0, 8),
    contrastFailCount: contrastFails.length,
    imgs: imgs.length,
    imgNoAlt,
    unlabeledControls: unlabeled,
    headingJumps,
    noAltFields,
    hasSkipLink: !!document.querySelector('a[href^="#"][class*="skip"], .skip-link, [class*="skip-to"]'),
    lang: document.documentElement.getAttribute('lang') || '',
    dir: document.documentElement.getAttribute('dir') || '',
  };
};

const b = await chromium.launch();
const results = [];

for (const name of targets) {
  const dist = path.join(GP, name, 'frontend', 'dist');
  if (!fs.existsSync(dist)) { results.push({ name, status: 'NO_DIST' }); continue; }
  const { server, port } = await serve(dist);
  const rec = { name, viewports: {} };
  for (const vp of VIEWPORTS) {
    const page = await b.newPage({ viewport: { width: vp.width, height: vp.height } });
    const errs = [];
    page.on('pageerror', (e) => errs.push(String(e.message).slice(0, 120)));
    page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text().slice(0, 120)); });
    try {
      await page.goto(`http://127.0.0.1:${port}/`, { waitUntil: 'load', timeout: 30000 });
      await page.waitForTimeout(1400);
      const r = await page.evaluate(probe);
      r.errors = errs;
      r.ok = r.overflowX === 0 && r.h1Count === 1 && r.landmarks.main >= 1 && errs.length === 0;
      rec.viewports[vp.label] = r;
    } catch (e) {
      rec.viewports[vp.label] = { ok: false, errors: [String(e.message).slice(0, 120)] };
    }
    await page.close();
  }

  // Reduced-motion pass: the bundle must not throw when animations are disabled.
  const rmPage = await b.newPage({ viewport: { width: 1280, height: 800 }, reducedMotion: 'reduce' });
  const rmErrs = [];
  rmPage.on('pageerror', (e) => rmErrs.push(String(e.message).slice(0, 120)));
  try {
    await rmPage.goto(`http://127.0.0.1:${port}/`, { waitUntil: 'load', timeout: 30000 });
    await rmPage.waitForTimeout(1200);
  } catch { /* recorded below */ }
  rec.reducedMotionErrors = rmErrs;
  await rmPage.close();

  const vps = Object.values(rec.viewports);
  rec.ok = vps.every((v) => v.ok) && rmErrs.length === 0;
  rec.worstOverflow = Math.max(...vps.map((v) => v.overflowX || 0));
  rec.totalContrastFails = vps.reduce((a, v) => a + (v.contrastFailCount || 0), 0);
  rec.totalImgNoAlt = vps.reduce((a, v) => a + (v.imgNoAlt || 0), 0);
  rec.totalUnlabeled = vps.reduce((a, v) => a + (v.unlabeledControls || 0), 0);
  results.push(rec);

  const bad = Object.entries(rec.viewports).filter(([, v]) => !v.ok).map(([k]) => k);
  console.log(
    `${rec.ok ? 'PASS' : 'FAIL'}  ${name.padEnd(30)} vpOK=${vps.filter((v) => v.ok).length}/6 ovf=${rec.worstOverflow} ` +
    `h1=${vps[0].h1Count} contrast=${rec.totalContrastFails} noAlt=${rec.totalImgNoAlt} unlabel=${rec.totalUnlabeled} rmErr=${rmErrs.length}` +
    (bad.length ? `  bad=${bad.join(',')}` : '')
  );
  await new Promise((r) => server.close(r));
}

await b.close();
const pass = results.filter((r) => r.ok).length;
fs.mkdirSync(OUT, { recursive: true });
fs.writeFileSync(path.join(OUT, 'responsive-a11y-verify.json'), JSON.stringify(results, null, 2));

const agg = {
  total: results.length,
  pass,
  allViewportsOk: results.filter((r) => Object.values(r.viewports).every((v) => v.ok)).length,
  zeroOverflow: results.filter((r) => r.worstOverflow === 0).length,
  singleH1: results.filter((r) => Object.values(r.viewports).every((v) => v.h1Count === 1)).length,
  hasMainLandmark: results.filter((r) => Object.values(r.viewports).every((v) => v.landmarks.main >= 1)).length,
  hasHeader: results.filter((r) => Object.values(r.viewports).every((v) => v.landmarks.header >= 1)).length,
  hasFooter: results.filter((r) => Object.values(r.viewports).every((v) => v.landmarks.footer >= 1)).length,
  reducedMotionClean: results.filter((r) => r.reducedMotionErrors.length === 0).length,
  imgAltClean: results.filter((r) => r.totalImgNoAlt === 0).length,
  controlsLabeled: results.filter((r) => r.totalUnlabeled === 0).length,
  contrastClean: results.filter((r) => r.totalContrastFails === 0).length,
  langAttrSet: results.filter((r) => r.viewports['desktop-1440'].lang).length,
};
fs.writeFileSync(path.join(OUT, 'responsive-a11y-summary.json'), JSON.stringify(agg, null, 2));
console.log('\n--- AGGREGATE ---');
Object.entries(agg).forEach(([k, v]) => console.log(`${k.padEnd(24)} ${v}/${results.length}`));
console.log(`\nQA (responsive+a11y) PASS: ${pass}/${results.length}`);
