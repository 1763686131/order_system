const instances = new WeakMap()
const STORAGE_PREFIX = 'table-column-widths:'
const HANDLE_CLASS = 'table-column-resize-handle'

const positiveNumber = (value, fallback) => {
  const number = Number(value)
  return Number.isFinite(number) && number > 0 ? number : fallback
}

const optionsFor = value => ({
  enabled: value !== false && value?.enabled !== false,
  storageKey: typeof value === 'string' ? value : value?.storageKey || '',
  minWidth: positiveNumber(value?.minWidth, 40),
  maxWidth: positiveNumber(value?.maxWidth, Infinity),
  resizeMode: value?.resizeMode === 'fit' ? 'fit' : 'expand',
  onResize: value?.onResize
})

function createInstance(table, value) {
  const document = table.ownerDocument
  const window = document.defaultView
  const originalStyle = {
    width: table.style.width,
    minWidth: table.style.minWidth,
    tableLayout: table.style.tableLayout
  }
  let options = optionsFor(value)
  let columns = []
  let savedWidths = new Map()
  let drag = null
  let pendingRestore = false

  const readStorage = () => {
    savedWidths = new Map()
    if (!options.storageKey) return
    try {
      const saved = JSON.parse(window.localStorage.getItem(STORAGE_PREFIX + options.storageKey))
      if (!saved || typeof saved !== 'object' || Array.isArray(saved)) return
      for (const [key, width] of Object.entries(saved)) {
        if (typeof width === 'number' && Number.isFinite(width) && width > 0) {
          savedWidths.set(key, width)
        }
      }
    } catch {
      // Storage can be unavailable or contain data from an older version.
    }
  }

  const saveStorage = () => {
    if (!options.storageKey) return
    try {
      window.localStorage.setItem(
        STORAGE_PREFIX + options.storageKey,
        JSON.stringify(Object.fromEntries(savedWidths))
      )
    } catch {
      // Resizing still works when browser storage is blocked or full.
    }
  }

  const limitWidth = (column, width) => Math.min(column.maxWidth, Math.max(column.minWidth, width))
  const measureWidths = () => columns.map(column => column.header.getBoundingClientRect().width)
  const resizedWidths = (widths, index, width) => {
    const next = widths.slice()
    const targetWidth = limitWidth(columns[index], width)
    if (options.resizeMode !== 'fit') {
      next[index] = targetWidth
      return next
    }
    const partnerIndex = columns.findLastIndex((column, current) => current !== index && column.resizable)
    if (partnerIndex < 0) return next
    const partner = columns[partnerIndex]
    const delta = Math.min(
      Math.max(0, widths[partnerIndex] - partner.minWidth),
      Math.max(-Math.max(0, partner.maxWidth - widths[partnerIndex]), targetWidth - widths[index])
    )
    next[index] += delta
    next[partnerIndex] -= delta
    return next
  }

  const fitSavedWidths = (widths, defaults) => {
    let remaining = defaults.reduce((sum, width) => sum + width, 0) -
      widths.reduce((sum, width) => sum + width, 0)
    // The rightmost resizable columns absorb saved-width differences.
    for (let index = columns.length - 1; index >= 0 && Math.abs(remaining) > 0.01; index--) {
      if (!columns[index].resizable) continue
      const nextWidth = limitWidth(columns[index], widths[index] + remaining)
      remaining -= nextWidth - widths[index]
      widths[index] = nextWidth
    }
    return Math.abs(remaining) < 0.5 ? widths : defaults
  }

  const updateAria = widths => columns.forEach((column, index) => {
    column.handle?.setAttribute('aria-valuenow', String(Math.round(widths[index])))
  })

  const applyWidths = widths => {
    // Pin every column so only the explicitly calculated widths change.
    const extraWidth = Math.max(0, table.getBoundingClientRect().width -
      measureWidths().reduce((sum, width) => sum + width, 0))
    columns.forEach((column, index) => {
      column.col.style.width = `${widths[index]}px`
      column.appliedWidth = column.col.style.width
    })
    const width = `${widths.reduce((sum, current) => sum + current, extraWidth)}px`
    table.style.width = width
    table.style.minWidth = width
    table.style.tableLayout = 'fixed'
    updateAria(widths)
  }

  const restoreStyles = () => {
    Object.assign(table.style, originalStyle)
    columns.forEach(column => {
      if (column.appliedWidth && column.col.style.width === column.appliedWidth) {
        column.col.style.width = column.originalWidth
      }
      column.appliedWidth = ''
    })
  }

  const restoreSavedWidths = () => {
    if (!columns.length) return
    const widths = measureWidths()
    pendingRestore = widths.some(width => width <= 0)
    if (pendingRestore) return
    if (columns.some(column => savedWidths.has(column.key))) {
      const restored = widths.map((width, index) => savedWidths.has(columns[index].key)
        ? limitWidth(columns[index], savedWidths.get(columns[index].key))
        : width)
      applyWidths(options.resizeMode === 'fit' ? fitSavedWidths(restored, widths) : restored)
    } else {
      updateAria(widths)
    }
  }

  const notifyResize = (column, width, persist = true, previousWidths) => {
    const widths = measureWidths()
    if (persist) {
      savedWidths.set(column.key, width)
      if (previousWidths) {
        columns.forEach((current, index) => {
          if (current.resizable && Math.abs(widths[index] - previousWidths[index]) > 0.01) {
            savedWidths.set(current.key, widths[index])
          }
        })
      }
      saveStorage()
    }
    options.onResize?.({
      key: column.key,
      index: columns.indexOf(column),
      width,
      widths
    })
  }

  const stopDrag = () => {
    if (!drag) return
    const current = drag
    drag = null
    document.removeEventListener('pointermove', moveDrag)
    document.removeEventListener('pointerup', endDrag)
    document.removeEventListener('pointercancel', endDrag)
    window.removeEventListener('blur', stopDrag)
    document.documentElement.classList.remove('is-resizing-table-column')
    current.column.handle?.classList.remove('is-resizing')
    if (current.changed) {
      notifyResize(current.column, current.widths[current.index], true, current.initialWidths)
    }
  }

  const endDrag = event => {
    if (event.pointerId === drag?.pointerId) stopDrag()
  }

  const moveDrag = event => {
    if (!drag || event.pointerId !== drag.pointerId) return
    event.preventDefault()
    const widths = resizedWidths(drag.initialWidths, drag.index, drag.startWidth + event.clientX - drag.startX)
    if (widths[drag.index] === drag.widths[drag.index]) return
    drag.widths = widths
    drag.changed = true
    applyWidths(drag.widths)
  }

  const startDrag = (event, column) => {
    if (event.button !== 0 || drag) return
    const widths = measureWidths()
    if (widths.some(width => width <= 0)) return
    event.preventDefault()
    event.stopPropagation()
    const index = columns.indexOf(column)
    drag = {
      column, index, widths, initialWidths: widths.slice(), pointerId: event.pointerId,
      startX: event.clientX, startWidth: widths[index], changed: false
    }
    column.handle.classList.add('is-resizing')
    document.documentElement.classList.add('is-resizing-table-column')
    document.addEventListener('pointermove', moveDrag, { passive: false })
    document.addEventListener('pointerup', endDrag)
    document.addEventListener('pointercancel', endDrag)
    window.addEventListener('blur', stopDrag)
  }

  const resetColumn = (event, column) => {
    event.preventDefault()
    event.stopPropagation()
    stopDrag()
    const previousWidths = measureWidths()
    const index = columns.indexOf(column)
    savedWidths.delete(column.key)
    restoreStyles()
    if (options.resizeMode === 'fit') {
      const widths = resizedWidths(previousWidths, index, measureWidths()[index])
      applyWidths(widths)
      columns.forEach((current, currentIndex) => {
        if (currentIndex !== index && current.resizable &&
          Math.abs(widths[currentIndex] - previousWidths[currentIndex]) > 0.01) {
          savedWidths.set(current.key, widths[currentIndex])
        }
      })
    } else {
      restoreSavedWidths()
    }
    saveStorage()
    notifyResize(column, measureWidths()[index], false)
  }

  const resizeWithKeyboard = (event, column) => {
    if (!['ArrowLeft', 'ArrowRight', 'Home'].includes(event.key)) return
    if (event.key === 'Home') return resetColumn(event, column)
    event.preventDefault()
    event.stopPropagation()
    const widths = measureWidths()
    const index = columns.indexOf(column)
    const next = resizedWidths(widths, index, widths[index] +
      (event.key === 'ArrowLeft' ? -1 : 1) * (event.shiftKey ? 1 : 10))
    if (next[index] === widths[index]) return
    applyWidths(next)
    notifyResize(column, next[index], true, widths)
  }

  const removeHandles = () => {
    columns.forEach(column => {
      column.handle?.remove()
      if (column.positionChanged) column.header.style.position = column.originalPosition
    })
  }

  const sync = value => {
    const nextOptions = optionsFor(value)
    const headers = Array.from(table.tHead?.rows[0]?.cells || [])
    const cols = Array.from(table.querySelectorAll(':scope > colgroup > col'))
    const occurrences = new Map()
    const nextColumns = headers.map((header, index) => {
      const col = cols[index]
      const label = header.textContent.replace(/\*/g, '').trim().replace(/\s+/g, ' ')
      const baseKey = header.dataset.columnKey || col?.dataset.columnKey || label || String(index)
      const count = occurrences.get(baseKey) || 0
      occurrences.set(baseKey, count + 1)
      const minWidth = positiveNumber(header.dataset.minWidth || col?.dataset.minWidth, nextOptions.minWidth)
      return {
        header, col, label, key: count ? `${baseKey}:${count}` : baseKey,
        minWidth,
        maxWidth: Math.max(minWidth, positiveNumber(header.dataset.maxWidth || col?.dataset.maxWidth, nextOptions.maxWidth)),
        resizable: header.dataset.resizable !== 'false' && col?.dataset.resizable !== 'false'
      }
    })
    const valid = nextOptions.enabled && table.tHead?.rows.length === 1 &&
      headers.length > 0 && headers.length === cols.length &&
      headers.every(header => header.colSpan === 1 && header.rowSpan === 1) &&
      cols.every(col => col.span === 1)
    const unchanged = valid && nextOptions.storageKey === options.storageKey &&
      nextOptions.minWidth === options.minWidth && nextOptions.maxWidth === options.maxWidth &&
      nextOptions.resizeMode === options.resizeMode &&
      nextColumns.length === columns.length && nextColumns.every((column, index) => {
        const previous = columns[index]
        return column.header === previous.header && column.col === previous.col &&
          column.key === previous.key && column.minWidth === previous.minWidth &&
          column.maxWidth === previous.maxWidth && column.resizable === previous.resizable &&
          (!previous.resizable || previous.handle?.parentNode === column.header) &&
          (!previous.appliedWidth || column.col.style.width === previous.appliedWidth)
      })
    if (unchanged) {
      options = nextOptions
      return
    }

    stopDrag()
    restoreStyles()
    removeHandles()
    if (nextOptions.storageKey !== options.storageKey) {
      options = nextOptions
      readStorage()
    } else {
      options = nextOptions
    }
    columns = []
    pendingRestore = false
    table.classList.toggle('resizable-columns-table', valid)
    if (!valid) return
    columns = nextColumns.map(column => ({
      ...column, originalWidth: column.col.style.width,
      originalPosition: column.header.style.position, appliedWidth: ''
    }))
    columns.forEach(column => {
      if (!column.resizable) return
      column.positionChanged = window.getComputedStyle(column.header).position === 'static'
      if (column.positionChanged) column.header.style.position = 'relative'
      const handle = document.createElement('span')
      handle.className = HANDLE_CLASS
      handle.tabIndex = 0
      handle.title = '\u62d6\u52a8\u8c03\u6574\u5217\u5bbd\uff0c\u53cc\u51fb\u6062\u590d\u9ed8\u8ba4'
      handle.setAttribute('role', 'separator')
      handle.setAttribute('aria-orientation', 'vertical')
      handle.setAttribute('aria-label', `\u8c03\u6574${column.label}\u5217\u5bbd`)
      handle.setAttribute('aria-valuemin', String(column.minWidth))
      if (Number.isFinite(column.maxWidth)) handle.setAttribute('aria-valuemax', String(column.maxWidth))
      handle.addEventListener('pointerdown', event => startDrag(event, column))
      handle.addEventListener('dblclick', event => resetColumn(event, column))
      handle.addEventListener('keydown', event => resizeWithKeyboard(event, column))
      handle.addEventListener('click', event => event.stopPropagation())
      column.handle = handle
      column.header.appendChild(handle)
    })
    restoreSavedWidths()
  }

  const observer = window.ResizeObserver ? new window.ResizeObserver(() => {
    if (pendingRestore) restoreSavedWidths()
  }) : null
  readStorage()
  sync(value)
  observer?.observe(table)

  return {
    sync,
    destroy() {
      stopDrag()
      observer?.disconnect()
      restoreStyles()
      removeHandles()
      table.classList.remove('resizable-columns-table')
    }
  }
}

export default {
  mounted(table, binding) {
    instances.set(table, createInstance(table, binding.value))
  },
  updated(table, binding) {
    instances.get(table)?.sync(binding.value)
  },
  beforeUnmount(table) {
    instances.get(table)?.destroy()
    instances.delete(table)
  }
}
