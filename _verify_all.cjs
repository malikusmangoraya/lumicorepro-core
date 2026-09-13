const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const sites = ['edulify-lms','telecare-health','realspace-estate','marketsphere','storefront-pro','travelbook-pro','eventticket-live','fooddelivery-express'];
  for (const site of sites) {
    const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
    try {
      await page.goto(`https://malikusmangoraya.github.io/${site}/`, { waitUntil: 'load', timeout: 45000 });
      await page.waitForTimeout(7000);
      const d = await page.evaluate(() => ({
        main: !!document.querySelector('main'),
        nav: !!document.querySelector('nav'),
        h1: (document.querySelector('h1') || {}).textContent || 'NONE'
      }));
      console.log(`${site}: main=${d.main} nav=${d.nav} h1="${d.h1.trim().slice(0,40)}"`);
    } catch (e) {
      console.log(`${site}: ERROR ${e.message.split('\n')[0]}`);
    }
    await page.close();
  }
  await browser.close();
})();
