import api from './index'

export const register = (username, password) =>
  api.post('/api/auth/register', { username, password })

export const login = (username, password) =>
  api.post('/api/auth/login', { username, password })
