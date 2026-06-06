<template>
  <el-dialog v-model="visible" title="编辑文档" width="700px" top="5vh"
             @close="visible = false">
    <el-input v-model="editText" type="textarea" :rows="16"
              placeholder="JSON 格式编辑" />
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { updateDoc } from '@/api/es'

const emit = defineEmits(['saved'])

const visible = ref(false)
const editText = ref('')
const saving = ref(false)
let currentIndex = ''
let currentDocId = ''

function open(index, row) {
  currentIndex = index
  currentDocId = row._id
  const editable = { ...row }
  delete editable._id
  editText.value = JSON.stringify(editable, null, 2)
  visible.value = true
}

async function handleSave() {
  try {
    const body = JSON.parse(editText.value)
    saving.value = true
    await updateDoc(currentIndex, currentDocId, body)
    ElMessage.success('更新成功')
    visible.value = false
    emit('saved')
  } catch (e) {
    if (e instanceof SyntaxError) {
      ElMessage.error('JSON 格式不正确')
    }
  } finally {
    saving.value = false
  }
}

defineExpose({ open })
</script>
