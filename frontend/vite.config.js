import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Use local backend URL for development
// Matches the inner docker-compose.yml port mapping if running locally
const backendTarget = 'http://localhost:9000'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000, // Changed to match docker-compose port
    allowedHosts: true,
    proxy: {
      '/upload': {
        target: backendTarget,
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path
      },
      '/result': {
        target: backendTarget,
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path
      },
      '/records': {
        target: backendTarget,
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path
      }
    }
  }
})
