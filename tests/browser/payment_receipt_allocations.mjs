import { spawn } from 'node:child_process'
import { existsSync } from 'node:fs'
import { mkdtemp, readFile, rm } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join, resolve, sep } from 'node:path'
import { fileURLToPath } from 'node:url'
import { createServer } from 'vite'

// node tests/browser/payment_receipt_allocations.mjs [mobile]
const root = fileURLToPath(new URL('../../', import.meta.url))
const mobile = process.argv.includes('mobile')
const browserPath = [
  process.env.CHROME_BIN,
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
  '/usr/bin/chromium'
].find(path => path && existsSync(path))
if (!browserPath) throw new Error('Set CHROME_BIN to an installed Chromium browser')

const html = `<!doctype html><html><head><meta charset="utf-8"><style>
body { margin: 0; font-family: Arial, sans-serif; }
</style></head><body><div id="app"></div><pre id="result">pending</pre>
<script type="module">
import { createApp, h, nextTick } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createMemoryHistory, RouterView } from 'vue-router'
import PaymentHistory from '/src/views/admin/finance/PaymentHistory.vue'
import request from '/src/api/request.js'

const result = { errors: [], checks: [] }
window.addEventListener('error', event => result.errors.push(event.message))
window.addEventListener('unhandledrejection', event => result.errors.push(String(event.reason)))
const assert = (condition, message) => { if (!condition) throw new Error(message) }
const pause = ms => new Promise(resolve => setTimeout(resolve, ms))
const settle = async () => { await nextTick(); await pause(50) }
const waitFor = async predicate => {
  for (let i = 0; i < 100; i++) { if (predicate()) return; await pause(50) }
  throw new Error('Timed out waiting for UI state')
}
const stores = [{ id: 1, name: 'Store A', status: 'active' }, { id: 2, name: 'Store B', status: 'active' }]
const customers = [{ id: 1, storeId: 1, customerName: 'Customer A', customerCode: '001', receivable: 250 },
  { id: 2, storeId: 2, customerName: 'Customer B', receivable: 0 }]
const documents = [
  { sourceType: 'order', sourceId: 101, documentNo: 'SO-OLD', documentDate: '2025-01-01', amount: 60, outstandingAmount: 60 },
  { sourceType: 'order', sourceId: 102, documentNo: 'SO-MIDDLE', documentDate: '2025-02-01', amount: 70, outstandingAmount: 70 },
  { sourceType: 'order', sourceId: 103, documentNo: 'SO-NEW', documentDate: '2025-03-01', amount: 100, outstandingAmount: 100 }
]
let failCustomer = false
let delayCustomer = false
let saved = null
request.defaults.adapter = async config => {
  let data
  if (config.url === '/stores') data = stores
  else if (config.url === '/customers') data = customers
  else if (config.url === '/bank-accounts/options') data = { items: [{ id: 1, storeId: 1, accountName: 'Bank', isDefault: true }] }
  else if (config.url === '/payment-receipts/next-number') data = { documentNo: 'SK-TEST' }
  else if (config.url === '/customers/1/receivable-documents') {
    if (delayCustomer) await pause(300)
    data = { receivable: 230, items: documents }
  } else if (config.url === '/customers/2/receivable-documents') {
    if (failCustomer) throw new Error('Simulated debt loading failure')
    data = { receivable: 0, items: [] }
  } else if (config.url === '/payment-receipts' && config.method === 'post') {
    const payload = JSON.parse(config.data)
    saved = { ...payload, id: 1, documentNo: 'SK-TEST', storeId: 1, storeName: 'Store A',
      customerName: 'Customer A', status: 'draft',
      writeoffAmount: payload.allocations.reduce((sum, row) => sum + row.amount, 0), advanceAmount: 0 }
    data = { receipt: saved }
  } else if (config.url === '/payment-receipts/1') data = saved
  else if (config.url === '/payment-receipts') data = { items: saved ? [saved] : [] }
  else throw new Error('Unexpected API request: ' + config.url)
  return { data, status: 200, statusText: 'OK', headers: {}, config }
}
const router = createRouter({ history: createMemoryHistory(), routes: [{ path: '/', component: PaymentHistory }] })
await router.push('/')
await router.isReady()
const app = createApp({ render: () => h(RouterView) })
app.use(createPinia()).use(router)
app.config.errorHandler = error => result.errors.push(String(error.stack || error))
app.mount('#app')
const form = () => document.querySelector('#receipt-document-form')
const storeSelect = () => form().querySelectorAll('select')[0]
const customerSelect = () => form().querySelectorAll('select')[1]
const checks = () => [...document.querySelectorAll('.receipt-allocation-table input[type=checkbox]')]
const amounts = () => [...document.querySelectorAll('.receipt-allocation-amount')].map(cell => Number(cell.textContent.replace(/[^0-9.]/g, '')))
const change = async (element, value) => { element.value = value; element.dispatchEvent(new Event('change', { bubbles: true })); await settle() }
const input = async (element, value) => { element.value = value; element.dispatchEvent(new Event('input', { bubbles: true })); await settle() }
const auto = () => document.querySelector('.receipt-allocation-header button').click()
const saveButton = () => document.querySelector('[form=receipt-document-form]')
try {
  await waitFor(() => document.querySelector('.toolbar-actions .button-primary'))
  await settle()
  document.querySelector('.toolbar-actions .button-primary').click()
  await settle()
  assert(customerSelect().disabled, 'Customer selection must wait for a store')
  await change(storeSelect(), '1')
  assert(customerSelect().options.length === 2 && customerSelect().options[1].textContent.trim() === 'Customer A', 'Customer options must show only names and match the store')
  await change(customerSelect(), '1')
  await waitFor(() => checks().length === 3)
  assert(checks().every(box => !box.checked), 'New receipts must allow explicit manual selection')
  assert(form().querySelector('.receipt-debt').value.replace(/[^0-9.]/g, '') === '230.00', 'Debt must refresh from the document endpoint')
  await input(form().querySelectorAll('input[type=number]')[0], '100')
  checks()[2].click()
  await settle()
  assert(JSON.stringify(amounts()) === '[0,0,100]', 'Manual selection must allocate only against the checked document')
  checks()[0].click()
  await settle()
  assert(JSON.stringify(amounts()) === '[0,0,100]', 'Manual selection must preserve the order in which documents were checked')
  auto()
  await settle()
  assert(JSON.stringify(amounts()) === '[60,40,0]', 'Auto allocation must use oldest documents first and partially cover the last one')
  assert(checks()[0].checked && checks()[1].checked && !checks()[2].checked, 'Auto allocation must replace the selection')
  await input(form().querySelectorAll('input[type=number]')[1], '10')
  assert(JSON.stringify(amounts()) === '[60,50,0]', 'Discount must be included in receivable reduction')
  form().dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }))
  await waitFor(() => !form())
  assert(saved.allocationMode === 'manual' && JSON.stringify(saved.allocations.map(row => row.amount)) === '[60,50]', 'Saving must persist the actual allocations')
  document.querySelector('.action-edit').click()
  await waitFor(() => checks().length === 3 && checks()[1].checked)
  assert(JSON.stringify(amounts()) === '[60,50,0]', 'Editing a draft must restore its allocations')
  result.checks.push('manual selection', 'oldest-first automatic allocation', 'partial allocation', 'discount', 'save and edit')

  await change(storeSelect(), '2')
  assert(customerSelect().value === '' && checks().length === 0, 'Store changes must clear customer and allocations')
  failCustomer = true
  await change(customerSelect(), '2')
  await waitFor(() => document.querySelector('.receipt-allocation-error'))
  assert(saveButton().disabled, 'Failed debt loading must prevent saving as an unintended advance')
  failCustomer = false
  document.querySelector('.receipt-allocation-error button').click()
  await waitFor(() => !document.querySelector('.receipt-allocation-error') && !saveButton().disabled)

  await change(storeSelect(), '1')
  delayCustomer = true
  await change(customerSelect(), '1')
  await change(storeSelect(), '2')
  await change(customerSelect(), '2')
  await pause(400)
  assert(checks().length === 0 && customerSelect().value === '2', 'Stale customer responses must not replace the current customer debt')
  delayCustomer = false
  await change(storeSelect(), '1')
  await change(customerSelect(), '1')
  await waitFor(() => checks().length === 3)
  auto()
  await settle()
  const dialog = document.querySelector('.supplier-finance-dialog').getBoundingClientRect()
  assert(dialog.left >= 0 && dialog.right <= innerWidth + 1, 'The modal must fit the viewport')
  const scroll = document.querySelector('.receipt-allocation-scroll')
  assert(scroll.getBoundingClientRect().right <= dialog.right, 'The debt table must scroll inside the modal on mobile')
  assert(result.errors.length === 0, 'The component must not report Vue errors')
  result.checks.push('store/customer linkage', 'load failure and retry', 'stale request rejection', 'responsive modal')
  result.pass = true
} catch (error) { result.errors.push(String(error.stack || error)); result.pass = false }
document.querySelector('#result').textContent = JSON.stringify(result)
</script></body></html>`

const profile = await mkdtemp(join(tmpdir(), 'receipt-allocation-check-'))
const server = await createServer({
  root,
  server: { host: '127.0.0.1', port: 0, open: false },
  plugins: [{
    name: 'receipt-allocation-check',
    configureServer(server) {
      server.middlewares.use('/__receipt-check', async (req, res, next) => {
        try {
          res.setHeader('Content-Type', 'text/html; charset=utf-8')
          res.end(await server.transformIndexHtml('/__receipt-check', html))
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
    '--remote-allow-origins=*',
    '--user-data-dir=' + profile, '--window-size=' + (mobile ? '390,844' : '1440,1000'),
    '--remote-debugging-port=0', 'http://127.0.0.1:' + port + '/__receipt-check'
  ], { windowsHide: true })
  let stderr = ''
  child.stderr.on('data', data => { stderr += data })
  const closed = new Promise((resolve, reject) => { child.once('error', reject); child.once('close', resolve) })
  let socket
  try {
    let debugPort
    for (let i = 0; i < 100 && !debugPort; i++) {
      try { debugPort = Number((await readFile(join(profile, 'DevToolsActivePort'), 'utf8')).split('\n')[0]) }
      catch { await new Promise(resolve => setTimeout(resolve, 100)) }
    }
    if (!debugPort) throw new Error('Chrome failed to start: ' + stderr.slice(-2000))
    const targets = await (await fetch('http://127.0.0.1:' + debugPort + '/json/list')).json()
    socket = new WebSocket(targets.find(target => target.type === 'page').webSocketDebuggerUrl)
    await Promise.race([new Promise((resolve, reject) => {
      socket.addEventListener('open', resolve, { once: true })
      socket.addEventListener('error', reject, { once: true })
    }), new Promise((_, reject) => setTimeout(() => reject(new Error('Chrome DevTools connection timed out')), 10000))])
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
    for (let i = 0; i < 200; i++) {
      const response = await send('Runtime.evaluate', { expression: 'document.querySelector("#result")?.textContent', returnByValue: true })
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
  if (!resolve(profile).toLowerCase().startsWith((resolve(tmpdir()) + sep).toLowerCase())) throw new Error('Refusing cleanup outside the temp directory')
  await rm(profile, { recursive: true, force: true, maxRetries: 5, retryDelay: 200 })
}
