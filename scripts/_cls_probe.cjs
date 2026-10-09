/**
 * CLS diagnostic: loads the built site in Chromium (mobile viewport), records
 * every layout-shift entry with its source nodes, and samples geometry of the
 * page skeleton over time so the element that moves can be identified.
 *
 * Usage: node scripts/_cls_probe.cjs [urlPath]
 * Serves dist/ with `vite preview` on port 4322 (spawned without a shell so
 * the server dies with this process).
 */
const { spawn } = require('child_process');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
const PORT = 4322;
const BASE = `http://127.0.0.1:${PORT}`;
const argv = process.argv.slice(2);
const THROTTLE = !argv.includes('no-throttle');
const positional = argv.filter((a) => a !== 'no-throttle');
const URL_PATH = positional.find((a) => a.startsWith('/')) || '/';
const PROBE_MS = Number(positional.find((a) => /^\d+$/.test(a)) || 20000);

async function waitReady(url, timeoutMs = 30000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const r = await fetch(url);
      if (r.ok) return true;
    } catch {
      /* not up */
    }
    await new Promise((res) => setTimeout(res, 300));
  }
  return false;
}

async function main() {
  const viteBin = path.join(ROOT, 'node_modules', 'vite', 'bin', 'vite.js');
  const preview = spawn(
    process.execPath,
    [viteBin, 'preview', '--port', String(PORT), '--strictPort', '--host', '127.0.0.1'],
    { cwd: ROOT, stdio: 'ignore' }
  );
  const stop = () => {
    if (!preview.killed) preview.kill();
  };

  try {
    if (!(await waitReady(`${BASE}/`))) {
      console.error('preview server never came up');
      process.exitCode = 1;
      return;
    }
    const browser = await chromium.launch();
    // Lighthouse mobile emulation: 412x823 @ DPR 2.625, Android UA, touch.
    const page = await browser.newPage({
      viewport: { width: 412, height: 823, deviceScaleFactor: 2.625 },
      isMobile: true,
      hasTouch: true,
      userAgent:
        'Mozilla/5.0 (Linux; Android 11; moto g power (2022)) AppleWebKit/537.36 ' +
        '(KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
    });

    // Lighthouse-like conditions: slow-4G network + 4x CPU slowdown,
    // so font/CSS/JS arrival order matches what the gate measures.
    if (THROTTLE) {
      const cdp = await page.context().newCDPSession(page);
      await cdp.send('Network.enable');
      await cdp.send('Network.emulateNetworkConditions', {
        offline: false,
        latency: 150,
        downloadThroughput: (1.6 * 1024 * 1024) / 8,
        uploadThroughput: (750 * 1024) / 8,
      });
      await cdp.send('Emulation.setCPUThrottlingRate', { rate: 4 });
      console.log('throttling: slow-4G network + 4x CPU (Lighthouse-like)');
    }

    // Track failed requests (backend is absent in a static run).
    const failed = [];
    page.on('requestfailed', (req) => {
      failed.push({ t: Date.now() - t0, url: req.url().slice(-60), err: req.failure()?.errorText });
    });
    page.on('response', (res) => {
      if (res.status() >= 500 || res.status() === 404) {
        failed.push({ t: Date.now() - t0, url: res.url().slice(-60), status: res.status() });
      }
    });

    // Record layout-shift entries live (same signal Lighthouse scores).
    await page.addInitScript(() => {
      window.__shifts = [];
      try {
        new PerformanceObserver((list) => {
          for (const e of list.getEntries()) {
            if (e.hadRecentInput) continue;
            window.__shifts.push({
              t: Math.round(e.startTime),
              value: Number(e.value.toFixed(4)),
              sources: (e.sources || []).map((s) => ({
                node: describe(s.node),
                prev: s.previousRect && [s.previousRect.y, s.previousRect.height],
                cur: s.currentRect && [s.currentRect.y, s.currentRect.height],
              })),
            });
          }
        }).observe({ type: 'layout-shift', buffered: true });
      } catch {
        /* unsupported */
      }
      function describe(node) {
        if (!node || !node.tagName) return String(node);
        const id = node.id ? `#${node.id}` : '';
        const cls =
          node.className && typeof node.className === 'string'
            ? '.' + node.className.split(/\s+/).filter(Boolean).slice(0, 3).join('.')
            : '';
        return `${node.tagName.toLowerCase()}${id}${cls}`.slice(0, 90);
      }
    });

    const samples = [];
    const t0 = Date.now();
    await page.goto(BASE + URL_PATH, { waitUntil: 'commit' });
    const start = Date.now();
    while (Date.now() - start < PROBE_MS) {
      const snap = await page.evaluate(() => {
        const rect = (el) => {
          if (!el) return null;
          const r = el.getBoundingClientRect();
          return [Math.round(r.top + window.scrollY), Math.round(r.height)];
        };
        const main = document.querySelector('main');
        // Deep sample: every section + every direct child wrapper, with a
        // text fingerprint so content swaps are visible, not just sizes.
        const nodes = main
          ? [...main.querySelectorAll(':scope > section, :scope > div, section')]
          : [];
        const seen = new Set();
        const blocks = [];
        nodes.forEach((el, i) => {
          const r = el.getBoundingClientRect();
          const key = `${i}:${Math.round(r.top + scrollY)}`;
          if (seen.has(key)) return;
          seen.add(key);
          blocks.push({
            i,
            cls: (el.className || '').toString().split(/\s+/).slice(0, 2).join('.'),
            top: Math.round(r.top + scrollY),
            h: Math.round(r.height),
            txt: (el.innerText || '').replace(/\s+/g, ' ').slice(0, 40),
          });
        });
        const fonts = [...document.fonts].map((f) => ({
          f: `${f.family} ${f.weight}`,
          s: f.status,
        }));
        return {
          docH: document.documentElement.scrollHeight,
          blocks,
          fontsLoaded: fonts.filter((f) => f.s === 'loaded').length,
          fontsTotal: fonts.length,
          footer: rect(document.querySelector('footer')),
          imgs: [...document.querySelectorAll('img')].map((img) => ({
            src: (img.currentSrc || img.src || '').split('/').pop().slice(0, 32),
            complete: img.complete,
            nw: img.naturalWidth,
          })),
        };
      });
      samples.push({ t: Date.now() - start, ...snap });
      await new Promise((res) => setTimeout(res, 60));
    }

    const shifts = await page.evaluate(() => window.__shifts || []);
    await browser.close();

    // Report: cumulative shift + biggest entries.
    const total = shifts.reduce((s, x) => s + x.value, 0);
    console.log(`URL: ${URL_PATH} | total layout-shift over ${PROBE_MS}ms: ${total.toFixed(4)}`);
    console.log('--- shift entries (top 8 by value):');
    shifts
      .sort((a, b) => b.value - a.value)
      .slice(0, 8)
      .forEach((s) => {
        console.log(
          `  t=${s.t}ms value=${s.value} sources=${JSON.stringify(s.sources).slice(0, 400)}`
        );
      });

    console.log('--- geometry/content transitions (delta > 30px or text swap):');
    for (let i = 1; i < samples.length; i++) {
      const a = samples[i - 1];
      const b = samples[i];
      const events = [];
      if (Math.abs(a.docH - b.docH) > 30) events.push(`docH ${a.docH} -> ${b.docH}`);
      if (a.fontsLoaded !== b.fontsLoaded) {
        events.push(`fonts ${a.fontsLoaded}/${a.fontsTotal} -> ${b.fontsLoaded}/${b.fontsTotal}`);
      }
      const prevByIdx = new Map(a.blocks.map((x) => [x.i, x]));
      b.blocks.forEach((kid) => {
        const prev = prevByIdx.get(kid.i);
        if (!prev) {
          events.push(`+block[${kid.i}] ${kid.cls} h=${kid.h}`);
          return;
        }
        if (Math.abs(prev.h - kid.h) > 30) {
          events.push(`block[${kid.i}] ${kid.cls} h ${prev.h} -> ${kid.h}`);
        }
        if (Math.abs(prev.top - kid.top) > 30) {
          events.push(`block[${kid.i}] ${kid.cls} top ${prev.top} -> ${kid.top}`);
        }
        if (prev.txt !== kid.txt) {
          events.push(
            `block[${kid.i}] txt "${prev.txt.slice(0, 18)}" -> "${kid.txt.slice(0, 18)}"`
          );
        }
        if (prev.h - kid.h > 100) {
          events.push(
            `SHRINK block[${kid.i}] ${kid.cls} ${prev.h} -> ${kid.h}`
          );
        }
      });
      if (a.footer && b.footer && Math.abs(a.footer[0] - b.footer[0]) > 30) {
        events.push(`footer top ${a.footer[0]} -> ${b.footer[0]}`);
      }
      const doneMap = new Map(a.imgs.map((x) => [x.src, x.complete]));
      b.imgs.forEach((img) => {
        const was = doneMap.get(img.src);
        if (was === false && img.complete) events.push(`img done: ${img.src}`);
      });
      if (events.length) console.log(`  t=${b.t}ms  ${events.join(' | ')}`);
    }

    const last = samples[samples.length - 1];
    console.log(`--- fonts: ${last.fontsLoaded}/${last.fontsTotal} loaded by end`);
    console.log('--- footer top over time:',
      samples.map((s) => (s.t + ':' + (s.footer ? s.footer[0] : 'x'))).join(' '));
    console.log('--- failed/4xx/5xx requests:');
    failed.slice(0, 12).forEach((f) => console.log('  ', JSON.stringify(f)));
    const newlyDone = last.imgs.filter((x) => x.complete && x.nw > 0);
    console.log(`--- images: ${newlyDone.length}/${last.imgs.length} complete by end`);

    console.log('--- images still pending at end:');
    const pending = samples[samples.length - 1].imgs.filter((x) => !x.complete);
    console.log(pending.length ? JSON.stringify(pending) : '  none');
  } finally {
    stop();
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
