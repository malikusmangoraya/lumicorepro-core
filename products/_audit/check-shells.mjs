/**
 * check-shells.mjs — compiles the files this session touched, per product, with the product's
 * own Vite (write:false, so nothing lands on disk).
 *
 * The app's build graph does not reach layouts/LandingLayout.jsx, layouts/AppLayout.jsx or
 * components/business/Hero.jsx — they are registered through lib/LazyLayouts.jsx, which no page
 * imports — so a green `vite build` proves nothing about them. This check builds them
 * explicitly, which resolves their imports and fails on any syntax error.
 *
 * Run: node products/_audit/check-shells.mjs
 */
import { existsSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
import path from 'node:path';

const PRODUCTS = [
  'apex',
  'aurelia-estates',
  'aurum-fitness',
  'claimflow-ai',
  'flowpilot',
  'meridian-capital',
  'nuage-events',
  'prestige-studio',
  'resupro',
  'saffron-voyage',
  'studio-lumen',
];

// Every file this session created or rewrote.
const TARGETS = [
  'src/App.jsx',
  'src/pages/NotFound.jsx',
  'src/layouts/LandingLayout.jsx',
  'src/layouts/AppLayout.jsx',
  'src/components/business/Hero.jsx',
  'src/components/checkout/CheckoutFlow.jsx',
  'src/lib/paymentProvider.js',
  'src/components/common/CookieConsent.jsx',
  'src/pages/Login.jsx',
  'src/pages/Register.jsx',
  'src/components/auth/SocialLogin.jsx',
  'src/components/common/SocialShare.jsx',
];

const results = [];
for (const id of PRODUCTS) {
  const root = `products/${id}/frontend`;
  const vitePath = path.join(root, 'node_modules', 'vite', 'dist', 'node', 'index.js');
  const reactCandidates = ['index.mjs', 'index.js'].map((f) =>
    path.join(root, 'node_modules', '@vitejs', 'plugin-react', 'dist', f)
  );
  const reactPath = reactCandidates.find((candidate) => existsSync(candidate));
  if (!existsSync(vitePath) || !reactPath) {
    results.push({ id, ok: false, error: 'dependencies not installed' });
    continue;
  }

  const { build } = await import(pathToFileURL(vitePath).href);
  const reactModule = await import(pathToFileURL(reactPath).href);
  const react = reactModule.default || reactModule;

  const entry = {};
  for (const target of TARGETS) {
    if (!existsSync(path.join(root, target))) continue;
    entry[target.replace(/[^a-zA-Z0-9]/g, '_')] = path.resolve(root, target);
  }

  try {
    await build({
      root: path.resolve(root),
      logLevel: 'error',
      plugins: [react()],
      build: {
        write: false,
        minify: false,
        lib: { entry, formats: ['es'] },
        rollupOptions: { external: [/^react/, /^react-dom/, /^react-router-dom/, /^lucide-react/, /^i18next/, /^react-i18next/, /^axios/, /^zustand/, /^framer-motion/, /^@tanstack/] },
      },
    });
    results.push({ id, ok: true, files: Object.keys(entry).length });
  } catch (error) {
    const first = String(error.message || error).split('\n').slice(0, 6).join(' | ');
    results.push({ id, ok: false, error: first });
  }
}

console.log('product            | files compiled | result');
console.log('-------------------|----------------|-------');
for (const r of results) {
  console.log(`${r.id.padEnd(18)} | ${String(r.files ?? 0).padStart(14)} | ${r.ok ? 'compiled' : `FAIL → ${r.error}`}`);
}
const failed = results.filter((r) => !r.ok);
const total = results.reduce((sum, r) => sum + (r.files || 0), 0);
console.log(`\n${results.length - failed.length}/${results.length} products compiled cleanly (${total} file compilations)`);
process.exitCode = failed.length ? 1 : 0;
