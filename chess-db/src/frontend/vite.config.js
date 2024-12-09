// vite.config.js
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  // Ensure proper module resolution and build settings
  build: {
    target: 'es2015',
    sourcemap: true,
  },
  // Development server configuration
  server: {
    port: 5173,
    host: true,
    cors: true,
  },
  // Optimize dependency pre-bundling
  optimizeDeps: {
    include: ['react', 'react-dom', 'recharts'],
  },
});