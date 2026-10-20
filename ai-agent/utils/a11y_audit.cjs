#!/usr/bin/env node
/* a11y_audit.cjs — axe-core audit of a live page via the repo's Playwright.
 * Usage: node a11y_audit.cjs <url>
 * axe-core is fetched from the jsDelivr CDN (keyless); Playwright resolves from
 * the repo root node_modules. Output: single JSON object on stdout. */
let playwright;
try {
  playwright = require('playwright');
} catch (e) {
  process.stdout.write(JSON.stringify({ status: 'skipped', message: 'playwright not installed' }));
  process.exit(0);
}

const url = process.argv[2];

async function main() {
  const { chromium } = playwright;
  const browser = await chromium.launch();
  try {
    // bypassCSP: generated sites ship strict CSP (script-src 'self') that
    // would otherwise block the axe injection.
    const page = await browser.newPage({ viewport: { width: 1280, height: 800 }, bypassCSP: true });
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 });
    await page.waitForTimeout(1200);
    await page.addScriptTag({ url: 'https://cdn.jsdelivr.net/npm/axe-core@4.10.2/axe.min.js' }).catch(() => {
      throw new Error('axe-core CDN unreachable');
    });
    const result = await page.evaluate(async () => {
      const axe = window.axe;
      if (!axe) return { status: 'failed', message: 'axe failed to load' };
      const r = await axe.run(window.document, {
        resultTypes: ['violations'],
        runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'] },
      });
      return {
        status: 'ok',
        url: r.url,
        passes: r.passes ? r.passes.reduce((n, p) => n + p.nodes.length, 0) : 0,
        violations: (r.violations || []).map((v) => ({
          id: v.id,
          impact: v.impact,
          help: v.help,
          nodes: v.nodes.length,
        })),
      };
    });
    process.stdout.write(JSON.stringify(result));
  } catch (err) {
    process.stdout.write(JSON.stringify({ status: 'failed', message: String(err && err.message || err).slice(0, 200) }));
  } finally {
    await browser.close();
  }
}

main();
