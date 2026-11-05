import assert from 'node:assert/strict'
import { spawn } from 'node:child_process'
import { existsSync } from 'node:fs'
import { mkdir, mkdtemp, readFile, rm, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join, resolve, sep } from 'node:path'
import { fileURLToPath } from 'node:url'
import { createServer } from 'vite'

// Uses fixture HTML from a stub print designer, real PNG capture, and the real preview components.
const root = fileURLToPath(new URL('../../', import.meta.url))
const browserPath = [
  process.env.CHROME_BIN,
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
  '/usr/bin/chromium',
  '/usr/bin/google-chrome'
].find(path => path && existsSync(path))
if (!browserPath) throw new Error('Set CHROME_BIN to an installed Chromium browser')

const designerStub = `
class FixtureDesigner extends HTMLElement {
  connectedCallback() { queueMicrotask(() => this.dispatchEvent(new Event('ready'))) }
  setLanguage() {}
  loadTemplateData() {}
  setTestData() {}
  setTemplateVariables() {}
  setVariables(variables) { this.variables = variables }
  getPreviewHtml() {
    return [1, 2].map(page => '<section class="print-page" style="box-sizing:border-box;width:600px;height:850px;padding:24px;background:white;position:relative;margin-bottom:16px;font-family:Arial,sans-serif">' +
      '<header style="height:64px;background:' + (page === 1 ? '#0f9f78' : '#1876d2') + ';color:white;padding:12px;font-size:24px;box-sizing:border-box">销售单 / SALES ORDER</header>' +
      '<h2 style="position:absolute;left:24px;top:100px;margin:0">' + this.variables.orderNumber + '</h2>' +
      '<p style="position:absolute;left:24px;top:140px;margin:0">客户 / Customer: 示例门店</p>' +
      '<table style="position:absolute;left:24px;top:200px;width:552px;table-layout:fixed;border-collapse:collapse;font-size:16px"><thead><tr style="height:32px"><th>商品 / Product</th><th>数量</th><th>金额</th></tr></thead><tbody>' +
      Array.from({ length: 12 }, (_, i) => '<tr style="height:32px;border-bottom:1px solid #ddd"><td>商品 ' + (i + 1) + '</td><td>10</td><td>100.00</td></tr>').join('') +
      '</tbody></table>' +
      '<div data-fixture-signoff style="position:absolute;top:640px;left:24px;right:24px;height:32px;background:#0f766e;color:white">制单人 / 业务员 / 电话</div>' +
      '<p style="position:absolute;left:24px;top:700px;margin:0">第 ' + page + ' 页 / Page ' + page + '</p>' +
      '<div style="position:absolute;bottom:24px;left:24px;right:24px;height:32px;background:#cf304a;color:white">单据末尾 / END OF PAGE</div></section>').join('')
  }
}
customElements.define('print-designer', FixtureDesigner)
`

const html = `<!doctype html><html lang="zh-CN"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
* { box-sizing: border-box; }
html, body { margin: 0; font-family: Arial, sans-serif; user-select: none; touch-action: pan-y; }
</style></head><body><div id="app"></div><pre id="result">pending</pre>
<script type="module">
import { createApp, h, ref, nextTick } from 'vue'
import { createRouter, createWebHistory, RouterView } from 'vue-router'
import OrderPrintPreview from '/src/components/print/OrderPrintPreview.vue'
const scenario = new URLSearchParams(location.search).get('scenario')
const result = { checks: [], errors: [], shares: 0, copies: 0 }
window.addEventListener('error', event => result.errors.push(event.message))
window.addEventListener('unhandledrejection', event => result.errors.push(String(event.reason)))
const assert = (condition, message) => { if (!condition) throw new Error(message) }
const waitFor = async (read, message) => {
  for (let i = 0; i < 200; i++) {
    if (read()) return read()
    await new Promise(resolve => setTimeout(resolve, 50))
  }
  throw new Error(message)
}
const settle = async () => { await nextTick(); await new Promise(resolve => requestAnimationFrame(resolve)) }
const mobile = scenario !== 'desktop'
Object.defineProperty(navigator, 'userAgent', { configurable: true, value: mobile
  ? 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X)' + (['wechat', 'back', 'back-skip'].includes(scenario) ? ' MicroMessenger/8.0' : ' Safari/605.1')
  : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)' })
let duringTap = false
document.addEventListener('click', () => {
  duringTap = true
  queueMicrotask(() => { duringTap = false })
}, true)
Object.defineProperty(navigator, 'canShare', { configurable: true, value: () => true })
Object.defineProperty(navigator, 'share', { configurable: true, value: scenario === 'no-api' ? undefined : data => {
  assert(duringTap, 'Native sharing must start during the click')
  result.shares++
  assert(data.files.length === 1 && data.files[0].type === 'image/png', 'Must share the actual PNG')
  if (scenario === 'denied') return Promise.reject(new DOMException('Denied', 'NotAllowedError'))
  if (scenario === 'cancel') return Promise.reject(new DOMException('Cancelled', 'AbortError'))
  return Promise.resolve()
} })
Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { write: async items => {
  result.copies++
  assert(items[0].data['image/png'].type === 'image/png', 'Desktop must copy the image')
} } })
window.ClipboardItem = class { constructor(data) { this.data = data } }
localStorage.setItem('order-system-print-client-config', JSON.stringify({ mode: 'browser' }))
const visible = ref(true)
const variables = ref({ orderNumber: 'PRINT-001', items: [] })
const template = { id: 1, name: '销售单模板', pageWidth: 159, pageHeight: 225,
  content: { canvasSize: { width: 600, height: 850 }, pages: [{ id: 'fixture', elements: [] }] } }
let sourceMounts = 0
const sourceComponent = { setup: () => {
  sourceMounts++
  return () => h(OrderPrintPreview, {
    visible: visible.value, template, variables: variables.value, documentNumber: variables.value.orderNumber,
    printEnabled: false, onClose: () => { visible.value = false }
  })
} }
const router = createRouter({
  history: createWebHistory(),
  routes: [{ path: '/:pathMatch(.*)*', component: sourceComponent }]
})
const app = createApp({ setup: () => () => h(RouterView, null, {
  default: ({ Component, route }) => h(Component, { key: route.fullPath })
}) })
app.config.errorHandler = error => result.errors.push(String(error.stack || error))
app.use(router)
await router.isReady()
const sourceUrl = location.href
const sourcePosition = history.state.position
app.mount('#app')
const shareButton = () => document.querySelector('.preview-share-button')
const preview = () => document.querySelector('.print-image-share')
const assertSource = () => {
  assert(location.href === sourceUrl, 'Dialog navigation must preserve the source URL, filters, and hash')
  assert(sourceMounts === 1, 'Dialog navigation must not remount a fullPath-keyed document form')
}
try {
  await waitFor(() => shareButton() && !shareButton().disabled, 'PNG preparation must finish')
  assertSource()
  assert(history.state.position === sourcePosition + 1, 'Print preview must reserve one back step')
  const paperDocument = document.querySelector('.preview-frame').contentDocument
  const paperContent = paperDocument.getElementById('preview-paper-content')
  const paperViewport = paperDocument.getElementById('preview-paper-viewport')
  const firstPaper = paperContent.querySelector('.print-page')
  const paperStyle = paperDocument.defaultView.getComputedStyle(firstPaper)
  assert(paperViewport && (!paperContent.style.zoom || paperContent.style.zoom === '1'), 'Preview must scale visually without changing paper layout through zoom')
  assert(paperStyle.getPropertyValue('text-size-adjust') === '100%' ||
    paperStyle.getPropertyValue('-webkit-text-size-adjust') === '100%', 'Paper text must retain the template size on mobile')
  const table = firstPaper.querySelector('table')
  const signoff = firstPaper.querySelector('[data-fixture-signoff]')
  assert(table.offsetTop + table.offsetHeight < signoff.offsetTop, 'The fixed signoff must remain below the table')
  assert(firstPaper.offsetWidth === 600 && firstPaper.offsetHeight === 850, 'Paper layout dimensions must stay independent of the screen')
  const scale = Number.parseFloat(paperViewport.style.width) / firstPaper.offsetWidth
  assert(Math.abs(firstPaper.getBoundingClientRect().width - firstPaper.offsetWidth * scale) < 1, 'Visual preview must fit its reserved viewport')
  assert(paperViewport.getBoundingClientRect().right <= paperDocument.documentElement.clientWidth, 'Scaled paper must fit the mobile preview')
  assert(paperDocument.documentElement.scrollWidth <= paperDocument.documentElement.clientWidth + 1, 'Unscaled paper must not leave horizontal overflow in the preview')
  result.checks.push('unscaled paper layout and fixed signoff', 'mobile text size', 'visual preview scaling')
  shareButton().focus()
  shareButton().click()
  if (['native', 'cancel', 'desktop'].includes(scenario)) {
    await settle()
    assert(!preview(), 'Native success/cancellation and desktop copies must not open a preview')
    assert(result.copies === (mobile ? 0 : 1), 'Only the desktop copies to clipboard')
    assert(result.shares === (mobile ? 1 : 0), 'Only mobile native sharing calls navigator.share')
    const status = document.querySelector('.order-print-preview-footer [role=status]').textContent
    assert(!status.includes('失败'), 'Cancellation must not be an error')
    if (scenario === 'cancel') assert(!status.includes('已交给'), 'Cancellation must not report success')
    result.checks.push('native result/cancellation', 'desktop copy isolation')
    if (scenario === 'native') {
      history.back()
      await waitFor(() => !document.querySelector('.order-print-preview-overlay'), 'Back must close the print preview')
      assertSource()
      assert(history.state.position === sourcePosition, 'Closing the preview must restore the original history position')
      result.checks.push('back returns to the source page')
    }
  } else {
    const layer = await waitFor(preview, 'Mobile fallback must open')
    const image = layer.querySelector('img')
    await image.decode()
    await settle()
    assertSource()
    assert(history.state.position === sourcePosition + 2, 'Image share must reserve a second back step')
    if (scenario === 'back-skip') {
      history.go(-2)
      await waitFor(() => !preview() && !document.querySelector('.order-print-preview-overlay'), 'Skipping both history entries must close both dialogs')
      assertSource()
      assert(history.state.position === sourcePosition, 'Skipping dialogs must stop at the source page')
      result.checks.push('multi-step back returns to the source page')
    } else if (scenario === 'back') {
      history.back()
      await waitFor(() => !preview(), 'First back must close the image share page')
      assert(document.querySelector('.order-print-preview-overlay'), 'First back must leave the print preview open')
      assertSource()
      assert(history.state.position === sourcePosition + 1, 'First back must consume only the image entry')
      history.back()
      await waitFor(() => !document.querySelector('.order-print-preview-overlay'), 'Second back must close the print preview')
      assertSource()
      assert(history.state.position === sourcePosition, 'Second back must restore the original history position')
      visible.value = true
      await waitFor(() => shareButton() && !shareButton().disabled, 'Print preview must reopen after back')
      document.querySelector('.preview-close').click()
      await nextTick()
      assert(!document.querySelector('.order-print-preview-overlay'), 'Close button must dismiss the print preview immediately')
      await waitFor(() => history.state.position === sourcePosition, 'Close button must consume the print history entry')
      assertSource()
      result.checks.push('back closes image share before print preview', 'back preserves the source route and document form', 'reopen and close-button history cleanup')
    } else {
    assert(image.naturalWidth === 1200 && image.naturalHeight === 3400, 'PNG must include both full pages')
    const canvas = document.createElement('canvas')
    canvas.width = image.naturalWidth
    canvas.height = image.naturalHeight
    const context = canvas.getContext('2d')
    context.drawImage(image, 0, 0)
    const pixel = (x, y) => [...context.getImageData(x, y, 1, 1).data]
    assert(pixel(55, 55).slice(0, 3).join(',') === '15,159,120', 'First page must render its green band')
    assert(pixel(55, 1290).slice(0, 3).join(',') === '15,118,110', 'Fixed signoff must retain its template position in the PNG')
    assert(pixel(55, 1755).slice(0, 3).join(',') === '24,118,210', 'Second page must render its blue band')
    assert(pixel(55, 2990).slice(0, 3).join(',') === '15,118,110', 'Second page signoff must retain its template position in the PNG')
    assert(pixel(55, 3340).slice(0, 3).join(',') === '207,48,74', 'The last page footer must not be cut off')
    const underlying = document.querySelector('.order-print-preview-dialog')
    assert(underlying.inert && underlying.getAttribute('aria-hidden') === 'true', 'Underlying dialog must be inactive')
    assert(document.body.style.overflow === 'hidden', 'Background scrolling must be locked')
    assert(document.elementFromPoint(20, 20).closest('.print-image-share'), 'Image dialog must be above the print preview')
    assert(document.activeElement.getAttribute('aria-label') === '返回打印预览', 'Focus must enter the image dialog')
    const contextMenu = new MouseEvent('contextmenu', { bubbles: true, cancelable: true })
    assert(image.dispatchEvent(contextMenu), 'Image long press/context menu must not be blocked')
    assert(getComputedStyle(image).webkitTouchCallout !== 'none', 'Image callout must remain enabled')
    for (const control of layer.querySelectorAll('button, a')) {
      const rect = control.getBoundingClientRect()
      assert(rect.left >= 0 && rect.right <= innerWidth + 1 && rect.bottom <= innerHeight + 1, 'All controls must fit')
    }
    const save = layer.querySelector('a[download]')
    assert(save.download === '销售单模板 - PRINT-001.png', 'Saving must use the current document filename')
    const oldUrl = save.href
    const download = await fetch(oldUrl)
    assert(download.ok && (await download.blob()).type === 'image/png', 'Save link must point to a real PNG')
    const area = layer.querySelector('.image-share-body')
    assert(area.scrollHeight > area.clientHeight, 'Long images must scroll')
    layer.querySelector('[aria-label="查看原图"]').click()
    await settle()
    assert(image.offsetWidth === image.naturalWidth && area.scrollWidth > area.clientWidth, 'Original size must allow horizontal scrolling')
    area.scrollLeft = 100
    assert(area.scrollLeft > 0, 'Original image can be panned horizontally')
    layer.querySelector('[aria-label="适应屏幕"]').click()
    await settle()
    assert(image.offsetWidth <= innerWidth && area.scrollLeft === 0, 'Fit mode must reset horizontal scrolling')
    if (scenario === 'denied') {
      assert(layer.textContent.includes('系统分享暂时不可用'), 'Share rejection must open the fallback')
      assert([...layer.querySelectorAll('button')].some(button => button.textContent.includes('系统分享')), 'Supported browsers must offer retry')
    } else {
      assert(result.shares === 0, 'WeChat/unsupported browsers must not call navigator.share')
    }
    window.captureReady = true
    await new Promise(resolve => { window.resumeAfterCapture = resolve })
    layer.querySelector('[aria-label="返回打印预览"]').click()
    await nextTick()
    assert(!preview() && !underlying.inert, 'Closing only the image must keep the print preview')
    shareButton().click()
    await waitFor(preview, 'Image must reopen after the pending back navigation finishes')
    await waitFor(() => history.state.position === sourcePosition + 2, 'Rapid reopening must retain the image back step')
    preview().querySelector('[aria-label="返回打印预览"]').click()
    await nextTick()
    await waitFor(() => history.state.position === sourcePosition + 1, 'Closing the image must consume its history entry')
    await settle()
    assert(document.activeElement === shareButton(), 'Focus must return to the share button')
    assert(document.body.style.overflow === '', 'Closing must restore scrolling')
    shareButton().click()
    await waitFor(preview, 'Preview must reopen from the cached image')
    variables.value = { ...variables.value, orderNumber: 'PRINT-002' }
    await settle()
    assert(!preview(), 'Changing document data must close the stale image')
    assert(await fetch(oldUrl).then(() => false, () => true), 'Old Blob URL must be revoked')
    await waitFor(() => shareButton() && !shareButton().disabled, 'New document image must finish')
    shareButton().click()
    const nextLayer = await waitFor(preview, 'Updated image must be available')
    assert(nextLayer.querySelector('a[download]').download.includes('PRINT-002'), 'New document filename must replace the old one')
    visible.value = false
    await settle()
    assert(!preview() && !document.querySelector('.order-print-preview-overlay'), 'Closing the print window must close both dialogs')
    await waitFor(() => history.state.position === sourcePosition, 'Closing both dialogs must leave no extra back steps')
    assertSource()
    result.checks.push('real two-page PNG and pixel content', 'overlay ordering and focus', 'long-press menu allowed',
      'download PNG and filename', 'long image scrolling and zoom', 'mobile layout', 'close and document invalidation',
      'rapid reopening and history cleanup', 'preserved source URL and document form')
    }
  }
  assert(result.errors.length === 0, 'No Vue or browser runtime errors')
  result.pass = true
} catch (error) {
  result.errors.push(String(error.stack || error))
  result.pass = false
} finally {
  app.unmount()
  document.querySelector('#result').textContent = JSON.stringify(result)
}
</script></body></html>`

const profile = await mkdtemp(join(tmpdir(), 'print-share-check-'))
const screenshots = join(tmpdir(), 'order-system-browser-checks')
const server = await createServer({
  root,
  cacheDir: join(profile, 'vite-cache'),
  optimizeDeps: {
    noDiscovery: true,
    include: ['vue', 'vue-router', '@lucide/vue', 'html-to-image'],
    exclude: ['vue-print-designer']
  },
  server: { host: '127.0.0.1', port: 0, open: false },
  plugins: [{
    name: 'print-share-fixture',
    enforce: 'pre',
    resolveId(source) {
      if (source === 'vue-print-designer') return '\0print-share-designer'
      if (source === 'vue-print-designer/style.css') return '\0print-share-designer-style'
    },
    load(id) {
      if (id === '\0print-share-designer') return designerStub
      if (id === '\0print-share-designer-style') return ''
    },
    configureServer(server) {
      server.middlewares.use('/__print-image-share-check', async (req, res, next) => {
        try {
          res.setHeader('Content-Type', 'text/html; charset=utf-8')
          res.end(await server.transformIndexHtml('/__print-image-share-check', html))
        } catch (error) { next(error) }
      })
    }
  }]
})
let child
let closed
let socket
try {
  await server.listen()
  child = spawn(browserPath, [
    '--headless', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
    '--disable-background-networking', '--disable-extensions', '--disable-background-timer-throttling',
    '--user-data-dir=' + profile, '--window-size=1200,900', '--remote-debugging-port=0', 'about:blank'
  ], { windowsHide: true })
  let stderr = ''
  child.stderr.on('data', data => { stderr += data })
  closed = new Promise((resolve, reject) => {
    child.once('error', reject)
    child.once('close', resolve)
  })
  let debugPort
  for (let count = 0; count < 100 && !debugPort; count++) {
    try {
      debugPort = Number((await readFile(join(profile, 'DevToolsActivePort'), 'utf8')).split('\n')[0])
    } catch { await new Promise(resolve => setTimeout(resolve, 100)) }
  }
  if (!debugPort) throw new Error('Chrome failed to start: ' + stderr.slice(-2000))
  const targets = await (await fetch('http://127.0.0.1:' + debugPort + '/json/list')).json()
  socket = new WebSocket(targets.find(target => target.type === 'page').webSocketDebuggerUrl)
  await new Promise((resolve, reject) => {
    socket.addEventListener('open', resolve, { once: true })
    socket.addEventListener('error', reject, { once: true })
  })
  let nextId = 0
  const send = (method, params = {}) => new Promise((resolve, reject) => {
    const id = ++nextId
    const timeout = setTimeout(() => {
      socket.removeEventListener('message', receive)
      reject(new Error('CDP timed out: ' + method))
    }, 20000)
    const receive = event => {
      const response = JSON.parse(event.data)
      if (response.id !== id) return
      clearTimeout(timeout)
      socket.removeEventListener('message', receive)
      if (response.error) reject(new Error(JSON.stringify(response.error)))
      else resolve(response.result)
    }
    socket.addEventListener('message', receive)
    socket.send(JSON.stringify({ id, method, params }))
  })
  const evaluate = async expression => {
    const response = await send('Runtime.evaluate', { expression, returnByValue: true })
    return response.result?.value
  }
  await send('Page.enable')
  for (const [scenario, width, height] of [
    ['back', 390, 844], ['back-skip', 390, 844], ['wechat', 390, 844], ['wechat', 320, 568], ['wechat', 768, 1024],
    ['no-api', 390, 844], ['denied', 390, 844], ['native', 390, 844],
    ['cancel', 390, 844], ['desktop', 1440, 900]
  ]) {
    await send('Emulation.setDeviceMetricsOverride', {
      width, height, deviceScaleFactor: 1, mobile: scenario !== 'desktop'
    })
    await send('Page.navigate', {
      url: `http://127.0.0.1:${server.httpServer.address().port}/__print-image-share-check?scenario=${scenario}&status=unpaid&page=3#order-PRINT-001`
    })
    let result
    for (let count = 0; count < 400; count++) {
      if (await evaluate('window.captureReady')) {
        await mkdir(screenshots, { recursive: true })
        const screenshot = await send('Page.captureScreenshot', { format: 'png' })
        const path = join(screenshots, `print-share-${scenario}-${width}.png`)
        await writeFile(path, Buffer.from(screenshot.data, 'base64'))
        console.log('Screenshot: ' + path)
        await evaluate('window.captureReady = false; window.resumeAfterCapture()')
      }
      const text = await evaluate('document.querySelector("#result")?.textContent')
      if (text && text !== 'pending') {
        result = JSON.parse(text)
        break
      }
      await new Promise(resolve => setTimeout(resolve, 100))
    }
    console.log(`${scenario}-${width}: ${JSON.stringify(result || { pass: false, error: 'Timed out' })}`)
    assert.equal(result?.pass, true, `${scenario}-${width} failed`)
  }
  await send('Browser.close')
} finally {
  socket?.close()
  if (child && child.exitCode === null) child.kill()
  if (closed) await closed
  await server.close()
  if (!resolve(profile).startsWith(resolve(tmpdir()) + sep)) throw new Error('Refusing cleanup outside the temporary directory')
  await rm(profile, { recursive: true, force: true, maxRetries: 5, retryDelay: 200 })
}
