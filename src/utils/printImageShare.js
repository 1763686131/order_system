const MAX_CANVAS_EDGE = 16000
const MAX_CANVAS_PIXELS = 16000000

export function printImageFileName(...parts) {
  const name = parts.filter(value => value !== '' && value != null)
    .join(' - ')
    .replace(/[<>:"/\\|?*\u0000-\u001f]/g, '_')
    .trim()
    .slice(0, 120)
    .replace(/[. ]+$/, '')
  return `${name || '单据'}.png`
}

export function isMobileShareDevice(navigator = globalThis.navigator) {
  return Boolean(
    navigator?.userAgentData?.mobile ||
    /Android|iPhone|iPad|iPod/i.test(navigator?.userAgent || '') ||
    (navigator?.platform === 'MacIntel' && navigator?.maxTouchPoints > 1)
  )
}

export function getPrintImageAction(file, environment = globalThis) {
  return isMobileShareDevice(environment.navigator) ? 'share' : 'copy'
}

function canWriteImageClipboard(environment) {
  const { navigator, ClipboardItem } = environment
  if (typeof navigator?.clipboard?.write !== 'function' || typeof ClipboardItem !== 'function') {
    return false
  }
  try {
    return !ClipboardItem.supports || ClipboardItem.supports('image/png')
  } catch {
    return false
  }
}

export function getPrintImageUnavailableReason(file, environment = globalThis) {
  const { navigator, document } = environment
  if (isMobileShareDevice(navigator)) {
    if (typeof navigator?.share !== 'function') {
      return '当前浏览器不支持系统图片分享，请在支持文件分享的手机浏览器中打开。'
    }
    try {
      if (typeof navigator.canShare === 'function' && !navigator.canShare({ files: [file] })) {
        return '当前浏览器无法分享这张图片，请换用支持图片文件分享的手机浏览器。'
      }
    } catch {
      return '当前浏览器无法检查图片分享能力，请换用支持文件分享的手机浏览器。'
    }
    return ''
  }
  if (canWriteImageClipboard(environment)) return ''
  if (typeof document?.execCommand === 'function' && typeof document?.createElement === 'function') {
    return ''
  }
  return '当前浏览器不支持复制图片，请换用支持图片剪贴板或网页复制的浏览器。'
}

export function blobToDataUrl(blob, environment = globalThis) {
  if (typeof environment.FileReader !== 'function') {
    return Promise.resolve('')
  }
  return new Promise((resolve, reject) => {
    const reader = new environment.FileReader()
    reader.onload = () => resolve(typeof reader.result === 'string' ? reader.result : '')
    reader.onerror = () => reject(reader.error || new Error('图片读取失败。'))
    reader.readAsDataURL(blob)
  })
}

function copyPrintImageWithLegacyApi(file, environment, dataUrl = '') {
  const document = environment.document
  const body = document?.body
  if (!body || typeof document.execCommand !== 'function') {
    throw new Error('当前浏览器不支持网页复制图片。')
  }

  const objectUrl = dataUrl ? '' : environment.URL?.createObjectURL?.(file)
  const imageUrl = dataUrl || objectUrl
  if (!imageUrl) throw new Error('当前浏览器无法准备图片复制内容。')

  const container = document.createElement('div')
  const image = document.createElement('img')
  container.contentEditable = 'true'
  container.setAttribute('aria-hidden', 'true')
  container.style.position = 'fixed'
  container.style.left = '-10000px'
  container.style.top = '0'
  container.style.width = '1px'
  container.style.height = '1px'
  container.style.opacity = '0.01'
  image.src = imageUrl
  image.alt = ''
  image.draggable = false
  container.appendChild(image)
  body.appendChild(container)

  const selection = environment.getSelection?.()
  const range = document.createRange()
  container.focus?.()
  range.selectNodeContents(container)
  selection?.removeAllRanges()
  selection?.addRange(range)

  let copied = false
  try {
    copied = Boolean(document.execCommand('copy'))
  } finally {
    selection?.removeAllRanges()
    container.remove()
    const revoke = () => objectUrl && environment.URL.revokeObjectURL(objectUrl)
    if (objectUrl && typeof environment.setTimeout === 'function') {
      // Some browsers read the selected image after execCommand returns.
      environment.setTimeout(revoke, 60000)
    } else if (objectUrl) {
      revoke()
    }
  }
  if (!copied) throw new Error('图片复制失败，请再次点击分享重试。')
}

export function sendPrintImage(file, action, environment = globalThis, options = {}) {
  const unavailableReason = getPrintImageUnavailableReason(file, environment)
  if (unavailableReason) throw new Error(unavailableReason)
  if (action === 'share') {
    // Files only: browsers without file sharing must not silently share just a title.
    return environment.navigator.share({ files: [file] })
  }
  if (action === 'copy') {
    if (canWriteImageClipboard(environment)) {
      return environment.navigator.clipboard.write([
        new environment.ClipboardItem({ 'image/png': file })
      ])
    }
    copyPrintImageWithLegacyApi(file, environment, options.legacyDataUrl)
    return Promise.resolve()
  }
  throw new Error('无法识别图片分享方式，请重新打开打印预览后重试。')
}

function abortError() {
  return new DOMException('图片生成已取消', 'AbortError')
}

async function waitForCapture(promise, signal, timeout = 30000) {
  if (signal?.aborted) throw abortError()
  let timer
  let handleAbort
  try {
    return await Promise.race([
      promise,
      new Promise((resolve, reject) => {
        timer = setTimeout(() => reject(new Error('单据图片生成超时，请重试。')), timeout)
        handleAbort = () => reject(abortError())
        signal?.addEventListener('abort', handleAbort, { once: true })
      })
    ])
  } finally {
    clearTimeout(timer)
    signal?.removeEventListener('abort', handleAbort)
  }
}

function readPrintPages(content) {
  const pages = Array.from(content.querySelectorAll?.('.print-page') || [])
  if (!pages.length) {
    return [{
      element: content,
      width: Math.ceil(Math.max(content.scrollWidth, content.offsetWidth)),
      height: Math.ceil(Math.max(content.scrollHeight, content.offsetHeight))
    }]
  }
  return pages.map(element => {
    const style = element.ownerDocument.defaultView.getComputedStyle(element)
    const dimension = axis => {
      const value = Number.parseFloat(style[axis])
      if (!Number.isFinite(value)) return axis === 'width' ? element.offsetWidth : element.offsetHeight
      const edges = axis === 'width' ? ['Left', 'Right'] : ['Top', 'Bottom']
      const extra = style.boxSizing === 'border-box' ? 0 : edges.reduce((total, edge) => (
        total + (Number.parseFloat(style[`padding${edge}`]) || 0) +
        (Number.parseFloat(style[`border${edge}Width`]) || 0)
      ), 0)
      return Math.ceil(value + extra)
    }
    // Computed paper dimensions are independent of preview zoom and flex stretching.
    return { element, width: dimension('width'), height: dimension('height') }
  })
}

function imageSize(pages) {
  const width = Math.max(...pages.map(page => page.width))
  const height = pages.reduce((total, page) => total + page.height, 0)
  if (!width || !height) throw new Error('暂无可分享的单据内容。')
  const pixelRatio = Math.min(
    2,
    MAX_CANVAS_EDGE / width,
    MAX_CANVAS_EDGE / height,
    Math.sqrt(MAX_CANVAS_PIXELS / (width * height))
  )
  if (pixelRatio < 0.5) throw new Error('单据过长，请减少单次预览页数后再分享。')
  return { width, height, pixelRatio }
}

export function getPrintImageSize(content) {
  return imageSize(readPrintPages(content))
}

export async function capturePrintImage(content, { signal } = {}) {
  if (!content?.isConnected) throw new Error('预览尚未加载完成，请稍后重试。')
  const document = content.ownerDocument
  const images = Array.from(content.querySelectorAll('img'))
  const assets = Promise.all([
    document.fonts?.ready,
    ...images.map(async image => {
      try {
        if (image.decode) await image.decode()
      } catch {
        throw new Error('单据中的图片未加载成功，请检查图片后重试。')
      }
      if (!image.complete || !image.naturalWidth) {
        throw new Error('单据中的图片未加载成功，请检查图片后重试。')
      }
    })
  ])
  await waitForCapture(assets, signal)
  if (!content.isConnected) throw abortError()

  const { toCanvas } = await waitForCapture(import('html-to-image'), signal)
  const pages = readPrintPages(content)
  const { width, height, pixelRatio } = imageSize(pages)
  const canvas = document.createElement('canvas')
  canvas.width = Math.ceil(width * pixelRatio)
  canvas.height = Math.ceil(height * pixelRatio)
  const context = canvas.getContext('2d')
  if (!context) throw new Error('当前浏览器无法生成单据图片。')
  context.fillStyle = '#fff'
  context.fillRect(0, 0, canvas.width, canvas.height)
  let top = 0
  for (const page of pages) {
    if (!content.isConnected || signal?.aborted) throw abortError()
    const pageCanvas = await waitForCapture(toCanvas(page.element, {
      width: page.width,
      height: page.height,
      pixelRatio,
      backgroundColor: '#fff',
      includeQueryParams: true,
      style: {
        zoom: '1',
        transform: 'none',
        position: 'relative',
        left: 'auto',
        top: 'auto',
        right: 'auto',
        bottom: 'auto',
        margin: '0',
        boxSizing: 'border-box',
        boxShadow: 'none',
        overflow: 'hidden',
        minWidth: '0',
        minHeight: '0',
        maxWidth: 'none',
        maxHeight: 'none',
        width: `${page.width}px`,
        height: `${page.height}px`
      }
    }), signal)
    const bottom = Math.round((top + page.height) * pixelRatio)
    const y = Math.round(top * pixelRatio)
    context.drawImage(pageCanvas, Math.round((width - page.width) * pixelRatio / 2), y,
      Math.round(page.width * pixelRatio), bottom - y)
    pageCanvas.width = 0
    pageCanvas.height = 0
    top += page.height
  }
  const blob = await waitForCapture(new Promise(resolve => canvas.toBlob(resolve, 'image/png')), signal)
  canvas.width = 0
  canvas.height = 0
  if (!blob?.size) throw new Error('单据图片生成失败，请重试。')
  return blob
}
