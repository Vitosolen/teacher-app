import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'node:path'

// 后端端口默认 8000；切换时在 .env 或 .env.local 里设 VITE_BACKEND_PORT=8002 即可
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const backendPort = env.VITE_BACKEND_PORT || '8000'
  const backendHost = env.VITE_BACKEND_HOST || '127.0.0.1'

  return {
    plugins: [vue()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src'),
      },
    },
    server: {
      host: '127.0.0.1',
      port: 5173,
      proxy: {
        '/api': {
          target: `http://${backendHost}:${backendPort}`,
          changeOrigin: true,
        },
        '/static': {
          target: `http://${backendHost}:${backendPort}`,
          changeOrigin: true,
        },
      },
    },
  }
})
