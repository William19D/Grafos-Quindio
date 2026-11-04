import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// En desarrollo (npm run dev) las peticiones a /api y /figuras van al backend FastAPI.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
      '/figuras': 'http://localhost:8000',
    },
  },
})
