#!/usr/bin/env node
/**
 * Lighthouse CI runner (AGENTS.md §7 performance targets).
 *
 * Finds a Chromium executable (CHROME_PATH wins, then the Playwright browser
 * cache, then system Chrome), builds `dist/` if it is missing, serves it with
 * `vite preview` on port 4319 and runs `lhci autorun` against the URLs in
 * `.lighthouserc.json`.
 *
 * Usage:  npm run test:perf
 * Targets live in .lighthouserc.json: performance >= 95 and LCP < 1.5s are
 * WARN (goals), CLS < 0.1 is ERROR (hard limit per AGENTS.md §7).
 */
import { spawn, spawnSync } from 'node:child_process';
import { existsSync, readdirSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const PORT = 4319;
const BASE_URL = `http://127.0.0.1:${PORT}`;

function findChrome() {
  if (process.env.CHROME_PATH && existsSync(process.env.CHROME_PATH)) {
    return process.env.CHROME_PATH;
  }
  const home = os.homedir();
  const cacheRoots = [
    process.env.LOCALAPPDATA && path.join(process.env.LOCALAPPDATA, 'ms-playwright'),
    path.join(home, 'AppData', 'Local', 'ms-playwright'),
    path.join(home, '.cache', 'ms-playwright'),
    path.join(home, 'Library', 'Caches', 'ms-playwright'),
  ].filter(Boolean);

  const relBinaries = [
    path.join('chrome-win64', 'chrome.exe'),
    path.join('chrome-win', 'chrome.exe'),
    path.join('chrome-linux', 'chrome'),
    path.join('chrome-linux64', 'chrome'),
    path.join('chrome-mac', 'Chromium.app', 'Contents', 'MacOS', 'Chromium'),
    path.join('chrome-mac-arm64', 'Chromium.app', 'Contents', 'MacOS', 'Chromium'),
  ];

  for (const root of cacheRoots) {
    if (!existsSync(root)) continue;
    const dirs = readdirSync(root)
      .filter((d) => d.startsWith('chromium-') && !d.includes('headless_shell'))
      .sort()
      .reverse();
    for (const dir of dirs) {
      for (const rel of relBinaries) {
        const candidate = path.join(root, dir, rel);
        if (existsSync(candidate)) return candidate;
      }
    }
  }

  const systemCandidates = [
    'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
    '/usr/bin/google-chrome',
    '/usr/bin/chromium',
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  ];
  for (const candidate of systemCandidates) {
    if (existsSync(candidate)) return candidate;
  }
  return null;
}

async function waitForServer(url, timeoutMs = 30000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const resp = await fetch(url);
      if (resp.ok) return true;
    } catch {
      /* not up yet */
    }
    await new Promise((r) => setTimeout(r, 500));
  }
  return false;
}

function main() {
  const chrome = findChrome();
  if (!chrome) {
    console.error(
      'No Chromium found. Install one (npx playwright install chromium) or set CHROME_PATH.'
    );
    process.exit(1);
  }
  console.log(`[lighthouse] chrome: ${chrome}`);

  if (!existsSync(path.join(ROOT, 'dist', 'index.html'))) {
    console.log('[lighthouse] dist/ missing — running npm run build ...');
    const build = spawnSync('npm', ['run', 'build'], { cwd: ROOT, stdio: 'inherit', shell: true });
    if (build.status !== 0) {
      console.error('[lighthouse] build failed');
      process.exit(build.status ?? 1);
    }
  }

  // Spawn vite via its JS entry with process.execPath (no shell) so
  // preview.kill() actually reaches the node process — killing a shell
  // wrapper on Windows leaves the server orphaned on port 4319.
  const viteBin = path.join(ROOT, 'node_modules', 'vite', 'bin', 'vite.js');
  const preview = spawn(
    process.execPath,
    [viteBin, 'preview', '--port', String(PORT), '--strictPort', '--host', '127.0.0.1'],
    { cwd: ROOT, stdio: 'ignore' }
  );

  let exitCode = 1;
  const stop = () => {
    if (!preview.killed) preview.kill();
  };

  waitForServer(`${BASE_URL}/`)
    .then(async (ready) => {
      if (!ready) {
        console.error(`[lighthouse] preview server never came up on ${BASE_URL}`);
        stop();
        process.exit(1);
      }
      console.log(`[lighthouse] serving dist/ at ${BASE_URL} — running lhci autorun ...`);
      const lhci = spawn(
        process.execPath,
        [path.join(ROOT, 'node_modules', '@lhci', 'cli', 'src', 'cli.js'), 'autorun'],
        {
          cwd: ROOT,
          stdio: 'inherit',
          env: { ...process.env, CHROME_PATH: chrome },
        }
      );
      lhci.on('exit', (code) => {
        exitCode = code ?? 1;
        stop();
        process.exit(exitCode);
      });
    })
    .catch((err) => {
      console.error('[lighthouse] failed:', err);
      stop();
      process.exit(1);
    });

  process.on('SIGINT', () => {
    stop();
    process.exit(130);
  });
}

main();
