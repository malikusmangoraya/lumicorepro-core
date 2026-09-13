const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  for (const site of ['edulify-lms', 'nexa-marketplace']) {
    const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
    try {
      await page.goto(`https://malikusmangoraya.github.io/${site}/`, { waitUntil: 'networkidle', timeout: 45000 });
      await page.waitForTimeout(1500);
      await page.screenshot({ path: `C:\\Users\\AZAM COMPUTERS\\AppData\\Local\\Temp\\opencode\\${site}.png` });
      const body = await page.evaluate(() => document.body.innerText.slice(0, 600));
      console.log(`=== ${site} ===`);
      console.log(body.replace(/\n+/g, ' | ').slice(0, 500));
    } catch (e) {
      console.log(`${site} ERROR: ${e.message}`);
    }
    await page.close();
  }
  await browser.close();
})();
