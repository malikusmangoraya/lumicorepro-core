import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  base: process.env.VITE_BASE_PATH || '/',
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(import.meta.dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://localhost:5000',
    },
  },
  build: {
    // Small icons and fonts become part of their importing chunk instead of
    // extra round trips.
    assetsInlineLimit: 8192,
    cssCodeSplit: true,
    reportCompressedSize: false,
    chunkSizeWarningLimit: 700,
    rollupOptions: {
      output: {
        // Vendor code changes far less often than product code, so keeping it
        // in its own chunk means a normal deploy does not force buyers to
        // re-download React, the router and the query client.
        manualChunks(id) {
          if (!id.includes('node_modules')) return undefined;
          if (/[\\/]node_modules[\\/](react|react-dom|scheduler)[\\/]/.test(id)) {
            return 'vendor-react';
          }
          if (/[\\/]node_modules[\\/](react-router|react-router-dom)[\\/]/.test(id)) {
            return 'vendor-router';
          }
          if (/[\\/]node_modules[\\/](i18next|react-i18next|intl-messageformat)[\\/]/.test(id)) {
            return 'vendor-i18n';
          }
          if (/[\\/]node_modules[\\/](@tanstack|zustand|axios)[\\/]/.test(id)) {
            return 'vendor-app';
          }
          if (/[\\/]node_modules[\\/](framer-motion|motion-dom|motion-utils)[\\/]/.test(id)) {
            return 'vendor-motion';
          }
          if (/[\\/]node_modules[\\/]lucide-react[\\/]/.test(id)) {
            return 'vendor-icons';
          }
          return 'vendor';
        },
      },
    },
  },
});
