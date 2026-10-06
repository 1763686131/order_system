import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import request from '@/api/request'
import { useUserStore } from '@/stores/user'
import { DOCUMENT_TYPES, inboundAmounts, isLockedInbound, localDate, money, purchasePayload, validatePurchase } from './documentModels'
import { useDocumentValidation } from './useDocumentValidation'

const BLANK_ROWS = 8
let rowKey = 0
const blankItem = () => ({
  key: ++rowKey, productType: '',
  purchaseOrderItemId: '', productId: '', productCode: '', goodsName: '', specification: '', unit: '', warehouseId: '', warehouseName: '', expectedQty: '',
  quantity: '', price: '', taxRate: 0, amount: 0, taxAmount: 0, taxIncludedAmount: 0,
  batchNo: '', binCode: '', remark: ''
})
const blankRows = () => Array.from({ length: BLANK_ROWS }, blankItem)

export function usePurchaseDocument(props) {
  const router = useRouter()
  const userStore = useUserStore()
  const validation = useDocumentValidation()
  const stores = ref([])
  const suppliers = ref([])
  const warehouses = ref([])
  const products = ref([])
  const units = ref([])
  const normalizeInboundType = value => String(value || '').toLowerCase() === 'finished-product'
    ? 'finished-product'
    : 'raw-material'
  const inboundType = ref(normalizeInboundType(props.productType))
  const form = ref({
    type: inboundType.value, storeId: '', supplierId: '', supplierName: '', warehouseId: '', purchaseOrderId: props.purchaseOrderId || null, documentDate: localDate(), documentNo: '',
    inspector: '', qualityNo: '', remark: '', taxEnabled: false, items: blankRows(),
    attachments: [], status: 'draft'
  })
  const saving = ref(false)
  const loading = ref(true)
  const loadFailed = ref(false)
  const savedDocumentId = ref(props.documentId)
  const purchaseOrderId = ref(props.purchaseOrderId || null)
  const purchaseOrder = ref(null)
  const inboundTypes = computed(() => purchaseOrder.value
    ? [...new Set((purchaseOrder.value.items || [])
      .filter(item => Number(item.remainingQty ?? item.orderedQty ?? 0) > 0)
      .map(item => normalizeInboundType(item.productType)))]
    : ['raw-material', 'finished-product'])
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
  const productsForItem = item => productOptions.value.filter(product =>
    product.productType === (item?.productType || inboundType.value)
    && (!product.warehouseId || String(product.warehouseId) === String(item?.warehouseId || form.value.warehouseId)))
  const selectedStore = computed(() => stores.value.find(item => String(item.id) === String(form.value.storeId)))
  const selectedSupplier = computed(() => suppliers.value.find(item => String(item.id) === String(form.value.supplierId)))
  const selectedWarehouse = computed(() => warehouses.value.find(item => String(item.id) === String(form.value.warehouseId)))
  const documentSource = computed(() => purchaseOrderId.value ? '采购订单' : '其他入库')
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
  const setInboundType = value => {
    inboundType.value = normalizeInboundType(value)
    form.value.type = inboundType.value
  }
  const onStoreChange = () => {
    if (purchaseOrderId.value) {
      form.value.warehouseId = ''
      form.value.items.forEach(item => {
        if (item.productId) {
          item.warehouseId = ''
          item.warehouseName = ''
          item.currentStock = 0
        }
      })
      return
    }
    form.value.supplierId = ''
    form.value.warehouseId = ''
    form.value.items = blankRows()
  }
  const onWarehouseChange = () => {
    if (purchaseOrderId.value) {
      form.value.items.forEach(item => {
        if (item.productId) {
          item.warehouseId = form.value.warehouseId || ''
          onItemWarehouseChange(item)
        }
      })
      return
    }
    form.value.items = blankRows()
  }
  const getProductStock = (product, item = {}) => stockBalances.value.filter(balance =>
    balance.productType === product.productType
    && String(balance.productId) === String(product.id)
    && String(balance.storeId) === String(form.value.storeId)
    && String(balance.warehouseId) === String(item.warehouseId || form.value.warehouseId))
    .reduce((sum, balance) => sum + Number(balance.quantity || 0), 0)
  const onItemWarehouseChange = item => {
    item.warehouseName = warehouses.value.find(warehouse => String(warehouse.id) === String(item.warehouseId))?.name || ''
    const product = productOptions.value.find(candidate =>
      candidate.productType === (item.productType || inboundType.value)
      && String(candidate.id) === String(item.productId))
    if (product) item.currentStock = getProductStock(product, item)
  }
  const onProductChange = item => {
    const product = productsForItem(item).find(candidate => String(candidate.id) === String(item.productId))
    if (!product) {
      Object.assign(item, blankItem(), { key: item.key })
      return
    }
    item.productType = product.productType
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
    const productTypes = purchaseOrderId.value
      ? ['raw-material', 'finished-product']
      : [inboundType.value]
    const productUrls = productTypes.map(type => type === 'raw-material' ? '/raw-material-products' : '/products')
    const [storeData, supplierData, warehouseData, productData, unitData, stockData] = await Promise.all([
      request({ url: '/stores', method: 'GET' }),
      request({ url: '/suppliers', method: 'GET' }),
      request({ url: '/warehouses', method: 'GET' }),
      Promise.all(productUrls.map(url => request({ url, method: 'GET' }))),
      request({ url: '/products/units/measurements', method: 'GET' }),
      Promise.all(productTypes.map(type => request({ url: '/stock-balances', method: 'GET', params: { type } })))
    ])
    stores.value = Array.isArray(storeData) ? storeData.filter(item => item.status !== 'inactive') : []
    suppliers.value = Array.isArray(supplierData) ? supplierData.filter(item => item.status !== 'inactive') : []
    warehouses.value = Array.isArray(warehouseData) ? warehouseData : []
    products.value = productData.flatMap((entries, index) =>
      (Array.isArray(entries) ? entries : []).map(product => ({ ...product, productType: productTypes[index] })))
    units.value = Array.isArray(unitData) ? unitData : []
    stockBalances.value = stockData.flatMap(entries => Array.isArray(entries) ? entries : [])
  }
  const normalizeInbound = data => {
    setInboundType(data.type)
    purchaseOrderId.value = data.purchaseOrderId || null
    form.value.purchaseOrderId = purchaseOrderId.value
    form.value = {
      ...form.value,
      type: inboundType.value,
      storeId: data.storeId ? String(data.storeId) : '',
      supplierId: data.supplierId ? String(data.supplierId) : '',
      supplierName: data.supplierName || '',
      warehouseId: data.warehouseId ? String(data.warehouseId) : '',
      documentDate: data.documentDate || localDate(), documentNo: data.documentNo || '',
      inspector: data.inspector || '', qualityNo: data.qualityNo || '', remark: data.remark || '',
      status: data.status || 'draft',
      taxEnabled: (data.items || []).some(item => Number(item.taxRate) > 0),
      attachments: data.attachments || [],
      items: (data.items || []).map(item => ({
        ...blankItem(), productType: normalizeInboundType(item.productType || data.type), purchaseOrderItemId: item.purchaseOrderItemId || '', productId: item.productId ? String(item.productId) : '', productCode: item.productCode || '', warehouseId: String(item.warehouseId || data.warehouseId || ''), warehouseName: warehouses.value.find(warehouse => String(warehouse.id) === String(item.warehouseId || data.warehouseId))?.name || '',
        goodsName: item.productName || item.goodsName || '', specification: item.specification || '', unit: item.unit || '',
        expectedQty: item.expectedQty ?? '', quantity: item.receivedQty ?? '', price: item.unitPrice ?? '',
        taxRate: Number(item.taxRate || 0), amount: Number(item.totalAmount || 0) - Number(item.taxAmount || 0),
        taxAmount: Number(item.taxAmount || 0), taxIncludedAmount: Number(item.totalAmount || 0), batchNo: item.batchNo || '',
        binCode: item.binCode || '', remark: item.remark || ''
      })).concat(blankRows()).slice(0, Math.max(BLANK_ROWS, (data.items || []).length + 1))
    }
    form.value.items.filter(item => item.productId).forEach(onItemWarehouseChange)
  }
  const normalizePurchaseOrder = data => {
    const remainingItems = (data.items || [])
      .filter(item => Number(item.remainingQty ?? item.orderedQty ?? 0) > 0)
    purchaseOrder.value = data
    purchaseOrderId.value = data.orderId || data.id || purchaseOrderId.value
    form.value.purchaseOrderId = purchaseOrderId.value
    const defaultWarehouse = remainingItems.find(item => item.warehouseId && warehouses.value.some(warehouse =>
      String(warehouse.id) === String(item.warehouseId) && String(warehouse.storeId ?? warehouse.store_id) === String(data.storeId)))
    form.value = {
      ...form.value,
      type: inboundType.value,
      storeId: data.storeId ? String(data.storeId) : '',
      supplierId: data.supplierId ? String(data.supplierId) : '',
      supplierName: data.supplierName || '',
      warehouseId: defaultWarehouse ? String(defaultWarehouse.warehouseId) : '',
      documentDate: localDate(),
      documentNo: data.inboundDocumentNo || '',
      remark: data.remark || '',
      items: remainingItems.map(item => ({
        ...blankItem(), productType: normalizeInboundType(item.productType), purchaseOrderItemId: item.orderItemId || item.id || '',
        productId: item.productId ? String(item.productId) : '', productCode: item.productCode || '',
        goodsName: item.productName || '', specification: item.specification || '', unit: item.unit || '',
        warehouseId: item.warehouseId ? String(item.warehouseId) : '', warehouseName: item.warehouseName || '',
        expectedQty: item.remainingQty ?? item.orderedQty ?? '', quantity: item.remainingQty ?? item.orderedQty ?? '',
        price: item.unitPrice ?? '', amount: 0
      })).concat(blankRows()).slice(0, Math.max(BLANK_ROWS, remainingItems.length + 1))
    }
    form.value.items.filter(item => item.productId).forEach(item => { item.warehouseId = item.warehouseId || form.value.warehouseId; onItemWarehouseChange(item); calculateRow(item) })
  }
  const loadExisting = async () => {
    if (!props.documentId) {
      if (props.purchaseOrderId) {
        const data = await request({ url: `/purchase-orders/${props.purchaseOrderId}/available-inbound`, method: 'GET' })
        purchaseOrder.value = data
        const type = inboundTypes.value.includes(inboundType.value) ? inboundType.value : inboundTypes.value[0]
        if (type && type !== inboundType.value) {
          setInboundType(type)
          await loadData()
        }
        normalizePurchaseOrder(data)
      }
      return
    }
    const data = await request({ url: `/stock-inbounds/${props.documentId}`, method: 'GET' })
    purchaseOrderId.value = data.purchaseOrderId || null
    if (data.type !== inboundType.value) {
      setInboundType(data.type)
    }
    if (purchaseOrderId.value) await loadData()
    normalizeInbound(data)
    readOnly.value = props.action === 'view' || isLockedInbound(form.value.status)
  }
  const restoreDraft = async draft => {
    if (!props.documentId && draft?.savedDocumentId) {
      try {
        const saved = await request({ url: `/stock-inbounds/${draft.savedDocumentId}`, method: 'GET' })
        if (isLockedInbound(saved.status)) return false
      } catch (error) {
        if (error?.response?.status !== 404) {
          showNotice(error?.response?.data?.message || error.message || '读取已保存批次失败', 'error')
        }
        return false
      }
    }
    const savedForm = JSON.parse(JSON.stringify(draft?.form || {}))
    const savedType = normalizeInboundType(savedForm.type || inboundType.value)
    if (savedType !== inboundType.value) {
      setInboundType(savedType)
      try {
        await loadData()
      } catch (error) {
        loadFailed.value = true
        showNotice(error?.response?.data?.message || error.message || '加载进货商品失败', 'error')
        return false
      }
    }
    form.value = {
      ...form.value,
      ...savedForm,
      type: savedType,
      items: Array.isArray(savedForm.items) ? savedForm.items : blankRows()
    }
    purchaseOrderId.value = form.value.purchaseOrderId || null
    savedDocumentId.value = draft?.savedDocumentId ?? props.documentId
    rowKey = Math.max(rowKey, ...form.value.items.map(item => Number(item.key) || 0))
  }
  const changeInboundType = type => router.push({
    name: 'admin-purchase-inbound-create',
    query: {
      ...(purchaseOrderId.value ? { purchaseOrderId: purchaseOrderId.value } : {}),
      ...(props.supplement ? { supplement: '1' } : {}),
      productType: normalizeInboundType(type)
    }
  })
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
    purchaseOrderId.value = null
    purchaseOrder.value = null
    form.value = { ...form.value, type: inboundType.value, storeId: '', supplierId: '', supplierName: '', warehouseId: '', purchaseOrderId: null, documentDate: localDate(), items: blankRows(), taxEnabled: false, inspector: '', qualityNo: '', remark: '' }
    if (!props.documentId) { savedDocumentId.value = null; form.value.documentNo = ''; form.value.attachments = [] }
  }
  const close = () => router.push({ name: 'admin-purchase-inbound' })
  onMounted(async () => {
    try { await loadData(); await loadExisting() } catch (error) { loadFailed.value = true; showNotice(error?.response?.data?.message || error.message || '加载进货单失败', 'error') } finally { loading.value = false }
  })
  onBeforeUnmount(() => window.clearTimeout(showNotice.timer))

  return {
    ...validation, validateForm, restoreDraft,
    config: { ...DOCUMENT_TYPES.purchase, title: props.supplement ? '补充入库' : '进货单', dateLabel: '入库日期' }, inboundType, inboundTypes, changeInboundType, form, stores, suppliers: filteredSuppliers, filteredWarehouses, products: productOptions, productsForItem, units, getProductStock,
    currentCreatorName, selectedStore, selectedSupplier, selectedWarehouse, documentSource, savedDocumentId, purchaseOrderId, purchaseOrder, saving, loading, loadFailed, readOnly, notice,
    taxEnabled: computed({ get: () => form.value.taxEnabled, set: value => { form.value.taxEnabled = value; form.value.items.forEach(item => { item.taxRate = value ? Number(item.taxRate) || 13 : 0; calculateRow(item) }) } }),
    totalPackages, totalQuantity, totalAmount, totalTaxAmount, totalIncludedAmount, money,
    addRow, removeRow, calculateRow, onProductChange, onStoreChange, onWarehouseChange, onItemWarehouseChange, save, clearForm, close, showNotice,
    onQuantityInput: index => calculateRow(form.value.items[index]), onPriceInput: index => calculateRow(form.value.items[index]), onTaxRateInput: index => calculateRow(form.value.items[index]),
    onIncludedPriceInput: index => { const item = form.value.items[index]; item.price = Number((Number(item.taxIncludedPrice || 0) / (1 + Number(item.taxRate || 0) / 100)).toFixed(4)); calculateRow(item) },
    printTemplateDialogOpen, printPreviewVisible, selectedPrintTemplate, selectedPrintPrinter, printPreviewAutoPrint,
    closePrintTemplateDialog, closePrintPreview, openPrint,
    previewSelectedPrintTemplate: (template, printer) => openPrintTemplate(template, printer, false),
    printSelectedPrintTemplate: (template, printer) => openPrintTemplate(template, printer, true),
    printVariables: computed(() => ({ ...form.value, orderNumber: form.value.documentNo, orderDate: form.value.documentDate, purchaseNumber: form.value.documentNo, purchaseDate: form.value.documentDate, storeName: selectedStore.value?.name || '', supplierName: selectedSupplier.value?.supplierName || selectedSupplier.value?.name || form.value.supplierName || '', warehouseName: selectedWarehouse.value?.name || '', totalQuantity: totalQuantity.value, totalAmount: totalIncludedAmount.value, totalTaxAmount: totalTaxAmount.value, totalTaxIncludedAmount: totalIncludedAmount.value, items: form.value.items.filter(item => item.productId).map((item, index) => ({ ...item, index: index + 1, spec: item.specification, name: item.goodsName, receivedQty: item.quantity, unitPrice: item.price, warehouseName: item.warehouseName || selectedWarehouse.value?.name || '' })) })),
    printNumber: computed(() => form.value.documentNo)
  }
}
