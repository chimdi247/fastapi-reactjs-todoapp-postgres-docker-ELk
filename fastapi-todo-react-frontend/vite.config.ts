import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // `npm run dev` mirrors what nginx does in docker: same-origin /api and /otlp.
    proxy: {
      '/api': {
        target: process.env.VITE_DEV_API_TARGET ?? 'http://localhost:8085',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      '/otlp': {
        target: process.env.VITE_DEV_OTLP_TARGET ?? 'http://localhost:4318',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/otlp/, ''),
      },
    },
  },
})
