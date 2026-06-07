<template>
  <el-dialog v-model="visible" title="文档详情" width="700px" top="5vh">
    <!-- 元数据（只读） -->
    <el-descriptions :column="3" border size="small">
      <el-descriptions-item label="_index">{{ content._index }}</el-descriptions-item>
      <el-descriptions-item label="_id">{{ content._id }}</el-descriptions-item>
      <el-descriptions-item label="_version">{{ content._version }}</el-descriptions-item>
    </el-descriptions>

    <!-- _source 内容 -->
    <h4 style="margin:16px 0 8px">_source</h4>
    <pre class="json-view">{{ formattedSource }}</pre>

    <template #footer>
      <el-button @click="visible = false">关闭</el-button>
      <el-button v-if="role !== 'viewer'" type="primary" @click="openEdit">编辑</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed } from 'vue'
import { getDoc } from '@/api/es'

const visible = ref(false)
const content = ref({})
const emit = defineEmits(['edit'])
const role = computed(() => localStorage.getItem('role') || 'viewer')

const formattedSource = computed(() => {
  const src = content.value._source || content.value
  return JSON.stringify(src, null, 2)
})

function getSource() {
  return content.value._source || content.value
}

async function open(index, docId) {
  visible.value = true
  const res = await getDoc(index, docId)
  content.value = res.data
}

function openEdit() {
  visible.value = false
  emit('edit', {
    _index: content.value._index,
    _id: content.value._id,
    _source: getSource()
  })
}

defineExpose({ open })
</script>

<style scoped>
.json-view {
  background: #f5f7fa;
  padding: 16px;
  border-radius: 4px;
  max-height: 45vh;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-all;
  font-size: 13px;
  line-height: 1.6;
}
</style>
