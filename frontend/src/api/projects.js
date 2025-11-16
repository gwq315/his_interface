import api from './index'

export const projectApi = {
  // 获取项目列表（支持分页与关键词）
  getList(params = {}) {
    return api.get('/projects', { params })
  },

  // 创建项目
  create(data) {
    return api.post('/projects', data)
  },

  // 获取项目详情
  getById(id) {
    return api.get(`/projects/${id}`)
  },

  // 更新项目
  update(id, data) {
    return api.put(`/projects/${id}`, data)
  },

  // 删除项目
  delete(id) {
    return api.delete(`/projects/${id}`)
  },

  // 获取项目下的接口
  getInterfaces(id, params = {}) {
    return api.get(`/projects/${id}/interfaces`, { params })
  },

  // 获取项目下的字典
  getDictionaries(id, params = {}) {
    return api.get(`/projects/${id}/dictionaries`, { params })
  },

  // 上传项目附件
  uploadAttachment(projectId, file) {
    const formData = new FormData()
    formData.append('file', file)
    // FormData 的 Content-Type 会在请求拦截器中自动处理
    return api.post(`/projects/${projectId}/attachments`, formData)
  },

  // 删除项目附件
  deleteAttachment(projectId, storedFilename) {
    return api.delete(`/projects/${projectId}/attachments/${storedFilename}`)
  }
}


