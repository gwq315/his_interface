import api from './index'

export const getFAQs = (params = {}) => {
  return api.get('/faqs', { params })
}

export const getFAQById = (id) => {
  return api.get(`/faqs/${id}`)
}

export const createFAQ = (data, isRichText = false) => {
  if (isRichText) {
    // 富文本类型：使用 JSON 方式提交
    return api.post('/faqs', data)
  } else {
    // 附件类型：使用 FormData 方式提交
    // 注意：不要手动设置 Content-Type，让浏览器自动设置（包括 boundary）
    return api.post('/faqs', data)
  }
}

export const updateFAQ = (id, data) => {
  return api.put(`/faqs/${id}`, data)
}

export const deleteFAQ = (id) => {
  return api.delete(`/faqs/${id}`)
}

export const getFAQPreviewUrl = (filePath) => {
  // 使用相对路径，通过 nginx 代理访问（生产环境）或 vite 代理访问（开发环境）
  return filePath.startsWith('/') ? filePath : `/${filePath}`
}

/**
 * 为常见问题添加附件
 * @param {number} id - 常见问题ID
 * @param {File} file - 文件对象
 */
export const addFAQAttachment = (id, file) => {
  const formData = new FormData()
  formData.append('file', file)
  return api.post(`/faqs/${id}/attachments`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 删除常见问题的指定附件
 * @param {number} id - 常见问题ID
 * @param {string} storedFilename - 存储的文件名（带时间戳）
 */
export const deleteFAQAttachment = (id, storedFilename) => {
  return api.delete(`/faqs/${id}/attachments/${storedFilename}`)
}

