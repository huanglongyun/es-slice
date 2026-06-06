<template>
  <div class="app-layout">
    <el-container>
      <el-aside width="220px">
        <Sidebar />
      </el-aside>
      <el-container>
        <el-header class="app-header">
          <span class="title">ES 索引管理后台</span>
          <div class="header-right">
            <el-tag :type="roleTagType" size="small">{{ roleText }}</el-tag>
            <span class="username">{{ userStore.realName || userStore.username }}</span>
            <el-button type="danger" text @click="handleLogout">退出</el-button>
          </div>
        </el-header>
        <el-main>
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import { ElMessageBox } from 'element-plus'
import Sidebar from './Sidebar.vue'

const router = useRouter()
const userStore = useUserStore()

const roleTagType = computed(() => {
  const map = { admin: 'danger', editor: 'warning', viewer: 'info' }
  return map[userStore.role] || 'info'
})

const roleText = computed(() => {
  const map = { admin: '管理员', editor: '编辑者', viewer: '只读' }
  return map[userStore.role] || '未知'
})

async function handleLogout() {
  await ElMessageBox.confirm('确定退出登录?', '提示', { type: 'warning' })
  userStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.app-layout { height: 100vh; }
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  padding: 0 20px;
}
.app-header .title { font-size: 16px; font-weight: bold; }
.header-right { display: flex; align-items: center; gap: 12px; }
.username { color: #606266; }
</style>
