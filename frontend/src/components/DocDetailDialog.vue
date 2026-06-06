<template>
  <el-dialog v-model="visible" title="文档详情" width="700px" top="5vh">
    <pre class="json-view">{{ formattedJson }}</pre>
    <template #footer>
      <el-button @click="visible = false">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed } from 'vue'
import { getDoc } from '@/api/es'

const visible = ref(false)
const content = ref({})

const formattedJson = computed(() => {
  return JSON.stringify(content.value, null, 2)
})

async function open(index, docId) {
  visible.value = true
  const res = await getDoc(index, docId)
  content.value = res.data
}

defineExpose({ open })
</script>

<style scoped>
.json-view {
  background: #f5f7fa;
  padding: 16px;
  border-radius: 4px;
  max-height: 60vh;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-all;
  font-size: 13px;
  line-height: 1.6;
}
</style>
