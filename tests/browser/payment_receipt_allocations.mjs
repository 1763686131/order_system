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
let includeMoreDocuments = false
let saved = null
request.defaults.adapter = async config => {
  let data
  if (config.url === '/stores') data = stores
  else if (config.url === '/customers') data = customers
  else if (config.url === '/bank-accounts/options') data = { items: [{ id: 1, storeId: 1, accountName: 'Bank', isDefault: true }] }
  else if (config.url === '/payment-receipts/next-number') data = { documentNo: 'SK-TEST' }
  else if (config.url === '/customers/1/receivable-documents') {
    if (delayCustomer) await pause(300)
    const extraDocuments = includeMoreDocuments
      ? Array.from({ length: 10 }, (_, index) => ({
        sourceType: 'order', sourceId: 200 + index, documentNo: 'SO-EXTRA-' + (index + 1),
        documentDate: '2025-04-' + String(index + 1).padStart(2, '0'), amount: 20, outstandingAmount: 20
      }))
      : []
    data = { receivable: 230 + extraDocuments.length * 20, items: [...documents, ...extraDocuments] }
  } else if (config.url === '/customers/2/receivable-documents') {
    if (failCustomer) throw new Error('Simulated debt loading failure')
    data = { receivable: 0, items: [] }
  } else if ((config.url === '/payment-receipts' && config.method === 'post') || (config.url === '/payment-receipts/1' && config.method === 'put')) {
    const payload = JSON.parse(config.data)
    const writeoffAmount = payload.allocationMode === 'manual'
      ? payload.allocations.reduce((sum, row) => sum + row.amount, 0)
      : Math.min(230, payload.paymentAmount + payload.discountAmount)
    saved = { ...payload, id: 1, documentNo: 'SK-TEST', storeId: 1, storeName: 'Store A',
      customerName: 'Customer A', status: 'draft',
      writeoffAmount, advanceAmount: payload.paymentAmount - (writeoffAmount - payload.discountAmount) }
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
const autoHint = () => document.querySelector('.receipt-auto-allocation-hint')
const amounts = () => [...document.querySelectorAll('.receipt-allocation-amount')].map(cell => Number(cell.textContent.replace(/[^0-9.]/g, '')))
const change = async (element, value) => { element.value = value; element.dispatchEvent(new Event('change', { bubbles: true })); await settle() }
const input = async (element, value) => { element.value = value; element.dispatchEvent(new Event('input', { bubbles: true })); await settle() }
const modeButton = mode => document.querySelectorAll('.receipt-allocation-mode button')[mode === 'fifo' ? 0 : 1]
const auto = () => modeButton('fifo').click()
const summaryAmount = index => Number(document.querySelectorAll('.sf-summary strong')[index].textContent.replace(/[^0-9.]/g, ''))
const toggleCheck = async index => { checks()[index].click(); await settle() }
const submit = async () => {
  form().dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }))
  await waitFor(() => !form())
}
const edit = async () => {
  document.querySelector('.action-edit').click()
  await waitFor(() => saved?.allocationMode === 'manual' ? checks().length === 3 : Boolean(autoHint()))
}
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
  await waitFor(() => Boolean(autoHint()))
  assert(modeButton('fifo').getAttribute('aria-pressed') === 'true' && !document.querySelector('.receipt-allocation-table'), 'Automatic mode must be the default and hide the document list')
  assert(form().querySelector('.receipt-debt').value.replace(/[^0-9.]/g, '') === '230.00', 'Debt must refresh from the document endpoint')
  await input(form().querySelectorAll('input[type=number]')[0], '100')
  assert(summaryAmount(1) === 100, 'Automatic allocation must run when the amount is entered, without clicking a button')
  await input(form().querySelectorAll('input[type=number]')[0], '200')
  assert(summaryAmount(1) === 200, 'Automatic allocation must follow amount changes and partially cover the final document')
  await input(form().querySelectorAll('input[type=number]')[0], '300')
  assert(summaryAmount(1) === 230 && summaryAmount(2) === 70, 'Excess automatic payment must become an advance')
  await submit()
  assert(saved.allocationMode === 'fifo' && saved.allocations.length === 0 && saved.advanceAmount === 70, 'Saving must preserve automatic mode and its advance')
  await edit()
  assert(modeButton('fifo').getAttribute('aria-pressed') === 'true' && !document.querySelector('.receipt-allocation-table'), 'Editing an automatic draft must restore automatic mode without showing documents')
  await input(form().querySelectorAll('input[type=number]')[0], '100')
  modeButton('manual').click()
  await settle()
  await waitFor(() => checks().length === 3)
  assert(checks().every(box => !box.disabled), 'Manual mode must allow editing the current selection')
  await toggleCheck(0)
  await toggleCheck(1)
  assert(summaryAmount(2) === 100, 'An empty manual selection must leave all cash as an advance: ' + JSON.stringify({ amounts: amounts(), summary: [...document.querySelectorAll('.sf-summary strong')].map(item => item.textContent), checked: checks().map(box => box.checked) }))
  await toggleCheck(2)
  assert(JSON.stringify(amounts()) === '[0,0,100]', 'Manual selection must allocate only against the checked document')
  await toggleCheck(0)
  assert(JSON.stringify(amounts()) === '[0,0,100]', 'Manual selection must preserve the order in which documents were checked')
  await toggleCheck(0)
  await input(form().querySelectorAll('input[type=number]')[0], '120')
  assert(JSON.stringify(amounts()) === '[0,0,100]' && summaryAmount(2) === 20, 'Manual amount changes must keep the selection and convert leftover cash into an advance')
  await input(form().querySelectorAll('input[type=number]')[1], '10')
  assert(summaryAmount(2) === 30, 'Manual discount must reduce cash writeoff without spending the remaining advance')
  await submit()
  assert(saved.allocationMode === 'manual' && saved.allocations.length === 1 && saved.allocations[0].sourceId === 103 && saved.advanceAmount === 30, 'Saving must persist manual selections and their advance')
  await edit()
  assert(modeButton('manual').getAttribute('aria-pressed') === 'true' && JSON.stringify(amounts()) === '[0,0,100]', 'Editing a manual draft must restore its mode and selection')
  auto()
  await waitFor(() => Boolean(autoHint()) && !document.querySelector('.receipt-allocation-table'))
  assert(summaryAmount(1) === 130, 'Switching back to automatic mode must restore oldest-first allocation and hide documents')
  await input(form().querySelectorAll('input[type=number]')[0], '100')
  assert(summaryAmount(1) === 110, 'Discount must be included in automatic receivable reduction')
  await submit()
  assert(saved.allocationMode === 'fifo' && saved.allocations.length === 0, 'Saving after a mode change must clear old manual allocations')
  await edit()
  assert(!document.querySelector('.receipt-allocation-table'), 'Editing must restore automatic mode and keep the document list hidden')
  result.checks.push('automatic default', 'live oldest-first allocation', 'manual mode and selection', 'surplus advance in both modes', 'partial allocation', 'discount', 'save and edit both modes')

  await change(storeSelect(), '2')
  assert(customerSelect().value === '' && checks().length === 0 && modeButton('fifo').getAttribute('aria-pressed') === 'true', 'Store changes must clear customer and allocations and default to automatic mode')
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
  await waitFor(() => Boolean(autoHint()))
  modeButton('manual').click()
  await waitFor(() => checks().length === 3)
  includeMoreDocuments = true
  await change(storeSelect(), '2')
  await change(storeSelect(), '1')
  await change(customerSelect(), '1')
  await waitFor(() => checks().length === 10 && document.querySelector('.receipt-allocation-pagination'))
  assert(document.querySelectorAll('.receipt-allocation-table tbody tr').length === 10, 'The allocation list must show ten rows on its first page')
  assert(document.querySelector('.receipt-allocation-pagination .page-number').textContent.trim() === '1 / 2', 'The allocation pager must show the current and total page')
  document.querySelector('[aria-label="抵扣明细下一页"]').click()
  await settle()
  assert(document.querySelectorAll('.receipt-allocation-table tbody tr').length === 3 && document.querySelector('.receipt-allocation-table tbody tr:first-child').textContent.includes('SO-EXTRA-8'), 'The next page must show the remaining allocation documents')
  document.querySelector('[aria-label="抵扣明细上一页"]').click()
  await settle()
  assert(document.querySelectorAll('.receipt-allocation-table tbody tr').length === 10, 'The previous-page control must return to the first ten documents')
  result.checks.push('ten rows per page', 'allocation pagination')
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
