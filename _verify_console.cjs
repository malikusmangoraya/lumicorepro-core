const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  const errors = [];
  page.on('console', m => { if (m.type() === 'error') errors.push('CONSOLE: ' + m.text()); });
  page.on('pageerror', e => errors.push('PAGEERROR: ' + e.message));
  page.on('requestfailed', r => errors.push('REQFAIL: ' + r.url().slice(0,200) + ' -> ' + (r.failure()?.errorText || '?')));
  await page.goto('https://malikusmangoraya.github.io/edulify-lms/', { waitUntil: 'networkidle', timeout: 45000 });
  await page.waitForTimeout(2500);
  const body = await page.evaluate(() => document.body.innerText.replace(/\n+/g, ' | ').slice(0, 1200));
  console.log('BODY:', body);
  console.log('\nERRORS (' + errors.length + '):');
  errors.slice(0, 12).forEach(e => console.log('  ' + e));
  await browser.close();
})();
