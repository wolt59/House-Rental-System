/**
 * 列表页通用分页 & 筛选 composable
 * 提供：
 *   - pagination: skip/limit 参数体、翻页状态、分页组件属性
 *   - statusTabs: 基于状态字段生成 tab 定义与计数
 *   - 统一 resetPage + 请求协调
 */
import { ref, reactive, computed } from 'vue'

export function usePagination(options = {}) {
  const pageSize = ref(options.pageSize ?? 10)
  const currentPage = ref(1)
  const total = ref(0)

  function skip() {
    return (currentPage.value - 1) * pageSize.value
  }

  function resetPage() {
    currentPage.value = 1
  }

  function paginationParams() {
    return {
      skip: skip(),
      limit: pageSize.value,
    }
  }

  function paginationProps() {
    return {
      total: total.value,
      pageSize: pageSize.value,
      currentPage: currentPage.value,
    }
  }

  return {
    pageSize,
    currentPage,
    total,
    skip,
    resetPage,
    paginationParams,
    paginationProps,
  }
}

/**
 * @param {import('vue').Ref<Array>} listRef   数据列表 ref
 * @param {Array<{name:string, label:string}>} tabDefs  tab 定义，name 对应 filter 函数的参数
 * @param {Record<string, Function>} filterFns  tabName → (item) => boolean
 */
export function useStatusTabs(listRef, tabDefs, filterFns = {}) {
  const tabCounts = computed(() => {
    const list = listRef.value || []
    const counts = {}
    for (const tab of tabDefs) {
      const fn = filterFns[tab.name]
      counts[tab.name] = fn ? list.filter(fn).length : list.length
    }
    return counts
  })

  return { tabCounts }
}