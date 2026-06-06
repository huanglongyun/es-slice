<template>
  <el-menu :default-active="activeMenu" router
           background-color="#304156" text-color="#bfcbd9"
           active-text-color="#409EFF" style="height:100%">
    <el-menu-item index="/index-manage">
      <el-icon><Search /></el-icon>
      <span>索引管理</span>
    </el-menu-item>
    <el-menu-item v-if="userStore.role === 'admin'" index="/audit-log">
      <el-icon><Document /></el-icon>
      <span>审计日志</span>
    </el-menu-item>
    <el-menu-item v-if="userStore.role === 'admin'" index="/user-manage">
      <el-icon><User /></el-icon>
      <span>用户管理</span>
    </el-menu-item>
  </el-menu>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useUserStore } from '@/store/user'

const route = useRoute()
const userStore = useUserStore()
const activeMenu = computed(() => route.path)
</script>
