import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import request from '@/api/request'
import { useUserStore } from '@/stores/user'
import { DOCUMENT_TYPES, inboundAmounts, isLockedInbound, localDate, money, purchasePayload, validatePurchase } from './documentModels'
import { useDocumentValidation } from './useDocumentValidation'

const blankItem = () => ({
  productId: '', productCode: '', goodsName: '', specification: '', unit: '', warehouseId: '', warehouseName: '', expectedQty: '',
  quantity: '', price: '', taxRate: 0, amount: 0, taxAmount: 0, taxIncludedAmount: 0,
  batchNo: '', binCode: '', remark: ''
})

export function usePurchaseDocument(props) {
  const router = useRouter()
  const userStore = useUserStore()
  const validation = useDocumentValidation()
  const stores = ref([])
  const suppliers = ref([])
  const warehouses = ref([])
  const products = ref([])
  const units = ref([])
  const form = ref({
    storeId: '', supplierId: '', warehouseId: '', documentDate: localDate(), documentNo: '',
    inspector: '', qualityNo: '', remark: '', taxEnabled: false, items: [blankItem(), blankItem()],
    attachments: [], status: 'draft'
  })
  const saving = ref(false)
  const loading = ref(true)
  const loadFailed = ref(false)
  const savedDocumentId = ref(props.documentId)
  const notice = ref({ visible: false, type: 'success', message: '' })
  const readOnly = ref(props.action === 'view')
  const stockBalances = ref([])
  const filteredSuppliers = computed(() => suppliers.value.filter(item => !item.storeId || String(item.storeId) === String(form.value.storeId)))
  const filteredWarehouses = computed(() => warehouses.value.filter(item => String(item.storeId ?? item.store_id) === String(form.value.storeId)))
  const productOptions = computed(() => {
    if (!form.value.storeId) return []
    return products.value.filter(product => {
      const storeIds = product.storeIds || product.store_ids || []
      return product.enabled !== false && Array.isArray(storeIds) && storeIds.some(id => String(id) === String(form.value.storeId))
    })
  })
  const productsForItem = item => productOptions.value.filter(product => !product.warehouseId || String(product.warehouseId) === String(item?.warehouseId || form.value.warehouseId))
  const selectedStore = computed(() => stores.value.find(item => String(item.id) === String(form.value.storeId)))
  const selectedSupplier = computed(() => suppliers.value.find(item => String(item.id) === String(form.value.supplierId)))
  const selectedWarehouse = computed(() => warehouses.value.find(item => String(item.id) === String(form.value.warehouseId)))
  const totalPackages = computed(() => form.value.items.reduce((sum, item) => sum + (Number(item.expectedQty) || 0), 0))
  const totalQuantity = computed(() => form.value.items.reduce((sum, item) => sum + (Number(item.quantity) || 0), 0))
  const totalAmount = computed(() => form.value.items.reduce((sum, item) => sum + (Number(item.amount) || 0), 0))
  const totalTaxAmount = computed(() => form.value.items.reduce((sum, item) => sum + (Number(item.taxAmount) || 0), 0))
  const totalIncludedAmount = computed(() => form.value.items.reduce((sum, item) => sum + (Number(item.taxIncludedAmount) || 0), 0))
  const currentCreatorName = computed(() => String(userStore.name || userStore.username || '').trim())
  const showNotice = (message, type = 'success') => {
    notice.value = { visible: true, type, message }
    window.clearTimeout(showNotice.timer)
    showNotice.timer = window.setTimeout(() => { notice.value.visible = false }, type === 'error' ? 5000 : 3000)
  }
  const calculateRow = item => Object.assign(item, inboundAmounts(item, form.value.taxEnabled))
  const onStoreChange = () => { form.value.supplierId = ''; form.value.warehouseId = ''; form.value.items = [blankItem(), blankItem()] }
  const onWarehouseChange = () => { form.value.items = [blankItem(), blankItem()] }
  const getProductStock = (product, item = {}) => stockBalances.value.filter(balance => String(balance.productId) === String(product.id) && String(balance.storeId) === String(form.value.storeId) && String(balance.warehouseId) === String(item.warehouseId || form.value.warehouseId)).reduce((sum, balance) => sum + Number(balance.quantity || 0), 0)
  const onItemWarehouseChange = item => {
    item.warehouseName = warehouses.value.find(warehouse => String(warehouse.id) === String(item.warehouseId))?.name || ''
    const product = productOptions.value.find(candidate => String(candidate.id) === String(item.productId))
    if (product) item.currentStock = getProductStock(product, item)
  }
  const onProductChange = item => {
    const product = productsForItem(item).find(candidate => String(candidate.id) === String(item.productId))
    if (!product) {
      Object.assign(item, blankItem())
      return
    }
    item.productCode = product.code || ''
    item.goodsName = product.name || ''
    item.specification = product.specification || ''
    item.unit = units.value.find(unit => String(unit.id) === String(product.unitId))?.name || product.unit || ''
    item.warehouseId = item.warehouseId || form.value.warehouseId || ''
    item.warehouseName = warehouses.value.find(warehouse => String(warehouse.id) === String(item.warehouseId))?.name || ''
    item.price = Number(product.price || 0)
    item.currentStock = getProductStock(product, item)
    item.taxRate = form.value.taxEnabled ? 13 : 0
    calculateRow(item)
  }
  const addRow = index => form.value.items.splice(index + 1, 0, blankItem())
  const removeRow = index => { if (form.value.items.length > 1) form.value.items.splice(index, 1) }
  const loadData = async () => {
    const [storeData, supplierData, warehouseData, productData, unitData, stockData] = await Promise.all([
      request({ url: '/stores', method: 'GET' }),
      request({ url: '/suppliers', method: 'GET' }),
      request({ url: '/warehouses', method: 'GET' }),
      request({ url: '/raw-material-products', method: 'GET' }),
      request({ url: '/products/units/measurements', method: 'GET' }),
      request({ url: '/stock-balances', method: 'GET', params: { type: 'raw-material' } })
    ])
    stores.value = Array.isArray(storeData) ? storeData.filter(item => item.status !== 'inactive') : []
    suppliers.value = Array.isArray(supplierData) ? supplierData.filter(item => item.status !== 'inactive') : []
    warehouses.value = Array.isArray(warehouseData) ? warehouseData : []
    products.value = Array.isArray(productData) ? productData : []
    units.value = Array.isArray(unitData) ? unitData : []
    stockBalances.value = Array.isArray(stockData) ? stockData : []
  }
  const normalizeInbound = data => {
    form.value = {
      ...form.value,
      storeId: data.storeId ? String(data.storeId) : '',
      supplierId: data.supplierId ? String(data.supplierId) : '',
      warehouseId: data.warehouseId ? String(data.warehouseId) : '',
      documentDate: data.documentDate || localDate(), documentNo: data.documentNo || '',
      inspector: data.inspector || '', qualityNo: data.qualityNo || '', remark: data.remark || '',
      status: data.status || 'draft',
      taxEnabled: (data.items || []).some(item => Number(item.taxRate) > 0),
      attachments: data.attachments || [],
      items: (data.items || []).map(item => ({
        ...blankItem(), productId: item.productId ? String(item.productId) : '', productCode: item.productCode || '', warehouseId: String(item.warehouseId || data.warehouseId || ''), warehouseName: warehouses.value.find(warehouse => String(warehouse.id) === String(item.warehouseId || data.warehouseId))?.name || '',
        goodsName: item.productName || item.goodsName || '', specification: item.specification || '', unit: item.unit || '',
        expectedQty: item.expectedQty ?? '', quantity: item.receivedQty ?? '', price: item.unitPrice ?? '',
        taxRate: Number(item.taxRate || 0), amount: Number(item.totalAmount || 0) - Number(item.taxAmount || 0),
        taxAmount: Number(item.taxAmount || 0), taxIncludedAmount: Number(item.totalAmount || 0), batchNo: item.batchNo || '',
        binCode: item.binCode || '', remark: item.remark || ''
      })).concat([blankItem(), blankItem()]).slice(0, Math.max(2, (data.items || []).length + 1))
    }
    form.value.items.filter(item => item.productId).forEach(onItemWarehouseChange)
  }
  const loadExisting = async () => {
    if (!props.documentId) return
    const data = await request({ url: `/stock-inbounds/${props.documentId}`, method: 'GET' })
    if (data.type !== 'raw-material') throw new Error('此页面只支持原材料进货单')
    normalizeInbound(data)
    readOnly.value = props.action === 'view' || isLockedInbound(form.value.status)
  }
  const printTemplateDialogOpen = ref(false)
  const printPreviewVisible = ref(false)
  const selectedPrintTemplate = ref(null)
  const selectedPrintPrinter = ref(null)
  const printPreviewAutoPrint = ref(false)
  const closePrintTemplateDialog = () => { printTemplateDialogOpen.value = false }
  const openPrintTemplate = (template, printer, autoPrint) => {
    selectedPrintTemplate.value = template
    selectedPrintPrinter.value = printer
    printPreviewAutoPrint.value = autoPrint
    printTemplateDialogOpen.value = false
    printPreviewVisible.value = true
  }
  const closePrintPreview = () => { printPreviewVisible.value = false; selectedPrintTemplate.value = null; selectedPrintPrinter.value = null; printPreviewAutoPrint.value = false }
  const openPrint = () => { printTemplateDialogOpen.value = true }
  const validateForm = () => {
    validation.dismissValidationHint()
    return !validatePurchase(form.value, validation.showValidationHint)
  }
  const save = async () => {
    if (readOnly.value || saving.value || loading.value || loadFailed.value) return
    if (!validateForm()) return
    saving.value = true
    try {
      const id = savedDocumentId.value
      const response = await request({ url: id ? `/stock-inbounds/${id}` : '/stock-inbounds', method: id ? 'PUT' : 'POST', data: purchasePayload(form.value) })
      if (!response?.success) throw new Error(response?.message || '保存失败')
      const saved = response.stockIn || {}
      savedDocumentId.value = response.id || saved.id || id
      form.value.documentNo = saved.documentNo || form.value.documentNo
      showNotice('进货单保存成功')
      openPrint()
    } catch (error) {
      showNotice(error?.response?.data?.message || error.message || '进货单保存失败', 'error')
    } finally { saving.value = false }
  }
  const clearForm = () => {
    if (readOnly.value) return
    form.value = { ...form.value, storeId: '', supplierId: '', warehouseId: '', documentDate: localDate(), items: [blankItem(), blankItem()], taxEnabled: false, inspector: '', qualityNo: '', remark: '' }
    if (!props.documentId) { savedDocumentId.value = null; form.value.documentNo = ''; form.value.attachments = [] }
  }
  const close = () => router.push({ name: 'admin-purchase-inbound' })
  onMounted(async () => {
    try { await loadData(); await loadExisting() } catch (error) { loadFailed.value = true; showNotice(error?.response?.data?.message || error.message || '加载进货单失败', 'error') } finally { loading.value = false }
  })
  onBeforeUnmount(() => window.clearTimeout(showNotice.timer))

  return {
    ...validation, validateForm,
    config: DOCUMENT_TYPES.purchase, form, stores, suppliers: filteredSuppliers, filteredWarehouses, products: productOptions, productsForItem, units, getProductStock,
    currentCreatorName, selectedStore, selectedSupplier, selectedWarehouse, savedDocumentId, saving, loading, loadFailed, readOnly, notice,
    taxEnabled: computed({ get: () => form.value.taxEnabled, set: value => { form.value.taxEnabled = value; form.value.items.forEach(item => { item.taxRate = value ? Number(item.taxRate) || 13 : 0; calculateRow(item) }) } }),
    totalPackages, totalQuantity, totalAmount, totalTaxAmount, totalIncludedAmount, money,
    addRow, removeRow, calculateRow, onProductChange, onStoreChange, onWarehouseChange, onItemWarehouseChange, save, clearForm, close, showNotice,
    onQuantityInput: index => calculateRow(form.value.items[index]), onPriceInput: index => calculateRow(form.value.items[index]), onTaxRateInput: index => calculateRow(form.value.items[index]),
    onIncludedPriceInput: index => { const item = form.value.items[index]; item.price = Number((Number(item.taxIncludedPrice || 0) / (1 + Number(item.taxRate || 0) / 100)).toFixed(4)); calculateRow(item) },
    printTemplateDialogOpen, printPreviewVisible, selectedPrintTemplate, selectedPrintPrinter, printPreviewAutoPrint,
    closePrintTemplateDialog, closePrintPreview, openPrint,
    previewSelectedPrintTemplate: (template, printer) => openPrintTemplate(template, printer, false),
    printSelectedPrintTemplate: (template, printer) => openPrintTemplate(template, printer, true),
    printVariables: computed(() => ({ ...form.value, orderNumber: form.value.documentNo, orderDate: form.value.documentDate, purchaseNumber: form.value.documentNo, purchaseDate: form.value.documentDate, storeName: selectedStore.value?.name || '', supplierName: selectedSupplier.value?.supplierName || selectedSupplier.value?.name || '', warehouseName: selectedWarehouse.value?.name || '', totalQuantity: totalQuantity.value, totalAmount: totalIncludedAmount.value, totalTaxAmount: totalTaxAmount.value, totalTaxIncludedAmount: totalIncludedAmount.value, items: form.value.items.filter(item => item.productId).map((item, index) => ({ ...item, index: index + 1, spec: item.specification, name: item.goodsName, receivedQty: item.quantity, unitPrice: item.price, warehouseName: item.warehouseName || selectedWarehouse.value?.name || '' })) })),
    printNumber: computed(() => form.value.documentNo)
  }
}
