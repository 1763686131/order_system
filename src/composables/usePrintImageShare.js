import { computed, onScopeDispose, ref, shallowRef, unref } from 'vue'
import {
  capturePrintImage,
  blobToDataUrl,
  getPrintImageAction,
  getPrintImageUnavailableReason,
  sendPrintImage
} from '../utils/printImageShare.js'

export function usePrintImageShare({ fileName, capture = capturePrintImage, environment = globalThis } = {}) {
  const imageFile = shallowRef(null)
  const preparing = ref(false)
  const sharing = ref(false)
  const error = ref('')
  const message = ref('')
  const legacyImageDataUrl = ref('')
  let requestId = 0
  let controller

  const action = computed(() => getPrintImageAction(imageFile.value, environment))
  const unavailableReason = computed(() => imageFile.value
    ? getPrintImageUnavailableReason(imageFile.value, environment)
    : '')
  const ready = computed(() => Boolean(imageFile.value) && !preparing.value && !sharing.value)
  const label = computed(() => {
    if (preparing.value) return '生成图片中'
    if (sharing.value) return action.value === 'copy' ? '复制中' : '分享中'
    if (error.value && !imageFile.value) return '重试图片'
    return '分享'
  })
  const title = computed(() => {
    if (error.value && !imageFile.value) return '图片生成失败，点击重试'
    if (preparing.value) return '正在生成完整单据图片'
    if (unavailableReason.value) return unavailableReason.value
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
    legacyImageDataUrl.value = ''
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
      const file = new environment.File([blob], unref(fileName) || '单据.png', { type: 'image/png' })
      const dataUrl = await blobToDataUrl(blob, environment).catch(() => '')
      if (current !== requestId) return
      imageFile.value = file
      legacyImageDataUrl.value = dataUrl
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
      await sendPrintImage(imageFile.value, currentAction, environment, {
        legacyDataUrl: legacyImageDataUrl.value
      })
      if (current !== requestId) return
      message.value = currentAction === 'copy'
        ? '单据图片已复制，可直接粘贴发送。'
        : '已交给系统分享。'
    } catch (cause) {
      if (current !== requestId || (currentAction === 'share' && cause?.name === 'AbortError')) return
      const blocked = cause?.name === 'NotAllowedError' || cause?.name === 'SecurityError'
      error.value = getPrintImageUnavailableReason(imageFile.value, environment) || (blocked
        ? currentAction === 'copy'
          ? '浏览器阻止了图片复制，请允许复制权限并保持页面在前台后重试。'
          : '浏览器阻止了系统分享，请在手机浏览器中直接打开页面并再次点击分享。'
        : currentAction === 'copy'
          ? '图片复制失败，请再次点击分享重试。'
          : '图片分享失败，请再次点击分享或换用支持文件分享的手机浏览器。')
    } finally {
      if (current === requestId) sharing.value = false
    }
  }

  onScopeDispose(invalidate)
  return { preparing, sharing, ready, action, unavailableReason, label, title, error, message, prepare, share, invalidate }
}
