import api from './index'

export const dictionaryApi = {
  // 获取字典列表
  getList(params = {}) {
    return api.get('/dictionaries/', { params })
  },

  // 获取字典详情
  getById(id) {
    return api.get(`/dictionaries/${id}`)
  },

  // 根据编码获取字典
  getByCode(code) {
    return api.get(`/dictionaries/code/${code}`)
  },

  // 创建字典
  create(data) {
    return api.post('/dictionaries/', data)
  },

  // 更新字典
  update(id, data) {
    return api.put(`/dictionaries/${id}`, data)
  },

  // 删除字典
  delete(id) {
    return api.delete(`/dictionaries/${id}`)
  },

  // 批量更新字典值
  batchUpdateValues(dictionaryId, values) {
    return api.put(`/dictionaries/${dictionaryId}/values`, values)
  }
}

