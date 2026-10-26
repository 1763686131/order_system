import { normalizeColumnOrder, normalizeHiddenColumnKeys } from '../composables/useTableColumnOrder.js'

const STORAGE_PREFIX = 'table-column-order:'
const HIDDEN_STORAGE_PREFIX = 'table-column-hidden:'
const HANDLE_SELECTOR = '.table-column-resize-handle'
const INPUT_SELECTOR = 'input, select, textarea, [contenteditable="true"]'

function moveNodes(parent, nodes) {
  nodes.forEach((node, index) => {
    const current = parent.childNodes[index] || null
    if (current === node) return
    if (parent.moveBefore && node.isConnected && parent.isConnected) parent.moveBefore(node, current)
    else parent.insertBefore(node, current)
  })
}

function preserveFocus(table, mutate) {
  const document = table.ownerDocument
  const active = document.activeElement
  if (!active || !table.contains(active)) return mutate()
  const { selectionStart, selectionEnd, selectionDirection } = active
  const suppressFocus = event => {
    if (event.target === active) event.stopImmediatePropagation()
  }
  const events = ['blur', 'focusout', 'focus', 'focusin']
  events.forEach(type => document.addEventListener(type, suppressFocus, true))
  try {
    mutate()
    if (active.isConnected && document.activeElement !== active) {
      active.focus({ preventScroll: true })
      if (typeof selectionStart === 'number') active.setSelectionRange(selectionStart, selectionEnd, selectionDirection)
    }
  } finally {
    events.forEach(type => document.removeEventListener(type, suppressFocus, true))
  }
}

export function readLayoutColumns(table) {
  const cols = Array.from(table.querySelectorAll(':scope > colgroup > col'))
  const occurrences = new Map()
  return Array.from(table.tHead?.rows[0]?.cells || []).map((header, index) => {
    const col = cols[index]
    const text = header.textContent.replace(/\*/g, '').trim().replace(/\s+/g, ' ')
    const baseKey = header.dataset.columnKey || col?.dataset.columnKey || text || String(index)
    const count = occurrences.get(baseKey) || 0
    occurrences.set(baseKey, count + 1)
    const checkbox = header.querySelector('input[type="checkbox"]')
    const fixed = header.dataset.columnFixed || col?.dataset.columnFixed
    return {
      key: count ? `${baseKey}:${count}` : baseKey,
      label: text || (checkbox ? '多选' : header.getAttribute('aria-label') || `第 ${index + 1} 列`),
      fixed: ['start', 'end'].includes(fixed) ? fixed : checkbox ? 'start' : undefined,
      hideable: header.dataset.columnHideable !== 'false' && col?.dataset.columnHideable !== 'false',
      header,
      col,
      index
    }
  })
}

// Map actual cells to logical columns, including cells covered by an earlier rowspan.
export function readLayoutRows(table, columnCount) {
  const sections = [...Array.from(table.tBodies), ...(table.tFoot ? [table.tFoot] : [])]
  return sections.flatMap(section => {
    const grid = []
    return Array.from(section.rows).map((row, rowIndex) => {
      grid[rowIndex] ||= []
      let index = 0
      let overlaps = false
      const cells = Array.from(row.cells).map(cell => {
        while (grid[rowIndex][index]) index++
        const start = index
        const span = cell.colSpan
        const rowSpan = cell.rowSpan || section.rows.length - rowIndex
        for (let nextRow = rowIndex; nextRow < rowIndex + rowSpan; nextRow++) {
          grid[nextRow] ||= []
          for (let nextColumn = start; nextColumn < start + span; nextColumn++) {
            if (grid[nextRow][nextColumn]) overlaps = true
            grid[nextRow][nextColumn] = cell
          }
        }
        index += span
        return { cell, start, span }
      })
      return {
        row,
        cells,
        valid: !overlaps && grid[rowIndex].length === columnCount &&
          Array.from({ length: columnCount }, (_, column) => Boolean(grid[rowIndex][column])).every(Boolean)
      }
    })
  })
}

export function createTableColumnLayout(table, { openDialog, onChange } = {}) {
  const document = table.ownerDocument
  const window = document.defaultView
  let value
  let storageKey
  let savedKeys = []
  let savedHiddenKeys = []
  let columns = []
  let rows = []
  let enabled = false
  let snapshots = []
  let attributeSnapshots = []
  let placeholders = []
  let headerAttributes = []
  let clickTimer = null
  let pendingClick = null
  let replayingClick = false
  let activeHeader = null

  const readStorage = (key, prefix) => {
    try {
      const saved = key ? JSON.parse(window.localStorage.getItem(prefix + key)) : []
      return Array.isArray(saved) ? [...new Set(saved.filter(item => typeof item === 'string'))] : []
    } catch {
      return []
    }
  }

  const setAttribute = (element, name, next) => {
    attributeSnapshots.push([element, name, element.getAttribute(name)])
    element.setAttribute(name, next)
  }

  const cancelClick = () => {
    if (clickTimer !== null) window.clearTimeout(clickTimer)
    clickTimer = null
    pendingClick = null
  }

  const restore = () => {
    preserveFocus(table, () => {
      for (const placeholder of placeholders) placeholder.remove()
      placeholders = []
      for (const [parent, children] of snapshots) moveNodes(parent, children)
      snapshots = []
      for (const [element, name, original] of attributeSnapshots.reverse()) {
        if (original === null) element.removeAttribute(name)
        else element.setAttribute(name, original)
      }
      attributeSnapshots = []
      for (const [name, original] of headerAttributes) {
        if (original === null) activeHeader.removeAttribute(name)
        else activeHeader.setAttribute(name, original)
      }
      headerAttributes = []
      activeHeader = null
    })
  }

  const orderedColumns = () => normalizeColumnOrder(columns, savedKeys)
  const dialogColumn = column => ({
    key: column.key,
    label: column.label,
    hideable: column.hideable,
    ...(column.fixed ? { fixed: column.fixed } : {})
  })

  const open = event => {
    if (!enabled || !activeHeader?.contains(event.target) ||
      event.target.closest(`${HANDLE_SELECTOR}, ${INPUT_SELECTOR}`)) return
    event.preventDefault()
    cancelClick()
    openDialog?.({
      columns: orderedColumns().map(dialogColumn),
      defaultColumns: columns.map(dialogColumn),
      hiddenKeys: normalizeHiddenColumnKeys(columns, savedHiddenKeys),
      apply
    })
  }

  const keydown = event => {
    if (event.target === activeHeader && ['Enter', ' '].includes(event.key)) open(event)
  }

  // Delay pointer clicks on headings so a double click cannot also sort table records.
  const click = event => {
    if (!enabled || replayingClick || event.detail === 0 || !activeHeader?.contains(event.target) ||
      event.target.closest(`${HANDLE_SELECTOR}, ${INPUT_SELECTOR}`)) return
    event.stopImmediatePropagation()
    event.preventDefault()
    if (event.detail > 1) {
      cancelClick()
      return
    }
    cancelClick()
    const target = event.target
    const header = activeHeader
    const key = storageKey
    pendingClick = { target, header, key }
    clickTimer = window.setTimeout(() => {
      const pending = pendingClick
      cancelClick()
      if (!pending || !enabled || key !== storageKey || !header.contains(target) || !table.isConnected) return
      replayingClick = true
      try {
        target.dispatchEvent(new window.MouseEvent('click', {
          bubbles: true, cancelable: true, detail: 1,
          ctrlKey: event.ctrlKey, shiftKey: event.shiftKey, altKey: event.altKey, metaKey: event.metaKey
        }))
      } finally {
        replayingClick = false
      }
    }, 500)
  }

  const renderOrder = () => {
    const ordered = orderedColumns()
    const hidden = new Set(normalizeHiddenColumnKeys(columns, savedHiddenKeys))
    const visible = ordered.filter(column => !hidden.has(column.key))
    const unchanged = !hidden.size && ordered.every((column, index) => column.index === index)
    const positions = new Map(visible.map((column, index) => [column.index, index]))
    const header = table.tHead.rows[0]
    const groups = Array.from(table.querySelectorAll(':scope > colgroup'))
    snapshots.push([header, Array.from(header.childNodes)])
    for (const group of groups) snapshots.push([group, Array.from(group.childNodes)])
    for (const column of columns) {
      for (const element of [column.header, column.col]) {
        setAttribute(element, 'data-column-key', column.key)
        setAttribute(element, 'data-layout-column-index', String(column.index + 1))
        setAttribute(element, 'data-layout-column-end-index', String(columns.length - column.index))
        if (hidden.has(column.key)) element.remove()
      }
    }
    if (!unchanged) moveNodes(header, [
      ...Array.from(header.childNodes).filter(node => !columns.some(column => column.header === node)),
      ...visible.map(column => column.header)
    ])
    // Existing tables have one colgroup; reject multiple groups in sync rather than moving across them.
    if (!unchanged) moveNodes(groups[0], [
      ...Array.from(groups[0].childNodes).filter(node => !columns.some(column => column.col === node)),
      ...visible.map(column => column.col)
    ])

    for (const { row, cells } of rows) {
      snapshots.push([row, Array.from(row.childNodes)])
      const segments = []
      for (const { cell, start, span } of cells) {
        const targets = Array.from({ length: span }, (_, offset) => positions.get(start + offset))
          .filter(index => index !== undefined).sort((a, b) => a - b)
        if (!targets.length) {
          cell.remove()
          continue
        }
        const runs = []
        for (const target of targets) {
          const last = runs.at(-1)
          if (last && last.start + last.span === target) last.span++
          else runs.push({ start: target, span: 1 })
        }
        runs.forEach((run, index) => {
          // Keep business content and input nodes once; separated parts of a merged cell remain empty.
          const element = index === 0 ? cell : cell.cloneNode(false)
          if (index > 0) {
            element.removeAttribute('id')
            element.removeAttribute('name')
            element.setAttribute('aria-hidden', 'true')
            placeholders.push(element)
          }
          if (index === 0) {
            setAttribute(element, 'colspan', String(run.span))
            setAttribute(element, 'data-column-key', columns[start].key)
            setAttribute(element, 'data-layout-column-index', String(start + 1))
            setAttribute(element, 'data-layout-column-end-index', String(columns.length - start))
          } else {
            element.colSpan = run.span
            element.dataset.layoutColumnIndex = String(start + 1)
          }
          segments.push({ cell: element, index: run.start })
        })
      }
      segments.sort((a, b) => a.index - b.index)
      if (!unchanged) moveNodes(row, [
        ...Array.from(row.childNodes).filter(node => !cells.some(entry => entry.cell === node)),
        ...segments.map(segment => segment.cell)
      ])
    }
  }

  const sync = nextValue => {
    value = nextValue
    const nextKey = typeof value === 'string' ? value : value?.storageKey || ''
    if (nextKey !== storageKey) {
      cancelClick()
      storageKey = nextKey
      savedKeys = readStorage(storageKey, STORAGE_PREFIX)
      savedHiddenKeys = readStorage(storageKey, HIDDEN_STORAGE_PREFIX)
    }
    columns = readLayoutColumns(table)
    rows = readLayoutRows(table, columns.length)
    enabled = value !== false && value?.enabled !== false && value?.reorder !== false &&
      table.tHead?.rows.length === 1 && columns.length > 0 &&
      table.querySelectorAll(':scope > colgroup').length === 1 &&
      table.querySelectorAll(':scope > colgroup > col').length === columns.length &&
      columns.every(column => column.col && column.header.colSpan === 1 && column.header.rowSpan === 1 && column.col.span === 1) &&
      rows.every(row => row.valid)
    table.classList.toggle('table-layout-reorderable', enabled)
    if (!enabled) return
    activeHeader = table.tHead
    for (const [name, next] of [
      ['title', '双击调整列顺序和显示；拖动列边缘调整列宽'],
      ['tabindex', '0'],
      ['aria-label', '表格标题，按回车调整列顺序和显示']
    ]) {
      headerAttributes.push([name, activeHeader.getAttribute(name)])
      activeHeader.setAttribute(name, next)
    }
    preserveFocus(table, renderOrder)
  }

  function apply(keys, hiddenKeys = normalizeHiddenColumnKeys(columns, savedHiddenKeys)) {
    const nextKeys = normalizeColumnOrder(columns, keys).map(column => column.key)
    const visible = new Set(nextKeys)
    const remaining = nextKeys.slice()
    savedKeys = [...savedKeys.map(key => visible.has(key) ? remaining.shift() : key), ...remaining]
    savedHiddenKeys = [
      ...savedHiddenKeys.filter(key => !visible.has(key)),
      ...normalizeHiddenColumnKeys(columns, hiddenKeys)
    ]
    if (storageKey) {
      for (const [prefix, saved] of [[STORAGE_PREFIX, savedKeys], [HIDDEN_STORAGE_PREFIX, savedHiddenKeys]]) {
        try {
          window.localStorage.setItem(prefix + storageKey, JSON.stringify(saved))
        } catch {
          // The current table remains usable when browser storage is unavailable.
        }
      }
    }
    cancelClick()
    onChange?.({
      keys: nextKeys,
      hiddenKeys: normalizeHiddenColumnKeys(columns, savedHiddenKeys),
      value
    })
  }

  table.addEventListener('dblclick', open)
  table.addEventListener('keydown', keydown)
  table.addEventListener('click', click, true)
  window.addEventListener('blur', cancelClick)

  return {
    sync,
    restore,
    destroy() {
      cancelClick()
      restore()
      table.removeEventListener('dblclick', open)
      table.removeEventListener('keydown', keydown)
      table.removeEventListener('click', click, true)
      window.removeEventListener('blur', cancelClick)
      table.classList.remove('table-layout-reorderable')
    }
  }
}
