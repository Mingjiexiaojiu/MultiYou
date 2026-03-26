import api from './index'

export const sendMessage = (sessionId, message) =>
  api.post('/api/chat', { session_id: sessionId, message })
