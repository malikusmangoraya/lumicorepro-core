const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  await page.goto('https://malikusmangoraya.github.io/edulify-lms/', { waitUntil: 'load', timeout: 45000 });
  await page.waitForTimeout(2000);
  const kids = await page.evaluate(() => {
    const root = document.getElementById('root');
    return Array.from(root.children).map((el, i) => ({
      i, tag: el.tagName, cls: (el.className || '').slice(0, 120), txt: (el.innerText || '').slice(0, 80)
    }));
  });
  console.log(JSON.stringify(kids, null, 1));
  await browser.close();
})();
