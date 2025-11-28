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
    resolve: {
      dedupe: ['highlight.js']
    },
    optimizeDeps: {
      include: ['highlight.js']
    },
    build: {
      rollupOptions: {
        output: {
          manualChunks: undefined
        },
        // 将 highlight.js 标记为外部依赖，避免构建时解析
        external: ['highlight.js']
      },
      commonjsOptions: {
        include: [/highlight\.js/, /node_modules/],
        transformMixedEsModules: true
      }
    },
    server: {
      host: '0.0.0.0',  // 监听所有网络接口，允许通过局域网IP访问
      port: 5173,
      proxy: {
        '/api': {
          target: apiBaseUrl,
          changeOrigin: true,
          secure: false,
          // 配置代理以支持大文件上传
          // Vite 使用 http-proxy-middleware
          configure: (proxy, _options) => {
            // 监听代理请求，确保大文件可以正常传输
            proxy.on('proxyReq', (proxyReq, req, _res) => {
              // 确保 Content-Length 头正确传递
              if (req.headers['content-length']) {
                const contentLength = parseInt(req.headers['content-length'], 10)
                // 允许任意大小的文件（实际限制在后端）
                if (contentLength > 0) {
                  proxyReq.setHeader('Content-Length', contentLength)
                }
              }
            })
            // 监听代理错误
            proxy.on('error', (err, req, res) => {
              console.error('代理错误:', err)
            })
          },
          // 增加超时时间，支持大文件上传
          timeout: 600000, // 10分钟
        },
        // 开发环境：代理 /uploads 到后端
        '/uploads': {
          target: apiBaseUrl,
          changeOrigin: true,
          secure: false,
          timeout: 600000, // 10分钟
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

