import api from './index'

export const authApi = {
  // 登录
  login(username, password) {
    return api.post('/auth/login', { username, password })
  },

  // 注册
  register(data) {
    return api.post('/auth/register', data)
  },

  // 获取当前用户信息
  getCurrentUser() {
    return api.get('/auth/me')
  },

  // 退出登录
  logout() {
    return api.post('/auth/logout')
  }
}

