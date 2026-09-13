const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  await page.goto('https://malikusmangoraya.github.io/edulify-lms/', { waitUntil: 'networkidle', timeout: 45000 });
  await page.waitForTimeout(3000);
  const info = await page.evaluate(() => {
    const main = document.querySelector('main');
    const nav = document.querySelector('nav');
    const root = document.getElementById('root');
    return {
      rootChildren: root ? root.children.length : 0,
      rootHTML: root ? root.innerHTML.slice(0, 600) : 'no root',
      mainExists: !!main,
      mainInner: main ? main.innerHTML.slice(0, 500) : 'no main',
      navExists: !!nav,
      allH1: Array.from(document.querySelectorAll('h1')).map(h => h.textContent).join(' | ')
    };
  });
  console.log(JSON.stringify(info, null, 2));
  await browser.close();
})();
