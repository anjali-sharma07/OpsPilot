import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    // DEV-ONLY proxy — Vite forwards these paths to the local FastAPI server
    // so VITE_API_URL can be left unset (empty string) during local development.
    // This proxy block is completely ignored in the production Vercel build.
    proxy: {
      '/upload': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
      '/chat': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
    },
  },
});
