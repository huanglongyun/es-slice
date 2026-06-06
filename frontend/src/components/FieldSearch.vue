<template>
  <div class="field-search">
    <div v-for="(item, idx) in conditions" :key="idx" class="search-row">
      <el-select v-model="item.field" placeholder="选择字段" style="width:200px" filterable>
        <el-option v-for="f in fields" :key="f.name" :label="f.name" :value="f.name" />
      </el-select>
      <el-select v-model="item.matchType" placeholder="匹配方式" style="width:140px">
        <el-option label="全匹配" value="term" />
        <el-option label="全词匹配" value="match_phrase" />
        <el-option label="分词匹配" value="match" />
      </el-select>
      <el-input v-model="item.value" placeholder="搜索值" style="width:250px" />
      <el-button :disabled="conditions.length <= 1" @click="removeRow(idx)"
                 icon="Delete" circle size="small" />
      <el-button v-if="idx === conditions.length - 1" @click="addRow"
                 icon="Plus" circle size="small" type="primary" />
    </div>
    <div class="search-actions">
      <el-button type="primary" @click="$emit('search')" icon="Search">搜索</el-button>
      <el-button @click="$emit('reset')" icon="Refresh">重置</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  fields: { type: Array, default: () => [] },
  modelValue: { type: Array, default: () => [] }
})

const emit = defineEmits(['update:modelValue', 'search', 'reset'])

const conditions = ref([{ field: '', matchType: 'match', value: '' }])

// 从父组件同步值（仅初始化）
watch(() => props.modelValue, (val) => {
  if (val && val.length > 0 && JSON.stringify(val) !== JSON.stringify(conditions.value)) {
    conditions.value = JSON.parse(JSON.stringify(val))
  }
}, { immediate: true })

// 向父组件同步值
watch(conditions, (val) => {
  emit('update:modelValue', JSON.parse(JSON.stringify(val)))
}, { deep: true })

function addRow() {
  conditions.value.push({ field: '', matchType: 'match', value: '' })
}

function removeRow(idx) {
  if (conditions.value.length > 1) {
    conditions.value.splice(idx, 1)
  }
}

defineExpose({ conditions })
</script>

<style scoped>
.search-row {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
}
.search-actions {
  margin-top: 12px;
}
</style>
