#!/usr/bin/env node
/* market_audit.cjs - global-market readiness audit of a live page via the
 * repo's Playwright (keyless, no external APIs).
 * Usage: node market_audit.cjs <url>
 * Checks: performance (LCP/CLS/TTFB/bytes/console errors, desktop + mobile),
 * SEO, i18n/currency signals, legal/trust surface, conversion basics, plus
 * robots.txt and sitemap.xml availability. Output: single JSON on stdout. */
let playwright;
try {
  playwright = require('playwright');
} catch (_e) {
  process.stdout.write(JSON.stringify({ status: 'skipped', message: 'playwright not installed' }));
  process.exit(0);
}

const url = process.argv[2];
if (!url) {
  process.stdout.write(JSON.stringify({ status: 'failed', message: 'usage: node market_audit.cjs <url>' }));
  process.exit(0);
}

const LAUNCH_ARGS = ['--disable-dev-shm-usage'];

async function measure(browser, viewport) {
  const context = await browser.newContext({ viewport, bypassCSP: true });
  const page = await context.newPage();
  let consoleErrors = 0;
  let pageErrors = 0;
  page.on('pageerror', () => { pageErrors += 1; });
  page.on('console', (msg) => { if (msg.type() === 'error') consoleErrors += 1; });

  let httpStatus = null;
  try {
    const resp = await page.goto(url, { waitUntil: 'load', timeout: 45000 });
    httpStatus = resp ? resp.status() : null;
  } catch (err) {
    await context.close().catch(() => {});
    return { status: 'failed', message: String(err && err.message || err).slice(0, 200) };
  }

  await page.waitForTimeout(2000); // settle LCP/CLS (buffered observers)

  const metrics = await page.evaluate(() => new Promise((resolve) => {
    const nav = performance.getEntriesByType('navigation')[0];
    const paint = performance.getEntriesByType('paint');
    const fcp = paint.length ? (paint.find((p) => p.name === 'first-contentful-paint') || {}).startTime ?? null : null;
    let lcp = null;
    let cls = 0;
    try {
      new PerformanceObserver((list) => {
        const es = list.getEntries();
        if (es.length) lcp = es[es.length - 1].startTime;
      }).observe({ type: 'largest-contentful-paint', buffered: true });
      const onShift = (list) => {
        for (const e of list.getEntries()) {
          if (!e.hadRecentInput) cls += e.value;
        }
      };
      new PerformanceObserver(onShift).observe({ type: 'layout-shift', buffered: true });
    } catch (_e) { /* older engine */ }
    const resources = performance.getEntriesByType('resource');
    const bytes = resources.reduce((n, r) => n + (r.transferSize || 0), 0);
    setTimeout(() => resolve({
      ttfb: nav ? Math.round(nav.responseStart) : null,
      fcp: fcp != null ? Math.round(fcp) : null,
      lcp: lcp != null ? Math.round(lcp) : null,
      cls: Number(cls.toFixed(4)),
      bytes,
      resource_count: resources.length,
    }), 800);
  }));

  await context.close().catch(() => {});
  return { status: 'ok', http_status: httpStatus, ...metrics, console_errors: consoleErrors, page_errors: pageErrors };
}

function domChecks() {
  const navEntries = performance.getEntriesByType('navigation');
  const nav = navEntries && navEntries[0];
  const html = () => document.documentElement;
  const meta = (sel) => {
    const el = document.querySelector(sel);
    return el ? (el.getAttribute('content') || '').trim() || null : null;
  };
  const text = (document.body ? document.body.innerText : '') || '';
  const anchors = Array.from(document.querySelectorAll('a[href]'));
  const lower = (s) => (s || '').toLowerCase();

  // Heading hierarchy jumps (h2 -> h4 without h3)
  let headingJumps = 0;
  let lastLevel = 0;
  document.querySelectorAll('h1,h2,h3,h4,h5,h6').forEach((h) => {
    const lvl = Number(h.tagName[1]);
    if (lastLevel && lvl - lastLevel > 1) headingJumps += 1;
    lastLevel = lvl;
  });

  const ctaWords = /^(get\s*started|start|buy|sign\s*up|create|try|explore|shop|order|book|subscribe|join|pricing|contact|learn\s*more|generate)/i;
  let ctaAboveFold = 0;
  document.querySelectorAll('a,button').forEach((el) => {
    const label = (el.innerText || '').trim();
    if (!label || !ctaWords.test(label)) return;
    const box = el.getBoundingClientRect();
    if (box.top >= 0 && box.top < window.innerHeight && box.width > 0) ctaAboveFold += 1;
  });

  const missingAlt = document.querySelectorAll('img:not([alt])').length;
  const inputs = Array.from(document.querySelectorAll('input:not([type=hidden]):not([type=submit]):not([type=checkbox]):not([type=radio]), select, textarea'));
  const unlabeled = inputs.filter((el) => {
    const id = el.getAttribute('id');
    return !(id && document.querySelector(`label[for="${CSS.escape(id)}"]`))
      && !el.getAttribute('aria-label') && !el.getAttribute('aria-labelledby') && !el.closest('label');
  }).length;

  const currencySignals = {
    symbols: /\$|\u20AC|\u00A3|\u20B9|\u20A8|USD|EUR|GBP|PKR|INR|AED|SAR/i.test(text) ? 'present' : 'none',
    switcher: Array.from(document.querySelectorAll('select, button, a')).some((el) =>
      /^(USD|EUR|GBP|PKR|INR|AED|SAR)$/i.test((el.innerText || el.value || '').trim())
    ),
  };

  const legal = {};
  const map = {
    privacy: /privacy/, terms: /terms|conditions/, refund: /refund|return|cancel/,
    gdpr_cookies: /cookie|consent|gdpr/,
  };
  for (const [key, re] of Object.entries(map)) {
    legal[key] = anchors.some((a) => re.test(lower(a.getAttribute('href'))) || re.test(lower(a.innerText)));
  }

  const hreflangs = Array.from(document.querySelectorAll('link[rel=alternate][hreflang]')).length;
  const jsonldTypes = (() => {
    const out = [];
    const currencies = [];
    document.querySelectorAll('script[type="application/ld+json"]').forEach((s) => {
      try {
        const data = JSON.parse(s.textContent);
        const walk = (node) => {
          if (Array.isArray(node)) return node.forEach(walk);
          if (node && typeof node === 'object') {
            if (node['@type']) out.push(...(Array.isArray(node['@type']) ? node['@type'] : [node['@type']]));
            if (typeof node.priceCurrency === 'string') currencies.push(node.priceCurrency.toUpperCase());
            if (node.offers && typeof node.offers === 'object' && typeof node.offers.priceCurrency === 'string') {
              currencies.push(node.offers.priceCurrency.toUpperCase());
            }
            if (node['@graph']) walk(node['@graph']);
          }
        };
        walk(data);
      } catch (_e) { out.push('invalid-json'); }
    });
    return out;
  })();

  const jsonldCurrency = (() => {
    let found = null;
    document.querySelectorAll('script[type="application/ld+json"]').forEach((s) => {
      try {
        JSON.stringify(JSON.parse(s.textContent)).replace(/"priceCurrency"\s*:\s*"([A-Z]{3})"/i, (_m, cur) => {
          found = found || cur.toUpperCase();
          return _m;
        });
      } catch (_e) { /* parse errors counted in jsonldTypes */ }
    });
    return found;
  })();

  const robotsLike = /lorem ipsum|placeholder|TODO/i.test(text.slice(0, 4000));

  return {
    title: document.title || null,
    meta_description: meta('meta[name=description]'),
    canonical: !!document.querySelector('link[rel=canonical]'),
    og: { title: !!meta('meta[property="og:title"]'), image: !!meta('meta[property="og:image"]') },
    twitter_card: !!meta('meta[name="twitter:card"]'),
    lang: html().getAttribute('lang'),
    dir: html().getAttribute('dir'),
    hreflangs,
    viewport: !!meta('meta[name=viewport]'),
    jsonld_types: jsonldTypes,
    jsonld_currency: jsonldCurrency,
    heading_jumps: headingJumps,
    cta_above_fold: ctaAboveFold,
    images_missing_alt: missingAlt,
    unlabeled_inputs: unlabeled,
    currency: currencySignals,
    legal,
    placeholder_copy: robotsLike,
    h1_count: document.querySelectorAll('h1').length,
    ttfb_ms: nav ? Math.round(nav.responseStart) : null,
  };
}

async function main() {
  const browser = await playwright.chromium.launch({ args: LAUNCH_ARGS });
  const out = { status: 'ok', url };
  try {
    out.desktop = await measure(browser, { width: 1440, height: 900 });
    if (out.desktop.status !== 'ok') {
      out.status = 'failed';
      out.message = `desktop load failed: ${out.desktop.message}`;
    } else {
      out.mobile = await measure(browser, { width: 390, height: 844 });
      if (out.mobile.status !== 'ok') {
        out.status = 'failed';
        out.message = `mobile load failed: ${out.mobile.message}`;
      } else {
        const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, bypassCSP: true });
        const page = await context.newPage();
        try {
          const resp = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 });
          if (!resp || resp.status() >= 400) throw new Error(`page HTTP ${resp ? resp.status() : '?'}`);
          await page.waitForTimeout(600);
          out.dom = await page.evaluate(domChecks);
          out.endpoint_tests = await Promise.all([
            ['robots_txt', '/robots.txt'],
            ['sitemap_xml', '/sitemap.xml'],
          ].map(async ([key, path]) => {
            try {
              const r = await context.request.get(new URL(path, url).href, { timeout: 15000 });
              return [key, r.status() < 400];
            } catch (_e) {
              return [key, false];
            }
          })).then(Object.fromEntries);
        } catch (err) {
          out.status = 'failed';
          out.message = String(err && err.message || err).slice(0, 200);
        } finally {
          await context.close().catch(() => {});
        }
      }
    }
  } catch (err) {
    out.status = 'failed';
    out.message = String(err && err.message || err).slice(0, 200);
  } finally {
    await browser.close().catch(() => {});
  }
  process.stdout.write(JSON.stringify(out));
}

main();
