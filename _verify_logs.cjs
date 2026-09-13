const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  const logs = [];
  page.on('console', m => logs.push(m.type().toUpperCase() + ': ' + m.text().slice(0, 300)));
  page.on('pageerror', e => logs.push('PAGEERR: ' + e.message));
  await page.goto('https://malikusmangoraya.github.io/edulify-lms/', { waitUntil: 'load', timeout: 45000 });
  await page.waitForTimeout(4000);
  const resources = await page.evaluate(() => performance.getEntriesByType('resource').map(r => r.name.replace('https://malikusmangoraya.github.io/','')));
  console.log('RESOURCES:', resources.join('\n  '));
  console.log('LOGS:');
  logs.forEach(l => console.log('  ' + l));
  await browser.close();
})();
