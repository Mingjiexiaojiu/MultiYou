import api from './index'

export const listAvatars = () => api.get('/api/avatars')
export const getAvatar = (id) => api.get(`/api/avatars/${id}`)

export const createAvatar = (formData) =>
  api.post('/api/avatars', formData, { headers: { 'Content-Type': 'multipart/form-data' } })

export const listPersonas = () => api.get('/api/personas')
export const createPersona = (body) => api.post('/api/personas', body)

export const listSessions = (avatarId) => api.get(`/api/avatars/${avatarId}/sessions`)
export const createSession = (avatarId) => api.post('/api/sessions', { avatar_id: avatarId })
export const updateSession = (sessionId, title) =>
  api.put(`/api/sessions/${sessionId}`, { title })

export const getLogs = (sessionId) => api.get(`/api/sessions/${sessionId}/logs`)
