import { spawn } from 'node:child_process'
import { existsSync } from 'node:fs'
import { mkdtemp, readFile, rm } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join, resolve, sep } from 'node:path'
import { fileURLToPath } from 'node:url'
import { createServer } from 'vite'

// Run from the repository root: node tests/browser/material_display_stock_history.mjs
const root = fileURLToPath(new URL('../../', import.meta.url))
const browserPath = [
  process.env.CHROME_BIN,
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
  '/usr/bin/chromium'
].find(path => path && existsSync(path))
if (!browserPath) throw new Error('Set CHROME_BIN to an installed Chromium browser')

const html = `<!doctype html><html><head><meta charset="utf-8"></head><body>
<div id="app"></div><pre id="result">pending</pre><script type="module">
import { createApp, nextTick } from 'vue'
import MaterialDisplay from '/src/views/front/MaterialDisplay.vue'
import request from '/src/api/request.js'

const result = { errors: [], checks: [] }
window.addEventListener('error', event => result.errors.push(event.message))
window.addEventListener('unhandledrejection', event => result.errors.push(String(event.reason)))
window.EventSource = class { addEventListener() {} close() {} }
const assert = (condition, message) => { if (!condition) throw new Error(message) }
const pause = () => new Promise(resolve => setTimeout(resolve, 50))
const item = (quantity, stockBefore, stockAfter, lineNo = 1) => ({
  productId: 1, productCode: 'M1', productName: 'Test material', unit: 'kg',
  quantity, stockBefore, stockAfter, lineNo
})
const record = (id, documentNo, status, items) => ({
  id, documentNo, status, documentDate: '2026-11-13',
  createdAt: '2026-11-13 08:00:00', warehouseId: 1, storeId: 1,
  totalQuantity: items.reduce((sum, row) => sum + row.quantity, 0), items
})
let recordData = [
  record(1, 'HISTORY', 'reviewed', [item(20, 100, 80, 1), item(30, 80, 50, 2)]),
  record(2, 'ZERO', 'posted', [item(100, 100, 0)]),
  record(3, 'LEGACY', 'reviewed', [item(20, null, null)]),
  record(4, 'EMPTY-SNAPSHOT', 'reviewed', [item(20, '', '')]),
  record(5, 'DRAFT-OLDER', 'draft', [item(10)]),
  record(6, 'DRAFT-NEWER', 'draft', [item(15)])
]
let liveStock = 500
let failStock = false
request.defaults.adapter = async config => {
  let data
  if (config.url === '/health') data = { serverDate: '2026-11-13' }
  else if (config.url === '/material-outbounds') data = recordData
  else if (config.url === '/stock-balances') {
    if (failStock) throw new Error('Simulated stock service failure')
    data = [
      { productId: 1, warehouseId: 1, storeId: 1, productType: 'raw-material', quantity: liveStock },
      { productId: 1, warehouseId: 2, storeId: 1, productType: 'raw-material', quantity: 9999 }
    ]
  } else if (config.url === '/material-outbound-settings') data = { allowedProductIds: [1] }
  else throw new Error('Unexpected request: ' + config.url)
  return { data, status: 200, statusText: 'OK', headers: {}, config }
}
let app
let display
const mount = async () => {
  app = createApp(MaterialDisplay)
  app.config.errorHandler = error => result.errors.push(String(error.stack || error))
  display = app.mount('#app')
  for (let count = 0; count < 100 && !document.querySelector('.material-card'); count++) await pause()
  await nextTick()
}
const card = documentNo => [...document.querySelectorAll('.material-card')].find(element =>
  element.querySelector('.card-document-no').textContent.trim() === documentNo
)
const balance = documentNo => card(documentNo).querySelector('.stock-balance strong').firstChild.textContent.trim()
const refresh = async () => { await display.refresh(); await nextTick() }
const assertHistory = () => {
  assert(balance('HISTORY-01') === '80' && balance('HISTORY-02') === '50', 'Each reviewed line must show its own historical balance')
  assert(balance('ZERO') === '0', 'A saved zero must remain a known historical balance')
  assert(balance('LEGACY') === '-' && balance('EMPTY-SNAPSHOT') === '-', 'Missing historical snapshots must never fall back to live stock or zero')
  assert(card('LEGACY').textContent.includes('历史库存未记录'), 'Old records must explain why their historical balance is unknown')
  assert(card('HISTORY-01').textContent.includes('100 - 20 = 80'), 'Reviewed calculations must use the saved pre-audit stock')
  assert(card('HISTORY-01').querySelector('.stock-balance .column-label').textContent === '审核后剩余库存', 'Reviewed balances must identify the time of the balance')
}
try {
  await mount()
  assertHistory()
  assert(balance('DRAFT-NEWER') === '485' && balance('DRAFT-OLDER') === '475', 'Draft balances must still use live stock and pending deductions')
  liveStock = 750
  await refresh()
  assertHistory()
  assert(balance('DRAFT-NEWER') === '735' && balance('DRAFT-OLDER') === '725', 'Only draft estimates must change when stock changes')
  app.unmount()
  await mount()
  assertHistory()
  failStock = true
  await refresh()
  assertHistory()
  assert(balance('DRAFT-NEWER') === '-', 'Draft estimates must be unknown when live stock is unavailable')
  failStock = false
  recordData = recordData.map(row => row.documentNo === 'HISTORY'
    ? { ...row, status: 'draft', items: row.items.map(value => ({ ...value, stockBefore: null, stockAfter: null })) }
    : row)
  await refresh()
  assert(card('HISTORY-01').querySelector('.stock-balance .column-label').textContent === '预计剩余库存', 'Reversed records must return to live estimates')
  assert(balance('HISTORY-01') === '705', 'Reversed lines must deduct from the current stock estimate')
  recordData = recordData.map(row => row.documentNo === 'HISTORY'
    ? { ...row, status: 'reviewed', items: [item(20, 750, 730, 1), item(30, 730, 700, 2)] }
    : row)
  await refresh()
  assert(balance('HISTORY-01') === '730' && balance('HISTORY-02') === '700', 'Re-audited lines must use their new snapshots')
  recordData = recordData.filter(row => row.documentNo === 'HISTORY')
  liveStock = 900
  await refresh()
  assert(balance('HISTORY-01') === '730' && balance('HISTORY-02') === '700', 'Historical balances must not depend on other visible records or current stock')
  assert(result.errors.length === 0, 'Rendering and refresh must not report runtime errors')
  result.checks = ['per-line snapshots', 'zero balance', 'missing legacy history', 'live draft estimates', 'stock changes', 'remount', 'live stock unavailable', 'reverse and re-audit', 'filtered history']
  result.pass = true
} catch (error) {
  result.errors.push(String(error.stack || error))
  result.pass = false
}
document.querySelector('#result').textContent = JSON.stringify(result)
app?.unmount()
</script></body></html>`

const profile = await mkdtemp(join(tmpdir(), 'material-stock-history-'))
const server = await createServer({
  root,
  server: { host: '127.0.0.1', port: 0, open: false },
  plugins: [{
    name: 'material-stock-history-check',
    configureServer(server) {
      server.middlewares.use('/__material-stock-history-check', async (req, res, next) => {
        try {
          res.setHeader('Content-Type', 'text/html; charset=utf-8')
          res.end(await server.transformIndexHtml('/__material-stock-history-check', html))
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
    '--user-data-dir=' + profile, '--window-size=1600,900', '--remote-debugging-port=0',
    'http://127.0.0.1:' + port + '/__material-stock-history-check'
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
    await new Promise((resolve, reject) => {
      const timer = setTimeout(() => reject(new Error('Chrome DevTools connection timed out')), 10000)
      socket.addEventListener('open', () => { clearTimeout(timer); resolve() }, { once: true })
      socket.addEventListener('error', error => { clearTimeout(timer); reject(error) }, { once: true })
    })
    let nextId = 0
    const send = (method, params = {}) => new Promise((resolve, reject) => {
      const id = ++nextId
      const timer = setTimeout(() => {
        socket.removeEventListener('message', receive)
        reject(new Error('Chrome command timed out: ' + method))
      }, 10000)
      const receive = event => {
        const response = JSON.parse(event.data)
        if (response.id !== id) return
        clearTimeout(timer)
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
    console.log('material-stock-history: ' + (result || stderr.slice(-2000)))
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
