import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
        secure: false,
        timeout: 30000,
        proxyTimeout: 30000,
      },
      '/ws': {
        target: 'ws://127.0.0.1:8001',
        ws: true,
        changeOrigin: true,
      }
    }
  }
})

