/**
 * E2E server launcher — serves the PRODUCTION build via `vite preview`.
 *
 * Why not the dev server: Vite's dev-time dependency optimizer plus per-module
 * transforms are extremely slow on this machine (measured cold: first request
 * 19-34s, a single lazy module 8.5s, and `/@vite/client` once never answered at
 * all within 120s). Because the HMR client is a load-blocking subresource, that
 * made `page.goto` abort with ERR_ABORTED and `npm run test:e2e` fail on any
 * cold checkout — a tooling problem masquerading as an app failure.
 *
 * `vite build` takes ~5s and `vite preview` serves static files with no
 * optimizer, no transform and no HMR client, so the run is deterministic and we
 * also test the artifact that actually ships. SPA deep links are handled by the
 * preview server's SPA fallback.
 */
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const ROOT = fileURLToPath(new URL('..', import.meta.url));
const PORT = process.env.E2E_PORT || '5173';
const ORIGIN = `http://localhost:${PORT}`;
const READY_TIMEOUT_MS = 300000; // builds are slow here; be generous
const VITE_BIN = fileURLToPath(new URL('../node_modules/vite/bin/vite.js', import.meta.url));

const run = (args, label) =>
  new Promise((resolve, reject) => {
    const child = spawn(process.execPath, [VITE_BIN, ...args], {
      cwd: ROOT,
      stdio: 'inherit',
      env: { ...process.env, BROWSER: 'none' },
    });
    child.on('error', reject);
    child.on('exit', (code) =>
      code === 0 ? resolve() : reject(new Error(`${label} exited with code ${code}`))
    );
  });

const probe = async (path) => {
  try {
    const res = await fetch(`${ORIGIN}${path}`, { signal: AbortSignal.timeout(15000) });
    await res.arrayBuffer();
    return res.ok;
  } catch {
    return false;
  }
};

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function waitUntilReady() {
  const deadline = Date.now() + READY_TIMEOUT_MS;
  while (Date.now() < deadline) {
    if (await probe('/')) return true;
    await sleep(500);
  }
  return false;
}

try {
  process.stdout.write('[e2e-server] building production bundle...\n');
  await run(['build'], 'vite build');
} catch (err) {
  process.stderr.write(`[e2e-server] build failed: ${err.message}\n`);
  process.exit(1);
}

const preview = spawn(process.execPath, [VITE_BIN, 'preview', '--port', PORT, '--strictPort'], {
  cwd: ROOT,
  stdio: ['ignore', 'pipe', 'pipe'],
  env: process.env,
});
preview.stdout.on('data', (d) => process.stdout.write(`[preview] ${d}`));
preview.stderr.on('data', (d) => process.stderr.write(`[preview] ${d}`));

const shutdown = (code) => {
  if (!preview.killed) preview.kill('SIGTERM');
  process.exit(code);
};
process.on('SIGINT', () => shutdown(0));
process.on('SIGTERM', () => shutdown(0));
preview.on('exit', (code) => process.exit(code ?? 0));

if (!(await waitUntilReady())) {
  process.stderr.write(`[e2e-server] preview never became ready at ${ORIGIN}\n`);
  shutdown(1);
}

// Warm the SPA fallback so the first deep link the tests hit is not cold.
for (const p of ['/index.html', '/login', '/templates']) await probe(p);

process.stdout.write(`[e2e-server] ready at ${ORIGIN}\n`);
await new Promise(() => {});
