const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  const reqs = [];
  page.on('request', r => { if (r.url().includes('/assets/')) reqs.push('REQ ' + r.url().split('/assets/')[1]); });
  page.on('requestfailed', r => { if (r.url().includes('/assets/')) reqs.push('FAIL ' + r.url().split('/assets/')[1] + ' ' + (r.failure()?.errorText || '')); });
  page.on('response', r => { if (r.url().includes('/assets/')) reqs.push('RES ' + r.status() + ' ' + r.url().split('/assets/')[1]); });
  await page.goto('https://malikusmangoraya.github.io/edulify-lms/', { waitUntil: 'networkidle', timeout: 45000 });
  await page.waitForTimeout(1500);
  console.log('ASSET REQUESTS (' + reqs.length + '):');
  reqs.slice(0, 25).forEach(r => console.log('  ' + r));
  await browser.close();
})();
