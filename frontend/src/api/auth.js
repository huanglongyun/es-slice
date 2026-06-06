import request from '@/utils/request'

export function login(username, password) {
  return request.post('/auth/login.do', { username, password })
}

export function logout() {
  return request.post('/auth/logout.do')
}

export function getUserInfo() {
  return request.get('/auth/userinfo.do')
}
