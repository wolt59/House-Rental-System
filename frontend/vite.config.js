import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig(({ mode }) => {
  // 加载项目根目录的环境变量
  const rootEnv = loadEnv(mode, path.resolve(__dirname, '..'), '')
  
  return {
    plugins: [vue()],
    server: {
      host: rootEnv.FRONTEND_HOST || 'localhost',
      port: parseInt(rootEnv.FRONTEND_PORT) || 3000,
      proxy: {
        '/api': {
          target: rootEnv.VITE_API_BASE_URL || 'http://127.0.0.1:8000',
          changeOrigin: true,
        },
        '/uploads': {
          target: rootEnv.VITE_UPLOADS_BASE_URL || 'http://127.0.0.1:8000',
          changeOrigin: true,
        },
      },
    },
  }
})
