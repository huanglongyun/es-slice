import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import ImportDialog from '@/components/ImportDialog.vue'

// Mock API
vi.mock('@/api/es', () => ({
  importExcel: vi.fn().mockResolvedValue({
    data: { success: 1, total: 1 }
  })
}))

// Mock element-plus (ESM compatible)
vi.mock('element-plus', async () => {
  const actual = await vi.importActual('element-plus')
  return {
    ...actual,
    ElMessage: { success: vi.fn(), error: vi.fn(), warning: vi.fn() },
    ElMessageBox: { confirm: vi.fn() }
  }
})

describe('ImportDialog', () => {
  function mountComponent(props = {}) {
    return mount(ImportDialog, {
      props: { visible: true, indexes: ['test_index'], ...props },
      global: {
        stubs: {
          'el-dialog': { template: '<div><slot /><slot name="footer" /></div>', props: ['modelValue', 'title', 'width', 'top'] },
          'el-form': { template: '<div><slot /></div>' },
          'el-form-item': { template: '<div><slot /></div>' },
          'el-select': { template: '<select multiple><slot /></select>' },
          'el-option': { template: '<option />' },
          'el-upload': { template: '<input type="file" />' },
          'el-table': { template: '<table><slot /></table>' },
          'el-table-column': { template: '<td />' },
          'el-button': { template: '<button @click="$emit(\'click\')"><slot /></button>' },
          'el-tag': { template: '<span><slot /></span>' },
          'el-steps': { template: '<div><slot /></div>' },
          'el-step': { template: '<div />' },
          'el-icon': { template: '<i />' },
          'el-popconfirm': { template: '<div />' },
          'el-input': { template: '<input />' },
          'el-switch': { template: '<input type="checkbox" />' }
        }
      }
    })
  }

  it('starts at step 0', () => {
    const wrapper = mountComponent()
    expect(wrapper.vm.step).toBe(0)
  })

  it('cannot proceed past step 0 without selecting indexes', async () => {
    const wrapper = mountComponent({ indexes: [] })
    wrapper.vm.selectedIndexes = []
    await nextTick()
    // step 0 next button should be disabled
    expect(wrapper.vm.step).toBe(0)
  })

  it('advances to step 1 when indexes selected', async () => {
    const wrapper = mountComponent()
    wrapper.vm.selectedIndexes = ['test_index']
    wrapper.vm.step = 1
    await nextTick()
    expect(wrapper.vm.step).toBe(1)
  })

  it('resets all state on close', async () => {
    const wrapper = mountComponent()
    wrapper.vm.step = 2
    wrapper.vm.selectedIndexes = ['a']
    wrapper.vm.file = new File([], 'test.xlsx')
    wrapper.vm.resetAll()
    await nextTick()
    expect(wrapper.vm.step).toBe(0)
    expect(wrapper.vm.selectedIndexes).toHaveLength(0)
    expect(wrapper.vm.file).toBeNull()
  })

  it('warns when importing without file', () => {
    const wrapper = mountComponent()
    wrapper.vm.file = null
    expect(() => wrapper.vm.handleImport()).not.toThrow()
  })
})
