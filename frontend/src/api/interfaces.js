import api from './index'

export const interfaceApi = {
  // 获取接口列表
  getList(params = {}) {
    return api.get('/interfaces/', { params })
  },

  // 搜索接口
  search(searchParams) {
    return api.post('/interfaces/search', searchParams)
  },

  // 获取接口详情
  getById(id) {
    return api.get(`/interfaces/${id}`).catch(error => {
      console.error('getById error:', error)
      throw error
    })
  },

  // 根据编码获取接口
  getByCode(code) {
    return api.get(`/interfaces/code/${code}`)
  },

  // 创建接口
  create(data) {
    return api.post('/interfaces/', data)
  },

  // 更新接口
  update(id, data) {
    return api.put(`/interfaces/${id}`, data)
  },

  // 删除接口
  delete(id) {
    return api.delete(`/interfaces/${id}`)
  }
}

