import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// The API runs locally on :8000 (backend/); the dev server proxies /api to it.
export default defineConfig({
  plugins: [react()],
  server: { proxy: { '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true } } },
})
