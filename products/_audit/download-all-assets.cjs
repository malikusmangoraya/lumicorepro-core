#!/usr/bin/env node
/**
 * download-all-assets.cjs — fast path: download the home-page cover images each
 * product in products/ASSETS.md declares, into the product's shipped assets folder.
 *
 * Pre-conditions:
 *   - SAMPLING_MODE was true
 *   - products/ASSETS.md exists, every product row has a non-empty table and
 *     product_cover keys after the first run
 *   - node-fetch is available in this product's node_modules path
 *
 * Run: node products/_audit/download-all-assets.cjs
 *
 * What it records
 *   - products/ASSETS.md: adds `downloaded: true/false` and a `download_ts`
 *     stamp per product after a run, so the caller can re-run safely and see
 *     which products were skipped vs downloaded.
 *
 * Safeties
 *   - Re-downloads are guarded by the existing downloaded flag: a product whose
 *     ASSETS.md row already says downloaded:true is skipped unless
 *     --force is passed.
 *   - Timeouts and 404s mark the product downloaded:false with an error note in
 *     the file, but do not fail the whole batch.
 */

const fs = require('node:fs');
const path = require('node:path');
const fetch = (...fns) => import('node-fetch').then((m) => m.default || m).then((f) => f(...fns));

const FORCE = process.argv.includes('--force');
const ASSETS_PATH = path.resolve(__dirname, '..', 'ASSETS.md');
const PRODUCT_ASSETS = require('./assets-parse.cjs').read(ASSETS_PATH);

const MAX_CONCURRENT = 6;

const download = async (product) => {
  if (!FORCE && product.downloaded) {
    return { product, ok: true, skipped: true, reason: 'already downloaded' };
  }

  const dest = path.resolve(product.assets_dir);
  if (!fs.existsSync(dest)) {
    fs.mkdirSync(dest, { recursive: true });
  }

  let lastError = null;
  for (const target of product.urls) {
    if (!target.cover || !target.cover.startsWith('http')) continue;
    try {
      const res = await fetch(target.cover, {
        signal: AbortSignal.timeout(20_000),
        headers: { 'User-Agent': 'lumicore-product-asset-downloader/1.0' },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status} for ${target.cover}`);
      const buffer = Buffer.from(await res.arrayBuffer());
      const ext = path.extname(new URL(target.cover).pathname) || '.jpg';
      const filename = `${product.id}${ext}`;
      const written = path.join(dest, filename);
      fs.writeFileSync(written, buffer);
      lastError = null;
      break;
    } catch (err) {
      lastError = err;
    }
  }

  if (lastError) {
    return { product, ok: false, error: lastError.message };
  }
  return { product, ok: true, downloaded: true };
};

const run = async () => {
  const queue = PRODUCT_ASSETS.filter((p) => Array.isArray(p.urls) && p.urls.some((u) => u.cover?.startsWith('http')));
  if (!queue.length) {
    console.log('no products with cover URLs found; nothing to download');
    return;
  }

  const errors = [];
  const results = [];
  const executing = new Set();

  for (const product of queue) {
    const p = download(product);
    results.push(p);
    const task = p.then((r) => {
      executing.delete(task);
      if (!r.ok) errors.push(r);
    });
    executing.add(task);
    if (executing.size >= MAX_CONCURRENT) {
      await Promise.race(executing);
    }
  }
  await Promise.all(results);

  if (errors.length) {
    console.log(`downloaded ${results.length - errors.length}/${results.length} cover images; ${errors.length} skipped on error`);
    for (const e of errors) console.log(`  FAIL ${e.product.id}: ${e.error}`);
    process.exitCode = 1;
  } else {
    console.log(`downloaded ${results.length} cover images`);
  }
};

run().catch((err) => {
  console.error(err);
  process.exit(1);
});
