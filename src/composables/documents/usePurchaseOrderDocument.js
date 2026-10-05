import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import request from '@/api/request'
import { DOCUMENT_TYPES, localDate, purchaseOrderPayload, validatePurchaseOrder } from './documentModels'
import { useDocumentValidation } from './useDocumentValidation'

function dateAfter(dateText, days = 7) {
  const date = new Date(`${dateText}T00:00:00`)
  if (Number.isNaN(date.getTime())) return ''
  date.setDate(date.getDate() + days)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

export function usePurchaseOrderDocument(props) {
  const router = useRouter()
  const validation = useDocumentValidation()
  const loading = ref(true)
  const loadFailed = ref(false)
  const saving = ref(false)
  const stores = ref([])
  const suppliers = ref([])
  const products = ref([])
  const units = ref([])
  const savedDocumentId = ref(props.documentId)
  const notice = ref({ visible: false, type: 'success', message: '' })
  let rowKey = 0
  let noticeTimer
  let redirectTimer
  const blankItem = () => ({
    key: ++rowKey, orderItemId: null, productId: '', productCode: '', goodsName: '',
    specification: '', unit: '', quantity: '', supplierId: '', supplierName: '',
    price: '', amount: '', remark: ''
  })
  const blankForm = () => {
    const orderDate = localDate()
    return {
      orderNo: '', storeId: '', orderDate, expectedDate: dateAfter(orderDate),
      expectedDateAuto: true, remark: '', status: 'draft', items: [blankItem()]
    }
  }
  const form = ref(blankForm())
  const auditMode = computed(() => props.action === 'audit' && form.value.status === 'pending')
  const readOnly = computed(() => props.action === 'view' ||
    (props.action === 'audit' && !auditMode.value) ||
    !['draft', 'pending'].includes(form.value.status))
  const config = computed(() => ({
    ...DOCUMENT_TYPES['purchase-order'],
    title: auditMode.value ? '审核采购申请' : readOnly.value ? '采购申请详情' : savedDocumentId.value ? '编辑采购申请' : '新增采购申请'
  }))
  const statusLabel = computed(() => ({
    draft: '草稿', pending: '待审核', approved: '已审核', partial: '部分入库',
    completed: '已完成', cancelled: '已取消'
  }[form.value.status] || form.value.status))
  const totalQuantity = computed(() => form.value.items.reduce((sum, item) => sum + (item.productId ? Number(item.quantity) || 0 : 0), 0))
  const totalAmount = computed(() => form.value.items.reduce((sum, item) => sum + (item.productId ? Number(item.amount) || 0 : 0), 0))
  const showNotice = (message, type = 'success') => {
    notice.value = { visible: true, type, message }
    window.clearTimeout(noticeTimer)
    noticeTimer = window.setTimeout(() => { notice.value.visible = false }, type === 'error' ? 5000 : 3000)
  }
  const calculateRow = item => {
    const hasValue = value => value !== '' && value != null
    if (hasValue(item.price) && hasValue(item.quantity)) {
      item.amount = Number((Number(item.price) * Number(item.quantity)).toFixed(2))
    }
  }
  const onProductChange = item => {
    const product = products.value.find(candidate => String(candidate.id) === String(item.productId))
    if (!product) {
      Object.assign(item, { productCode: '', goodsName: '', specification: '', unit: '' })
      return
    }
    item.productCode = product.code || ''
    item.goodsName = product.name || ''
    item.specification = product.specification || ''
    item.unit = units.value.find(unit => String(unit.id) === String(product.unitId))?.name || product.unit || ''
    calculateRow(item)
  }
  const onDateChange = () => {
    if (form.value.expectedDateAuto && form.value.orderDate) form.value.expectedDate = dateAfter(form.value.orderDate)
  }
  const onExpectedDateInput = () => { form.value.expectedDateAuto = false }
  const addRow = index => {
    if (readOnly.value || saving.value) return
    form.value.items.splice(index + 1, 0, blankItem())
  }
  const removeRow = index => {
    if (!readOnly.value && !saving.value && form.value.items.length > 1) form.value.items.splice(index, 1)
  }
  const normalize = data => {
    const orderDate = data.orderDate || localDate()
    form.value = {
      orderNo: data.orderNo || '', orderDate, expectedDate: data.expectedDate || dateAfter(orderDate),
      expectedDateAuto: !data.expectedDate || data.expectedDate === dateAfter(orderDate),
      storeId: data.storeId ? String(data.storeId) : '', remark: data.remark || '', status: data.status || 'draft',
      items: (data.items || []).map(item => ({
        ...blankItem(), orderItemId: item.orderItemId || item.id,
        productId: item.productId ? String(item.productId) : '', productCode: item.productCode || '',
        goodsName: item.productName || '', specification: item.specification || '', unit: item.unit || '',
        quantity: item.orderedQty ?? '', supplierId: item.supplierId ? String(item.supplierId) : '',
        supplierName: item.supplierName || '', price: item.unitPrice ?? '', amount: item.amount ?? '', remark: item.remark || ''
      }))
    }
    if (!form.value.items.length) form.value.items.push(blankItem())
  }
  const restoreDraft = draft => {
    form.value = JSON.parse(JSON.stringify(draft.form))
    rowKey = Math.max(rowKey, ...form.value.items.map(item => Number(item.key) || 0))
    savedDocumentId.value = draft.savedDocumentId ?? props.documentId
  }
  const validateForm = () => {
    validation.dismissValidationHint()
    return !validatePurchaseOrder(form.value, auditMode.value, validation.showValidationHint)
  }
  const close = () => router.push({ name: 'admin-purchase-orders' })
  const save = async (status = 'pending') => {
    if (saving.value || readOnly.value || loading.value || loadFailed.value || !validateForm()) return false
    const isAudit = auditMode.value
    saving.value = true
    let savedSuccessfully = false
    try {
      const id = savedDocumentId.value
      const response = await request({
        url: isAudit ? `/purchase-orders/${id}/audit` : id ? `/purchase-orders/${id}` : '/purchase-orders',
        method: isAudit ? 'POST' : id ? 'PUT' : 'POST',
        data: purchaseOrderPayload(form.value, isAudit ? 'pending' : status)
      })
      if (!response?.success) throw new Error(response?.message || '保存失败')
      savedSuccessfully = true
      savedDocumentId.value = response.id || response.purchaseOrder?.orderId || response.purchaseOrder?.id || id
      if (response.purchaseOrder) normalize(response.purchaseOrder)
      showNotice(isAudit ? '采购申请已审核通过' : status === 'pending' ? '采购申请已提交审核' : '采购申请草稿已保存')
      redirectTimer = window.setTimeout(close, 500)
      return true
    } catch (error) {
      showNotice(error?.response?.data?.message || error.message || '保存采购申请失败', 'error')
      return false
    } finally {
      if (!savedSuccessfully) saving.value = false
    }
  }
  const clearForm = () => {
    if (readOnly.value || saving.value) return
    const { orderNo, status } = form.value
    form.value = { ...blankForm(), orderNo, status }
    validation.dismissValidationHint()
  }
  onMounted(async () => {
    try {
      const [storeData, supplierData, productData, unitData] = await Promise.all([
        request({ url: '/stores', method: 'GET' }), request({ url: '/suppliers', method: 'GET' }),
        request({ url: '/raw-material-products', method: 'GET' }), request({ url: '/products/units/measurements', method: 'GET' })
      ])
      stores.value = Array.isArray(storeData) ? storeData.filter(item => item.status !== 'inactive') : []
      suppliers.value = Array.isArray(supplierData) ? supplierData.filter(item => item.status !== 'inactive') : []
      products.value = Array.isArray(productData) ? productData.filter(item => item.enabled !== false) : []
      units.value = Array.isArray(unitData) ? unitData : []
      if (props.documentId) normalize(await request({ url: `/purchase-orders/${props.documentId}`, method: 'GET' }))
    } catch (error) {
      loadFailed.value = true
      showNotice(error?.response?.data?.message || error.message || '加载采购申请资料失败', 'error')
    } finally {
      loading.value = false
    }
  })
  onBeforeUnmount(() => {
    window.clearTimeout(noticeTimer)
    window.clearTimeout(redirectTimer)
  })
  return {
    ...validation, config, form, loading, loadFailed, saving, readOnly, auditMode, statusLabel,
    stores, suppliers, products, savedDocumentId, notice, totalQuantity, totalAmount,
    productsForItem: () => products.value,
    addRow, removeRow, onProductChange, onDateChange, onExpectedDateInput, restoreDraft,
    validateForm, save, clearForm, close,
    onQuantityInput: index => calculateRow(form.value.items[index]),
    onPriceInput: index => calculateRow(form.value.items[index])
  }
}
