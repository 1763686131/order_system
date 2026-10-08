import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import request from '@/api/request'
import { useUserStore } from '@/stores/user'
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
  const userStore = useUserStore()
  const validation = useDocumentValidation()
  const loading = ref(true)
  const loadFailed = ref(false)
  const saving = ref(false)
  const stores = ref([])
  const suppliers = ref([])
  const warehouses = ref([])
  const rawMaterialProducts = ref([])
  const finishedProducts = ref([])
  const units = ref([])
  const employees = ref([])
  const bankAccounts = ref([])
  const visiblePaymentAccountId = ref(null)
  const savedDocumentId = ref(props.documentId)
  const notice = ref({ visible: false, type: 'success', message: '' })
  const focusedRow = ref(-1)
  const productInputRefs = new Map()
  const productDropdownRef = ref(null)
  const productDropdownStyle = ref({})
  const focusedSupplierRow = ref(-1)
  const supplierInputRefs = new Map()
  const supplierDropdownRef = ref(null)
  const supplierDropdownStyle = ref({})
  const supplierSearch = ref('')
  const supplierPage = ref(1)
  const supplierDropdownOpen = ref(false)
  const SUPPLIER_PAGE_SIZE = 15
  let rowKey = 0
  let noticeTimer
  let redirectTimer
  const blankItem = () => ({
    key: ++rowKey, orderItemId: null, productId: '', productCode: '', goodsName: '',
    specification: '', unit: '', productType: '', categoryId: '', categoryName: '',
    warehouseId: '', warehouseName: '', quantity: '', supplierId: '', supplierName: '',
    price: '', amount: '', remark: '', showDropdown: false, filteredProducts: []
  })
  const blankForm = () => {
    const orderDate = localDate()
    return {
      orderNo: '', storeId: '', orderDate, expectedDate: dateAfter(orderDate),
      expectedDateAuto: true, purchaser: '', creator: '', paymentAmount: 0, paymentAmountTouched: false, otherFees: 0,
      settlementAccount: '', invoiceRequired: false, paymentMethod: '', paymentAccountId: '',
      currentPayment: 0, remark: '', status: 'draft',
      items: Array.from({ length: 8 }, blankItem)
    }
  }
  const form = ref(blankForm())
  const currentCreatorName = computed(() =>
    String(userStore.name || userStore.username || '').trim()
  )
  const creatorNameStyle = computed(() => {
    const nameLength = Array.from(currentCreatorName.value).length
    const width = Math.min(220, Math.max(78, nameLength * 16 + 24))
    return { width: `${width}px`, minWidth: `${width}px` }
  })
  const purchasePeople = computed(() => employees.value
    .filter(employee => employee.displayName)
    .slice()
    .sort((a, b) => String(a.displayName).localeCompare(String(b.displayName), 'zh-CN')))
  const storeBankAccounts = computed(() => bankAccounts.value
    .filter(account => String(account.storeId ?? account.store_id) === String(form.value.storeId))
    .slice()
    .sort((a, b) => Number(Boolean(b.isDefault)) - Number(Boolean(a.isDefault))))
  const selectedPaymentAccount = computed(() =>
    storeBankAccounts.value.find(account => String(account.id) === String(form.value.paymentAccountId)) || null
  )
  const paymentBalanceVisible = computed(() =>
    Boolean(form.value.paymentAccountId) && visiblePaymentAccountId.value === Number(form.value.paymentAccountId)
  )
  const accountBalanceLoading = ref(false)
  watch(currentCreatorName, creator => {
    if (!form.value.creator || form.value.status === 'draft') form.value.creator = creator
  }, { immediate: true })
  const filteredWarehouses = computed(() => warehouses.value.filter(warehouse =>
    String(warehouse.storeId ?? warehouse.store_id) === String(form.value.storeId)))
  const products = computed(() => [
    ...rawMaterialProducts.value.map(product => ({ ...product, productType: 'raw-material' })),
    ...finishedProducts.value.map(product => ({ ...product, productType: 'finished-product' }))
  ])
  const supplierSearchResults = computed(() => {
    const keyword = String(supplierSearch.value || '').trim().toLowerCase()
    if (!keyword) return suppliers.value
    return suppliers.value.filter(supplier => [
      supplier.supplierName, supplier.name, supplier.supplierCode, supplier.code,
      supplier.contactPerson, supplier.phone
    ].some(value => String(value || '').toLowerCase().includes(keyword)))
  })
  const supplierTotalPages = computed(() =>
    Math.max(1, Math.ceil(supplierSearchResults.value.length / SUPPLIER_PAGE_SIZE))
  )
  const paginatedSuppliers = computed(() => {
    const start = (supplierPage.value - 1) * SUPPLIER_PAGE_SIZE
    return supplierSearchResults.value.slice(start, start + SUPPLIER_PAGE_SIZE)
  })
  const categoriesForItem = item => {
    const warehouse = warehouses.value.find(candidate => String(candidate.id) === String(item?.warehouseId))
    return Array.isArray(warehouse?.categories) ? warehouse.categories : []
  }
  const productMatchesItem = (product, item) => {
    if (!form.value.storeId || !item?.warehouseId) return false
    if (categoriesForItem(item).length && !item.categoryId) return false
    const storeIds = product.storeIds || product.store_ids
    if (Array.isArray(storeIds) && storeIds.length &&
      !storeIds.map(value => String(value)).includes(String(form.value.storeId))) return false
    const warehouseId = String(item.warehouseId)
    const productWarehouseId = product.warehouseId ?? product.warehouse_id
    const warehouseMapping = product.warehouseCategories || product.warehouse_categories
    const hasWarehouseMapping = warehouseMapping && typeof warehouseMapping === 'object' &&
      Object.prototype.hasOwnProperty.call(warehouseMapping, warehouseId)
    if (productWarehouseId != null && String(productWarehouseId) !== warehouseId && !hasWarehouseMapping) return false
    if (item.categoryId) {
      const mappedCategories = hasWarehouseMapping
        ? (Array.isArray(warehouseMapping[warehouseId]) ? warehouseMapping[warehouseId] : []).map(value => String(value))
        : []
      const productCategory = product.categoryId ?? product.category ?? product.category_id
      if (mappedCategories.length
        ? !mappedCategories.includes(String(item.categoryId))
        : String(productCategory ?? '') !== String(item.categoryId)) return false
    }
    return true
  }
  const productsForItem = item => products.value
    .filter(product => product.enabled !== false && productMatchesItem(product, item))
  const getUnitName = unitId => units.value.find(unit => String(unit.id) === String(unitId))?.name || ''
  const getProductStock = product => Number(product?.currentStock ?? product?.stock ?? 0)
  const activeProductRow = computed(() => {
    const item = form.value.items[focusedRow.value]
    return item?.showDropdown ? item : null
  })
  const setProductInputRef = (index, element) => {
    if (element) productInputRefs.set(index, element)
    else productInputRefs.delete(index)
  }
  const setProductDropdownRef = element => { productDropdownRef.value = element }
  const updateProductDropdownPosition = () => {
    const input = productInputRefs.get(focusedRow.value)
    const item = activeProductRow.value
    if (!input || !item) {
      productDropdownStyle.value = {}
      return
    }

    const rect = input.getBoundingClientRect()
    const viewportPadding = 12
    const gap = 4
    const dropdownWidth = Math.min(720, Math.max(280, window.innerWidth - viewportPadding * 2))
    const estimatedHeight = Math.min(300, Math.max(42, item.filteredProducts.length * 42 + 42))
    const availableBelow = Math.max(80, window.innerHeight - rect.bottom - viewportPadding)
    const availableAbove = Math.max(80, rect.top - viewportPadding)
    const shouldOpenAbove = availableBelow < Math.min(estimatedHeight, 220) && availableAbove > availableBelow
    const maxHeight = Math.min(300, shouldOpenAbove ? availableAbove : availableBelow)
    const top = shouldOpenAbove
      ? Math.max(viewportPadding, rect.top - maxHeight - gap)
      : rect.bottom + gap
    const left = Math.min(
      Math.max(viewportPadding, rect.left),
      Math.max(viewportPadding, window.innerWidth - dropdownWidth - viewportPadding)
    )

    productDropdownStyle.value = {
      top: `${Math.round(top)}px`,
      left: `${Math.round(left)}px`,
      width: `${Math.round(dropdownWidth)}px`,
      maxHeight: `${Math.round(maxHeight)}px`
    }
  }
  const canOpenProductDropdown = item => Boolean(
    form.value.storeId &&
    item?.warehouseId &&
    !(categoriesForItem(item).length && !item.categoryId)
  )
  const productMatchesSearch = (product, searchText) => {
    const keyword = String(searchText || '').trim().toLowerCase()
    if (!keyword) return true
    return [product.code, product.name, product.specification]
      .filter(Boolean)
      .some(value => String(value).toLowerCase().includes(keyword))
  }
  const filterProducts = index => {
    const item = form.value.items[index]
    if (!item) return
    if (!canOpenProductDropdown(item)) {
      item.showDropdown = false
      item.filteredProducts = []
      if (focusedRow.value === index) productDropdownStyle.value = {}
      return
    }

    item.filteredProducts = productsForItem(item)
      .filter(product => productMatchesSearch(product, item.goodsName))
      .slice(0, 80)
    item.showDropdown = true
    focusedRow.value = index
    nextTick(updateProductDropdownPosition)
  }
  const showProductDropdown = index => {
    const item = form.value.items[index]
    if (!item || !canOpenProductDropdown(item)) return
    focusedRow.value = index
    item.showDropdown = true
    filterProducts(index)
  }
  const hideProductDropdown = index => {
    window.setTimeout(() => {
      const item = form.value.items[index]
      if (!item) return
      item.showDropdown = false
      if (focusedRow.value === index) productDropdownStyle.value = {}
    }, 180)
  }
  const closeProductDropdown = () => {
    form.value.items.forEach(item => {
      item.showDropdown = false
      item.filteredProducts = []
    })
    focusedRow.value = -1
    productDropdownStyle.value = {}
  }
  const setSupplierInputRef = (index, element) => {
    if (element) supplierInputRefs.set(index, element)
    else supplierInputRefs.delete(index)
  }
  const setSupplierDropdownRef = element => { supplierDropdownRef.value = element }
  const updateSupplierDropdownPosition = () => {
    const input = supplierInputRefs.get(focusedSupplierRow.value)
    if (!input || !supplierDropdownOpen.value) {
      supplierDropdownStyle.value = {}
      return
    }

    const rect = input.getBoundingClientRect()
    const viewportPadding = 12
    const gap = 4
    const dropdownWidth = Math.min(420, Math.max(280, window.innerWidth - viewportPadding * 2))
    const rowHeight = 38
    const paginationHeight = supplierTotalPages.value > 1 ? 44 : 0
    const desiredHeight = Math.min(
      620,
      Math.max(44, paginatedSuppliers.value.length * rowHeight + paginationHeight)
    )
    const spaceBelow = Math.max(120, window.innerHeight - rect.bottom - viewportPadding)
    const spaceAbove = Math.max(120, rect.top - viewportPadding)
    const shouldOpenAbove = desiredHeight > spaceBelow && spaceAbove > spaceBelow
    const availableHeight = shouldOpenAbove ? spaceAbove : spaceBelow
    const height = Math.min(desiredHeight, availableHeight)
    const top = shouldOpenAbove
      ? Math.max(viewportPadding, rect.top - height - gap)
      : Math.min(window.innerHeight - height - viewportPadding, rect.bottom + gap)
    const left = Math.min(
      Math.max(viewportPadding, rect.left),
      Math.max(viewportPadding, window.innerWidth - dropdownWidth - viewportPadding)
    )

    supplierDropdownStyle.value = {
      top: `${Math.round(top)}px`,
      left: `${Math.round(left)}px`,
      width: `${Math.round(dropdownWidth)}px`,
      height: `${Math.round(height)}px`
    }
  }
  const openSupplierDropdown = index => {
    if (!form.value.items[index]?.productId) return
    focusedSupplierRow.value = index
    supplierDropdownOpen.value = true
    supplierSearch.value = ''
    supplierPage.value = 1
    nextTick(updateSupplierDropdownPosition)
  }
  const hideSupplierDropdown = index => {
    window.setTimeout(() => {
      if (focusedSupplierRow.value === index) closeSupplierDropdown()
    }, 180)
  }
  const closeSupplierDropdown = () => {
    supplierDropdownOpen.value = false
    supplierSearch.value = ''
    supplierPage.value = 1
    focusedSupplierRow.value = -1
    supplierDropdownStyle.value = {}
  }
  const handleSupplierSearchInput = (index, event) => {
    focusedSupplierRow.value = index
    supplierDropdownOpen.value = true
    supplierSearch.value = event.target.value
    supplierPage.value = 1
    nextTick(updateSupplierDropdownPosition)
  }
  const selectSupplier = (index, supplier) => {
    const item = form.value.items[index]
    if (!item || !supplier) return
    item.supplierId = String(supplier.id)
    item.supplierName = supplier.supplierName || supplier.name || ''
    closeSupplierDropdown()
    supplierInputRefs.get(index)?.blur()
    validation.dismissValidationHint(`item-supplier-${index}`)
  }
  const changeSupplierPage = page => {
    supplierPage.value = Math.min(Math.max(1, page), supplierTotalPages.value)
    nextTick(updateSupplierDropdownPosition)
  }
  const clearProductSelection = item => Object.assign(item, {
    productId: '', productCode: '', goodsName: '', specification: '', unit: '', productType: '', price: '', amount: ''
  })
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
  const purchaseOrderPayable = computed(() => {
    const base = form.value.paymentAmount !== '' && form.value.paymentAmount != null
      ? Number(form.value.paymentAmount) || 0
      : totalAmount.value
    return Math.max(0, base + (Number(form.value.otherFees) || 0))
  })
  const currentPayable = computed(() => {
    if (form.value.payableCount) return Number(form.value.unpaidAmount || 0)
    return Math.max(0, purchaseOrderPayable.value - (Number(form.value.currentPayment) || 0))
  })
  const supplierPayable = computed(() => {
    const selectedSupplierIds = new Set(
      form.value.items
        .filter(item => item.productId && item.supplierId)
        .map(item => String(item.supplierId))
    )
    return [...selectedSupplierIds].reduce((sum, supplierId) => {
      const supplier = suppliers.value.find(item => String(item.id) === supplierId)
      return sum + (Number(supplier?.payable ?? supplier?.payableAmount) || 0)
    }, 0)
  })
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
  watch(totalAmount, value => {
    if (form.value.paymentAmount === '' || form.value.paymentAmount == null || !form.value.paymentAmountTouched) {
      form.value.paymentAmount = Number(value.toFixed(2))
    }
  })
  const markPaymentAmountManual = () => { form.value.paymentAmountTouched = true }
  const onPaymentMethodChange = () => {
    visiblePaymentAccountId.value = null
    form.value.paymentAccountId = form.value.paymentMethod === 'bank_transfer' && storeBankAccounts.value.length
      ? String(storeBankAccounts.value[0].id)
      : ''
    if (form.value.paymentMethod !== 'other') form.value.settlementAccount = ''
  }
  const hidePaymentAccountBalance = () => {
    visiblePaymentAccountId.value = null
  }
  const togglePaymentAccountBalance = async () => {
    if (!form.value.paymentAccountId || accountBalanceLoading.value) return
    const accountId = Number(form.value.paymentAccountId)
    if (visiblePaymentAccountId.value === accountId) {
      visiblePaymentAccountId.value = null
      return
    }
    accountBalanceLoading.value = true
    const storeId = form.value.storeId
    try {
      const response = await request({
        url: '/bank-accounts/options', method: 'GET',
        params: { storeId, includeBalance: 1 }
      })
      bankAccounts.value = [
        ...bankAccounts.value.filter(account => String(account.storeId) !== String(storeId)),
        ...response.data
      ]
      if (Number(form.value.paymentAccountId) === accountId && selectedPaymentAccount.value) {
        visiblePaymentAccountId.value = accountId
      }
    } catch (error) {
      showNotice(error?.response?.data?.message || error.message || '获取账户余额失败', 'error')
    } finally {
      accountBalanceLoading.value = false
    }
  }
  const onProductChange = item => {
    const product = productsForItem(item).find(candidate => String(candidate.id) === String(item.productId))
    if (!product) {
      clearProductSelection(item)
      return
    }
    item.productCode = product.code || ''
    item.goodsName = product.name || ''
    item.productType = product.productType
    item.specification = product.specification || ''
    item.unit = getUnitName(product.unitId) || product.unit || ''
    calculateRow(item)
  }
  const onProductInput = index => {
    const item = form.value.items[index]
    if (!item) return
    const searchText = item.goodsName
    if (item.productId) {
      clearProductSelection(item)
      item.goodsName = searchText
    }
    filterProducts(index)
  }
  const selectProduct = (index, product) => {
    const item = form.value.items[index]
    if (!item || !product) return
    item.productId = String(product.id)
    item.productType = product.productType || ''
    item.productCode = product.code || ''
    item.goodsName = product.name || ''
    item.specification = product.specification || ''
    item.unit = getUnitName(product.unitId) || product.unit || ''
    calculateRow(item)
    item.showDropdown = false
    item.filteredProducts = []
    if (focusedRow.value === index) productDropdownStyle.value = {}
    closeSupplierDropdown()
  }
  const onCategoryChange = item => {
    const category = categoriesForItem(item).find(candidate => String(candidate.id) === String(item.categoryId))
    item.categoryName = category?.name || ''
    if (item.productId && !productsForItem(item).some(product => String(product.id) === String(item.productId))) {
      clearProductSelection(item)
    }
  }
  const onItemWarehouseChange = item => {
    closeProductDropdown()
    closeSupplierDropdown()
    const warehouse = warehouses.value.find(candidate => String(candidate.id) === String(item.warehouseId))
    item.warehouseName = warehouse?.name || ''
    if (!categoriesForItem(item).some(category => String(category.id) === String(item.categoryId))) {
      item.categoryId = ''
      item.categoryName = ''
    } else {
      onCategoryChange(item)
    }
    if (item.productId && !productsForItem(item).some(product => String(product.id) === String(item.productId))) {
      clearProductSelection(item)
    }
  }
  const onStoreChange = () => {
    closeProductDropdown()
    closeSupplierDropdown()
    form.value.paymentAccountId = form.value.paymentMethod === 'bank_transfer' && storeBankAccounts.value.length
      ? String(storeBankAccounts.value[0].id)
      : ''
    visiblePaymentAccountId.value = null
    form.value.items.forEach(item => {
      if (item.warehouseId && !filteredWarehouses.value.some(warehouse => String(warehouse.id) === String(item.warehouseId))) {
        item.warehouseId = ''
        item.warehouseName = ''
        item.categoryId = ''
        item.categoryName = ''
        clearProductSelection(item)
      } else {
        onItemWarehouseChange(item)
      }
    })
    validation.dismissValidationHint()
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
      orderNo: data.orderNo || '', version: data.version, orderDate, expectedDate: data.expectedDate || dateAfter(orderDate),
      expectedDateAuto: !data.expectedDate || data.expectedDate === dateAfter(orderDate),
      storeId: data.storeId ? String(data.storeId) : '', purchaser: data.purchaser || '',
      creator: data.creator || currentCreatorName.value,
      paymentAmount: data.paymentAmount ?? '',
      paymentAmountTouched: data.paymentAmount != null,
      otherFees: data.otherFees ?? 0,
      settlementAccount: data.settlementAccount || '',
      invoiceRequired: Boolean(data.invoiceRequired),
      paymentMethod: data.paymentMethod || '',
      paymentAccountId: data.paymentAccountId ? String(data.paymentAccountId) : '',
      currentPayment: data.currentPayment ?? 0,
      remark: data.remark || '', status: data.status || 'draft',
      confirmedPayable: data.confirmedPayable || 0, unpaidAmount: data.unpaidAmount || 0,
      payableCount: data.payableCount || 0,
      billedAmount: data.billedAmount || 0, allocatedAmount: data.allocatedAmount || 0,
      items: (data.items || []).map(item => ({
        ...blankItem(), orderItemId: item.orderItemId || item.id,
        productId: item.productId ? String(item.productId) : '', productCode: item.productCode || '',
        goodsName: item.productName || '', specification: item.specification || '', unit: item.unit || '',
        productType: item.productType === 'finished-product' ? 'finished-product' : '',
        categoryId: item.categoryId ? String(item.categoryId) : '', categoryName: item.categoryName || '',
        warehouseId: item.warehouseId ? String(item.warehouseId) : '', warehouseName: item.warehouseName || '',
        quantity: item.orderedQty ?? '', supplierId: item.supplierId ? String(item.supplierId) : '',
        supplierName: item.supplierName || '', price: item.unitPrice ?? '', amount: item.amount ?? '', remark: item.remark || ''
      }))
    }
    const minimumRows = readOnly.value ? 1 : 8
    while (form.value.items.length < minimumRows) form.value.items.push(blankItem())
  }
  const restoreDraft = draft => {
    form.value = JSON.parse(JSON.stringify(draft.form))
    form.value.purchaser ??= ''
    form.value.creator ||= currentCreatorName.value
    form.value.paymentAmount ??= ''
    form.value.otherFees ??= 0
    form.value.settlementAccount ??= ''
    form.value.currentPayment ??= 0
    form.value.items = form.value.items.map(item => ({
      productType: '', categoryId: '', categoryName: '', warehouseId: '', warehouseName: '', ...item
    }))
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
    form.value.creator = currentCreatorName.value
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
    window.addEventListener('resize', updateProductDropdownPosition)
    window.addEventListener('scroll', updateProductDropdownPosition, true)
    window.addEventListener('resize', updateSupplierDropdownPosition)
    window.addEventListener('scroll', updateSupplierDropdownPosition, true)
    try {
      const [storeData, supplierData, warehouseData, rawMaterialData, finishedProductData, unitData] = await Promise.all([
        request({ url: '/stores', method: 'GET' }), request({ url: '/suppliers', method: 'GET' }),
        request({ url: '/warehouses', method: 'GET' }),
        request({ url: '/raw-material-products', method: 'GET' }),
        request({ url: '/products', method: 'GET' }),
        request({ url: '/products/units/measurements', method: 'GET' }),
      ])
      const [directoryResult, bankAccountResult] = await Promise.allSettled([
        request({ url: '/admin/directory', method: 'GET' }),
        request({ url: '/bank-accounts/options', method: 'GET' })
      ])
      const directoryData = directoryResult.status === 'fulfilled' ? directoryResult.value : null
      const bankAccountData = bankAccountResult.status === 'fulfilled' ? bankAccountResult.value : null
      stores.value = Array.isArray(storeData) ? storeData.filter(item => item.status !== 'inactive') : []
      suppliers.value = Array.isArray(supplierData) ? supplierData.filter(item => item.status !== 'inactive') : []
      warehouses.value = Array.isArray(warehouseData) ? warehouseData.filter(item => item.status !== 'inactive') : []
      rawMaterialProducts.value = Array.isArray(rawMaterialData) ? rawMaterialData.filter(item => item.enabled !== false) : []
      finishedProducts.value = Array.isArray(finishedProductData) ? finishedProductData.filter(item => item.enabled !== false) : []
      units.value = Array.isArray(unitData) ? unitData : []
      employees.value = Array.isArray(directoryData?.employees)
        ? directoryData.employees.map(employee => ({
            ...employee,
            displayName: employee.displayName || employee.name || employee.username || ''
          }))
        : []
      bankAccounts.value = Array.isArray(bankAccountData?.data)
        ? bankAccountData.data
        : (Array.isArray(bankAccountData?.items) ? bankAccountData.items : [])
      form.value.creator = currentCreatorName.value
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
    window.removeEventListener('resize', updateProductDropdownPosition)
    window.removeEventListener('scroll', updateProductDropdownPosition, true)
    window.removeEventListener('resize', updateSupplierDropdownPosition)
    window.removeEventListener('scroll', updateSupplierDropdownPosition, true)
    productInputRefs.clear()
    supplierInputRefs.clear()
  })
  return {
    ...validation, config, form, loading, loadFailed, saving, readOnly, auditMode, statusLabel,
    stores, suppliers, filteredWarehouses, products, savedDocumentId, notice, totalQuantity, totalAmount,
    currentCreatorName, creatorNameStyle, purchasePeople, storeBankAccounts,
    supplierPayable, purchaseOrderPayable, currentPayable,
    productsForItem, categoriesForItem, addRow, removeRow, onProductChange, onProductInput, selectProduct,
    showProductDropdown, hideProductDropdown, closeProductDropdown, activeProductRow, focusedRow,
    productDropdownRef, productDropdownStyle, setProductInputRef, setProductDropdownRef,
    getUnitName, getProductStock,
    supplierDropdownOpen, supplierSearch, supplierPage, paginatedSuppliers, supplierTotalPages,
    focusedSupplierRow, supplierDropdownStyle, setSupplierInputRef, setSupplierDropdownRef,
    openSupplierDropdown, hideSupplierDropdown, closeSupplierDropdown,
    handleSupplierSearchInput, selectSupplier, changeSupplierPage,
    onCategoryChange,
    onItemWarehouseChange, onStoreChange, onDateChange, onExpectedDateInput, restoreDraft,
    visiblePaymentAccountId, selectedPaymentAccount, paymentBalanceVisible, accountBalanceLoading,
    markPaymentAmountManual, onPaymentMethodChange, hidePaymentAccountBalance, togglePaymentAccountBalance,
    validateForm, save, clearForm, close,
    onQuantityInput: index => calculateRow(form.value.items[index]),
    onPriceInput: index => calculateRow(form.value.items[index])
  }
}
