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
  const { navigator, ClipboardItem, isSecureContext } = environment
  if (isSecureContext === false) return 'download'
  if (isMobileShareDevice(navigator)) {
    try {
      return navigator?.share && navigator?.canShare?.({ files: [file] }) ? 'share' : 'download'
    } catch {
      return 'download'
    }
  }
  return navigator?.clipboard?.write && ClipboardItem &&
    (!ClipboardItem.supports || ClipboardItem.supports('image/png'))
    ? 'copy'
    : 'download'
}

export function downloadPrintImage(file, environment = globalThis) {
  const url = environment.URL.createObjectURL(file)
  const link = environment.document.createElement('a')
  link.href = url
  link.download = file.name
  environment.document.body.appendChild(link)
  try {
    link.click()
  } finally {
    link.remove()
    // Mobile browsers may read the download URL after the click handler returns.
    environment.setTimeout(() => environment.URL.revokeObjectURL(url), 60000)
  }
}

export function sendPrintImage(file, action, environment = globalThis) {
  if (action === 'share') {
    return environment.navigator.share({ files: [file], title: file.name.replace(/\.png$/i, '') })
  }
  if (action === 'copy') {
    return environment.navigator.clipboard.write([
      new environment.ClipboardItem({ 'image/png': file })
    ])
  }
  downloadPrintImage(file, environment)
  return Promise.resolve()
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
