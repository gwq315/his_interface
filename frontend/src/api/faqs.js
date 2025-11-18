import api from './index'

export const getFAQs = (params = {}) => {
  return api.get('/faqs', { params })
}

export const getFAQById = (id) => {
  return api.get(`/faqs/${id}`)
}

export const createFAQ = (formData) => {
  return api.post('/faqs', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
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

