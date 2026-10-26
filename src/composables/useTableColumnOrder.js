import { computed, ref, unref, watch } from 'vue'

const STORAGE_PREFIX = 'table-column-order:'
const HIDDEN_STORAGE_PREFIX = 'table-column-hidden:'

export function normalizeHiddenColumnKeys(columns, keys = []) {
  const hideable = new Set(columns.filter(column => column.hideable !== false).map(column => column.key))
  const hidden = [...new Set((Array.isArray(keys) ? keys : []).filter(key => hideable.has(key)))]
  if (columns.length && hidden.length === columns.length) {
    return hidden.filter(key => key !== columns[0].key)
  }
  return hidden
}

export function normalizeColumnOrder(columns, keys = []) {
  const available = new Map(columns.map(column => [column.key, column]))
  const ordered = []
  for (const key of Array.isArray(keys) ? keys : []) {
    const column = available.get(key)
    if (!column) continue
    ordered.push(column)
    available.delete(key)
  }
  ordered.push(...available.values())
  return [
    ...columns.filter(column => column.fixed === 'start'),
    ...ordered.filter(column => !column.fixed),
    ...columns.filter(column => column.fixed === 'end')
  ]
}

export function useTableColumnOrder(columns, { storageKey = '' } = {}) {
  const savedKeys = ref([])
  const savedHiddenKeys = ref([])
  const columnOrderVisible = ref(false)
  const orderedColumns = computed(() => normalizeColumnOrder(unref(columns), savedKeys.value))
  const hiddenColumnKeys = computed(() => normalizeHiddenColumnKeys(unref(columns), savedHiddenKeys.value))
  const visibleColumns = computed(() => {
    const hidden = new Set(hiddenColumnKeys.value)
    return orderedColumns.value.filter(column => !hidden.has(column.key))
  })

  watch(() => unref(storageKey), key => {
    columnOrderVisible.value = false
    savedKeys.value = []
    savedHiddenKeys.value = []
    if (!key) return
    for (const [prefix, target] of [[STORAGE_PREFIX, savedKeys], [HIDDEN_STORAGE_PREFIX, savedHiddenKeys]]) {
      try {
        const saved = JSON.parse(window.localStorage.getItem(prefix + key))
        if (Array.isArray(saved)) {
          target.value = [...new Set(saved.filter(item => typeof item === 'string'))]
        }
      } catch {
        // Keep the default layout when storage is unavailable or invalid.
      }
    }
  }, { immediate: true, flush: 'sync' })

  const openColumnOrder = event => {
    if (event?.target?.closest('.table-column-resize-handle, input, select')) return
    columnOrderVisible.value = true
  }

  const applyColumnOrder = (keys, hiddenKeys = hiddenColumnKeys.value) => {
    const nextKeys = normalizeColumnOrder(unref(columns), keys).map(column => column.key)
    // Retain preferences for columns temporarily hidden by permissions.
    const visibleKeys = new Set(nextKeys)
    const remainingKeys = [...nextKeys]
    const merged = savedKeys.value.map(key => visibleKeys.has(key) ? remainingKeys.shift() : key)
    savedKeys.value = [...merged, ...remainingKeys]
    savedHiddenKeys.value = [
      ...savedHiddenKeys.value.filter(key => !visibleKeys.has(key)),
      ...normalizeHiddenColumnKeys(unref(columns), hiddenKeys)
    ]
    const key = unref(storageKey)
    if (key) {
      for (const [prefix, saved] of [[STORAGE_PREFIX, savedKeys.value], [HIDDEN_STORAGE_PREFIX, savedHiddenKeys.value]]) {
        try {
          window.localStorage.setItem(prefix + key, JSON.stringify(saved))
        } catch {
          // The current page still uses the new layout if persistence fails.
        }
      }
    }
    columnOrderVisible.value = false
  }

  return {
    orderedColumns, visibleColumns, hiddenColumnKeys,
    columnOrderVisible, openColumnOrder, applyColumnOrder
  }
}
