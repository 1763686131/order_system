<template>
  <OrderPrintPreview
    :visible="visible"
    :template="selectedTemplate"
    :variables="variables"
    :title="title"
    :document-number="documentNumber"
    :preview-label="previewLabel"
    :print-enabled="printEnabled"
    template-selection
    :template-options="templates"
    :templates-loading="loading"
    :templates-error="errorMessage"
    @select-template="selectTemplate"
    @reload-templates="loadTemplates"
    @close="emit('close')"
  />
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { getTemplates } from '@/api/printTemplate'
import OrderPrintPreview from '@/components/print/OrderPrintPreview.vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  businessType: { type: String, required: true },
  title: { type: String, default: '打印单据' },
  documentNumber: { type: [String, Number], default: '' },
  variables: { type: Object, default: () => ({}) },
  previewLabel: { type: String, default: '当前单据数据预览' },
  printEnabled: { type: Boolean, default: true }
})

const emit = defineEmits(['close'])
const templates = ref([])
const selectedTemplateId = ref(null)
const loading = ref(false)
const errorMessage = ref('')
let loadRequestId = 0

const selectedTemplate = computed(() => (
  templates.value.find(template => String(template.id) === String(selectedTemplateId.value)) || null
))

const getStorageKey = businessType => `order-system-print-template-selection:${businessType}`

const getStoredTemplateId = (businessType) => {
  try {
    const stored = JSON.parse(window.localStorage.getItem(getStorageKey(businessType)) || 'null')
    return stored?.templateId ?? stored?.id ?? null
  } catch {
    return null
  }
}

const selectTemplate = (id) => {
  const template = templates.value.find(candidate => String(candidate.id) === String(id))
  if (!template || loading.value) return
  selectedTemplateId.value = template.id

  try {
    window.localStorage.setItem(getStorageKey(props.businessType), JSON.stringify({
      version: 1,
      businessType: props.businessType,
      templateId: template.id,
      savedAt: new Date().toISOString()
    }))
  } catch {
    // The selection remains usable when browser storage is unavailable.
  }
}

const loadTemplates = async () => {
  if (!props.visible) return
  const requestId = ++loadRequestId
  const businessType = props.businessType
  const currentSelectionId = selectedTemplateId.value
  const isCurrentRequest = () => (
    requestId === loadRequestId && props.visible && props.businessType === businessType
  )
  loading.value = true
  errorMessage.value = ''

  try {
    const response = await getTemplates({ businessType, enabledOnly: true })
    if (!isCurrentRequest()) return
    if (!response?.success) throw new Error(response?.message || '打印模板加载失败')

    templates.value = (response.data || [])
      .filter(template => (
        template.enabled &&
        template.businessType === businessType &&
        (template.content || template.design || template.data)
      ))
      .sort((left, right) => Number(right.isDefault) - Number(left.isDefault))

    const storedId = getStoredTemplateId(businessType)
    const findTemplate = id => templates.value.find(template => String(template.id) === String(id))
    const preferredTemplate = findTemplate(currentSelectionId) ||
      findTemplate(storedId) ||
      templates.value[0] ||
      null
    selectedTemplateId.value = preferredTemplate?.id ?? null

    if (storedId !== null && !findTemplate(storedId)) {
      try {
        window.localStorage.removeItem(getStorageKey(businessType))
      } catch {
        // Ignore failures to remove an outdated preference.
      }
    }
  } catch (error) {
    if (!isCurrentRequest()) return
    templates.value = []
    selectedTemplateId.value = null
    errorMessage.value = error?.message || '打印模板加载失败，请稍后重试'
  } finally {
    if (isCurrentRequest()) loading.value = false
  }
}

watch(
  [() => props.visible, () => props.businessType],
  ([visible]) => {
    loadRequestId += 1
    templates.value = []
    selectedTemplateId.value = null
    errorMessage.value = ''
    loading.value = false
    if (visible) loadTemplates()
  },
  { immediate: true }
)

const handleTemplatesUpdated = () => loadTemplates()

onMounted(() => {
  window.addEventListener('order-system-print-templates-updated', handleTemplatesUpdated)
})

onBeforeUnmount(() => {
  loadRequestId += 1
  window.removeEventListener('order-system-print-templates-updated', handleTemplatesUpdated)
})
</script>
