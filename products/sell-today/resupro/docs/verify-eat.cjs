const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const url = process.argv[2];
  if (!url) { console.error('pass URL'); process.exit(1); }
  const errs = [];
  page.on('pageerror', (e) => errs.push(e.message));
  await page.goto(url, { waitUntil: 'networkidle', timeout: 45000 });
  await page.waitForTimeout(1500);
  const out = {};
  out.title = await page.title();
  out.images = await page.evaluate(() => {
    const host = location.host;
    return Array.from(document.images).map((i) => {
      const u = new URL(i.src, location.href);
      return { local: u.host === host, src: u.pathname.split('/').pop(), ok: i.complete && i.naturalWidth > 0 };
    }).filter((x, idx, a) => a.findIndex((y) => y.src === x.src) === idx);
  });
  out.external = await page.evaluate(() => {
    const host = location.host;
    return performance.getEntriesByType('resource').filter((r) => r.initiatorType === 'img' && !r.name.includes(host)).map((r) => r.name);
  });
  out.errs = errs;
  console.log(JSON.stringify(out, null, 2));
  await browser.close();
})().catch((e) => { console.error(e.message); process.exit(1); });