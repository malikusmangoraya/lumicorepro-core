import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Manual chunk groups are limited to third-party runtimes that are always large,
// always on the initial path, and change rarely. Everything under src/ is
// deliberately NOT grouped.
//
// `three`, `recharts` AND `framer-motion` are deliberately ABSENT from this list
// even though they are large. Naming them in manualChunks made rolldown emit them
// as STATIC imports of the entry chunk: the forced chunk became a static
// dependency of every chunk that touched the group, so `three` (~218 KB gzip)
// shipped on first paint even though the only importer is the lazy HeroCanvas,
// and `recharts` (~97 KB gzip) did the same from lazy admin/dashboard routes.
//
// `framer-motion` was the same bug: all of its consumers sit on lazy routes
// (advanced/motion/ui primitives, AIDashboard, ApiSettings), yet grouping it forced
// ~38 KB gzip onto the critical path. Large + lazily reachable is exactly the case
// that must NOT be pre-hoisted - let the bundler split it at the dynamic-import
// boundary instead.
//
// Measured (`npm run size`, hard gate 300 KB initial JS gzip):
//   before any of this        15 chunks / 225.1 KB gzip  -> FAIL
//   drop the framer-motion group ALONE
//                             15 chunks / 224.9 KB gzip  -> still FAIL
//   + CSS-ify Tooltip + ButtonMotion, lazy NotFound
//                             13 chunks / 182.8 KB gzip  -> PASS
// The group was the reason to look, not the cause: the real cost was two *statically
// reachable* components importing framer-motion above the lazy boundary. Removing only
// the group fixes nothing on its own - do not re-add it and do not re-measure by hand.
const VENDOR_GROUPS = [
  {
    name: 'vendor-react',
    packages: ['react', 'react-dom', 'react-router', 'react-router-dom', 'scheduler'],
  },
  { name: 'vendor-icons', packages: ['lucide-react'] },
  { name: 'vendor-http', packages: ['axios', 'qs'] },
];

// Matches the package that owns a resolved module id, so project rules can never
// capture a dependency's internals (e.g. framer-motion/dist/es/render/components).
const PKG_RE = /(?:^|\/)node_modules\/(?:\.pnpm\/[^/]+\/node_modules\/)?((?:@[^/]+\/)?[^/]+)\//;

function manualChunks(id) {
  const match = PKG_RE.exec(id.replace(/\\/g, '/'));
  if (!match) return undefined;
  const pkg = match[1];
  for (const group of VENDOR_GROUPS) {
    if (group.packages.includes(pkg) || group.packages.some((p) => pkg.startsWith(`${p}/`))) {
      return group.name;
    }
  }
  return undefined;
}

export default defineConfig({
  plugins: [
    react({
      // Faster HMR — babel only runs on JSX files
      include: '**/*.{jsx,tsx}',
    }),
  ],

  test: {
    environment: 'jsdom',
    globals: true,
    css: true,
    setupFiles: ['./src/test/setup.js'],
    // Unit tests live under src/ per AGENTS.md §6. Without an explicit include,
    // vitest globs the whole repo and collects test files from .opencode/ and
    // backend/node_modules/, which report hundreds of bogus suite failures.
    include: ['src/**/*.{test,spec}.{js,jsx,ts,tsx}'],
    exclude: [
      '**/node_modules/**',
      '**/dist/**',
      '**/.history/**',
      '.opencode/**',
      'generated-projects/**',
      'backend-library/**',
      'ai-agent/**',
      'backend/**',
      'database/**',
      'docs/**',
      'k8s/**',
      'nginx/**',
      'public/**',
      'templates/**',
      'src/templates/**',
      'e2e/**',
    ],
  },

  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },

  build: {
    // Uncompressed KB per chunk. Mirrors the gzip budget in AGENTS.md §7
    // (JS < 200 KB target / < 300 KB hard limit gzip) — see `npm run size`,
    // which is the real gate because this limit is measured before gzip.
    chunkSizeWarningLimit: 300,

    // Target modern browsers for smaller output
    target: 'es2020',

    // Enable CSS code splitting per chunk
    cssCodeSplit: true,

    // Emits .vite/manifest.json so `npm run size` can walk the entry chunk's
    // real static-import graph instead of summing every lazy route in the app.
    manifest: true,

    rollupOptions: {
      output: {
        manualChunks,

        // Deterministic file names for better caching
        entryFileNames:   'assets/[name]-[hash].js',
        chunkFileNames:   'assets/[name]-[hash].js',
        assetFileNames:   'assets/[name]-[hash][extname]',
      },
    },
  },

  // Faster local dev server
  server: {
    port: 5173,
    hmr: { overlay: true },
    // Proxy API calls (including AI generate + ZIP download) to the Express backend
    proxy: {
      '/api': {
        target: process.env.VITE_API_PROXY_TARGET || 'http://localhost:5000',
        changeOrigin: true,
      },
    },
    // Pre-bundle only what's actually imported
    warmup: {
      clientFiles: [
        './src/main.jsx',
        './src/App.jsx',
        './src/layouts/MainLayout.jsx',
        './src/pages/Home.jsx',
      ],
    },
  },

  // Pre-bundle heavy deps to avoid waterfall on first load
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      'lucide-react',
      'framer-motion',
    ],
    exclude: ['three'],    // load 3D libs only when actually needed
  },
});
