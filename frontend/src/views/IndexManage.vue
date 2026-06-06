<template>
  <div class="index-manage">
    <div class="section">
      <el-select v-model="selectedIndex" placeholder="选择索引（搜索）" style="width:300px"
                 filterable @change="onIndexChange">
        <el-option v-for="idx in indexes" :key="idx" :label="idx" :value="idx" />
      </el-select>
    </div>

    <div class="section" v-if="selectedIndex">
      <h4>字段搜索</h4>
      <FieldSearch ref="fieldSearchRef" :fields="indexFields"
                   v-model="searchConditions"
                   @search="handleSearch" @reset="handleReset" />
    </div>

    <div class="section" v-if="selectedIndex && dslVisible">
      <h4>
        自定义 DSL
        <el-button text size="small" @click="dslVisible = false">收起</el-button>
      </h4>
      <el-input v-model="dslText" type="textarea" :rows="6"
                placeholder='{"query":{"bool":{"must":[...]}}}' />
    </div>
    <div class="section" v-else-if="selectedIndex">
      <el-button text size="small" @click="dslVisible = true; syncDsl()">
        展开自定义 DSL
      </el-button>
    </div>

    <div class="section" v-if="selectedIndex">
      <el-button @click="handleExport" icon="Download"
                 :disabled="role === 'viewer'">导出 JSONL</el-button>
      <el-button @click="importDialogVisible = true" icon="Upload"
                 :disabled="role === 'viewer'">导入 Excel</el-button>
    </div>

    <div class="section" v-if="selectedIndex">
      <el-table :data="tableData" border stripe v-loading="tableLoading" style="width:100%">
        <el-table-column type="index" label="序号" width="60" />
        <el-table-column v-for="col in tableColumns" :key="col"
                         :prop="col" :label="col" :show-overflow-tooltip="true"
                         min-width="150" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="showDetail(row)">详情</el-button>
            <el-button text type="warning" size="small" @click="showEdit(row)"
                       :disabled="role === 'viewer'">编辑</el-button>
            <el-popconfirm title="确定删除?" @confirm="handleDelete(row)">
              <template #reference>
                <el-button text type="danger" size="small"
                           :disabled="role === 'viewer'">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination">
        <el-pagination v-model:current-page="page" :page-size="pageSize"
                       :total="total" :page-sizes="[10,20,50,100]"
                       layout="total,sizes,prev,pager,next"
                       @current-change="handleSearch"
                       @size-change="handleSearch" />
      </div>
    </div>

    <DocDetailDialog ref="detailDialogRef" />
    <DocEditDialog ref="editDialogRef" @saved="handleSearch" />
    <ImportDialog v-model:visible="importDialogVisible" :indexes="indexes"
                  @imported="handleSearch" />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/store/user'
import { getIndexes, getIndexFields, searchDocs, deleteDoc, exportDocs } from '@/api/es'
import FieldSearch from '@/components/FieldSearch.vue'
import DocDetailDialog from '@/components/DocDetailDialog.vue'
import DocEditDialog from '@/components/DocEditDialog.vue'
import ImportDialog from '@/components/ImportDialog.vue'

const userStore = useUserStore()
const role = computed(() => userStore.role)

const indexes = ref([])
const selectedIndex = ref('')
const indexFields = ref([])

const fieldSearchRef = ref(null)
const searchConditions = ref([])
const dslVisible = ref(false)
const dslText = ref('')

const tableData = ref([])
const tableColumns = ref([])
const tableLoading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

const detailDialogRef = ref(null)
const editDialogRef = ref(null)
const importDialogVisible = ref(false)

getIndexes().then(res => { indexes.value = res.data }).catch(() => {})

async function onIndexChange(val) {
  if (!val) return
  const res = await getIndexFields(val)
  indexFields.value = res.data
  tableColumns.value = res.data.map(f => f.name)
  handleReset()
}

function handleReset() {
  searchConditions.value = [{ field: '', matchType: 'match', value: '' }]
  dslText.value = ''
  page.value = 1
}

async function handleSearch() {
  tableLoading.value = true
  try {
    let dsl = null
    if (dslText.value) {
      try { dsl = JSON.parse(dslText.value) } catch (e) { /* ignore */ }
    }
    const res = await searchDocs(selectedIndex.value, {
      conditions: searchConditions.value.filter(c => c.field && c.value),
      dsl,
      page: page.value,
      pageSize: pageSize.value
    })
    tableData.value = res.data.list
    total.value = res.data.total
  } finally {
    tableLoading.value = false
  }
}

function syncDsl() {
  const conds = searchConditions.value.filter(c => c.field && c.value)
  if (conds.length) {
    const must = conds.map(c => ({ [c.matchType]: { [c.field]: c.value } }))
    dslText.value = JSON.stringify({ query: { bool: { must } } }, null, 2)
  } else {
    dslText.value = JSON.stringify({ query: { match_all: {} } }, null, 2)
  }
}

function showDetail(row) {
  detailDialogRef.value.open(selectedIndex.value, row._id)
}

function showEdit(row) {
  editDialogRef.value.open(selectedIndex.value, row)
}

async function handleDelete(row) {
  await deleteDoc(selectedIndex.value, row._id)
  ElMessage.success('删除成功')
  handleSearch()
}

async function handleExport() {
  let dsl = null
  if (dslText.value) {
    try { dsl = JSON.parse(dslText.value) } catch (e) {}
  }
  const res = await exportDocs(selectedIndex.value, {
    conditions: searchConditions.value.filter(c => c.field && c.value),
    dsl
  })
  const blob = new Blob([res], { type: 'application/octet-stream' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${selectedIndex.value}_export.jsonl`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('导出成功')
}
</script>

<style scoped>
.index-manage { max-width: 1400px; }
.section { margin-bottom: 16px; }
.pagination { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
