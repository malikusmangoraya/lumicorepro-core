const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  const logs = [];
  page.on('console', m => logs.push(m.type() + ': ' + m.text().slice(0,200)));
  await page.goto('https://malikusmangoraya.github.io/edulify-lms/', { waitUntil: 'load', timeout: 45000 });
  await page.waitForTimeout(15000);
  const info = await page.evaluate(() => {
    const html = document.getElementById('root').innerHTML;
    return {
      len: html.length,
      hasSpin: html.includes('animate-spin'),
      mainChild: Array.from(document.querySelectorAll('#root > *')).map(e=>e.tagName+':'+(e.className||'').slice(0,40)).join(' | ')
    };
  });
  console.log(JSON.stringify(info,null,1));
  console.log('LOGS:'); logs.forEach(l=>console.log('  '+l));
  await browser.close();
})();
