const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  const statuses = [];
  page.on('response', r => { if (r.url().includes('malikusmangoraya')) statuses.push(r.status() + ' ' + r.url().replace('https://malikusmangoraya.github.io/','')); });
  page.on('requestfailed', r => statuses.push('FAIL ' + r.url().replace('https://malikusmangoraya.github.io/','') + ' ' + (r.failure()?.errorText||'')));
  await page.goto('https://malikusmangoraya.github.io/edulify-lms/', { waitUntil: 'domcontentloaded', timeout: 45000 });
  await page.waitForTimeout(2000);
  // manual module import of Home chunk
  try {
    await page.evaluate(async () => {
      try {
        const m = await import('./assets/Home-DPpSPEBI.js');
        window.__homeMod = Object.keys(m);
      } catch (e) { window.__homeErr = String(e); }
    });
    const res = await page.evaluate(() => ({ mod: window.__homeMod, err: window.__homeErr }));
    console.log('DIRECT MODULE IMPORT:', JSON.stringify(res));
  } catch (e) { console.log('eval err', e.message); }
  console.log('STATUSES:');
  statuses.forEach(s => console.log('  ' + s));
  await browser.close();
})();
