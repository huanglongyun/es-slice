<template>
  <el-dialog title="导入 Excel" :model-value="props.visible"
             @update:model-value="$emit('update:visible', $event)"
             width="700px" top="5vh" @close="resetAll">
    <!-- 步骤指示器 -->
    <el-steps :active="step" align-center style="margin-bottom:20px">
      <el-step title="选择索引" />
      <el-step title="上传文件" />
      <el-step title="预览确认" />
    </el-steps>

    <!-- 步骤 0: 选择索引 + 下载模板 -->
    <div v-if="step === 0">
      <el-form>
        <el-form-item label="目标索引（可多选）">
          <el-select v-model="selectedIndexes" placeholder="选择索引" multiple
                     filterable style="width:100%">
            <el-option v-for="idx in props.indexes" :key="idx" :label="idx" :value="idx" />
          </el-select>
        </el-form-item>
      </el-form>
      <div style="color:#909399;font-size:13px;margin-bottom:12px">
        提示：导入的 Excel 第一行为字段名，须包含 <b>_id</b> 列用于匹配文档。
        可先下载模板，填好数据后上传。
      </div>
    </div>

    <!-- 步骤 1: 上传文件 -->
    <div v-if="step === 1">
      <el-upload :auto-upload="false" :limit="1" accept=".xlsx,.xls"
                 :on-change="handleFileChange" :file-list="fileList"
                 drag>
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div>拖拽或点击上传 Excel 文件</div>
      </el-upload>
    </div>

    <!-- 步骤 2: 预览 -->
    <div v-if="step === 2" v-loading="previewing">
      <div v-if="previewData.length" style="margin-bottom:8px;color:#606266">
        将更新 <b>{{ selectedIndexes.length }}</b> 个索引，共 <b>{{ previewData.length }}</b> 行
      </div>
      <el-table :data="previewData.slice(0, 10)" border stripe max-height="300" size="small">
        <el-table-column v-for="col in previewCols" :key="col"
                         :prop="col" :label="col" :show-overflow-tooltip="true"
                         min-width="120" />
      </el-table>
      <div v-if="previewData.length > 10" style="text-align:center;color:#909399;margin-top:4px">
        ... 仅展示前 10 行，共 {{ previewData.length }} 行
      </div>
    </div>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button v-if="step > 0" @click="step--">上一步</el-button>
      <el-button v-if="step === 0" type="primary" :disabled="selectedIndexes.length === 0"
                 @click="step = 1">下一步</el-button>
      <el-button v-if="step === 1" type="primary" :disabled="!file"
                 @click="handlePreview">预览</el-button>
      <el-button v-if="step === 2" type="primary" :loading="importing"
                 :disabled="previewData.length === 0"
                 @click="handleImport">确认导入</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { importExcel } from '@/api/es'

const props = defineProps({
  visible: Boolean,
  indexes: { type: Array, default: () => [] }
})

const emit = defineEmits(['update:visible', 'imported'])

const step = ref(0)
const selectedIndexes = ref([])
const file = ref(null)
const fileList = ref([])
const importing = ref(false)
const previewing = ref(false)
const previewData = ref([])
const previewCols = ref([])

function handleFileChange(uploadFile) {
  file.value = uploadFile.raw
  fileList.value = [uploadFile]
}

async function handlePreview() {
  if (!file.value) {
    ElMessage.warning('请选择文件')
    return
  }
  previewing.value = true
  try {
    const formData = new FormData()
    formData.append('file', file.value)
    formData.append('preview', 'true')
    const res = await importExcel(formData)
    previewData.value = res.data.rows || []
    if (previewData.value.length) {
      previewCols.value = Object.keys(previewData.value[0])
    }
    if (!previewData.value.length || !previewData.value[0].hasOwnProperty('_id')) {
      ElMessage.warning('Excel 中未找到 _id 列，请检查表格格式')
    }
    step.value = 2
  } catch (e) {
    ElMessage.error(e.message || '预览失败')
  } finally {
    previewing.value = false
  }
}

async function handleImport() {
  if (!file.value) {
    ElMessage.warning('文件已丢失，请重新上传')
    step.value = 1
    return
  }
  const formData = new FormData()
  formData.append('file', file.value, file.value.name)
  formData.append('indexes', selectedIndexes.value.join(','))
  importing.value = true
  try {
    const res = await importExcel(formData)
    ElMessage.success(`导入完成: 成功 ${res.data.success} 条`)
    emit('update:visible', false)
    emit('imported')
  } catch (e) {
    ElMessage.error(e.message || '导入失败')
  } finally {
    importing.value = false
  }
}

function handleClose() {
  emit('update:visible', false)
}

function resetAll() {
  step.value = 0
  selectedIndexes.value = []
  file.value = null
  fileList.value = []
  previewData.value = []
  previewCols.value = []
}

watch(() => props.visible, (v) => {
  if (!v) resetAll()
})
</script>
