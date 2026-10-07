import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import request from '@/api/request'
import { useUserStore } from '@/stores/user'
import { operationKey, sumMoney } from '@/utils/supplierFinance'
import {
  DOCUMENT_TYPES, localDate, purchaseReturnOriginalCost, purchaseReturnPayload,
  purchaseReturnStatusLabels, validatePurchaseReturn
} from './documentModels'
import { useDocumentValidation } from './useDocumentValidation'

export function usePurchaseReturnDocument(props) {
  const router = useRouter()
  const user = useUserStore()
  const validation = useDocumentValidation()
  const loading = ref(true)
  const loadFailed = ref(false)
  const saving = ref(false)
  const stores = ref([])
  const supplierOptions = ref([])
  const sources = ref([])
  const sourceLoading = ref(false)
  const sourceError = ref('')
  const savedDocumentId = ref(props.documentId)
  const notice = ref({ visible: false, type: 'success', message: '' })
  let rowKey = 0
  let sourceRequest = 0
  let noticeTimer
  let redirectTimer
  const blankItem = () => ({
    key: ++rowKey, inboundItemId: '', quantity: '', returnAmount: '', differenceReason: '',
    inboundDocumentNo: '', productName: '', productCode: '', specification: '', unit: '',
    warehouseId: '', warehouseName: '', batchNo: '', binCode: '', originalUnitPrice: 0
  })
  const blankRows = () => Array.from({ length: 8 }, blankItem)
  const blankForm = () => ({
    supplierId: '', supplierName: '', storeId: '', storeName: '', businessDate: localDate(),
    documentNo: '', remark: '', items: blankRows(), status: 'draft', version: null
  })
  const form = ref(blankForm())
  const can = action => user.hasPerm(`admin.purchase.return.${action}`)
  const readOnly = computed(() => props.action === 'view' || form.value.status !== 'draft'
    || Boolean(form.value.lockedAt) || !can(savedDocumentId.value ? 'edit' : 'create'))
  const partyLocked = computed(() => Boolean(savedDocumentId.value))
  const canEdit = computed(() => Boolean(savedDocumentId.value) && form.value.status === 'draft'
    && !form.value.lockedAt && can('edit'))
  const canAudit = computed(() => Boolean(savedDocumentId.value)
    && ['draft', 'reversed'].includes(form.value.status) && !form.value.lockedAt && can('audit'))
  const canReverseAudit = computed(() => Boolean(savedDocumentId.value)
    && form.value.status === 'audited' && !form.value.lockedAt && can('reverse_audit'))
  const suppliers = computed(() => supplierOptions.value.filter(row =>
    !row.storeId || String(row.storeId) === String(form.value.storeId)))
  const config = computed(() => ({
    ...DOCUMENT_TYPES['purchase-return'],
    title: readOnly.value ? '采购退货详情' : savedDocumentId.value ? '编辑采购退货' : '新增采购退货'
  }))
  const statusLabel = computed(() => purchaseReturnStatusLabels[form.value.status] || form.value.status)
  const currentCreatorName = computed(() => form.value.createdBy || user.name || user.username || '')
  const selectedItems = computed(() => form.value.items.filter(item => item.inboundItemId))
  const originalCost = item => readOnly.value && item.originalCost != null
    ? Number(item.originalCost) : purchaseReturnOriginalCost(item)
  const hasDifference = item => Math.round(originalCost(item) * 100) !== Math.round(Number(item.returnAmount || 0) * 100)
  const totalQuantity = computed(() => selectedItems.value.reduce((sum, item) => sum + Number(item.quantity || 0), 0))
  const totalOriginalCost = computed(() => selectedItems.value.reduce((sum, item) => sum + Math.round(originalCost(item) * 100), 0) / 100)
  const totalReturnAmount = computed(() => sumMoney(selectedItems.value, 'returnAmount'))
  const totalDifference = computed(() => Math.round((totalOriginalCost.value - totalReturnAmount.value) * 100) / 100)
  const totalAppliedPayable = computed(() => sumMoney(selectedItems.value, 'appliedPayable'))
  const totalCreditAmount = computed(() => sumMoney(selectedItems.value, 'creditAmount'))
  const sourceFor = item => sources.value.find(row => Number(row.inboundItemId) === Number(item.inboundItemId))
  const sourcesForItem = item => sources.value.filter(source =>
    Number(source.inboundItemId) === Number(item.inboundItemId)
    || !form.value.items.some(line => Number(line.inboundItemId) === Number(source.inboundItemId)))
  const sourceLabel = source => [source.inboundDocumentNo, source.productCode, source.productName,
    source.batchNo || '无批次'].filter(Boolean).join(' · ')
  const showNotice = (message, type = 'success') => {
    notice.value = { visible: true, type, message }
    clearTimeout(noticeTimer)
    noticeTimer = setTimeout(() => { notice.value.visible = false }, type === 'error' ? 6000 : 3000)
  }
  const applySource = (item, source) => {
    for (const field of ['inboundDocumentNo', 'productName', 'productCode', 'specification', 'unit',
      'warehouseId', 'warehouseName', 'batchNo', 'binCode', 'originalUnitPrice']) {
      item[field] = source[field] ?? ''
    }
  }
  const loadSources = async () => {
    const requestId = ++sourceRequest
    sources.value = []
    sourceError.value = ''
    sourceLoading.value = false
    if (readOnly.value || !form.value.storeId || !form.value.supplierId) return
    sourceLoading.value = true
    try {
      const result = await request.get(`/suppliers/${form.value.supplierId}/purchase-return-sources`, {
        params: { storeId: form.value.storeId }
      })
      if (requestId !== sourceRequest) return
      sources.value = result.items || []
      selectedItems.value.forEach(item => {
        const source = sourceFor(item)
        if (source) applySource(item, source)
      })
    } catch (error) {
      if (requestId === sourceRequest) sourceError.value = error.response?.data?.message || error.message || '读取可退入库批次失败'
    } finally {
      if (requestId === sourceRequest) sourceLoading.value = false
    }
  }
  const onStoreChange = () => {
    if (partyLocked.value) return
    if (!suppliers.value.some(row => String(row.id) === String(form.value.supplierId))) form.value.supplierId = ''
    form.value.items = blankRows()
    validation.dismissValidationHint()
    loadSources()
  }
  const onSupplierChange = () => {
    if (partyLocked.value) return
    form.value.items = blankRows()
    validation.dismissValidationHint()
    loadSources()
  }
  const selectSource = (index, id) => {
    if (readOnly.value || saving.value || sourceLoading.value) return
    const item = form.value.items[index]
    const source = sourcesForItem(item).find(row => Number(row.inboundItemId) === Number(id))
    const key = item.key
    Object.assign(item, blankItem(), { key })
    if (source) {
      item.inboundItemId = Number(source.inboundItemId)
      applySource(item, source)
      item.quantity = Math.min(1, Number(source.availableQuantity))
      item.returnAmount = purchaseReturnOriginalCost(item)
    }
    validation.dismissValidationHint()
  }
  const onQuantityInput = index => {
    const item = form.value.items[index]
    if (item.inboundItemId) item.returnAmount = purchaseReturnOriginalCost(item)
  }
  const addRow = index => {
    if (!readOnly.value && !saving.value) form.value.items.splice(index + 1, 0, blankItem())
  }
  const removeRow = index => {
    if (!readOnly.value && !saving.value && form.value.items.length > 1) form.value.items.splice(index, 1)
  }
  const normalize = data => {
    savedDocumentId.value = data.id
    form.value = {
      ...blankForm(), ...data,
      supplierId: String(data.supplierId || ''), storeId: String(data.storeId || ''),
      items: (data.items || []).map(item => ({ ...blankItem(), ...item }))
    }
    if (!readOnly.value) while (form.value.items.length < 8) form.value.items.push(blankItem())
  }
  const restoreDraft = async draft => {
    if (savedDocumentId.value && (
      Number(draft.form.version) !== Number(form.value.version)
      || String(draft.form.supplierId) !== form.value.supplierId
      || String(draft.form.storeId) !== form.value.storeId
    )) return false
    form.value = { ...form.value, ...draft.form, items: draft.form.items.map(item => ({ ...blankItem(), ...item })) }
    rowKey = Math.max(rowKey, ...form.value.items.map(item => Number(item.key) || 0))
    await loadSources()
    return true
  }
  const validateForm = () => {
    validation.dismissValidationHint()
    if (sourceLoading.value || sourceError.value) {
      showNotice(sourceLoading.value ? '正在读取可退入库批次，请稍后保存。' : sourceError.value, 'error')
      return false
    }
    return !validatePurchaseReturn(form.value, sources.value, validation.showValidationHint)
  }
  const close = () => router.push({ name: 'admin-purchase-returns' })
  const edit = () => {
    if (canEdit.value) router.push({ name: 'admin-purchase-return-edit', params: { id: savedDocumentId.value } })
  }
  const save = async () => {
    if (readOnly.value || saving.value || loading.value || loadFailed.value || !validateForm()) return false
    saving.value = true
    let saved = false
    try {
      const id = savedDocumentId.value
      const response = await request({
        url: id ? `/purchase-returns/${id}` : '/purchase-returns',
        method: id ? 'PUT' : 'POST',
        data: { ...purchaseReturnPayload(form.value), idempotencyKey: operationKey() }
      })
      if (!response?.success || !response.purchaseReturn) throw new Error(response?.message || '保存失败')
      normalize(response.purchaseReturn)
      saved = true
      showNotice('采购退货草稿已保存')
      redirectTimer = setTimeout(close, 500)
      return true
    } catch (error) {
      showNotice(error.response?.data?.message || error.message || '保存采购退货失败', 'error')
      return false
    } finally {
      if (!saved) saving.value = false
    }
  }
  const performAction = async action => {
    if (saving.value || loading.value || loadFailed.value
      || (action === 'audit' ? !canAudit.value : action !== 'reverse-audit' || !canReverseAudit.value)) return
    saving.value = true
    try {
      const response = await request.post(`/purchase-returns/${savedDocumentId.value}/${action}`, {
        version: form.value.version, idempotencyKey: operationKey()
      })
      if (!response?.success || !response.purchaseReturn) throw new Error(response?.message || '操作失败')
      normalize(response.purchaseReturn)
      showNotice(action === 'audit' ? '采购退货已审核' : '采购退货已反审核')
    } catch (error) {
      showNotice(error.response?.data?.message || error.message || '操作失败', 'error')
    } finally { saving.value = false }
  }
  const clearForm = () => {
    if (readOnly.value || saving.value) return
    if (partyLocked.value) {
      form.value = { ...form.value, businessDate: localDate(), remark: '', items: blankRows() }
    } else form.value = blankForm()
    validation.dismissValidationHint()
    loadSources()
  }
  onMounted(async () => {
    try {
      const options = await request.get('/purchase-returns/options')
      stores.value = options.stores || []
      supplierOptions.value = options.suppliers || []
      if (props.documentId) normalize(await request.get(`/purchase-returns/${props.documentId}`))
      await loadSources()
    } catch (error) {
      loadFailed.value = true
      showNotice(error.response?.data?.message || error.message || '加载采购退货失败', 'error')
    } finally { loading.value = false }
  })
  onBeforeUnmount(() => {
    sourceRequest += 1
    clearTimeout(noticeTimer)
    clearTimeout(redirectTimer)
  })
  return {
    ...validation, config, form, stores, suppliers, sources, sourceLoading, sourceError,
    loading, loadFailed, saving, readOnly, partyLocked, savedDocumentId, notice, statusLabel,
    canEdit, canAudit, canReverseAudit, currentCreatorName, totalQuantity, totalOriginalCost,
    totalReturnAmount, totalDifference, totalAppliedPayable, totalCreditAmount,
    sourceFor, sourcesForItem, sourceLabel, originalCost, hasDifference, loadSources, selectSource,
    onStoreChange, onSupplierChange, onQuantityInput, addRow, removeRow,
    normalize, restoreDraft, validateForm, clearForm, save, close, edit, performAction
  }
}
