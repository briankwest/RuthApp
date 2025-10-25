import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0', // Listen on all interfaces for Docker
    port: 3000,
    proxy: {
      '/api': {
        // Use environment variable or default to localhost (for local dev outside Docker)
        // Inside Docker, this is set via docker-compose environment
        target: process.env.VITE_API_PROXY_TARGET || 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
})
