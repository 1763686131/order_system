const SCRIPT_TIMEOUT = 5000

let lodopLoader = null

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

const normalizeSdkUrl = (value) => {
  const url = String(value || '').trim().replace(/\/+$/, '')
  if (!url) return ''
  if (/CLodopfuncs\.js/i.test(url)) {
    return url.includes('?') ? url : `${url}?name=CLODOP`
  }
  return `${url}/CLodopfuncs.js?name=CLODOP`
}

const getSdkUrls = () => {
  const configuredUrl = normalizeSdkUrl(import.meta.env.VITE_CLODOP_URL)
  const isHttps = window.location.protocol === 'https:'
  const protocol = isHttps ? 'https:' : 'http:'
  const port = isHttps ? 8443 : 8000

  return [
    configuredUrl,
    `${protocol}//localhost:${port}/CLodopfuncs.js?name=CLODOP`,
    `${protocol}//127.0.0.1:${port}/CLodopfuncs.js?name=CLODOP`
  ].filter((url, index, urls) => url && urls.indexOf(url) === index)
}

const loadSdkScript = (url) => new Promise((resolve, reject) => {
  const script = document.createElement('script')
  const timer = window.setTimeout(() => {
    script.remove()
    reject(new Error(`连接打印服务超时：${url}`))
  }, SCRIPT_TIMEOUT)

  script.src = url
  script.async = true
  script.dataset.clodopSdk = url
  script.onload = () => {
    window.clearTimeout(timer)
    const lodop = getLodopInstance()
    if (isLodopAvailable(lodop)) {
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

export const getLodop = async () => {
  const existing = getLodopInstance()
  if (isLodopAvailable(existing)) return existing

  if (!lodopLoader) {
    lodopLoader = (async () => {
      const errors = []
      for (const url of getSdkUrls()) {
        try {
          return await loadSdkScript(url)
        } catch (error) {
          errors.push(error?.message || String(error))
        }
      }

      throw new Error(
        '未连接到 C-Lodop 打印服务，请确认软件已启动，并允许浏览器访问 localhost:8000。' +
        (errors.length ? `\n${errors.join('\n')}` : '')
      )
    })().catch((error) => {
      lodopLoader = null
      throw error
    })
  }

  return lodopLoader
}

const getPrinterProperty = (lodop, index, property) => {
  try {
    return String(lodop.GET_PRINTER_NAME(`${index}:${property}`) || '')
  } catch {
    return ''
  }
}

export const getLocalPrinters = async () => {
  const lodop = await getLodop()
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

const createPrintDocument = (html, pageWidth, pageHeight) => {
  const baseUrl = typeof document === 'undefined' ? '' : document.baseURI
  const printableHtml = normalizeLodopVerticalText(html)

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
  printer = null
}) => {
  if (!String(html || '').trim()) {
    throw new Error('没有可打印的模板内容。')
  }

  const width = normalizePageSize(pageWidth, 210)
  const height = normalizePageSize(pageHeight, 140)
  const lodop = await getLodop()
  const printDocument = createPrintDocument(html, width, height)
  const printerName = String(printer?.name || '').trim()

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
