import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import fs from 'fs'
import path from 'path'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    {
      name: 'serve-profile',
      configureServer(server) {
        server.middlewares.use('/profile.json', (_req, res) => {
          const filePath = path.resolve(__dirname, '..', 'profile.json')
          if (fs.existsSync(filePath)) {
            res.setHeader('Content-Type', 'application/json')
            fs.createReadStream(filePath).pipe(res)
          } else {
            res.statusCode = 404
            res.end('profile.json not found')
          }
        })
      },
    },
  ],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
