const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ args: ['--disable-application-cache','--no-first-run'] });
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  const errs = [];
  page.on('pageerror', e => errs.push('PAGEERR: ' + e.message));
  page.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') errs.push(m.type() + ': ' + m.text().slice(0,150)); });
  await page.goto('https://malikusmangoraya.github.io/edulify-lms/', { waitUntil: 'load', timeout: 45000 });
  await page.waitForTimeout(12000);
  const info = await page.evaluate(() => ({
    hasMain: !!document.querySelector('main'),
    hasNav: !!document.querySelector('nav'),
    h1: Array.from(document.querySelectorAll('h1')).map(h => h.textContent.trim()).join(' | '),
    bodyLen: document.body.innerText.length,
    bodyText: document.body.innerText.replace(/\n+/g,' | ').slice(0,300),
    htmlLen: document.querySelector('#root').innerHTML.length
  }));
  console.log(JSON.stringify(info, null, 1));
  console.log('ERRS (' + errs.length + '):');
  errs.slice(0,10).forEach(e => console.log('  ' + e));
  await browser.close();
})();
