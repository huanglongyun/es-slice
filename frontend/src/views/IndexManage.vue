<template>
  <div class="index-manage">
    <div class="section">
      <el-select v-model="selectedIndex" placeholder="选择索引（搜索）" style="width:300px"
                 filterable @change="onIndexChange">
        <el-option v-for="idx in indexes" :key="idx" :label="idx" :value="idx" />
      </el-select>
    </div>

    <div class="section">
      <h4>字段搜索</h4>
      <FieldSearch ref="fieldSearchRef" :fields="indexFields"
                   @search="handleSearch" @reset="handleReset" @change="syncDsl" />
    </div>

    <div class="section" v-if="dslVisible">
      <h4>
        自定义 DSL
        <el-button text size="small" @click="dslVisible = false">收起</el-button>
      </h4>
      <el-input v-model="dslText" type="textarea" :rows="6"
                placeholder='{"query":{"bool":{"must":[...]}}}' />
    </div>
    <div class="section" v-else>
      <el-button text size="small" @click="dslVisible = true; syncDsl()">
        展开自定义 DSL
      </el-button>
    </div>

    <div class="section">
      <el-dropdown @command="handleExport" :disabled="role === 'viewer' || !selectedIndex">
        <el-button icon="Download" :disabled="role === 'viewer' || !selectedIndex">
          导出 JSONL <el-icon class="el-icon--right"><ArrowDown /></el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="selected">勾选记录</el-dropdown-item>
            <el-dropdown-item command="current">当前页</el-dropdown-item>
            <el-dropdown-item command="all">全部记录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
      <el-button @click="importDialogVisible = true" icon="Upload"
                 :disabled="role === 'viewer'">导入 Excel</el-button>
    </div>

    <div class="section">
      <el-table :data="tableData" ref="tableRef" border stripe v-loading="tableLoading"
                @selection-change="onSelectionChange" style="width:100%">
        <el-table-column type="selection" width="50" />
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
        <el-pagination v-model:current-page="page" v-model:page-size="pageSize"
                       :total="total" :page-sizes="[10,20,50,100]"
                       layout="total,sizes,prev,pager,next"
                       @current-change="onPageChange"
                       @size-change="onPageChange" />
      </div>
    </div>

    <DocDetailDialog ref="detailDialogRef" />
    <DocEditDialog ref="editDialogRef" @saved="doSearch" />
    <ImportDialog v-model:visible="importDialogVisible" :indexes="indexes"
                  @imported="doSearch" />
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
const dslVisible = ref(true)
const dslText = ref('')

const tableRef = ref(null)
const tableData = ref([])
const selectedRows = ref([])
const tableColumns = ref([])
const tableLoading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

const detailDialogRef = ref(null)
const editDialogRef = ref(null)
const importDialogVisible = ref(false)

// 默认 DSL 模板
function buildDefaultDsl(conds) {
  const query = conds && conds.length
    ? { bool: { must: conds.map(c => ({ [c.matchType]: { [c.field]: c.value } })) } }
    : { query_string: { query: '*' } }
  return {
    query,
    size: pageSize.value,
    from: (page.value - 1) * pageSize.value,
    sort: []
  }
}

function stringifyDsl(conds) {
  return JSON.stringify(buildDefaultDsl(conds), null, 2)
}

// 初始化默认 DSL
dslText.value = stringifyDsl()

getIndexes().then(res => { indexes.value = res.data }).catch(() => {})

async function onIndexChange(val) {
  if (!val) return
  tableLoading.value = true
  try {
    const res = await getIndexFields(val)
    indexFields.value = res.data
    tableColumns.value = res.data.map(f => f.name)
  } finally {
    tableLoading.value = false
  }
  fieldSearchRef.value?.reset()
  handleReset()
}

function handleReset() {
  page.value = 1
  pageSize.value = 20
  tableData.value = []
  total.value = 0
  dslText.value = stringifyDsl()
}

function handleSearch(conditions) {
  page.value = 1
  syncPaginationInDsl()
  doSearch(conditions)
}

function onPageChange(newPage) {
  // newPage is the updated page number (current-change) or new size (size-change)
  syncPaginationInDsl()
  doSearch()
}

function syncPaginationInDsl() {
  // 更新 DSL 中的 from/size，保持用户的 query 不变
  try {
    const dsl = JSON.parse(dslText.value)
    dsl.size = pageSize.value
    dsl.from = (page.value - 1) * pageSize.value
    dslText.value = JSON.stringify(dsl, null, 2)
  } catch (e) { /* 保持原样 */ }
}

async function doSearch(conditions) {
  if (!selectedIndex.value) return
  tableLoading.value = true
  try {
    let body = {}
    try { body = JSON.parse(dslText.value) } catch (e) { /* fallback */ }
    // 始终用当前分页覆盖
    body.size = pageSize.value
    body.from = (page.value - 1) * pageSize.value
    if (!body.sort) body.sort = []
    const res = await searchDocs(selectedIndex.value, body)
    const hits = res.data.hits || {}
    tableData.value = (hits.hits || []).map(h => ({ _id: h._id, _index: h._index, _score: h._score, ...h._source }))
    const t = hits.total || 0
    total.value = typeof t === 'object' ? t.value : t
  } finally {
    tableLoading.value = false
  }
}

function syncDsl() {
  const conds = fieldSearchRef.value?.getConditions() || []
  dslText.value = stringifyDsl(conds)
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
  doSearch()
}

function onSelectionChange(rows) {
  selectedRows.value = rows
}

async function handleExport(mode) {
  let dsl = {}
  try { dsl = JSON.parse(dslText.value) } catch (e) {}

  if (mode === 'selected') {
    if (selectedRows.value.length === 0) {
      ElMessage.warning('请先勾选要导出的记录')
      return
    }
    const ids = selectedRows.value.map(r => r._id)
    dsl = { query: { terms: { _id: ids } }, size: ids.length }
  } else if (mode === 'current') {
    dsl.size = pageSize.value
    dsl.from = (page.value - 1) * pageSize.value
  } else {
    // all: scroll all, remove from
    delete dsl.from
    dsl.size = 10000
  }
  if (!dsl.sort) dsl.sort = []

  try {
    const res = await exportDocs(selectedIndex.value, dsl)
    const blob = res.data
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${selectedIndex.value}_export.jsonl`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (e) {
    ElMessage.error(e.message || '导出失败')
  }
}
</script>

<style scoped>
.index-manage { max-width: 1400px; }
.section { margin-bottom: 16px; }
.pagination { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
