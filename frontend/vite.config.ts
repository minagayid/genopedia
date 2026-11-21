import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/auth': 'http://localhost:8000',
      '/analyses': 'http://localhost:8000',
      '/ai': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
  },
});
