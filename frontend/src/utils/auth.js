/**
 * 认证工具函数
 * 用于管理Token和用户信息
 */

const TOKEN_KEY = 'access_token'
const USER_KEY = 'user_info'

/**
 * 保存Token
 */
export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token)
}

/**
 * 获取Token
 */
export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

/**
 * 删除Token
 */
export function removeToken() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

/**
 * 保存用户信息
 */
export function setUser(user) {
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

/**
 * 获取用户信息
 */
export function getUser() {
  const userStr = localStorage.getItem(USER_KEY)
  if (userStr) {
    try {
      return JSON.parse(userStr)
    } catch (e) {
      return null
    }
  }
  return null
}

/**
 * 检查是否已登录
 */
export function isAuthenticated() {
  return !!getToken()
}

/**
 * 检查是否是管理员
 */
export function isAdmin() {
  const user = getUser()
  return user && user.role === 'admin'
}

/**
 * 检查是否可以操作项目
 * @param {Object} project - 项目对象
 * @returns {boolean}
 */
export function canOperateProject(project) {
  const user = getUser()
  if (!user) return false
  
  // 管理员可以操作所有项目
  if (user.role === 'admin') return true
  
  // 普通用户只能操作自己创建的项目
  return project.creator_id === user.id
}

