import api from './index'

/**
 * 文档/截图API
 */

/**
 * 获取文档列表
 * @param {Object} params - 查询参数
 * @param {string} params.keyword - 关键词（搜索标题、简要描述）
 * @param {string} params.document_type - 文档类型（pdf/image）
 * @param {string} params.region - 地区
 * @param {string} params.person - 人员
 * @param {number} params.page - 页码
 * @param {number} params.page_size - 每页数量
 */
export function getDocuments(params = {}) {
  return api.get('/documents', { params })
}

/**
 * 获取文档详情
 * @param {number} id - 文档ID
 */
export function getDocument(id) {
  return api.get(`/documents/${id}`)
}

/**
 * 创建文档/截图
 * @param {FormData} formData - 表单数据（包含文件）
 */
export function createDocument(formData) {
  return api.post('/documents', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 更新文档信息
 * @param {number} id - 文档ID
 * @param {Object} data - 更新数据
 */
export function updateDocument(id, data) {
  return api.put(`/documents/${id}`, data)
}

/**
 * 删除文档
 * @param {number} id - 文档ID
 */
export function deleteDocument(id) {
  return api.delete(`/documents/${id}`)
}

/**
 * 获取文档预览URL
 * @param {string} filePath - 文件路径（相对路径）
 */
export function getDocumentPreviewUrl(filePath) {
  // 使用相对路径，通过 nginx 代理访问（生产环境）或 vite 代理访问（开发环境）
  // 这样不需要知道具体的端口号，nginx/vite 会自动代理到后端
  if (!filePath) {
    console.error('getDocumentPreviewUrl: filePath 为空')
    return '#'
  }
  
  // 标准化路径
  const normalizedPath = filePath.replace(/\\/g, '/')
  // 确保路径以/开头
  const relativePath = normalizedPath.startsWith('/') ? normalizedPath : `/${normalizedPath}`
  
  // 直接返回相对路径，浏览器会自动使用当前页面的协议、主机和端口
  // 在生产环境中，nginx 会代理 /uploads 到后端
  // 在开发环境中，vite 会代理 /uploads 到后端
  return relativePath
}

