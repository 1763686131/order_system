import {
  getPrintClientConfig,
  getPrintConfigFromSdkUrl,
  getPrintSdkUrl,
  normalizePrintClientConfig
} from '@/utils/printClientConfig'

const SCRIPT_TIMEOUT = 5000
const DETECTION_TIMEOUT = 1800

let lodopLoader = null
let lodopLoaderUrl = ''
let activeSdkUrl = ''

const getLodopInstance = () => {
  try {
    if (typeof window.getCLodop === 'function') {
      const instance = window.getCLodop()
      if (instance) return instance
    }
  } catch {
    // Continue with the globals exposed by CLodopfuncs.js.
  }

  return window.CLODOP || window.LODOP || null
}

const isLodopAvailable = (lodop) => (
  lodop &&
  typeof lodop.PRINT_INIT === 'function' &&
  typeof lodop.SET_PRINT_PAGESIZE === 'function' &&
  typeof lodop.ADD_PRINT_HTM === 'function' &&
  typeof lodop.PREVIEW === 'function'
)

const loadSdkScript = (url, timeout = SCRIPT_TIMEOUT) => new Promise((resolve, reject) => {
  document
    .querySelectorAll('script[data-clodop-sdk]')
    .forEach((script) => {
      if (script.dataset.clodopSdk !== url) script.remove()
    })

  const script = document.createElement('script')
  const timer = window.setTimeout(() => {
    script.remove()
    reject(new Error(`连接打印服务超时：${url}`))
  }, timeout)

  script.src = url
  script.async = true
  script.dataset.clodopSdk = url
  script.onload = () => {
    window.clearTimeout(timer)
    const lodop = getLodopInstance()
    if (isLodopAvailable(lodop)) {
      activeSdkUrl = url
      resolve(lodop)
      return
    }
    script.remove()
    reject(new Error(`打印服务未返回有效接口：${url}`))
  }
  script.onerror = () => {
    window.clearTimeout(timer)
    script.remove()
    reject(new Error(`无法加载打印服务：${url}`))
  }

  document.head.appendChild(script)
})

export const getLodop = async (config = getPrintClientConfig()) => {
  const normalizedConfig = normalizePrintClientConfig(config)
  const sdkUrl = getPrintSdkUrl(normalizedConfig)
  const existing = getLodopInstance()
  if (isLodopAvailable(existing) && (!activeSdkUrl || activeSdkUrl === sdkUrl)) {
    activeSdkUrl = sdkUrl
    return existing
  }

  if (!lodopLoader || lodopLoaderUrl !== sdkUrl) {
    lodopLoaderUrl = sdkUrl
    lodopLoader = loadSdkScript(sdkUrl).catch((error) => {
      lodopLoader = null
      lodopLoaderUrl = ''
      throw error
    })
  }

  try {
    return await lodopLoader
  } catch (error) {
    throw new Error(
      `未连接到 C-Lodop 打印服务，请确认软件已启动，并检查服务地址 ${sdkUrl}。\n` +
      (error?.message || '')
    )
  }
}

const getPrinterProperty = (lodop, index, property) => {
  try {
    return String(lodop.GET_PRINTER_NAME(`${index}:${property}`) || '')
  } catch {
    return ''
  }
}

const readLocalPrinters = (lodop) => {
  if (
    typeof lodop.GET_PRINTER_COUNT !== 'function' ||
    typeof lodop.GET_PRINTER_NAME !== 'function'
  ) {
    throw new Error('当前 C-Lodop 版本不支持读取本地打印机列表。')
  }

  const count = Math.max(0, Number(lodop.GET_PRINTER_COUNT()) || 0)
  const defaultName = String(lodop.GET_PRINTER_NAME(-1) || '')
  const printers = []

  for (let index = 0; index < count; index += 1) {
    const name = String(lodop.GET_PRINTER_NAME(index) || '').trim()
    if (!name) continue

    printers.push({
      index,
      name,
      driverName: getPrinterProperty(lodop, index, 'DriverName'),
      portName: getPrinterProperty(lodop, index, 'PortName'),
      paperName: getPrinterProperty(lodop, index, 'FormName'),
      isDefault: name === defaultName
    })
  }

  return printers
}

export const getLocalPrinters = async (config = getPrintClientConfig()) => {
  const lodop = await getLodop(config)
  return readLocalPrinters(lodop)
}

const getDetectionSdkUrls = (config) => {
  const normalized = normalizePrintClientConfig(config)
  const hosts = [normalized.host, 'localhost', '127.0.0.1']
    .filter((host, index, values) => host && values.indexOf(host) === index)
  const candidates = [
    getPrintSdkUrl(normalized),
    ...hosts.flatMap(host => [
      `http://${host}:8000/CLodopfuncs.js?name=CLODOP`,
      `http://${host}:18000/CLodopfuncs.js?name=CLODOP`,
      `https://${host}:8443/CLodopfuncs.js?name=CLODOP`
    ])
  ]

  return candidates.filter((url, index, urls) => urls.indexOf(url) === index)
}

export const detectLodopService = async (config = getPrintClientConfig()) => {
  const errors = []

  for (const sdkUrl of getDetectionSdkUrls(config)) {
    try {
      const existing = getLodopInstance()
      const lodop = isLodopAvailable(existing) && activeSdkUrl === sdkUrl
        ? existing
        : await loadSdkScript(sdkUrl, DETECTION_TIMEOUT)
      const detectedConfig = getPrintConfigFromSdkUrl(sdkUrl, config)

      return {
        config: detectedConfig,
        printers: readLocalPrinters(lodop),
        version: String(lodop.VERSION || '')
      }
    } catch (error) {
      errors.push(error?.message || String(error))
    }
  }

  throw new Error(
    '未检测到 C-Lodop 服务，请确认软件已启动。' +
    (errors.length ? `\n${errors.join('\n')}` : '')
  )
}

const normalizePageSize = (value, fallback) => {
  const size = Number(value)
  return Number.isFinite(size) && size > 0 ? size : fallback
}

const escapeAttribute = (value) => String(value || '')
  .replace(/&/g, '&amp;')
  .replace(/"/g, '&quot;')
  .replace(/</g, '&lt;')
  .replace(/>/g, '&gt;')

const LODOP_VERTICAL_PUNCTUATION = {
  '(': '︵',
  ')': '︶',
  '（': '︵',
  '）': '︶',
  '[': '﹇',
  ']': '﹈',
  '［': '﹇',
  '］': '﹈',
  '〔': '︹',
  '〕': '︺',
  '【': '︻',
  '】': '︼',
  '{': '︷',
  '}': '︸',
  '｛': '︷',
  '｝': '︸',
  '〈': '︿',
  '〉': '﹀',
  '《': '︽',
  '》': '︾',
  '，': '︐',
  '、': '︑',
  '。': '︒',
  '：': '︓',
  '；': '︔',
  '！': '︕',
  '？': '︖',
  '…': '︙'
}

const getLodopVerticalCharacter = (character) => (
  LODOP_VERTICAL_PUNCTUATION[character] || character
)

const normalizeLodopVerticalText = (html) => {
  if (typeof DOMParser === 'undefined') return html

  const printDocument = new DOMParser().parseFromString(
    `<body>${String(html || '')}</body>`,
    'text/html'
  )

  printDocument.body
    .querySelectorAll('[data-lodop-vertical-wrapper="true"]')
    .forEach((wrapper) => {
      wrapper.style.setProperty('writing-mode', 'horizontal-tb', 'important')
      wrapper.style.setProperty('-webkit-writing-mode', 'horizontal-tb', 'important')
      wrapper.style.removeProperty('text-orientation')
      wrapper.removeAttribute('data-lodop-vertical-wrapper')
    })

  printDocument.body
    .querySelectorAll('[data-lodop-vertical-text="true"]')
    .forEach((content) => {
      const text = content.textContent || ''
      const verticalAlign = content.dataset.lodopVerticalAlign === 'middle'
        ? 'middle'
        : content.dataset.lodopVerticalAlign === 'bottom'
          ? 'bottom'
          : 'top'
      const table = printDocument.createElement('table')
      const row = printDocument.createElement('tr')
      const cell = printDocument.createElement('td')

      table.setAttribute('width', '100%')
      table.setAttribute('height', '100%')
      table.setAttribute('cellpadding', '0')
      table.setAttribute('cellspacing', '0')
      table.setAttribute('border', '0')
      table.style.setProperty('width', '100%', 'important')
      table.style.setProperty('height', '100%', 'important')
      table.style.setProperty('border-collapse', 'collapse', 'important')
      table.style.setProperty('table-layout', 'fixed', 'important')
      cell.setAttribute('align', 'center')
      cell.setAttribute('valign', verticalAlign)
      cell.style.setProperty('text-align', 'center', 'important')
      cell.style.setProperty('vertical-align', verticalAlign, 'important')
      cell.style.setProperty('padding', '0', 'important')

      Array.from(text).forEach((character) => {
        if (character === '\r') return

        const line = printDocument.createElement('span')
        line.style.setProperty('display', 'block', 'important')
        line.style.setProperty('width', '100%', 'important')
        line.style.setProperty('line-height', '1.05', 'important')
        line.textContent = character === '\n' || /\s/.test(character)
          ? '\u00a0'
          : getLodopVerticalCharacter(character)
        cell.appendChild(line)
      })

      row.appendChild(cell)
      table.appendChild(row)
      content.replaceChildren(table)
      content.style.setProperty('display', 'block', 'important')
      content.style.setProperty('width', '100%', 'important')
      content.style.setProperty('height', '100%', 'important')
      content.style.setProperty('writing-mode', 'horizontal-tb', 'important')
      content.style.setProperty('-webkit-writing-mode', 'horizontal-tb', 'important')
      content.style.setProperty('white-space', 'normal', 'important')
      content.style.setProperty('overflow', 'hidden', 'important')
      content.style.removeProperty('text-orientation')
      content.removeAttribute('data-lodop-vertical-text')
      content.removeAttribute('data-lodop-vertical-align')
    })

  return printDocument.body.innerHTML
}

const createPrintDocument = (
  html,
  pageWidth,
  pageHeight,
  { normalizeVerticalText = false } = {}
) => {
  const baseUrl = typeof document === 'undefined' ? '' : document.baseURI
  const printableHtml = normalizeVerticalText
    ? normalizeLodopVerticalText(html)
    : String(html || '')

  return `<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <base href="${escapeAttribute(baseUrl)}" />
    <style>
      @page { size: ${pageWidth}mm ${pageHeight}mm; margin: 0; }
      html, body {
        width: ${pageWidth}mm;
        min-height: ${pageHeight}mm;
        margin: 0;
        padding: 0;
        background: #fff;
      }
      * { box-sizing: border-box; }
    </style>
  </head>
  <body>${printableHtml}</body>
</html>`
}

export const openLodopPrintPreview = async ({
  html,
  taskName = '单据打印',
  pageWidth = 210,
  pageHeight = 140,
  printer = null,
  config = getPrintClientConfig()
}) => {
  if (!String(html || '').trim()) {
    throw new Error('没有可打印的模板内容。')
  }

  const width = normalizePageSize(pageWidth, 210)
  const height = normalizePageSize(pageHeight, 140)
  const normalizedConfig = normalizePrintClientConfig(config)
  const lodop = await getLodop(normalizedConfig)
  const printDocument = createPrintDocument(html, width, height, {
    normalizeVerticalText: true
  })
  const printerName = String(
    printer?.name || normalizedConfig.printerName || ''
  ).trim()

  lodop.PRINT_INIT(String(taskName || '单据打印'))
  if (printerName) {
    if (typeof lodop.SET_PRINTER_INDEX !== 'function') {
      throw new Error('当前 C-Lodop 版本不支持指定打印机。')
    }
    if (lodop.SET_PRINTER_INDEX(printerName) === false) {
      throw new Error(`未找到打印机“${printerName}”，请重新选择。`)
    }
  }
  lodop.SET_PRINT_PAGESIZE(0, Math.round(width * 10), Math.round(height * 10), '')
  lodop.ADD_PRINT_HTM(0, 0, '100%', '100%', printDocument)
  lodop.PREVIEW()

  return {
    version: lodop.VERSION || '',
    pageWidth: width,
    pageHeight: height,
    printerName: printerName || String(lodop.GET_PRINTER_NAME?.(-1) || '')
  }
}

export const openBrowserPrintPreview = async ({
  html,
  pageWidth = 210,
  pageHeight = 140
}) => {
  if (!String(html || '').trim()) {
    throw new Error('没有可打印的模板内容。')
  }

  const width = normalizePageSize(pageWidth, 210)
  const height = normalizePageSize(pageHeight, 140)
  const printDocument = createPrintDocument(html, width, height)
  const frame = document.createElement('iframe')
  let cleanupTimer = null

  frame.title = '浏览器打印'
  frame.style.position = 'fixed'
  frame.style.right = '0'
  frame.style.bottom = '0'
  frame.style.width = '1px'
  frame.style.height = '1px'
  frame.style.opacity = '0'
  frame.style.pointerEvents = 'none'
  frame.setAttribute('aria-hidden', 'true')
  document.body.appendChild(frame)

  const cleanup = () => {
    if (cleanupTimer !== null) {
      window.clearTimeout(cleanupTimer)
      cleanupTimer = null
    }
    frame.remove()
  }

  try {
    const frameWindow = frame.contentWindow
    const frameDocument = frame.contentDocument
    if (!frameWindow || !frameDocument) {
      throw new Error('浏览器打印窗口创建失败。')
    }

    frameDocument.open()
    frameDocument.write(printDocument)
    frameDocument.close()

    await new Promise(resolve => window.setTimeout(resolve, 80))
    if (frameDocument.fonts?.ready) {
      await frameDocument.fonts.ready
    }

    frameWindow.addEventListener('afterprint', cleanup, { once: true })
    cleanupTimer = window.setTimeout(cleanup, 60000)
    frameWindow.focus()
    frameWindow.print()
  } catch (error) {
    cleanup()
    throw error
  }

  return {
    mode: 'browser',
    pageWidth: width,
    pageHeight: height,
    printerName: '浏览器打印'
  }
}

export const openConfiguredPrintPreview = async (options = {}) => {
  const config = getPrintClientConfig()

  if (config.mode === 'browser') {
    return openBrowserPrintPreview(options)
  }

  return openLodopPrintPreview({
    ...options,
    config,
    printer: {
      ...(options.printer || {}),
      name: config.printerName || options.printer?.name || ''
    }
  })
}
