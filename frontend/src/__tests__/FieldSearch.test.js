import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import FieldSearch from '@/components/FieldSearch.vue'

// Mock element-plus 图标
vi.mock('@element-plus/icons-vue', () => ({}))

// Mock element-plus 组件
const mockElSelect = {
  template: '<select :value="modelValue" @change="$emit(\'update:modelValue\', $event.target.value)"><slot /></select>',
  props: ['modelValue']
}

describe('FieldSearch', () => {
  let wrapper

  function mountComponent(props = {}) {
    return mount(FieldSearch, {
      props: { fields: [], ...props },
      global: {
        stubs: {
          'el-select': true,
          'el-option': true,
          'el-input': true,
          'el-button': true,
          'el-icon': true
        }
      }
    })
  }

  it('renders with one default row', () => {
    wrapper = mountComponent()
    expect(wrapper.vm.getConditions()).toHaveLength(0) // empty condition filtered out
  })

  it('addRow adds a new empty condition', async () => {
    wrapper = mountComponent()
    wrapper.vm.addRow()
    await nextTick()
    const conds = wrapper.vm.conditions
    expect(conds).toHaveLength(2)
  })

  it('removeRow removes the specified row', async () => {
    wrapper = mountComponent()
    wrapper.vm.addRow()
    await nextTick()
    wrapper.vm.removeRow(0)
    await nextTick()
    expect(wrapper.vm.conditions).toHaveLength(1)
  })

  it('cannot remove the last row (button disabled, but direct call removes it)', () => {
    wrapper = mountComponent()
    wrapper.vm.conditions = [{ field: 'a', matchType: 'match', value: 'b' }]
    wrapper.vm.removeRow(0)
    expect(wrapper.vm.conditions).toHaveLength(0)
  })

  it('getConditions filters out empty field/value', () => {
    wrapper = mountComponent()
    wrapper.vm.conditions = [
      { field: 'title', matchType: 'match', value: 'hello' },
      { field: '', matchType: 'match', value: '' },
      { field: 'name', matchType: 'term', value: '' },
    ]
    const conds = wrapper.vm.getConditions()
    expect(conds).toHaveLength(1)
    expect(conds[0].field).toBe('title')
  })

  it('reset clears conditions to one empty row', () => {
    wrapper = mountComponent()
    wrapper.vm.addRow()
    wrapper.vm.addRow()
    wrapper.vm.reset()
    expect(wrapper.vm.conditions).toHaveLength(1)
    expect(wrapper.vm.conditions[0].field).toBe('')
  })

  it('emits search event with filtered conditions', async () => {
    wrapper = mountComponent()
    wrapper.vm.conditions = [
      { field: 'title', matchType: 'match', value: 'test' },
    ]
    wrapper.vm.handleSearch()
    await nextTick()
    expect(wrapper.emitted('search')).toBeTruthy()
    expect(wrapper.emitted('search')[0][0]).toHaveLength(1)
    expect(wrapper.emitted('search')[0][0][0].field).toBe('title')
  })

  it('emits reset event on handleReset', async () => {
    wrapper = mountComponent()
    wrapper.vm.handleReset()
    await nextTick()
    expect(wrapper.emitted('reset')).toBeTruthy()
  })

  it('emits change event when conditions change', async () => {
    wrapper = mountComponent()
    wrapper.vm.addRow()
    await nextTick()
    expect(wrapper.emitted('change')).toBeTruthy()
  })
})
