import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import request from '@/api/request'
import { useUserStore } from '@/stores/user'
import { localDate } from './documentModels'

export function useReturnDocument(props) {
  const router = useRouter()
  const userStore = useUserStore()
  const loading = ref(true)
  const loadFailed = ref(false)
  const readOnly = ref(props.action === 'view')
  const productType = ref(props.productType)
  const currentCreatorName = computed(() =>
    String(userStore.name || userStore.username || '').trim()
  )
  const creatorNameStyle = computed(() => {
    const nameLength = Array.from(currentCreatorName.value).length
    const width = Math.min(220, Math.max(78, nameLength * 16 + 24))
    return {
      width: `${width}px`,
      minWidth: `${width}px`
    }
  })
  const saving = ref(false)
  const savedReturnId = ref(props.returnId)
  const stores = ref([])
  const customers = ref([])
  const warehouses = ref([])
  const products = ref([])
  const units = ref([])
  const stockBalances = ref([])
  const bankAccounts = ref([])
  const packagingUnits = ref([])
  const employees = ref([])
  const departments = ref([])
  const focusedRow = ref(-1)
  const productInputRefs = new Map()
  const productDropdownRef = ref(null)
  const productDropdownStyle = ref({})
  const customerSearch = ref('')
  const customerPage = ref(1)
  const customerDropdownOpen = ref(false)
  const customerInputRef = ref(null)
  const customerDropdownRef = ref(null)
  const customerDropdownStyle = ref({})
  const CUSTOMER_PAGE_SIZE = 15
  const printTemplateDialogOpen = ref(false)
  const printPreviewVisible = ref(false)
  const selectedPrintTemplate = ref(null)
  const selectedPrintPrinter = ref(null)
  const printPreviewAutoPrint = ref(false)
  const notice = ref({ visible: false, type: 'success', message: '' })
  let noticeTimer = null
  let rowKey = 0
  const ORDER_FORM_DEFAULTS_STORAGE_KEY = 'admin_order_form_default_selections'
  
  const readOrderFormDefaults = () => {
    if (typeof window === 'undefined') {
      return { settlementAccountsByStore: {} }
    }
  
    try {
      const parsed = JSON.parse(window.localStorage.getItem(ORDER_FORM_DEFAULTS_STORAGE_KEY) || '{}')
      if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
        return { settlementAccountsByStore: {} }
      }
  
      const defaults = { ...parsed }
      delete defaults.creator
  
      return {
        ...defaults,
        settlementAccountsByStore: parsed.settlementAccountsByStore &&
          typeof parsed.settlementAccountsByStore === 'object' &&
          !Array.isArray(parsed.settlementAccountsByStore)
          ? parsed.settlementAccountsByStore
          : {}
      }
    } catch (error) {
      console.warn('读取订单默认选项失败:', error)
      return { settlementAccountsByStore: {} }
    }
  }
  
  const today = localDate
  const blankItem = () => ({
    key: ++rowKey,
    productId: '',
    productCode: '',
    goodsName: '',
    specification: '',
    unit: '',
    warehouseId: '',
    currentStock: 0,
    packages: null,
    quantity: null,
    price: null,
    amount: 0,
    taxRate: 13,
    taxIncludedPrice: 0,
    taxAmount: 0,
    taxIncludedAmount: 0,
    conversionRate: null,
    unitConversions: [],
    remark: '',
    showDropdown: false,
    filteredProducts: []
  })
  
  const form = ref({
    storeId: '',
    customerId: '',
    warehouseId: '',
    returnDate: today(),
    originalOrderNumber: '',
    returnNumber: '',
    taxEnabled: false,
    items: Array.from({ length: 8 }, blankItem),
    returnAmount: 0,
    refundAmount: 0,
    settlementAccount: '',
    salesPerson: '',
    creator: '',
    packaging: '桶装',
    remark: ''
  })
  
  watch(currentCreatorName, creator => {
    form.value.creator = creator
  }, { immediate: true })
  
  const idEquals = (a, b) => String(a ?? '') === String(b ?? '')
  const asIds = value => {
    if (Array.isArray(value)) return value
    if (typeof value === 'string') {
      try {
        const parsed = JSON.parse(value)
        return Array.isArray(parsed) ? parsed : []
      } catch {
        return value.split(',').map(item => item.trim()).filter(Boolean)
      }
    }
    return []
  }
  
  const filteredCustomers = computed(() => {
    if (!form.value.storeId) return []
    return customers.value.filter(item => idEquals(item.storeId ?? item.store_id, form.value.storeId))
  })
  
  const customerSearchResults = computed(() => {
    const keyword = String(customerSearch.value || '').trim().toLowerCase()
    if (!keyword) return filteredCustomers.value
  
    return filteredCustomers.value.filter(customer => [
      customer.customerName,
      customer.name,
      customer.customerCode,
      customer.code,
      customer.contactPerson,
      customer.phone
    ].some(value => String(value || '').toLowerCase().includes(keyword)))
  })
  
  const customerTotalPages = computed(() => Math.max(
    1,
    Math.ceil(customerSearchResults.value.length / CUSTOMER_PAGE_SIZE)
  ))
  
  const paginatedCustomers = computed(() => {
    const start = (customerPage.value - 1) * CUSTOMER_PAGE_SIZE
    return customerSearchResults.value.slice(start, start + CUSTOMER_PAGE_SIZE)
  })
  
  const filteredWarehouses = computed(() => {
    if (!form.value.storeId) return []
    return warehouses.value.filter(item => idEquals(item.storeId ?? item.store_id, form.value.storeId))
  })
  
  const storeBankAccounts = computed(() => bankAccounts.value
    .filter(account => idEquals(account.storeId, form.value.storeId))
    .slice()
    .sort((a, b) => Number(Boolean(b.isDefault)) - Number(Boolean(a.isDefault))))
  
  const getPreferredSettlementAccount = () => {
    if (!form.value.storeId) return ''
    const defaults = readOrderFormDefaults()
    const storeKey = String(form.value.storeId)
    const accountDefaults = defaults.settlementAccountsByStore
    if (Object.prototype.hasOwnProperty.call(accountDefaults, storeKey)) {
      const savedAccount = accountDefaults[storeKey] || ''
      if (!savedAccount || storeBankAccounts.value.some(account =>
        (account.value || account.accountName) === savedAccount
      )) {
        return savedAccount
      }
    }
  
    const defaultAccount = storeBankAccounts.value.find(account => account.isDefault) ||
      storeBankAccounts.value[0]
    return defaultAccount?.value || defaultAccount?.accountName || ''
  }
  
  const applyOrderFormDefaults = () => {
    const defaults = readOrderFormDefaults()
    form.value.packaging = defaults.packaging || '桶装'
    form.value.salesPerson = salesPeople.value.some(employee =>
      employee.displayName === defaults.salesPerson
    ) ? defaults.salesPerson : ''
    form.value.creator = currentCreatorName.value
    form.value.settlementAccount = getPreferredSettlementAccount()
  }
  
  const persistOrderFormDefaults = () => {
    const defaults = readOrderFormDefaults()
    const nextDefaults = {
      ...defaults,
      packaging: form.value.packaging || '桶装',
      salesPerson: form.value.salesPerson || '',
      settlementAccountsByStore: {
        ...(defaults.settlementAccountsByStore || {})
      }
    }
    if (form.value.storeId) {
      nextDefaults.settlementAccountsByStore[String(form.value.storeId)] =
        form.value.settlementAccount || ''
    }
    if (typeof window === 'undefined') return
  
    try {
      window.localStorage.setItem(ORDER_FORM_DEFAULTS_STORAGE_KEY, JSON.stringify(nextDefaults))
    } catch (error) {
      console.warn('保存订单默认选项失败:', error)
    }
  }
  
  const salesPeople = computed(() => {
    const salesDepartmentIds = new Set(
      departments.value
        .filter(department => department.name === '销售部')
        .map(department => String(department.id))
    )
  
    return employees.value.filter(employee =>
      employee.displayName &&
      (employee.departmentIds || []).some(id => salesDepartmentIds.has(String(id)))
    )
  })
  
  const packagingOptions = computed(() => {
    const customPackaging = packagingUnits.value
      .map(unit => unit.name)
      .filter(Boolean)
  
    return [...new Set([
      '无',
      '桶装',
      '纸箱',
      '托盘',
      '袋装',
      ...customPackaging,
      ...(form.value.packaging ? [form.value.packaging] : [])
    ])]
  })
  
  const productsForItem = item => {
    if (!form.value.storeId) return []
    let result = products.value.filter(product =>
      asIds(product.storeIds ?? product.store_ids).some(id => idEquals(id, form.value.storeId))
    )
    if (item?.warehouseId) {
      result = result.filter(product =>
        !product.warehouseId || idEquals(product.warehouseId, item.warehouseId)
      )
    } else if (form.value.warehouseId) {
      result = result.filter(product =>
        !product.warehouseId || idEquals(product.warehouseId, form.value.warehouseId)
      )
    }
    return result
  }
  
  const totalPackages = computed(() => form.value.items.reduce((sum, item) => sum + (Number(item.packages) || 0), 0))
  const totalQuantity = computed(() => form.value.items.reduce((sum, item) => sum + (Number(item.quantity) || 0), 0))
  const totalAmount = computed(() => form.value.items.reduce((sum, item) => sum + (Number(item.amount) || 0), 0))
  const totalTaxAmount = computed(() => form.value.items.reduce((sum, item) => sum + (Number(item.taxAmount) || 0), 0))
  const totalTaxIncludedAmount = computed(() => form.value.items.reduce((sum, item) => sum + (Number(item.taxIncludedAmount) || 0), 0))
  
  const money = value => Number(value || 0).toFixed(2)
  const number = value => Number(value || 0).toFixed(2)
  const getUnitName = unitId => {
    const unit = units.value.find(item => idEquals(item.id, unitId))
    return unit?.name || ''
  }
  
  const getProductStock = (product, item = {}) => {
    if (product?.stock !== undefined && product?.stock !== null) {
      return Number(product.stock || 0)
    }
    return stockBalances.value
      .filter(balance =>
        idEquals(balance.productId, product?.id) &&
        (!form.value.storeId || idEquals(balance.storeId, form.value.storeId)) &&
        (!item.warehouseId || idEquals(balance.warehouseId, item.warehouseId))
      )
      .reduce((sum, balance) => sum + (Number(balance.quantity) || 0), 0)
  }
  
  const selectedStoreName = computed(() => {
    const store = stores.value.find(item => idEquals(item.id, form.value.storeId))
    return store?.name || ''
  })
  
  const selectedCustomerName = computed(() => {
    const customer = customers.value.find(item => idEquals(item.id, form.value.customerId))
    return customer?.customerName || customer?.name || ''
  })
  
  const selectedWarehouseName = computed(() => {
    const warehouse = warehouses.value.find(item => idEquals(item.id, form.value.warehouseId))
    return warehouse?.name || ''
  })
  
  const activeProductItem = computed(() => {
    const item = form.value.items[focusedRow.value]
    return item?.showDropdown ? item : null
  })
  
  const returnPrintVariables = computed(() => {
    const taxEnabled = Boolean(form.value.taxEnabled)
    const validItems = form.value.items
      .filter(item => item.productId || item.goodsName)
      .map((item, index) => ({
        index: index + 1,
        productId: item.productId || '',
        productCode: item.productCode || '',
        goodsName: item.goodsName || '',
        spec: item.specification || '',
        specification: item.specification || '',
        unit: item.unit || '',
        warehouseId: item.warehouseId || '',
        warehouseName: selectedWarehouseName.value,
        currentStock: Number(item.currentStock) || 0,
        conversionRate: Number(item.conversionRate) || 0,
        unitConversions: Array.isArray(item.unitConversions) ? item.unitConversions : [],
        packages: Number(item.packages) || 0,
        quantity: Number(item.quantity) || 0,
        price: Number(item.price) || 0,
        taxRate: taxEnabled ? (Number(item.taxRate) || 0) : 0,
        taxIncludedPrice: taxEnabled ? (Number(item.taxIncludedPrice) || 0) : 0,
        amount: Number(item.amount) || 0,
        taxAmount: taxEnabled ? (Number(item.taxAmount) || 0) : 0,
        taxIncludedAmount: taxEnabled ? (Number(item.taxIncludedAmount) || 0) : 0,
        remark: item.remark || ''
      }))
    const firstItem = validItems[0] || {}
    const returnAmount = Number(form.value.returnAmount) || 0
    const refundAmount = Number(form.value.refundAmount) || 0
  
    return {
      ...firstItem,
      storeId: form.value.storeId || '',
      storeName: selectedStoreName.value,
      customerId: form.value.customerId || '',
      customerName: selectedCustomerName.value,
      warehouseId: form.value.warehouseId || '',
      warehouseName: selectedWarehouseName.value,
      returnNumber: form.value.returnNumber || '',
      returnNo: form.value.returnNumber || '',
      returnDate: form.value.returnDate || '',
      originalOrderNumber: form.value.originalOrderNumber || '',
      originalOrderNo: form.value.originalOrderNumber || '',
      taxEnabled,
      totalPackages: Number(totalPackages.value) || 0,
      totalQuantity: Number(totalQuantity.value) || 0,
      totalAmount: Number(totalAmount.value) || 0,
      totalTaxAmount: Number(totalTaxAmount.value) || 0,
      totalTaxIncludedAmount: Number(totalTaxIncludedAmount.value) || 0,
      returnAmount,
      refundAmount,
      writeoffAmount: Math.max(0, returnAmount - refundAmount),
      settlementAccount: form.value.settlementAccount || '',
      salesPerson: form.value.salesPerson || '',
      creator: currentCreatorName.value,
      packaging: form.value.packaging || '',
      goodsPackaging: form.value.packaging || '',
      remark: form.value.remark || '',
      items: validItems
    }
  })
  
  const showNotice = (message, type = 'success') => {
    window.clearTimeout(noticeTimer)
    notice.value = { visible: true, type, message: String(message || '') }
    noticeTimer = window.setTimeout(() => {
      notice.value.visible = false
      noticeTimer = null
    }, type === 'error' ? 5000 : 3200)
  }
  
  const closePrintTemplateDialog = () => {
    printTemplateDialogOpen.value = false
    if (!printPreviewVisible.value) {
      selectedPrintTemplate.value = null
      selectedPrintPrinter.value = null
      printPreviewAutoPrint.value = false
    }
  }
  
  const openSelectedPrintTemplate = (template, printer, autoPrint) => {
    selectedPrintTemplate.value = template
    selectedPrintPrinter.value = printer
    printPreviewAutoPrint.value = autoPrint
    printTemplateDialogOpen.value = false
    printPreviewVisible.value = true
  }
  
  const previewSelectedPrintTemplate = (template, printer) => {
    openSelectedPrintTemplate(template, printer, false)
  }
  
  const printSelectedPrintTemplate = (template, printer) => {
    openSelectedPrintTemplate(template, printer, true)
  }
  
  const closePrintPreview = () => {
    printPreviewVisible.value = false
    selectedPrintTemplate.value = null
    selectedPrintPrinter.value = null
    printPreviewAutoPrint.value = false
  }
  
  const calculateRow = item => {
    const quantity = Number(item.quantity) || 0
    const price = Number(item.price) || 0
    const taxRate = form.value.taxEnabled ? (Number(item.taxRate) || 0) : 0
    item.amount = Number((quantity * price).toFixed(2))
    item.taxIncludedPrice = Number((price * (1 + taxRate / 100)).toFixed(2))
    item.taxAmount = Number((item.amount * taxRate / 100).toFixed(2))
    item.taxIncludedAmount = Number((item.amount + item.taxAmount).toFixed(2))
    syncReturnAmount()
  }
  
  const calculateFromTaxIncluded = item => {
    const taxRate = Number(item.taxRate) || 0
    item.price = Number((Number(item.taxIncludedPrice || 0) / (1 + taxRate / 100)).toFixed(2))
    calculateRow(item)
  }
  
  const syncReturnAmount = () => {
    form.value.returnAmount = Number((form.value.taxEnabled ? totalTaxIncludedAmount.value : totalAmount.value).toFixed(2))
  }
  
  const onPackagesChange = item => {
    if (item.conversionRate && Number(item.packages) >= 0) {
      item.quantity = Number((Number(item.packages || 0) * Number(item.conversionRate)).toFixed(4))
    }
    calculateRow(item)
  }
  
  const onQuantityChange = item => {
    if (item.conversionRate && Number(item.quantity) >= 0) {
      item.packages = Number((Number(item.quantity || 0) / Number(item.conversionRate)).toFixed(4))
    }
    calculateRow(item)
  }
  
  const resetItems = () => {
    form.value.items = Array.from({ length: 8 }, blankItem)
    form.value.returnAmount = 0
  }
  
  const onStoreChange = () => {
    closeCustomerDropdown()
    form.value.customerId = ''
    form.value.warehouseId = ''
    form.value.settlementAccount = getPreferredSettlementAccount()
    resetItems()
  }
  
  const onWarehouseChange = () => {
    closeProductDropdown()
    resetItems()
  }
  
  const onItemWarehouseChange = item => {
    if (!item.productId) return
    const product = products.value.find(candidate => idEquals(candidate.id, item.productId))
    if (product) item.currentStock = getProductStock(product, item)
  }
  
  const setProductInputRef = (index, element) => {
    if (element) {
      productInputRefs.set(index, element)
    } else {
      productInputRefs.delete(index)
    }
  }
  
  const updateProductDropdownPosition = () => {
    const input = productInputRefs.get(focusedRow.value)
    const item = activeProductItem.value
    if (!input || !item || !item.filteredProducts.length) {
      productDropdownStyle.value = {}
      return
    }
  
    const rect = input.getBoundingClientRect()
    const viewportPadding = 12
    const gap = 4
    const dropdownWidth = Math.min(
      720,
      Math.max(360, window.innerWidth - viewportPadding * 2)
    )
    const rowHeight = 38
    const headerHeight = 38
    const desiredHeight = Math.min(
      360,
      headerHeight + item.filteredProducts.length * rowHeight
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
  
    productDropdownStyle.value = {
      top: `${Math.round(top)}px`,
      left: `${Math.round(left)}px`,
      width: `${Math.round(dropdownWidth)}px`,
      height: `${Math.round(height)}px`
    }
  }
  
  const showProductDropdown = index => {
    if (!form.value.storeId) return
    focusedRow.value = index
    const item = form.value.items[index]
    item.showDropdown = true
    filterProducts(index)
    nextTick(updateProductDropdownPosition)
  }
  
  const hideProductDropdown = index => {
    window.setTimeout(() => {
      if (form.value.items[index]) {
        form.value.items[index].showDropdown = false
        if (focusedRow.value === index) {
          productDropdownStyle.value = {}
        }
      }
    }, 180)
  }
  
  const filterProducts = index => {
    const item = form.value.items[index]
    if (!item) return
    const keyword = String(item.goodsName || '').trim().toLowerCase()
    const source = productsForItem(item)
    item.filteredProducts = source.filter(product => {
      if (!keyword) return true
      return [product.code, product.name, product.specification]
        .filter(Boolean)
        .some(value => String(value).toLowerCase().includes(keyword))
    }).slice(0, 80)
    item.showDropdown = true
    focusedRow.value = index
    nextTick(updateProductDropdownPosition)
  }

  const handleProductInput = index => filterProducts(index)
  
  const selectProduct = (index, product) => {
    const item = form.value.items[index]
    item.productId = product.id
    item.productCode = product.code || ''
    item.goodsName = product.name || ''
    item.specification = product.specification || ''
    item.unit = getUnitName(product.unitId) || product.unit || ''
    item.unitConversions = Array.isArray(product.unitConversions) ? product.unitConversions : []
    item.conversionRate = Number(item.unitConversions[0]?.value || 0) || null
    item.warehouseId = form.value.warehouseId || (product.warehouseId ? String(product.warehouseId) : '')
    item.currentStock = getProductStock(product, item)
    item.price = Number(product.price || 0)
    item.taxRate = form.value.taxEnabled ? 13 : 0
    item.packages = item.packages || null
    item.quantity = item.quantity || null
    item.showDropdown = false
    if (focusedRow.value === index) {
      productDropdownStyle.value = {}
    }
    calculateRow(item)
  }
  
  const closeProductDropdown = () => {
    form.value.items.forEach(item => {
      item.showDropdown = false
    })
    focusedRow.value = -1
    productDropdownStyle.value = {}
  }
  
  const updateCustomerDropdownPosition = () => {
    const input = customerInputRef.value
    if (!input || !customerDropdownOpen.value) {
      customerDropdownStyle.value = {}
      return
    }
  
    const rect = input.getBoundingClientRect()
    const viewportPadding = 12
    const gap = 4
    const dropdownWidth = Math.min(
      420,
      Math.max(280, window.innerWidth - viewportPadding * 2)
    )
    const rowHeight = 38
    const paginationHeight = customerTotalPages.value > 1 ? 42 : 0
    const desiredHeight = Math.min(
      620,
      Math.max(80, paginatedCustomers.value.length * rowHeight + paginationHeight)
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
  
    customerDropdownStyle.value = {
      top: `${Math.round(top)}px`,
      left: `${Math.round(left)}px`,
      width: `${Math.round(dropdownWidth)}px`,
      height: `${Math.round(height)}px`
    }
  }
  
  const openCustomerDropdown = () => {
    customerDropdownOpen.value = true
    customerSearch.value = ''
    customerPage.value = 1
    nextTick(updateCustomerDropdownPosition)
  }
  
  const closeCustomerDropdown = () => {
    customerDropdownOpen.value = false
    customerSearch.value = ''
    customerPage.value = 1
    customerDropdownStyle.value = {}
  }
  
  const handleCustomerSearchInput = event => {
    customerDropdownOpen.value = true
    customerSearch.value = event.target.value
    customerPage.value = 1
    nextTick(updateCustomerDropdownPosition)
  }
  
  const selectCustomer = customer => {
    form.value.customerId = String(customer.id)
    closeCustomerDropdown()
    customerInputRef.value?.blur()
  }
  
  const changeCustomerPage = page => {
    customerPage.value = Math.min(
      Math.max(1, page),
      customerTotalPages.value
    )
    nextTick(updateCustomerDropdownPosition)
  }
  
  const handleCustomerDocumentPointerdown = event => {
    if (!customerDropdownOpen.value) return
  
    const input = customerInputRef.value
    const dropdown = customerDropdownRef.value
    if (input?.contains(event.target) || dropdown?.contains(event.target)) return
  
    closeCustomerDropdown()
  }
  
  const addRow = index => {
    closeProductDropdown()
    const position = Math.max(0, Math.min(Number(index) + 1, form.value.items.length))
    form.value.items.splice(position, 0, blankItem())
  }
  
  const removeRow = index => {
    if (form.value.items.length <= 1) return
    closeProductDropdown()
    form.value.items.splice(index, 1)
    syncReturnAmount()
  }
  
  const clearForm = () => {
    closeCustomerDropdown()
    closeProductDropdown()
    form.value.storeId = ''
    form.value.customerId = ''
    form.value.warehouseId = ''
    form.value.returnDate = today()
    form.value.originalOrderNumber = ''
    form.value.taxEnabled = false
    form.value.returnAmount = 0
    form.value.refundAmount = 0
    form.value.settlementAccount = ''
    form.value.salesPerson = ''
    form.value.creator = currentCreatorName.value
    form.value.packaging = '桶装'
    form.value.remark = ''
    if (!props.returnId) {
      savedReturnId.value = null
      form.value.returnNumber = ''
    }
    resetItems()
    if (!props.returnId) {
      applyOrderFormDefaults()
    }
  }
  
  const close = () => router.push({ name: 'admin-sales-returns' })
  
  watch(() => form.value.taxEnabled, enabled => {
    form.value.items.forEach(item => {
      item.taxRate = enabled ? (Number(item.taxRate) || 13) : 0
      calculateRow(item)
    })
  })
  
  watch(
    [() => form.value.storeId, customerSearch],
    () => {
      customerPage.value = 1
      if (customerDropdownOpen.value) {
        nextTick(updateCustomerDropdownPosition)
      }
    }
  )
  
  watch(customerTotalPages, totalPages => {
    if (customerPage.value > totalPages) {
      customerPage.value = totalPages
    }
  })
  
  const loadData = async () => {
    try {
      const productUrl = productType.value === 'raw-material'
        ? '/raw-material-products'
        : '/products/inventory'
      const [
        storeData,
        customerData,
        warehouseData,
        productData,
        unitData,
        stockData,
        bankAccountData,
        packagingData,
        directoryData
      ] = await Promise.all([
        request({ url: '/stores', method: 'GET' }),
        request({ url: '/customers', method: 'GET' }),
        request({ url: '/warehouses', method: 'GET' }),
        request({ url: productUrl, method: 'GET' }),
        request({ url: '/products/units/measurements', method: 'GET' }),
      productType.value === 'raw-material'
          ? request({ url: '/stock-balances', method: 'GET', params: { type: 'raw-material' } })
          : Promise.resolve([]),
        request({ url: '/bank-accounts/options', method: 'GET' }),
        request({ url: '/products/units/packagings', method: 'GET' }).catch(error => {
          console.warn('加载包装单位失败:', error)
          return []
        }),
        request.get('/admin/directory').catch(error => {
          console.warn('加载员工目录失败:', error)
          return { departments: [], employees: [] }
        })
      ])
      stores.value = Array.isArray(storeData) ? storeData.filter(item => item.status !== 'inactive') : []
      customers.value = Array.isArray(customerData) ? customerData.filter(item => item.status !== 'inactive') : []
      warehouses.value = Array.isArray(warehouseData) ? warehouseData : []
      products.value = Array.isArray(productData) ? productData.filter(item => item.enabled !== false) : []
      units.value = Array.isArray(unitData) ? unitData : []
      stockBalances.value = Array.isArray(stockData) ? stockData : []
      bankAccounts.value = Array.isArray(bankAccountData?.data)
        ? bankAccountData.data
        : (Array.isArray(bankAccountData?.items) ? bankAccountData.items : [])
      packagingUnits.value = Array.isArray(packagingData) ? packagingData : []
      departments.value = Array.isArray(directoryData?.departments)
        ? directoryData.departments
        : []
      employees.value = Array.isArray(directoryData?.employees)
        ? directoryData.employees.map(employee => ({
            ...employee,
            departmentIds: Array.isArray(employee.departmentIds)
              ? employee.departmentIds.map(Number).filter(Number.isFinite)
              : []
          }))
        : []
    } catch (error) {
      console.error('加载退货单基础数据失败:', error)
      loadFailed.value = true
      showNotice(error?.response?.data?.message || '加载退货单基础数据失败', 'error')
    }
  }
  
  const loadExistingReturn = async () => {
    if (!savedReturnId.value) return
    try {
      const data = await request({ url: `/returns/${savedReturnId.value}`, method: 'GET' })
      form.value.returnNumber = data.returnNumber || ''
      form.value.storeId = data.storeId ? String(data.storeId) : ''
      form.value.customerId = data.customerId ? String(data.customerId) : ''
      form.value.warehouseId = data.items?.[0]?.warehouseId ? String(data.items[0].warehouseId) : ''
      form.value.returnDate = data.returnDate || today()
      form.value.originalOrderNumber = data.originalOrderNumber || ''
      form.value.taxEnabled = Boolean(data.taxEnabled)
      form.value.refundAmount = Number(data.refundAmount || 0)
      form.value.settlementAccount = data.settlementAccount || ''
      form.value.salesPerson = data.salesPerson || ''
      form.value.creator = currentCreatorName.value
      form.value.packaging = data.packaging || '桶装'
      form.value.remark = data.remark || ''
      const rows = (data.items || []).map(item => {
        const product = products.value.find(candidate => idEquals(candidate.id, item.productId)) || {}
        return {
          ...blankItem(),
          productId: item.productId ? String(item.productId) : '',
          productCode: item.productCode || '',
          goodsName: item.goodsName || '',
          specification: item.specification || '',
          unit: item.unit || '',
          warehouseId: item.warehouseId ? String(item.warehouseId) : '',
          currentStock: getProductStock(product, item),
          packages: Number(item.packages || 0),
          quantity: Number(item.quantity || 0),
          price: Number(item.price || 0),
          amount: Number(item.amount || 0),
          taxRate: Number(item.taxRate || 0),
          taxIncludedPrice: Number(item.taxIncludedPrice || 0),
          taxAmount: Number(item.taxAmount || 0),
          taxIncludedAmount: Number(item.taxIncludedAmount || 0),
          conversionRate: Number(product.unitConversions?.[0]?.value || 0) || null,
          unitConversions: Array.isArray(product.unitConversions) ? product.unitConversions : [],
          remark: item.remark || ''
        }
      })
      form.value.items = rows.concat(Array.from({ length: Math.max(8 - rows.length, 0) }, blankItem))
      form.value.returnAmount = Number(data.totalAmount || 0)
    } catch (error) {
      showNotice(error?.response?.data?.message || '加载退货单失败', 'error')
    }
  }
  
  const save = async () => {
    if (saving.value || loading.value || readOnly.value || loadFailed.value) return
    if (form.value.items.some(item => item.goodsName && !item.productId)) {
      showNotice('请从商品列表选择有效商品', 'error')
      return
    }
    const validItems = form.value.items.filter(item => item.productId && Number(item.quantity) > 0)
    if (!form.value.storeId || !form.value.customerId) {
      showNotice('请选择门店和客户', 'error')
      return
    }
    if (!form.value.originalOrderNumber) {
      showNotice('请输入原订单编号', 'error')
      return
    }
    if (!validItems.length) {
      showNotice('请至少选择一条商品并填写数量', 'error')
      return
    }
    const returnAmount = Number(form.value.returnAmount || 0)
    const refundAmount = Number(form.value.refundAmount || 0)
    if (!Number.isFinite(returnAmount) || returnAmount < 0) {
      showNotice('应退金额不能小于0', 'error')
      return
    }
    if (!Number.isFinite(refundAmount) || refundAmount < 0) {
      showNotice('本次退款不能小于0', 'error')
      return
    }
    if (refundAmount > returnAmount) {
      showNotice('本次退款不能超过应退金额', 'error')
      return
    }
  
    saving.value = true
    try {
      const returnId = savedReturnId.value
      const response = await request({
        url: returnId ? `/returns/${returnId}` : '/returns',
        method: returnId ? 'PUT' : 'POST',
        data: {
          productType: productType.value,
          storeId: Number(form.value.storeId),
          customerId: Number(form.value.customerId),
          returnDate: form.value.returnDate,
          originalOrderNumber: form.value.originalOrderNumber,
          taxEnabled: form.value.taxEnabled,
          returnAmount: Number(form.value.returnAmount) || 0,
          refundAmount: Number(form.value.refundAmount) || 0,
          settlementAccount: form.value.settlementAccount,
          salesPerson: form.value.salesPerson,
          creator: currentCreatorName.value,
          packaging: form.value.packaging,
          remark: form.value.remark,
          items: validItems.map(item => ({
            productId: Number(item.productId),
            productCode: item.productCode,
            goodsName: item.goodsName,
            specification: item.specification,
            unit: item.unit,
            warehouseId: item.warehouseId ? Number(item.warehouseId) : null,
            packages: Number(item.packages) || 0,
            quantity: Number(item.quantity) || 0,
            price: Number(item.price) || 0,
            amount: Number(item.amount) || 0,
            taxRate: form.value.taxEnabled ? Number(item.taxRate) || 0 : 0,
            taxIncludedPrice: form.value.taxEnabled ? Number(item.taxIncludedPrice) || 0 : 0,
            remark: item.remark
          }))
        }
      })
      if (!response?.success) throw new Error(response?.message || '保存失败')
      persistOrderFormDefaults()
      const savedReturn = response.returnOrder || response.data?.returnOrder || {}
      savedReturnId.value = response.returnId || savedReturn.id || returnId
      form.value.returnNumber = response.returnNumber || savedReturn.returnNumber || form.value.returnNumber
      const actionLabel = returnId ? '退货单修改成功' : '退货单保存成功'
      showNotice(`${actionLabel}${form.value.returnNumber ? ` · 单号：${form.value.returnNumber}` : ''}`)
      selectedPrintTemplate.value = null
      selectedPrintPrinter.value = null
      printPreviewAutoPrint.value = false
      printTemplateDialogOpen.value = true
    } catch (error) {
      console.error('保存退货单失败:', error)
      showNotice(error?.response?.data?.message || error.message || '保存退货单失败', 'error')
    } finally {
      saving.value = false
    }
  }
  
  onMounted(async () => {
    window.addEventListener('resize', updateProductDropdownPosition)
    window.addEventListener('scroll', updateProductDropdownPosition, true)
    window.addEventListener('resize', updateCustomerDropdownPosition)
    window.addEventListener('scroll', updateCustomerDropdownPosition, true)
    document.addEventListener('pointerdown', handleCustomerDocumentPointerdown)
    try {
      if (savedReturnId.value) {
        const existing = await request({ url: `/returns/${savedReturnId.value}`, method: 'GET' })
        productType.value = existing.productType || productType.value
        readOnly.value = props.action === 'view' || ['audited', 'completed'].includes(existing.status)
      }
      await loadData()
      if (!savedReturnId.value) applyOrderFormDefaults()
      await loadExistingReturn()
    } catch (error) {
      loadFailed.value = true
      showNotice(error?.response?.data?.message || '加载退货单失败', 'error')
    } finally {
      loading.value = false
    }
  })
  
  onBeforeUnmount(() => {
    window.removeEventListener('resize', updateProductDropdownPosition)
    window.removeEventListener('scroll', updateProductDropdownPosition, true)
    window.removeEventListener('resize', updateCustomerDropdownPosition)
    window.removeEventListener('scroll', updateCustomerDropdownPosition, true)
    document.removeEventListener('pointerdown', handleCustomerDocumentPointerdown)
    productInputRefs.clear()
    window.clearTimeout(noticeTimer)
  })

  return {
    loading,
    loadFailed,
    readOnly,
    productType,
    handleProductInput,
    openPrint: () => { printTemplateDialogOpen.value = true },
    router,
    userStore,
    currentCreatorName,
    creatorNameStyle,
    saving,
    savedReturnId,
    stores,
    customers,
    warehouses,
    products,
    units,
    stockBalances,
    bankAccounts,
    packagingUnits,
    employees,
    departments,
    focusedRow,
    productInputRefs,
    productDropdownRef,
    productDropdownStyle,
    customerSearch,
    customerPage,
    customerDropdownOpen,
    customerInputRef,
    customerDropdownRef,
    customerDropdownStyle,
    CUSTOMER_PAGE_SIZE,
    printTemplateDialogOpen,
    printPreviewVisible,
    selectedPrintTemplate,
    selectedPrintPrinter,
    printPreviewAutoPrint,
    notice,
    noticeTimer,
    rowKey,
    ORDER_FORM_DEFAULTS_STORAGE_KEY,
    readOrderFormDefaults,
    today,
    blankItem,
    form,
    idEquals,
    asIds,
    filteredCustomers,
    customerSearchResults,
    customerTotalPages,
    paginatedCustomers,
    filteredWarehouses,
    storeBankAccounts,
    getPreferredSettlementAccount,
    applyOrderFormDefaults,
    persistOrderFormDefaults,
    salesPeople,
    packagingOptions,
    productsForItem,
    totalPackages,
    totalQuantity,
    totalAmount,
    totalTaxAmount,
    totalTaxIncludedAmount,
    money,
    number,
    getUnitName,
    getProductStock,
    selectedStoreName,
    selectedCustomerName,
    selectedWarehouseName,
    activeProductItem,
    returnPrintVariables,
    showNotice,
    closePrintTemplateDialog,
    openSelectedPrintTemplate,
    previewSelectedPrintTemplate,
    printSelectedPrintTemplate,
    closePrintPreview,
    calculateRow,
    calculateFromTaxIncluded,
    syncReturnAmount,
    onPackagesChange,
    onQuantityChange,
    resetItems,
    onStoreChange,
    onWarehouseChange,
    onItemWarehouseChange,
    setProductInputRef,
    updateProductDropdownPosition,
    showProductDropdown,
    hideProductDropdown,
    filterProducts,
    selectProduct,
    closeProductDropdown,
    updateCustomerDropdownPosition,
    openCustomerDropdown,
    closeCustomerDropdown,
    handleCustomerSearchInput,
    selectCustomer,
    changeCustomerPage,
    handleCustomerDocumentPointerdown,
    addRow,
    removeRow,
    clearForm,
    close,
    loadData,
    loadExistingReturn,
    save
  }
}
