import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'

/** Прокси на uvicorn: при пустом VITE_API_BASE_URL fetch('/api/...') идёт на этот же хост (Vite). */
const backendProxy = {
  '/api': {
    target: 'http://127.0.0.1:8000',
    changeOrigin: true,
  },
  '/uploads': {
    target: 'http://127.0.0.1:8000',
    changeOrigin: true,
  },
}

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': '/src',
    },
  },
  // dev: без VITE_API_BASE_URL — относительные /api на 5173 → сюда.
  server: { proxy: backendProxy },
  // preview: иначе /api попадёт в SPA и вернёт index.html вместо JSON.
  preview: { proxy: backendProxy },
  test: {
    environment: 'node',
    include: ['src/**/*.test.ts'],
  },
})
