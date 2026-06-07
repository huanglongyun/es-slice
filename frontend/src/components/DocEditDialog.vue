<template>
  <el-dialog v-model="visible" title="编辑文档" width="700px" top="5vh"
             @close="visible = false">
    <el-descriptions :column="2" border size="small">
      <el-descriptions-item label="_index">{{ docMeta._index }}</el-descriptions-item>
      <el-descriptions-item label="_id">{{ docMeta._id }}</el-descriptions-item>
    </el-descriptions>
    <h4 style="margin:16px 0 8px">_source（可编辑）</h4>
    <el-input v-model="editText" type="textarea" :rows="16"
              placeholder="JSON 格式编辑" />
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { updateDoc } from '@/api/es'

const emit = defineEmits(['saved'])

const visible = ref(false)
const editText = ref('')
const saving = ref(false)
const docMeta = reactive({ _index: '', _id: '' })

function open(index, row) {
  // row 可能是完整文档 或 {_index, _id, _source}
  docMeta._index = row._index || index
  docMeta._id = row._id
  const src = row._source || row
  // 去掉元数据字段
  const editable = { ...src }
  delete editable._id
  delete editable._index
  delete editable._version
  delete editable._score
  editText.value = JSON.stringify(editable, null, 2)
  visible.value = true
}

async function handleSave() {
  try {
    const body = JSON.parse(editText.value)
    saving.value = true
    await updateDoc(docMeta._index, docMeta._id, body)
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
