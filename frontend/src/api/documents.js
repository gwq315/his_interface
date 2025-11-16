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
  // 使用当前页面的origin构建URL，确保使用正确的IP地址和端口
  // 这样无论前端运行在哪个地址（localhost:5173 或 192.168.1.198:5173），都能正确访问
  if (!filePath) {
    console.error('getDocumentPreviewUrl: filePath 为空')
    return '#'
  }
  
  // 标准化路径
  const normalizedPath = filePath.replace(/\\/g, '/')
  // 确保路径以/开头
  const relativePath = normalizedPath.startsWith('/') ? normalizedPath : `/${normalizedPath}`
  
  // 使用当前页面的origin构建绝对URL
  const fullUrl = `${window.location.origin}${relativePath}`
  
  // 开发环境：打印调试信息
  if (import.meta.env.DEV) {
    console.log('文档预览URL生成:', {
      filePath,
      normalizedPath,
      relativePath,
      origin: window.location.origin,
      fullUrl
    })
  }
  
  return fullUrl
}

