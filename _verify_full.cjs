const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  await page.goto('https://malikusmangoraya.github.io/edulify-lms/', { waitUntil: 'networkidle', timeout: 45000 });
  await page.waitForTimeout(2000);
  const body = await page.evaluate(() => document.body.innerText);
  console.log('=== FULL BODY TEXT (first 1500) ===');
  console.log(body.replace(/\n+/g, ' | ').slice(0, 1500));
  console.log('\n=== HTML class hints ===');
  const classes = await page.evaluate(() => {
    const el = document.querySelector('main') || document.body;
    return el.outerHTML.slice(0, 800);
  });
  console.log(classes);
  await browser.close();
})();
