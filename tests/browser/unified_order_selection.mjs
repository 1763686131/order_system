import { spawn } from 'node:child_process'
import { existsSync } from 'node:fs'
import { mkdtemp, readFile, rm } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { createServer } from 'vite'

// Run from the repository root: node tests/browser/unified_order_selection.mjs [scenario]
// Scenarios: default, reordered, reordered-hidden, reordered-legacy, reordered-mobile, reordered-persistence.
const root = fileURLToPath(new URL('../../', import.meta.url))
const scenario = process.argv[2] || 'reordered-hidden'
const browserPath = [
  process.env.CHROME_BIN,
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
  '/usr/bin/chromium',
  '/usr/bin/google-chrome'
].find(path => path && existsSync(path))
if (!browserPath) throw new Error('Set CHROME_BIN to an installed Chromium browser to run this test')

const html = `<!doctype html>
<html><head><meta charset="utf-8"><style>
body { margin: 0; }
.test-header { height: 60px; }
.main-content { height: 500px; padding: 20px; overflow-y: auto; }
</style></head><body><div id="app"></div><pre id="result">pending</pre>
<script type="module">
import { createApp, h, ref, nextTick } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createMemoryHistory, RouterView } from 'vue-router'
import OrderList from '/src/views/admin/sales/UnifiedOrderList.vue'
import tableLayout from '/src/directives/tableLayout.js'
import { provideAdminStickyPanel } from '/src/composables/useAdminStickyPanel.js'
import { useUserStore } from '/src/stores/user.js'
import { useOrderSelectionStore } from '/src/stores/orderSelection.js'
import request from '/src/api/request.js'

const results = { errors: [], calls: [], scroll: [] }
if (location.search.includes('legacy')) Element.prototype.moveBefore = undefined
if (location.search.includes('reordered')) {
  localStorage.setItem('table-column-order:sales-finance-list', JSON.stringify([
    'selection', 'status', 'actions', 'customer', 'date', 'order-number'
  ]))
  localStorage.setItem('table-column-widths:sales-finance-list', JSON.stringify({ date: 150, goods: 200 }))
}
if (location.search.includes('hidden')) {
  localStorage.setItem('table-column-hidden:sales-finance-list', JSON.stringify(['phone', 'address']))
}
window.addEventListener('error', event => results.errors.push(event.message))
window.addEventListener('unhandledrejection', event => results.errors.push(String(event.reason)))
const pause = () => new Promise(resolve => setTimeout(resolve, 50))
const frame = () => new Promise(resolve => requestAnimationFrame(resolve))
const settle = async () => { await nextTick(); await frame(); await frame(); await pause() }
const assert = (condition, message) => { if (!condition) throw new Error(message) }
let orderData = Array.from({ length: 40 }, (_, index) => ({
  id: index + 1, order_number: 'TEST-' + (index + 1),
  order_client: 'Test customer', store_id: 1,
  date: '2026-10-29', status: 'shipped', audit_state: index % 2,
  order_goods: [{ product_id: 1, product_name: 'Test product', quantity: 1, price: 10 }],
  total_amount: 10
}))
let failOrders = false
let delayOrders = false
request.defaults.adapter = async config => {
  results.calls.push([config.method, config.url])
  let data = []
  if (config.url === '/orders') {
    if (delayOrders) await new Promise(resolve => setTimeout(resolve, 400))
    if (failOrders) throw new Error('Simulated order refresh failure')
    data = orderData
  }
  if (config.url === '/stores') data = [{ id: 1, name: 'Test store', status: 'active' }]
  return { data, status: 200, statusText: 'OK', headers: {}, config }
}
const pinia = createPinia()
let stickyController
useUserStore(pinia).$patch({ id: 7, isSuperAdmin: true, allStores: true, allWarehouses: true })
const form = {
  render: () => h('button', { class: 'return-to-list', onClick: () => router.push('/') }, 'Return')
}
const router = createRouter({
  history: createMemoryHistory(),
  routes: [
    { path: '/', name: 'admin-sales', component: OrderList, props: { mode: 'finance' } },
    { path: '/sales/create', name: 'admin-sales-create', component: form },
    { path: '/sales/edit/:id', name: 'admin-sales-edit', component: form },
    { path: '/logistics', name: 'admin-sales-logistics', component: OrderList, props: { mode: 'logistics' } }
  ]
})
await router.push('/')
await router.isReady()
const app = createApp({
  setup() {
    const main = ref(null)
    const header = ref(null)
    const sticky = provideAdminStickyPanel(main, header)
    stickyController = sticky
    return () => h('div', [
      h('header', { class: 'test-header', ref: header }),
      h('main', { class: 'main-content', ref: main, onScroll: sticky.handleScroll }, [
        h(RouterView)
      ])
    ])
  }
})
app.use(pinia).use(router).directive('table-layout', tableLayout)
app.config.errorHandler = error => results.errors.push(String(error.stack || error))
app.mount('#app')
const waitForOrders = async () => {
  for (let count = 0; count < 100 && document.querySelectorAll('.record-row').length < 30; count++) await pause()
  await settle()
  assert(document.querySelectorAll('.record-row').length === 30, 'Orders must finish loading')
}
const findOrderRow = id => [...document.querySelectorAll('.record-row')].find(row =>
  row.querySelector('[data-column-key="order-number"]')?.textContent.trim() === 'TEST-' + id
)
const checkPersistedSelection = async () => {
  const store = useOrderSelectionStore(pinia)
  const selectedIds = () => [...store.selectedIdsFor('finance', 7)].sort((a, b) => a - b)
  const assertSelection = ids => assert(JSON.stringify(selectedIds()) === JSON.stringify(ids), 'The original selected IDs must be preserved')
  if (sessionStorage.getItem('order-selection-test-phase') === 'reload') {
    assertSelection([])
    assert(!findOrderRow(1)?.querySelector('input').checked, 'Browser reload must clear the first checkbox')
    assert(!findOrderRow(2)?.querySelector('input').checked, 'Browser reload must clear audited selections')
    assert(!document.querySelector('.selection-count'), 'Browser reload must clear the selected count')
    assert(!document.querySelector('.records-table thead input').indeterminate, 'Browser reload must reset select-all')
    assert(document.querySelector('.button-delete').disabled, 'Browser reload must disable deletion without a selection')
    sessionStorage.removeItem('order-selection-test-phase')
    results.phase = 'complete'
    return
  }
  findOrderRow(1).querySelector('input').click()
  findOrderRow(2).querySelector('input').click()
  await settle()
  document.querySelector('[title="下一页"]').click()
  await settle()
  findOrderRow(35).querySelector('input').click()
  await settle()
  assertSelection([1, 2, 35])
  document.querySelector('.create-button').click()
  await settle()
  assert(router.currentRoute.value.name === 'admin-sales-create', 'New order must navigate to the form')
  assert(!document.querySelector('.records-table'), 'The list must be unmounted while the form is open')
  assert(!window.refreshUnifiedOrderList, 'Unmounting must remove the stale refresh callback')
  document.querySelector('.return-to-list').click()
  await waitForOrders()
  assertSelection([1, 2, 35])
  assert(findOrderRow(1).querySelector('input').checked, 'Returning from new order must restore checkboxes')
  findOrderRow(1).click()
  await settle()
  document.querySelector('.detail-modal-footer .button-edit').click()
  await settle()
  assert(router.currentRoute.value.name === 'admin-sales-edit', 'Modify must navigate to the edit form')
  orderData = orderData.map(order => order.id === 1 ? { ...order, order_client: 'Edited customer' } : order)
  document.querySelector('.return-to-list').click()
  await waitForOrders()
  assertSelection([1, 2, 35])
  assert(findOrderRow(1).textContent.includes('Edited customer'), 'Returning from edit must show fresh data')
  assert(findOrderRow(1).querySelector('input').checked, 'Returning from edit must restore the checkbox')
  await router.push('/logistics')
  await waitForOrders()
  assert(document.querySelectorAll('.record-row.selected').length === 0, 'Logistics must have its own selection')
  findOrderRow(3).querySelector('input').click()
  await settle()
  await router.push('/')
  await waitForOrders()
  assertSelection([1, 2, 35])
  assert(!findOrderRow(3).querySelector('input').checked, 'Logistics selection must not leak into sales')
  delayOrders = true
  const refresh = window.refreshUnifiedOrderList()
  await settle()
  assert(document.querySelector('.button-delete').disabled, 'Cached selections must not be deletable while data loads')
  await refresh
  delayOrders = false
  failOrders = true
  await window.refreshUnifiedOrderList()
  await settle()
  assertSelection([1, 2, 35])
  document.querySelector('.button-delete').click()
  await settle()
  assert(!document.querySelector('.confirm-dialog'), 'Failed refresh must not allow deleting stale selections')
  failOrders = false
  orderData = orderData.filter(order => order.id !== 35)
  await window.refreshUnifiedOrderList()
  await waitForOrders()
  assertSelection([1, 2])
  document.querySelector('.button-delete').click()
  await settle()
  assert(document.querySelector('.notice-error')?.textContent.includes('反审核'), 'Restoring selections must preserve audit deletion protection')
  assert(!results.calls.some(([method]) => method === 'delete'), 'Persistence tests must never submit a delete')
  sessionStorage.setItem('order-selection-test-phase', 'reload')
  results.phase = 'reload'
}
try {
  await waitForOrders()
  if (location.search.includes('persistence')) {
    await checkPersistedSelection()
  } else {
  const main = document.querySelector('.main-content')
  const table = document.querySelector('.records-table')
  const inputs = [...table.querySelectorAll('tbody input[type=checkbox]')]
  results.rowCount = inputs.length
  assert(inputs.length === 30, 'Expected 30 displayed orders')
  if (location.search.includes('reordered')) {
    assert(table.querySelectorAll('thead th')[1].dataset.columnKey === 'status', 'Saved column order must be applied')
  }
  const audited = inputs.find(input => input.title.includes('反审核'))
  assert(audited && !audited.disabled, 'Audited orders must be selectable')
  audited.focus()
  audited.click()
  await settle()
  assert(audited.checked, 'Audited order must stay selected')
  const header = table.querySelector('thead input')
  assert(header.indeterminate, 'A partial selection must set the header indeterminate')
  header.click()
  await settle()
  assert(inputs.every(input => input.checked), 'Select-all must include audited orders')
  document.querySelector('.button-delete').click()
  await settle()
  assert(document.querySelector('.notice-error')?.textContent.includes('反审核'), 'Mixed batch delete must require reversing audit')
  assert(!document.querySelector('.confirm-dialog'), 'Locked batch must not open delete confirmation')
  assert(!results.calls.some(([method]) => method === 'delete'), 'Locked batch must not issue DELETE')
  header.click()
  await settle()
  assert(inputs.every(input => !input.checked), 'Select-all must also deselect audited orders')
  const unlocked = inputs.find(input => !input.title.includes('反审核'))
  unlocked.click()
  await settle()
  document.querySelector('.button-delete').click()
  await settle()
  assert(document.querySelector('.confirm-dialog'), 'Unaudited orders must still allow delete confirmation')
  document.querySelector('.confirm-dialog-cancel').click()
  await settle()
  header.click()
  await settle()
  const focusInput = location.search.includes('mobile')
    ? document.querySelectorAll('.mobile-order-select input')[18]
    : inputs[18]
  focusInput.focus()
  await settle()
  results.scroll.push({ step: 'focused', main: main.scrollTop, inner: table.parentElement.scrollTop, panelStyle: document.querySelector('.search-panel-content').getAttribute('style') })
  const scrollStep = Math.max(160, Math.ceil(main.scrollTop / 8))
  for (let index = 0; index < 12; index++) {
    main.scrollTop = Math.max(0, main.scrollTop - scrollStep)
    const intended = main.scrollTop
    stickyController.handleScroll()
    await settle()
    results.scroll.push({ step: index, intended, main: main.scrollTop, inner: table.parentElement.scrollTop, panelStyle: document.querySelector('.search-panel-content').getAttribute('style') })
    assert(Math.abs(main.scrollTop - intended) < 1, 'Scrolling must not jump back to the focused checkbox')
  }
  results.active = document.activeElement === focusInput
  assert(results.active, 'Layout updates must preserve keyboard focus')
  assert(main.scrollTop === 0, 'The list must be able to scroll to the top')
  assert(inputs.every(input => input.checked), 'Scrolling must preserve selected orders')
  const mobileInputs = [...document.querySelectorAll('.mobile-order-select input')]
  const mobileAudited = mobileInputs.find(input => input.title.includes('反审核'))
  assert(mobileAudited && !mobileAudited.disabled, 'Mobile audited orders must be selectable')
  mobileAudited.click()
  await settle()
  assert(!mobileAudited.checked && !audited.checked, 'Mobile selection must update the shared selection')
  assert(header.indeterminate, 'Mobile changes must update the desktop select-all state')
  if (location.search.includes('mobile')) {
    assert(getComputedStyle(document.querySelector('.mobile-order-list')).display !== 'none', 'Mobile view must be displayed')
  }
  assert(!results.calls.some(([method]) => method === 'delete'), 'Tests must never submit a delete')
  assert(results.errors.length === 0, 'Vue must not report runtime errors')
  results.tableStyle = table.getAttribute('style')
  }
  results.pass = true
} catch (error) {
  results.errors.push(String(error.stack || error))
  results.pass = false
}
document.querySelector('#result').textContent = JSON.stringify(results)
app.unmount()
</script></body></html>`

const profile = await mkdtemp(join(tmpdir(), 'order-selection-check-'))
const server = await createServer({
  root,
  server: { host: '127.0.0.1', port: 0, open: false },
  plugins: [{
    name: 'order-selection-check',
    configureServer(server) {
      server.middlewares.use('/__order-selection-check', async (req, res, next) => {
        try {
          res.setHeader('Content-Type', 'text/html; charset=utf-8')
          res.end(await server.transformIndexHtml('/__order-selection-check', html))
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
    '--disable-background-networking', '--disable-extensions',
    '--disable-background-timer-throttling', '--disable-renderer-backgrounding',
    '--user-data-dir=' + profile, '--window-size=' + (scenario.includes('mobile') ? '390,844' : '1600,900'),
    '--remote-debugging-port=0',
    'http://127.0.0.1:' + port + '/__order-selection-check?' + scenario
  ], { windowsHide: true })
  let stderr = ''
  child.stderr.on('data', data => { stderr += data })
  const closed = new Promise((resolve, reject) => {
    child.once('error', reject)
    child.once('close', resolve)
  })
  let socket
  try {
    let debugPort
    for (let count = 0; count < 100 && !debugPort; count++) {
      try {
        debugPort = Number((await readFile(join(profile, 'DevToolsActivePort'), 'utf8')).split('\n')[0])
      } catch { await new Promise(resolve => setTimeout(resolve, 100)) }
    }
    if (!debugPort) throw new Error('Chrome failed to start: ' + stderr.slice(-3000))
    const targets = await (await fetch('http://127.0.0.1:' + debugPort + '/json/list')).json()
    const page = targets.find(target => target.type === 'page')
    socket = new WebSocket(page.webSocketDebuggerUrl)
    await new Promise((resolve, reject) => {
      socket.addEventListener('open', resolve, { once: true })
      socket.addEventListener('error', reject, { once: true })
    })
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
    const readResult = async (reloading = false) => {
      let result
      for (let count = 0; count < 200; count++) {
        const response = await send('Runtime.evaluate', {
          expression: 'document.querySelector("#result")?.textContent',
          returnByValue: true
        })
        result = response.result?.value
        if (result && result !== 'pending') {
          const parsed = JSON.parse(result)
          if (!reloading || parsed.phase !== 'reload' || !parsed.pass) return result
        }
        await new Promise(resolve => setTimeout(resolve, 100))
      }
      return result
    }
    let result = await readResult()
    if (result && result !== 'pending' && JSON.parse(result).pass && JSON.parse(result).phase === 'reload') {
      await send('Page.reload')
      result = await readResult(true)
      if (result && result !== 'pending' && JSON.parse(result).phase !== 'complete') process.exitCode = 1
    }
    console.log(scenario + ': ' + (result || stderr.slice(-3000)))
    if (!result || result === 'pending' || !JSON.parse(result).pass) process.exitCode = 1
    await send('Browser.close')
  } finally {
    socket?.close()
    if (child.exitCode === null) child.kill()
    await closed
  }
} finally {
  await server.close()
  await rm(profile, { recursive: true, force: true, maxRetries: 5, retryDelay: 200 })
}
