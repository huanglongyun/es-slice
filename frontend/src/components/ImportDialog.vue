<template>
  <el-dialog title="导入 Excel" :model-value="props.visible"
             @update:model-value="$emit('update:visible', $event)"
             width="500px" top="10vh">
    <el-form>
      <el-form-item label="目标索引（可多选）">
        <el-select v-model="selectedIndexes" placeholder="选择索引" multiple
                   filterable style="width:100%">
          <el-option v-for="idx in props.indexes" :key="idx" :label="idx" :value="idx" />
        </el-select>
      </el-form-item>
      <el-form-item label="选择 Excel 文件">
        <el-upload :auto-upload="false" :limit="1" accept=".xlsx,.xls"
                   :on-change="handleFileChange" :file-list="fileList"
                   drag>
          <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
          <div>拖拽或点击上传 Excel 文件</div>
        </el-upload>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="$emit('update:visible', false)">取消</el-button>
      <el-button type="primary" :loading="importing"
                 :disabled="!file || selectedIndexes.length === 0"
                 @click="handleImport">开始导入</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { importExcel } from '@/api/es'

const props = defineProps({
  visible: Boolean,
  indexes: { type: Array, default: () => [] }
})

const emit = defineEmits(['update:visible', 'imported'])

const selectedIndexes = ref([])
const file = ref(null)
const fileList = ref([])
const importing = ref(false)

function handleFileChange(uploadFile) {
  file.value = uploadFile.raw
  fileList.value = [uploadFile]
}

async function handleImport() {
  if (!file.value) {
    ElMessage.warning('请选择文件')
    return
  }
  const formData = new FormData()
  formData.append('file', file.value)
  formData.append('indexes', selectedIndexes.value.join(','))
  importing.value = true
  try {
    const res = await importExcel(formData)
    ElMessage.success(`导入完成: 成功 ${res.data.success} 条`)
    emit('update:visible', false)
    emit('imported')
  } finally {
    importing.value = false
  }
}
</script>
