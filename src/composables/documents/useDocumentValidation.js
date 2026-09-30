import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'

export function useDocumentValidation() {
  const validationHint = ref({ key: '', message: '' })
  const validationHintStyle = ref({})
  const validationHintPlacement = ref('below')
  const validationFieldRefs = new Map()
  let hintElement = null
  let timer

  const setValidationFieldRef = (key, element) => {
    if (element) validationFieldRefs.set(key, element)
    else validationFieldRefs.delete(key)
  }
  const setValidationHintRef = element => { hintElement = element }
  const dismissValidationHint = (key = '') => {
    if (key && key !== validationHint.value.key) return
    clearTimeout(timer)
    validationHint.value = { key: '', message: '' }
    validationHintStyle.value = {}
  }
  const updateValidationHintPosition = () => {
    const target = validationFieldRefs.get(validationHint.value.key)
    if (!target || !validationHint.value.key || !hintElement) return
    const rect = target.getBoundingClientRect()
    if (rect.bottom < 0 || rect.top > window.innerHeight || rect.right < 0 || rect.left > window.innerWidth) {
      dismissValidationHint()
      return
    }
    const padding = 12
    const gap = 9
    const width = hintElement.offsetWidth
    const height = hintElement.offsetHeight
    const above = rect.bottom + gap + height > window.innerHeight - padding && rect.top > height + gap + padding
    const left = Math.max(padding, Math.min(rect.left, window.innerWidth - width - padding))
    const top = above ? rect.top - height - gap : rect.bottom + gap
    validationHintPlacement.value = above ? 'above' : 'below'
    validationHintStyle.value = {
      left: `${Math.round(left)}px`,
      top: `${Math.round(top)}px`,
      '--hint-arrow-left': `${Math.max(14, Math.min(rect.left + rect.width / 2 - left, width - 14))}px`
    }
  }
  const showValidationHint = (key, message) => {
    clearTimeout(timer)
    const target = validationFieldRefs.get(key)
    target?.scrollIntoView?.({ block: 'nearest', inline: 'nearest' })
    if (!key.startsWith('item-product-')) target?.focus?.({ preventScroll: true })
    validationHint.value = { key, message }
    nextTick(updateValidationHintPosition)
    timer = setTimeout(dismissValidationHint, 6000)
  }
  onMounted(() => {
    window.addEventListener('resize', updateValidationHintPosition)
    window.addEventListener('scroll', updateValidationHintPosition, true)
  })
  onBeforeUnmount(() => {
    clearTimeout(timer)
    window.removeEventListener('resize', updateValidationHintPosition)
    window.removeEventListener('scroll', updateValidationHintPosition, true)
    validationFieldRefs.clear()
  })
  return {
    validationHint, validationHintStyle, validationHintPlacement, validationFieldRefs,
    setValidationFieldRef, setValidationHintRef, dismissValidationHint,
    showValidationHint, updateValidationHintPosition
  }
}
