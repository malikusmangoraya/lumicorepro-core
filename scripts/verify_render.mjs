import { chromium } from 'playwright';
import fs from 'node:fs';

const PORT = process.env.PROBE_PORT || 8902;
const meta = JSON.parse(fs.readFileSync('C:/Users/AZAM COMPUTERS/AppData/Local/Temp/opencode/serve_seq.json', 'utf8'));
const BASE = `http://127.0.0.1:${PORT}/`;
const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
const page = await ctx.newPage();

let pass = 0;
const fails = [];
for (const name of meta.projects) {
  const errs = [];
  const onErr = (m) => { if (m.type() === 'error') errs.push(m.text()); };
  const onPageErr = (e) => errs.push(String(e.message || e));
  page.on('console', onErr);
  page.on('pageerror', onPageErr);
  let ok = true;
  try {
    await fetch(`${BASE}__set__/${name}`);
    await page.goto(`${BASE}?cb=${Date.now()}`, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForSelector('h1', { timeout: 15000 });
    const info = await page.evaluate(() => {
      const h1 = document.querySelector('h1');
      const sec = h1 && h1.closest('section');
      return {
        h1: !!h1,
        hero: !!sec,
        text: h1 ? h1.textContent.trim().length : 0,
        raw: h1 ? h1.textContent.trim() : '',
        sections: document.querySelectorAll('section').length,
      };
    });
    if (!info.h1 || info.text < 3 || info.sections < 2) {
      ok = false;
      errs.push(`structure: ${JSON.stringify(info)}`);
    }
    if (/people who ship|lorem|undefined|NaN|\[object/i.test(info.raw)) {
      ok = false;
      errs.push(`placeholder copy: ${info.raw.slice(0, 80)}`);
    }
    const real = errs.filter((e) => !/favicon|404|net::ERR|third-party|analytics/i.test(e));
    if (real.length) { ok = false; errs.push(...real.slice(0, 3)); }
  } catch (e) {
    ok = false;
    errs.push(String(e.message || e).slice(0, 160));
  }
  page.off('console', onErr);
  page.off('pageerror', onPageErr);
  if (ok) pass++; else fails.push({ name, errs });
}
await browser.close();
console.log(JSON.stringify({ pass, total: meta.projects.length, fails }, null, 1));