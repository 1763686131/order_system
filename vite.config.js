import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

const apiProxyTarget = process.env.API_PROXY_TARGET || 'http://localhost:7899'

export default defineConfig({
  plugins: [
    vue({
      template: {
        compilerOptions: {
          isCustomElement: (tag) => tag === 'print-designer'
        }
      }
    })
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        // target: 'http://192.168.31.236:7899',
        target: apiProxyTarget,
        changeOrigin: true
      },
      '/uploads': {
        // 让开发环境也能直接预览后端保存的银行卡图片。
        target: apiProxyTarget,
        changeOrigin: true
      }
    }
  }
})
