<template>
  <div class="audit-log">
    <el-card>
      <template #header>审计日志</template>
      <el-form :inline="true" :model="filters">
        <el-form-item label="用户">
          <el-input v-model="filters.username" placeholder="用户名" clearable />
        </el-form-item>
        <el-form-item label="索引">
          <el-input v-model="filters.indexName" placeholder="索引名" clearable />
        </el-form-item>
        <el-form-item label="操作">
          <el-select v-model="filters.action" placeholder="全部" clearable style="width:120px">
            <el-option label="创建" value="CREATE" />
            <el-option label="更新" value="UPDATE" />
            <el-option label="删除" value="DELETE" />
            <el-option label="导出" value="EXPORT" />
            <el-option label="导入" value="IMPORT" />
          </el-select>
        </el-form-item>
        <el-form-item label="时间">
          <el-date-picker v-model="filters.dateRange" type="datetimerange"
                          range-separator="至" start-placeholder="开始" end-placeholder="结束"
                          value-format="YYYY-MM-DDTHH:mm:ss" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="tableData" border stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="username" label="操作用户" width="120" />
        <el-table-column prop="action" label="操作" width="80" />
        <el-table-column prop="indexName" label="索引" width="140" />
        <el-table-column prop="docId" label="文档ID" width="120" show-overflow-tooltip />
        <el-table-column prop="ipAddress" label="IP" width="130" />
        <el-table-column prop="createdAt" label="时间" width="170" />
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="showDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination v-model:current-page="page" :page-size="pageSize"
                       :total="total" layout="total,prev,pager,next"
                       @current-change="handleSearch" />
      </div>
    </el-card>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailVisible" title="操作详情" width="700px" top="5vh">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="ID">{{ detailRow.id }}</el-descriptions-item>
        <el-descriptions-item label="操作">{{ detailRow.action }}</el-descriptions-item>
        <el-descriptions-item label="操作用户">{{ detailRow.username }}</el-descriptions-item>
        <el-descriptions-item label="IP地址">{{ detailRow.ipAddress }}</el-descriptions-item>
        <el-descriptions-item label="索引">{{ detailRow.indexName }}</el-descriptions-item>
        <el-descriptions-item label="文档ID">{{ detailRow.docId }}</el-descriptions-item>
        <el-descriptions-item label="时间" :span="2">{{ detailRow.createdAt }}</el-descriptions-item>
      </el-descriptions>
      <div style="margin-top:16px">
        <el-row :gutter="16" v-if="detailRow.beforeContent">
          <el-col :span="12">
            <h4>修改前</h4>
            <pre class="json-view">{{ formatJson(detailRow.beforeContent) }}</pre>
          </el-col>
          <el-col :span="12" v-if="detailRow.afterContent">
            <h4>修改后</h4>
            <pre class="json-view">{{ formatJson(detailRow.afterContent) }}</pre>
          </el-col>
        </el-row>
        <div v-else-if="detailRow.beforeContent">
          <h4>操作内容</h4>
          <pre class="json-view">{{ formatJson(detailRow.beforeContent) }}</pre>
        </div>
      </div>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { getAuditLogs } from '@/api/audit'

const filters = reactive({
  username: '',
  indexName: '',
  action: '',
  dateRange: null
})

const tableData = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

const detailVisible = ref(false)
const detailRow = ref({})

async function handleSearch() {
  loading.value = true
  try {
    const params = { page: page.value, pageSize: pageSize.value }
    if (filters.username) params.username = filters.username
    if (filters.indexName) params.indexName = filters.indexName
    if (filters.action) params.action = filters.action
    if (filters.dateRange) {
      params.startTime = filters.dateRange[0]
      params.endTime = filters.dateRange[1]
    }
    const res = await getAuditLogs(params)
    tableData.value = res.data.list
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

function handleReset() {
  filters.username = ''
  filters.indexName = ''
  filters.action = ''
  filters.dateRange = null
  handleSearch()
}

function showDetail(row) {
  detailRow.value = row
  detailVisible.value = true
}

function formatJson(str) {
  try {
    return JSON.stringify(JSON.parse(str), null, 2)
  } catch (e) {
    return str
  }
}

handleSearch()
</script>

<style scoped>
.pagination { margin-top: 16px; display: flex; justify-content: flex-end; }
.json-view {
  background: #f5f7fa;
  padding: 16px;
  border-radius: 4px;
  max-height: 40vh;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-all;
  font-size: 13px;
  line-height: 1.6;
}
</style>
