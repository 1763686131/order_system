import { spawn } from 'node:child_process'
import { existsSync } from 'node:fs'
import { mkdtemp, readFile, rm } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join, resolve, sep } from 'node:path'
import { fileURLToPath } from 'node:url'
import { createServer } from 'vite'

const root = fileURLToPath(new URL('../../', import.meta.url))
const mobile = process.argv.includes('mobile')
const browserPath = [
  process.env.CHROME_BIN,
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
  '/usr/bin/chromium'
].find(path => path && existsSync(path))
if (!browserPath) throw new Error('Set CHROME_BIN to an installed Chromium browser')

const html = `<!doctype html><html><head><meta charset="utf-8"><style>body{margin:0}</style></head><body>
<div id="app"></div><pre id="result">pending</pre>
<script type="module">
import { createApp, h } from 'vue'
import { createPinia } from 'pinia'
import AccountManage from '/src/views/admin/hr/AccountManage.vue'
import tableLayout from '/src/directives/tableLayout.js'
import { useUserStore } from '/src/stores/user.js'
import request from '/src/api/request.js'

const result = { errors: [], checks: [] }
window.addEventListener('error', event => result.errors.push(event.message))
window.addEventListener('unhandledrejection', event => result.errors.push(String(event.reason)))
const assert = (condition, message) => { if (!condition) throw new Error(message) }
const pause = ms => new Promise(resolve => setTimeout(resolve, ms))
const waitFor = async predicate => {
  for (let index = 0; index < 100; index++) { if (predicate()) return; await pause(50) }
  throw new Error('Timed out waiting for employee table')
}
const employees = [
  { id: 1, employeeNo: 'E001', displayName: '王甲', username: 'wang', accountStatus: 'active',
    department: '研发部', position: '研发经理', departmentIds: [1], phone: '13800000001', birthDate: '1990-01-02',
    employmentType: '全职', employmentStatus: 'active', roleIds: [1], lastActiveDevice: null,
    hireDate: '2020-01-01', lastActiveAt: '2026-10-30 10:00:00' },
  { id: 2, employeeNo: 'E002', displayName: '周乙', username: 'zhou', accountStatus: 'pending',
    department: '销售部', position: '销售经理', departmentIds: [2], phone: '13800000002', birthDate: '1992-03-04',
    employmentType: '全职', employmentStatus: 'probation', roleIds: [], lastActiveDevice: null,
    hireDate: '2024-02-01', lastActiveAt: '' }
]
request.defaults.adapter = async config => {
  let data
  if (config.url === '/admin/employees') data = { employees }
  else if (config.url === '/admin/roles') data = { roles: [{ id: 1, name: '管理员' }] }
  else if (config.url === '/admin/permissions') data = { modules: [] }
  else if (config.url === '/admin/departments') data = { departments: [] }
  else if (config.url === '/stores' || config.url === '/warehouses') data = []
  else throw new Error('Unexpected API request: ' + config.url)
  return { data, status: 200, statusText: 'OK', headers: {}, config }
}

const pinia = createPinia()
useUserStore(pinia).$patch({ isSuperAdmin: true, allStores: true, allWarehouses: true })
let app
function mount() {
  app = createApp({ render: () => h(AccountManage) })
  app.use(pinia)
  app.directive('table-layout', tableLayout)
  app.mount('#app')
}
mount()
const table = () => document.querySelector('.employee-table')
const headers = () => [...table().tHead.rows[0].cells]
try {
  await waitFor(() => table()?.querySelectorAll('tbody tr.record-row').length === 2)
  assert(headers().length === 11 && table().querySelectorAll(':scope > colgroup > col').length === 11, 'All employee columns must have matching layout definitions')
  assert(table().classList.contains('resizable-columns-table') && table().classList.contains('table-layout-reorderable'), 'Employee table must enable resizing and layout settings')
  table().tHead.dispatchEvent(new MouseEvent('dblclick', { bubbles: true, cancelable: true }))
  await waitFor(() => document.querySelector('.column-order-overlay'))
  const dialog = document.querySelector('.column-order-overlay')
  assert(dialog.querySelectorAll('.column-order-row').length === 11, 'The layout dialog must list all columns')
  assert(dialog.querySelector('[data-column-order-key="actions"] .column-order-lock'), 'The operation column must stay fixed at the end')
  const jobGrip = dialog.querySelector('[data-column-order-key="job"] .column-order-grip')
  const accountRowBounds = dialog.querySelector('[data-column-order-key="account"]').getBoundingClientRect()
  jobGrip.dispatchEvent(new PointerEvent('pointerdown', {
    bubbles: true, cancelable: true, button: 0, pointerId: 5, isPrimary: true
  }))
  document.dispatchEvent(new PointerEvent('pointermove', {
    bubbles: true, cancelable: true, pointerId: 5,
    clientX: accountRowBounds.left + 80, clientY: accountRowBounds.top + 1
  }))
  document.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, pointerId: 5 }))
  await pause(50)
  assert(dialog.querySelectorAll('.column-order-row')[1].dataset.columnOrderKey === 'job', 'Dragging the column grip must update the draft order')
  dialog.querySelector('[aria-label="显示联系电话列"]').click()
  dialog.querySelector('.column-order-apply').click()
  await waitFor(() => !document.querySelector('.column-order-overlay') && headers()[1]?.dataset.columnKey === 'job')
  assert(headers().length === 10 && headers().at(-1).dataset.columnKey === 'actions', 'Applying layout must reorder columns and keep actions at the end')
  const firstRow = table().querySelector('tbody tr.record-row')
  assert(firstRow.cells.length === 10 && firstRow.cells[1].textContent.includes('研发经理') && firstRow.cells[2].textContent.includes('wang'), 'Employee cells must follow the changed column order')
  assert(!headers().some(header => header.dataset.columnKey === 'phone'), 'Hidden columns must be removed from the table')
  assert(JSON.parse(localStorage.getItem('table-column-hidden:hr-account-employee-list')).includes('phone'), 'Hidden column preferences must persist')
  result.checks.push('column settings dialog', 'column reordering', 'column hiding', 'row alignment', 'fixed operation column')

  const employeeFilter = document.querySelector('.toolbar-search input')
  employeeFilter.value = 'no matching employee'
  employeeFilter.dispatchEvent(new Event('input', { bubbles: true }))
  await waitFor(() => table().querySelector('tbody tr:not(.record-row)'))
  assert(table().querySelector('tbody tr:not(.record-row) td[colspan="10"]'), 'Empty-state colspan must follow the visible column count')
  employeeFilter.value = '周'
  employeeFilter.dispatchEvent(new Event('input', { bubbles: true }))
  await waitFor(() => table().querySelectorAll('tbody tr.record-row').length === 1)
  assert(headers()[1].dataset.columnKey === 'job' && table().querySelector('tbody tr.record-row').cells[1].textContent.includes('销售经理'), 'Column layout and row alignment must survive Vue data updates')

  const accountHeader = table().querySelector('th[data-column-key="account"]')
  const resizeHandle = accountHeader.querySelector('.table-column-resize-handle')
  assert(resizeHandle, 'Resizable columns must expose a keyboard and pointer handle')
  const originalColumnWidth = accountHeader.getBoundingClientRect().width
  const originalTableWidth = table().getBoundingClientRect().width
  const bounds = accountHeader.getBoundingClientRect()
  resizeHandle.dispatchEvent(new PointerEvent('pointerdown', {
    bubbles: true, cancelable: true, button: 0, pointerId: 7, isPrimary: true,
    clientX: bounds.right, clientY: bounds.top + bounds.height / 2
  }))
  document.dispatchEvent(new PointerEvent('pointermove', {
    bubbles: true, cancelable: true, pointerId: 7, clientX: bounds.right + 32
  }))
  document.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, pointerId: 7 }))
  await pause(50)
  assert(accountHeader.getBoundingClientRect().width >= originalColumnWidth + 20, 'Dragging a header edge must resize its column')
  assert(Math.abs(table().getBoundingClientRect().width - originalTableWidth) < 2, 'Fit mode must keep the overall table width unchanged')
  assert(JSON.parse(localStorage.getItem('table-column-widths:hr-account-employee-list')).account > originalColumnWidth, 'Column widths must persist independently')
  const savedWidth = accountHeader.getBoundingClientRect().width
  app.unmount()
  mount()
  await waitFor(() => table()?.querySelectorAll('tbody tr.record-row').length === 2)
  assert(headers().length === 10 && headers()[1].dataset.columnKey === 'job' && headers().at(-1).dataset.columnKey === 'actions', 'Remounting must restore saved order and visibility')
  assert(Math.abs(table().querySelector('th[data-column-key="account"]').getBoundingClientRect().width - savedWidth) < 2, 'Remounting must restore saved widths')
  assert(!table().querySelector('th[data-column-key="actions"] .table-column-resize-handle'), 'Fixed operation columns must keep their original width')
  assert(result.errors.length === 0, 'The employee table must not report Vue errors')
  result.checks.push('layout survives filtering', 'pointer column resize', 'fit-width compensation', 'column width persistence', 'saved layout restored on mount')
  result.pass = true
} catch (error) {
  result.errors.push(String(error.stack || error))
  result.pass = false
}
document.querySelector('#result').textContent = JSON.stringify(result)
</script></body></html>`

const profile = await mkdtemp(join(tmpdir(), 'account-table-layout-'))
const server = await createServer({
  root,
  server: { host: '127.0.0.1', port: 0, open: false },
  plugins: [{
    name: 'account-table-layout-check',
    configureServer(server) {
      server.middlewares.use('/__account-table-layout-check', async (req, res, next) => {
        try {
          res.setHeader('Content-Type', 'text/html; charset=utf-8')
          res.end(await server.transformIndexHtml('/__account-table-layout-check', html))
        } catch (error) { next(error) }
      })
    }
  }]
})

try {
  await server.listen()
  const port = server.httpServer.address().port
  const child = spawn(browserPath, [
    '--headless', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
    '--disable-background-networking', '--disable-extensions', '--remote-allow-origins=*',
    '--user-data-dir=' + profile, '--window-size=' + (mobile ? '390,844' : '1600,900'),
    '--remote-debugging-port=0', 'http://127.0.0.1:' + port + '/__account-table-layout-check'
  ], { windowsHide: true })
  let stderr = ''
  child.stderr.on('data', data => { stderr += data })
  const closed = new Promise((resolve, reject) => { child.once('error', reject); child.once('close', resolve) })
  let socket
  try {
    let debugPort
    for (let index = 0; index < 100 && !debugPort; index++) {
      try { debugPort = Number((await readFile(join(profile, 'DevToolsActivePort'), 'utf8')).split('\n')[0]) }
      catch { await new Promise(resolve => setTimeout(resolve, 100)) }
    }
    if (!debugPort) throw new Error('Chrome failed to start: ' + stderr.slice(-2000))
    const targets = await (await fetch('http://127.0.0.1:' + debugPort + '/json/list')).json()
    socket = new WebSocket(targets.find(target => target.type === 'page').webSocketDebuggerUrl)
    await Promise.race([
      new Promise((resolve, reject) => {
        socket.addEventListener('open', resolve, { once: true })
        socket.addEventListener('error', reject, { once: true })
      }),
      new Promise((_, reject) => setTimeout(() => reject(new Error('Chrome DevTools connection timed out')), 10000))
    ])
    let nextId = 0
    const send = (method, params = {}) => new Promise((resolve, reject) => {
      const id = ++nextId
      const receive = event => {
        const response = JSON.parse(event.data)
        if (response.id !== id) return
        socket.removeEventListener('message', receive)
        if (response.error) reject(new Error(JSON.stringify(response.error)))
        else resolve(response.result)
      }
      socket.addEventListener('message', receive)
      socket.send(JSON.stringify({ id, method, params }))
    })
    let result
    for (let index = 0; index < 200; index++) {
      const response = await send('Runtime.evaluate', {
        expression: 'document.querySelector("#result")?.textContent', returnByValue: true
      })
      result = response.result?.value
      if (result && result !== 'pending') break
      await new Promise(resolve => setTimeout(resolve, 100))
    }
    console.log((mobile ? 'mobile' : 'desktop') + ': ' + (result || stderr.slice(-2000)))
    if (!result || result === 'pending' || !JSON.parse(result).pass) process.exitCode = 1
    await send('Browser.close')
  } finally {
    socket?.close()
    if (child.exitCode === null) child.kill()
    await closed
  }
} finally {
  await server.close()
  if (!resolve(profile).toLowerCase().startsWith((resolve(tmpdir()) + sep).toLowerCase())) {
    throw new Error('Refusing cleanup outside the temp directory')
  }
  await rm(profile, { recursive: true, force: true, maxRetries: 5, retryDelay: 200 })
}
