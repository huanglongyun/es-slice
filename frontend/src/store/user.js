import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const username = ref(localStorage.getItem('username') || '')
  const realName = ref(localStorage.getItem('realName') || '')
  const role = ref(localStorage.getItem('role') || '')

  function setLogin(data) {
    token.value = data.token
    username.value = data.userInfo.username
    realName.value = data.userInfo.realName
    role.value = data.userInfo.role
    localStorage.setItem('token', data.token)
    localStorage.setItem('username', data.userInfo.username)
    localStorage.setItem('realName', data.userInfo.realName)
    localStorage.setItem('role', data.userInfo.role)
  }

  function logout() {
    token.value = ''
    username.value = ''
    realName.value = ''
    role.value = ''
    localStorage.clear()
  }

  return { token, username, realName, role, setLogin, logout }
})
