import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ mode }) => {
  // 加载环境变量
  const env = loadEnv(mode, process.cwd(), '')
  
  // 从环境变量读取后端地址，默认为 localhost:8000
  // 如果后端在远程服务器，创建 .env 文件并设置：
  // VITE_API_BASE_URL=http://192.168.1.198:8000
  const apiBaseUrl = env.VITE_API_BASE_URL || 'http://localhost:8000'
  
  return {
    plugins: [vue()],
    server: {
      host: '0.0.0.0',  // 监听所有网络接口，允许通过局域网IP访问
      port: 5173,
      proxy: {
        '/api': {
          target: apiBaseUrl,
          changeOrigin: true,
          secure: false
        },
        // 开发环境：代理 /uploads 到后端
        '/uploads': {
          target: apiBaseUrl,
          changeOrigin: true,
          secure: false
        }
      }
    }
  }
})

// 注意：
// 1. 此配置仅用于开发环境（npm run dev）
// 2. 生产环境使用 Docker + Nginx，代理配置在 nginx.conf 中
// 3. 生产环境构建时，Vite 只执行构建，不启动开发服务器
// 4. 因此，此文件在生产环境部署时无需修改

