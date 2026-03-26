import api from './index'

export const listModels = () => api.get('/api/models')
export const createModel = (body) => api.post('/api/models', body)
export const updateModel = (id, body) => api.put(`/api/models/${id}`, body)
export const deleteModel = (id) => api.delete(`/api/models/${id}`)
export const testModel = (id) => api.post(`/api/models/${id}/test`)
