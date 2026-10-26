import { computed, onScopeDispose, ref, shallowRef, unref } from 'vue'
import {
  capturePrintImage,
  getPrintImageAction,
  isMobileShareDevice,
  sendPrintImage
} from '../utils/printImageShare.js'

export function usePrintImageShare({ fileName, capture = capturePrintImage } = {}) {
  const imageFile = shallowRef(null)
  const preparing = ref(false)
  const sharing = ref(false)
  const error = ref('')
  const message = ref('')
  const downloadOnly = ref(false)
  let requestId = 0
  let controller

  const action = computed(() => downloadOnly.value ? 'download' : imageFile.value
    ? getPrintImageAction(imageFile.value)
    : isMobileShareDevice() ? 'share' : 'copy')
  const ready = computed(() => Boolean(imageFile.value) && !preparing.value && !sharing.value)
  const label = computed(() => {
    if (preparing.value) return '生成图片中'
    if (sharing.value) return action.value === 'copy' ? '复制中' : '分享中'
    if (error.value && !imageFile.value) return '重试图片'
    return action.value === 'download' ? '下载图片' : '分享'
  })
  const title = computed(() => {
    if (error.value && !imageFile.value) return '图片生成失败，点击重试'
    if (preparing.value) return '正在生成完整单据图片'
    if (action.value === 'download') return '当前浏览器不支持直接分享或复制，下载单据图片'
    return action.value === 'share' ? '将单据图片分享到应用' : '将单据图片复制到剪贴板'
  })

  const invalidate = () => {
    requestId++
    controller?.abort()
    controller = null
    imageFile.value = null
    preparing.value = false
    sharing.value = false
    error.value = ''
    message.value = ''
    downloadOnly.value = false
  }

  const prepare = async content => {
    invalidate()
    if (!content) return
    const current = requestId
    controller = new AbortController()
    preparing.value = true
    try {
      const blob = await capture(content, { signal: controller.signal })
      if (current !== requestId) return
      imageFile.value = new File([blob], unref(fileName) || '单据.png', { type: 'image/png' })
    } catch (cause) {
      if (current === requestId && cause?.name !== 'AbortError') {
        error.value = cause?.message || '单据图片生成失败，请重试。'
      }
    } finally {
      if (current === requestId) preparing.value = false
    }
  }

  const share = async () => {
    if (!ready.value) return
    const current = requestId
    const currentAction = action.value
    sharing.value = true
    error.value = ''
    message.value = ''
    try {
      // Invoke the native API before any await to retain the user's click activation.
      await sendPrintImage(imageFile.value, currentAction)
      if (current !== requestId) return
      message.value = currentAction === 'copy'
        ? '单据图片已复制，可直接粘贴发送。'
        : currentAction === 'share' ? '已交给系统分享。' : '已发起单据图片下载。'
    } catch (cause) {
      if (current !== requestId || (currentAction === 'share' && cause?.name === 'AbortError')) return
      downloadOnly.value = true
      error.value = currentAction === 'copy'
        ? '复制图片失败，请点击“下载图片”保存后发送。'
        : '当前浏览器无法完成分享，请点击“下载图片”保存后发送。'
    } finally {
      if (current === requestId) sharing.value = false
    }
  }

  onScopeDispose(invalidate)
  return { preparing, sharing, ready, action, label, title, error, message, prepare, share, invalidate }
}
