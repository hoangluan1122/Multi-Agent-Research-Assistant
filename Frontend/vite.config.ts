/**
 * Cấu hình Vite cho ứng dụng Frontend PaperFlow (React + TypeScript + Tailwind CSS).
 * Thiết lập plugin React và proxy reverse tới backend FastAPI tại port 8000.
 */
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Chuyển tiếp các request /api sang máy chủ Backend FastAPI
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})

