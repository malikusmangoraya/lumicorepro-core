import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

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
    exclude: ['node_modules', 'dist', '.history', 'generated-projects', 'backend-library', 'ai-agent', 'backend', 'database', 'docs', 'k8s', 'nginx', 'public', 'templates', 'src/templates', 'e2e'],
  },

  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },

  build: {
    // Raise warning threshold — we know images are large
    chunkSizeWarningLimit: 600,

    // Target modern browsers for smaller output
    target: 'es2020',

    // Enable CSS code splitting per chunk
    cssCodeSplit: true,

    rollupOptions: {
      output: {
        // Manual chunk strategy — split vendor libs from app code
        manualChunks(id) {
          // Core React runtime — smallest, most cached chunk
          if (id.includes('node_modules/react/') ||
              id.includes('node_modules/react-dom/') ||
              id.includes('node_modules/react-router')) {
            return 'vendor-react';
          }
          // Framer Motion — lazy-loaded per-chunk (NOT a shared vendor chunk)
          // Each template that uses motion will include motion in its own chunk
          if (id.includes('node_modules/framer-motion') ||
              id.includes('node_modules/motion-dom') ||
              id.includes('node_modules/motion-utils')) {
            return 'vendor-motion';
          }
          // Lucide icons — large, rarely changes
          if (id.includes('node_modules/lucide-react')) {
            return 'vendor-icons';
          }
          // Three.js / GSAP — very large, lazy load only
          if (id.includes('node_modules/three') ||
              id.includes('node_modules/gsap')) {
            return 'vendor-3d';
          }
          // Axios + other HTTP libs
          if (id.includes('node_modules/axios') ||
              id.includes('node_modules/qs')) {
            return 'vendor-http';
          }
          // Charts libraries (recharts)
          if (id.includes('node_modules/recharts') ||
              id.includes('node_modules/d3-') ||
              id.includes('node_modules/victory')) {
            return 'vendor-charts';
          }
          // Form libraries
          if (id.includes('node_modules/react-hook-form') ||
              id.includes('node_modules/formik') ||
              id.includes('node_modules/yup') ||
              id.includes('node_modules/zod')) {
            return 'vendor-forms';
          }
          // Utility libraries (date-fns, uuid, etc.)
          if (id.includes('node_modules/date-fns') ||
              id.includes('node_modules/uuid') ||
              id.includes('node_modules/classnames') ||
              id.includes('node_modules/clsx')) {
            return 'vendor-utils';
          }
          // UI libraries (react-select, react-spring, etc.)
          if (id.includes('node_modules/react-select') ||
              id.includes('node_modules/react-spring') ||
              id.includes('node_modules/@radix-ui') ||
              id.includes('node_modules/tailwind-')) {
            return 'vendor-ui';
          }
          // All other node_modules
          if (id.includes('node_modules/')) {
            return 'vendor-misc';
          }
          // Template chunks — group by category so each is only loaded on demand
          if (id.includes('/templates/dashboard/'))   return 'templates-dashboard';
          if (id.includes('/templates/ecommerce/'))   return 'templates-ecommerce';
          if (id.includes('/templates/ai/'))          return 'templates-ai';
          if (id.includes('/templates/business/'))    return 'templates-business';
          if (id.includes('/templates/restaurant/'))  return 'templates-restaurant';
          if (id.includes('/templates/realestate/'))  return 'templates-realestate';
          if (id.includes('/templates/healthcare/'))  return 'templates-healthcare';
          if (id.includes('/templates/fitness/'))     return 'templates-fitness';
          if (id.includes('/templates/education/'))   return 'templates-education';
          if (id.includes('/templates/travel/'))      return 'templates-travel';
          if (id.includes('/templates/portfolio/'))   return 'templates-portfolio';
          if (id.includes('/templates/creative/'))    return 'templates-creative';
          // Motion components — keep separate from vendor-motion
          if (id.includes('/components/motion/'))     return 'components-motion-ui';
          // Dashboard components — heavy charts, only on dashboard routes
          if (id.includes('/components/dashboard/'))  return 'components-dashboard';
        },

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
    exclude: ['three', 'gsap'],    // load 3D libs only when actually needed
  },
});
