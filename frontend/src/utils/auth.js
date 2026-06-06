export function getToken() {
  return localStorage.getItem('token')
}

export function getRole() {
  return localStorage.getItem('role')
}

export function hasPermission(minRole) {
  const roles = { viewer: 0, editor: 1, admin: 2 }
  const current = localStorage.getItem('role') || 'viewer'
  return roles[current] >= roles[minRole]
}
