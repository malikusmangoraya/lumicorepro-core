const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  await page.goto('https://malikusmangoraya.github.io/edulify-lms/', { waitUntil: 'load', timeout: 45000 });
  await page.waitForTimeout(2500);
  const info = await page.evaluate(() => {
    const html = document.getElementById('root').innerHTML;
    return {
      hasSpin: html.includes('animate-spin'),
      hasMain: html.includes('<main'),
      hasLoaderText: 'Loader',
      bg950: (html.match(/bg-slate-950/g) || []).length,
      rootLen: html.length,
      first600: html.slice(0, 600)
    };
  });
  console.log(JSON.stringify(info, null, 1));
  await browser.close();
})();
