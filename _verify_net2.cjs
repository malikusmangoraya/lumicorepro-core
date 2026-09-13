const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  const reqs = [];
  page.on('request', r => reqs.push(r.url()));
  await page.goto('https://malikusmangoraya.github.io/edulify-lms/', { waitUntil: 'domcontentloaded', timeout: 45000 });
  await page.waitForTimeout(6000);
  console.log('ALL REQUESTS (' + reqs.length + '):');
  reqs.forEach(u => console.log('  ' + u.replace('https://malikusmangoraya.github.io/', '')));
  await page.screenshot({ path: 'C:\\Users\\AZAM COMPUTERS\\AppData\\Local\\Temp\\opencode\\edulify_debug.png' });
  const txt = await page.evaluate(() => document.body.innerText.slice(0, 400));
  console.log('BODY:', txt.replace(/\n+/g, ' | '));
  await browser.close();
})();
