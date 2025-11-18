import axios from 'axios'
import { getToken, removeToken } from '../utils/auth'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    // 添加Token到请求头
    // 每次都重新读取，确保获取最新的Token
    const token = getToken()
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    } else {
      // 如果没有Token，删除Authorization头
      delete config.headers.Authorization
    }
    
    // 如果是 FormData，删除默认的 Content-Type，让浏览器自动设置
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type']
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    console.error('API Error:', {
      url: error.config?.url,
      method: error.config?.method,
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data,
      message: error.message
    })
    
    // 401未授权，清除Token并跳转到登录页
    // 但登录接口(/auth/login)和注册接口(/auth/register)的401错误不应该自动跳转
    const isAuthEndpoint = error.config?.url?.includes('/auth/login') || error.config?.url?.includes('/auth/register')
    if (error.response?.status === 401 && !isAuthEndpoint) {
      // 检查是否是登录后立即的请求失败（可能是Token还没准备好）
      // 如果是登录后1秒内的401错误，可能是时序问题，不立即跳转
      const isRecentLogin = Date.now() - (window.__lastLoginTime || 0) < 2000
      
      if (!isRecentLogin) {
        removeToken()
        // 如果不在登录页，跳转到登录页
        if (window.location.pathname !== '/login') {
          // 延迟跳转，避免在请求处理过程中跳转
          setTimeout(() => {
            if (window.location.pathname !== '/login') {
              window.location.href = '/login'
            }
          }, 100)
        }
      }
    }
    
    // 保留完整的错误对象，以便上层可以访问 error.response
    const apiError = new Error()
    apiError.message = error.response?.data?.detail || error.message || '请求失败'
    apiError.response = error.response
    apiError.config = error.config
    return Promise.reject(apiError)
  }
)

export default api

