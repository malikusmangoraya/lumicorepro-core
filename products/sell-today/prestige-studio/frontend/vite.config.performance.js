/**
 * Vite Performance Config — saas
 * Merge this into your vite.config.js build section
 * LCP target: <2500ms | Bundle JS: <300KB
 */
export const performanceBuildConfig = {
  build: {
    target: 'es2020',
    minify: 'terser',
    terserOptions: {
      compress: { drop_console: true, drop_debugger: true, pure_funcs: ['console.log'] },
    },
    rollupOptions: {
      output: {
        // Route-based code splitting
        manualChunks(id) {
          if (id.includes('node_modules')) {
            // Vendor chunk: react ecosystem
            if (id.includes('react') || id.includes('react-dom') || id.includes('react-router')) {
              return 'vendor-react';
            }
            // Charts separate chunk
            if (id.includes('recharts') || id.includes('d3')) {
              return 'vendor-charts';
            }
            // Animation separate chunk
            if (id.includes('framer-motion') || id.includes('gsap')) {
              return 'vendor-animation';
            }
            // Everything else in vendor
            return 'vendor';
          }
          // Page-level splitting
          if (id.includes('/pages/')) {
            const page = id.split('/pages/')[1].split('/')[0];
            return `page-${page}`;
          }
        },
        chunkFileNames: 'assets/js/[name]-[hash].js',
        entryFileNames: 'assets/js/[name]-[hash].js',
        assetFileNames: 'assets/[ext]/[name]-[hash].[ext]',
      },
    },
    // Warn if chunks exceed budget
    chunkSizeWarningLimit: 300,
    // Report compressed sizes
    reportCompressedSize: true,
    // Enable source maps for error monitoring
    sourcemap: process.env.NODE_ENV !== 'production',
  },
  // Image optimization
  assetsInclude: ['**/*.avif', '**/*.webp'],
};
