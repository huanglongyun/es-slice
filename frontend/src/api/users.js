import request from '@/utils/request'

export function getUsers() {
  return request.get('/users/list.do')
}

export function createUser(data) {
  return request.post('/users/create.do', data)
}

export function updateUser(id, data) {
  return request.put(`/users/${id}.do`, data)
}

export function deleteUser(id) {
  return request.delete(`/users/${id}.do`)
}
