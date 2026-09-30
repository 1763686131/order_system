import { ref, computed, inject, nextTick, onBeforeUnmount, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import request from '@/api/request'
import { useOrderDraftStore } from '@/stores/orderDraft'
import { useUserStore } from '@/stores/user'
import { toChineseMoney } from '@/utils/chineseMoney'

export function useSalesDocument(props) {
  const router = useRouter()
  const route = useRoute()
  const orderDraftStore = useOrderDraftStore()
  const userStore = useUserStore()
  const loading = ref(true)
  const loadFailed = ref(false)
  const readOnly = ref(props.action === 'view')
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
  const setHeaderActions = inject('setHeaderActions', null)
  
  // 含税开关状态
  const showTaxColumns = ref(false)
  const DEFAULT_TAX_RATE = 13
  
  // 关闭确认弹窗
  const showCloseConfirmModal = ref(false)
  
  // 清空确认弹窗
  const showClearConfirmModal = ref(false)
  
  // 打印模板选择与预览
  const printTemplateDialogOpen = ref(false)
  const printPreviewVisible = ref(false)
  const selectedPrintTemplate = ref(null)
  const selectedPrintPrinter = ref(null)
  const printPreviewAutoPrint = ref(false)
  const printOrderVariables = ref(null)
  const saveToast = ref({ visible: false, message: '' })
  let saveToastTimer = null
  
  // Props 定义
  
  
  // 判断是否为编辑模式
  const isEditMode = computed(() => props.orderId !== null)
  const copySourceId = computed(() => {
    const orderId = Number(props.copySourceId || route.query.copyFrom)
    return Number.isInteger(orderId) && orderId > 0 ? orderId : null
  })
  const draftKey = computed(() => {
    if (isEditMode.value) {
      return `edit:${props.orderId}`
    }
    return copySourceId.value ? `create:${copySourceId.value}` : 'create:new'
  })
  const orderFormRoute = {
    key: draftKey.value,
    path: route.fullPath,
    name: route.name,
    params: { ...route.params },
    query: { ...route.query }
  }
  
  // 自定义弹窗
  const showModal = ref(false)
  const modalType = ref('success') // success 或 error
  const modalTitle = ref('')
  const modalMessage = ref('')
  const validationHint = ref({ key: '', message: '' })
  const validationHintStyle = ref({})
  const validationHintPlacement = ref('below')
  const validationFieldRefs = new Map()
  let validationHintTimer = null
  
  const setValidationFieldRef = (key, element) => {
    if (element) {
      validationFieldRefs.set(key, element)
    } else {
      validationFieldRefs.delete(key)
    }
  }
  
  const dismissValidationHint = (key = '') => {
    if (key && validationHint.value.key !== key) return
  
    clearTimeout(validationHintTimer)
    validationHint.value = { key: '', message: '' }
    validationHintStyle.value = {}
  }
  
  const updateValidationHintPosition = () => {
    const target = validationFieldRefs.get(validationHint.value.key)
    if (!target || !validationHint.value.key) {
      validationHintStyle.value = {}
      return
    }
  
    const rect = target.getBoundingClientRect()
    const viewportPadding = 16
    const gap = 10
    const estimatedHeight = 48
    const popoverWidth = Math.min(320, window.innerWidth - viewportPadding * 2)
    const spaceBelow = window.innerHeight - rect.bottom - viewportPadding
    const spaceAbove = rect.top - viewportPadding
    const shouldPlaceAbove =
      (validationHint.value.key.startsWith('item-') || spaceBelow < estimatedHeight + gap) &&
      spaceAbove >= estimatedHeight + gap
  
    validationHintPlacement.value = shouldPlaceAbove ? 'above' : 'below'
    const top = shouldPlaceAbove
      ? Math.max(viewportPadding, rect.top - estimatedHeight - gap)
      : Math.min(window.innerHeight - estimatedHeight - viewportPadding, rect.bottom + gap)
    const left = Math.min(
      Math.max(viewportPadding, rect.left),
      Math.max(viewportPadding, window.innerWidth - popoverWidth - viewportPadding)
    )
  
    validationHintStyle.value = {
      top: `${Math.round(top)}px`,
      left: `${Math.round(left)}px`,
      maxWidth: `${Math.round(popoverWidth)}px`
    }
  }
  
  const showValidationHint = (key, message) => {
    clearTimeout(validationHintTimer)
  
    const target = validationFieldRefs.get(key)
    if (target && typeof target.focus === 'function' && !key.startsWith('item-product-')) {
      target.focus({ preventScroll: true })
    }
  
    validationHint.value = { key, message }
    nextTick(updateValidationHintPosition)
    validationHintTimer = setTimeout(() => {
      if (validationHint.value.key === key) {
        validationHint.value = { key: '', message: '' }
        validationHintStyle.value = {}
      }
    }, 4000)
  }
  
  const dismissSaveToast = () => {
    saveToast.value.visible = false
    clearTimeout(saveToastTimer)
  }
  
  const showSuccessToast = (message) => {
    saveToast.value = {
      visible: true,
      message: String(message || '').replace(/\s*\n\s*/g, ' · ')
    }
    clearTimeout(saveToastTimer)
    saveToastTimer = setTimeout(dismissSaveToast, 3000)
  }
  
  const showErrorModal = (message) => {
    modalType.value = 'error'
    modalTitle.value = '操作失败'
    modalMessage.value = message
    showModal.value = true
  }
  
  const closeModal = () => {
    showModal.value = false
  }
  
  // 基础数据
  const stores = ref([])
  const customers = ref([])
  const warehouses = ref([])
  const products = ref([])
  const units = ref([])
  const packagingUnits = ref([])
  const bankAccounts = ref([])
  const employees = ref([])
  const departments = ref([])
  
  const DEFAULT_PACKAGING_OPTIONS = ['无', '桶装', '纸箱', '托盘', '袋装']
  const ADD_PACKAGING_VALUE = '__add_packaging__'
  const logisticsServiceOptions = [
    '送货上门+回单拍照回传',
    '送货上门+回单邮回',
    '送货上门',
    '用户自提',
    '无'
  ]
  
  const ORDER_FORM_DEFAULTS_STORAGE_KEY = 'admin_order_form_default_selections'
  const SERVER_ORDER_DEFAULTS = Object.freeze({
    logisticsService: logisticsServiceOptions[0],
    packaging: '桶装',
    salesPerson: ''
  })
  
  const readOrderFormDefaults = () => {
    const fallback = {
      ...SERVER_ORDER_DEFAULTS,
      settlementAccountsByStore: {}
    }
  
    if (typeof window === 'undefined') {
      return fallback
    }
  
    try {
      const stored = window.localStorage.getItem(ORDER_FORM_DEFAULTS_STORAGE_KEY)
      if (!stored) {
        return fallback
      }
  
      const parsed = JSON.parse(stored)
      const settlementAccountsByStore = parsed?.settlementAccountsByStore &&
        typeof parsed.settlementAccountsByStore === 'object'
        ? parsed.settlementAccountsByStore
        : {}
  
      return {
        logisticsService: String(parsed?.logisticsService || fallback.logisticsService),
        packaging: String(parsed?.packaging || fallback.packaging),
        salesPerson: String(parsed?.salesPerson || ''),
        settlementAccountsByStore
      }
    } catch (error) {
      console.warn('读取订单默认选项失败:', error)
      return fallback
    }
  }
  
  const orderFormDefaults = ref(readOrderFormDefaults())
  
  const getCurrentOrderDate = () => {
    const now = new Date()
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
  }
  
  // 表单数据
  const formData = ref({
    storeId: '',
    customerId: '',
    warehouseId: '',
    orderDate: getCurrentOrderDate(),
    orderNumber: '',
    contactPerson: '',
    contactPhone: '',
    contactAddress: '',
    projectName: '',
    packaging: '桶装',
    logisticsService: '送货上门+回单拍照回传',
    salesPerson: '',
    creator: '',
    orderRemark: '',
    taxRate: 0,
    discountAmount: null,
    otherFees: null,
    settlementAccount: '',
    currentPayment: 0,
    items: []
  })
  
  watch(currentCreatorName, creator => {
    formData.value.creator = creator
  }, { immediate: true })
  
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
  
    const currentPackaging = formData.value.packaging &&
      formData.value.packaging !== ADD_PACKAGING_VALUE
      ? [formData.value.packaging]
      : []
  
    return [...new Set([
      ...DEFAULT_PACKAGING_OPTIONS,
      ...customPackaging,
      ...currentPackaging
    ])]
  })
  
  const normalizeLogisticsService = (value) => {
    if (Array.isArray(value)) {
      return value[0] || logisticsServiceOptions[0]
    }
    return String(value || logisticsServiceOptions[0])
  }
  
  const getServerDefaultSettlementAccount = (storeId) => {
    if (!storeId) {
      return ''
    }
  
    const accounts = bankAccounts.value.filter(account =>
      String(account.storeId) === String(storeId)
    )
    const defaultAccount = accounts.find(account => account.isDefault) || accounts[0]
    return defaultAccount?.value || defaultAccount?.accountName || ''
  }
  
  const getPreferredSettlementAccount = (storeId) => {
    if (!storeId) {
      return ''
    }
  
    const accountDefaults = orderFormDefaults.value.settlementAccountsByStore || {}
    const storeKey = String(storeId)
    if (Object.prototype.hasOwnProperty.call(accountDefaults, storeKey)) {
      const savedAccount = accountDefaults[storeKey] || ''
      if (!savedAccount || bankAccounts.value.some(account =>
        String(account.storeId) === storeKey &&
        (account.value || account.accountName) === savedAccount
      )) {
        return savedAccount
      }
    }
  
    return getServerDefaultSettlementAccount(storeId)
  }
  
  const applyNewOrderDefaults = () => {
    const defaults = orderFormDefaults.value
    formData.value.logisticsService = logisticsServiceOptions.includes(defaults.logisticsService)
      ? defaults.logisticsService
      : SERVER_ORDER_DEFAULTS.logisticsService
    formData.value.packaging = defaults.packaging || SERVER_ORDER_DEFAULTS.packaging
    formData.value.salesPerson = salesPeople.value.some(employee =>
      employee.displayName === defaults.salesPerson
    ) ? defaults.salesPerson : ''
    formData.value.creator = currentCreatorName.value
    formData.value.settlementAccount = getPreferredSettlementAccount(formData.value.storeId)
  }
  
  const persistOrderFormDefaults = () => {
    const nextDefaults = {
      logisticsService: formData.value.logisticsService || SERVER_ORDER_DEFAULTS.logisticsService,
      packaging: formData.value.packaging || SERVER_ORDER_DEFAULTS.packaging,
      salesPerson: formData.value.salesPerson || '',
      settlementAccountsByStore: {
        ...(orderFormDefaults.value.settlementAccountsByStore || {})
      }
    }
  
    if (formData.value.storeId) {
      nextDefaults.settlementAccountsByStore[String(formData.value.storeId)] =
        formData.value.settlementAccount || ''
    }
  
    orderFormDefaults.value = nextDefaults
  
    if (typeof window === 'undefined') {
      return
    }
  
    try {
      window.localStorage.setItem(
        ORDER_FORM_DEFAULTS_STORAGE_KEY,
        JSON.stringify(nextDefaults)
      )
    } catch (error) {
      console.warn('保存订单默认选项失败:', error)
    }
  }
  
  const draftReady = ref(false)
  let draftSaveTimer = null
  
  const cloneDraftValue = (value) => JSON.parse(JSON.stringify(value))
  
  const getDraftFormData = () => {
    const snapshot = cloneDraftValue(formData.value)
    snapshot.items = (snapshot.items || []).map(item => ({
      ...item,
      showDropdown: false,
      filteredProducts: []
    }))
    return snapshot
  }
  
  const persistDraft = () => {
    if (readOnly.value) return
    if (!draftReady.value) {
      return
    }
  
    orderDraftStore.saveDraft({
      key: orderFormRoute.key,
      mode: isEditMode.value ? 'edit' : 'create',
      orderId: props.orderId,
      formData: getDraftFormData(),
      showTaxColumns: showTaxColumns.value,
      totalPackages: totalPackages.value,
      path: orderFormRoute.path,
      route: {
        name: orderFormRoute.name,
        params: orderFormRoute.params,
        query: orderFormRoute.query
      }
    })
  }
  
  const scheduleDraftSave = () => {
    if (!draftReady.value) {
      return
    }
  
    clearTimeout(draftSaveTimer)
    draftSaveTimer = setTimeout(persistDraft, 120)
  }
  
  const restoreDraft = async (draft) => {
    const restoredFormData = cloneDraftValue(draft.formData)
    formData.value = {
      ...formData.value,
      ...restoredFormData
    }
    formData.value.creator = currentCreatorName.value
    formData.value.items = (formData.value.items || []).map(item => ({
      ...item,
      showDropdown: false,
      filteredProducts: []
    }))
    showTaxColumns.value = Boolean(draft.showTaxColumns)
    normalizeTaxRows(showTaxColumns.value, true)
  
    // 恢复总件数：保留手动值，直到下一次明细件数变化。
    const restoredTotalPackages = draft.totalPackages ?? draft.manualTotalPackages
    if (restoredTotalPackages !== undefined && restoredTotalPackages !== null) {
      totalPackages.value = restoredTotalPackages
      totalPackagesManuallyEdited.value = true
    } else {
      // 草稿中没有总件数，自动计算
      totalPackages.value = totalPackagesCalculated.value
      totalPackagesManuallyEdited.value = false
    }
  
    // 金额联动的 watcher 会在恢复商品行后执行，下一帧再还原用户手工输入值。
    await nextTick()
    formData.value.discountAmount = restoredFormData.discountAmount ?? null
  }
  
  const discardDraft = () => {
    draftReady.value = false
    clearTimeout(draftSaveTimer)
    orderDraftStore.clearDraft()
  }
  
  // 过滤后的客户（根据门店）
  const filteredCustomers = computed(() => {
    if (!formData.value.storeId) {
      return customers.value
    }
    return customers.value.filter(c =>
      String(c.storeId) === String(formData.value.storeId)
    )
  })
  
  const CUSTOMER_PAGE_SIZE = 15
  const customerSearch = ref('')
  const customerPage = ref(1)
  const customerDropdownOpen = ref(false)
  const customerInputRef = ref(null)
  const customerDropdownRef = ref(null)
  const customerDropdownStyle = ref({})
  
  const setCustomerInputRef = (element) => {
    customerInputRef.value = element
    setValidationFieldRef('customerId', element)
  }
  
  const customerSearchResults = computed(() => {
    const keyword = String(customerSearch.value || '').trim().toLowerCase()
    if (!keyword) {
      return filteredCustomers.value
    }
  
    return filteredCustomers.value.filter(customer => {
      const searchableValues = [
        customer.customerName,
        customer.name,
        customer.customerCode,
        customer.code,
        customer.contactPerson,
        customer.phone
      ]
  
      return searchableValues.some(value =>
        String(value || '').toLowerCase().includes(keyword)
      )
    })
  })
  
  const customerTotalPages = computed(() => Math.max(
    1,
    Math.ceil(customerSearchResults.value.length / CUSTOMER_PAGE_SIZE)
  ))
  
  const paginatedCustomers = computed(() => {
    const start = (customerPage.value - 1) * CUSTOMER_PAGE_SIZE
    return customerSearchResults.value.slice(start, start + CUSTOMER_PAGE_SIZE)
  })
  
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
    const paginationHeight = customerTotalPages.value > 1 ? 44 : 0
    const desiredHeight = Math.min(
      620,
      Math.max(44, paginatedCustomers.value.length * rowHeight + paginationHeight)
    )
    const spaceBelow = Math.max(120, window.innerHeight - rect.bottom - viewportPadding)
    const spaceAbove = Math.max(120, rect.top - viewportPadding)
    const shouldOpenAbove = desiredHeight > spaceBelow && spaceAbove > spaceBelow
    const availableHeight = shouldOpenAbove ? spaceAbove : spaceBelow
    const height = Math.min(desiredHeight, availableHeight)
    const top = shouldOpenAbove
      ? Math.max(viewportPadding, rect.top - height - gap)
      : Math.min(
          window.innerHeight - height - viewportPadding,
          rect.bottom + gap
        )
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
  
  const handleCustomerSearchInput = (event) => {
    customerDropdownOpen.value = true
    customerSearch.value = event.target.value
    customerPage.value = 1
    nextTick(updateCustomerDropdownPosition)
  }
  
  const selectCustomer = (customer) => {
    formData.value.customerId = customer.id
    customerSearch.value = ''
    customerPage.value = 1
    customerDropdownOpen.value = false
    customerDropdownStyle.value = {}
    customerInputRef.value?.blur()
    onCustomerChange()
    dismissValidationHint('customerId')
  }
  
  const changeCustomerPage = (page) => {
    customerPage.value = Math.min(
      Math.max(1, page),
      customerTotalPages.value
    )
    nextTick(updateCustomerDropdownPosition)
  }
  
  const handleCustomerDocumentPointerdown = (event) => {
    if (!customerDropdownOpen.value) {
      return
    }
  
    const input = customerInputRef.value
    const dropdown = customerDropdownRef.value
    if (input?.contains(event.target) || dropdown?.contains(event.target)) {
      return
    }
  
    closeCustomerDropdown()
  }
  
  watch(
    [() => formData.value.storeId, customerSearch],
    () => {
      customerPage.value = 1
      if (customerDropdownOpen.value) {
        nextTick(updateCustomerDropdownPosition)
      }
    }
  )
  
  watch(customerTotalPages, (totalPages) => {
    if (customerPage.value > totalPages) {
      customerPage.value = totalPages
    }
  })
  
  // 过滤后的仓库（根据门店）
  const filteredWarehouses = computed(() => {
    if (!formData.value.storeId) {
      return warehouses.value
    }
    return warehouses.value.filter(w => w.storeId === formData.value.storeId)
  })
  
  // 选中的门店名称（用于结算账户显示）
  const selectedStoreName = computed(() => {
    const store = stores.value.find(s => String(s.id) === String(formData.value.storeId))
    return store ? store.name : ''
  })
  
  const storeBankAccounts = computed(() => bankAccounts.value
    .filter(account => String(account.storeId) === String(formData.value.storeId))
    .slice()
    .sort((a, b) => Number(Boolean(b.isDefault)) - Number(Boolean(a.isDefault))))
  
  const selectedCustomerName = computed(() => {
    const customer = customers.value.find(
      item => String(item.id) === String(formData.value.customerId)
    )
    return customer ? (customer.customerName || customer.name || '') : ''
  })
  
  const selectedWarehouseName = computed(() => {
    const warehouse = warehouses.value.find(
      item => String(item.id) === String(formData.value.warehouseId)
    )
    return warehouse ? warehouse.name : ''
  })
  
  const orderPrintVariables = computed(() => {
    const taxEnabled = showTaxColumns.value
    const validItems = formData.value.items
      .filter(item => item.productId || item.goodsName)
      .map((item, index) => ({
        index: index + 1,
        productId: item.productId || '',
        goodsName: item.goodsName || '',
        spec: item.spec || '',
        unit: item.unit || '',
        warehouseId: item.warehouseId || '',
        warehouseName: item.warehouseName || selectedWarehouseName.value,
        currentStock: Number(item.currentStock) || 0,
        baseUnitId: item.baseUnitId || '',
        conversionRate: Number(item.conversionRate) || 0,
        unitConversions: Array.isArray(item.unitConversions) ? item.unitConversions : [],
        packages: Number(item.packages) || 0,
        quantity: Number(item.quantity) || 0,
        price: Number(item.price) || 0,
        taxRate: taxEnabled ? (Number(item.taxRate) || DEFAULT_TAX_RATE) : 0,
        taxIncludedPrice: taxEnabled ? (Number(item.taxIncludedPrice) || 0) : 0,
        amount: Number(item.amount) || 0,
        totalAmount: taxEnabled ? (Number(item.totalAmount) || 0) : 0,
        remark: item.remark || ''
      }))
  
    // 设计器中直接放入表格单元格的 @goodsName、@quantity 等变量，
    // 默认按根对象解析。单据通常至少有一条商品明细，因此将第一条明细
    // 同步为根级别别名，保证单元格预览能显示当前订单数据。
    const firstItem = validItems[0] || {}
    const discountAmount = Number(formData.value.discountAmount) || 0
    const otherFees = Number(formData.value.otherFees) || 0
    const currentPayment = Number(formData.value.currentPayment) || 0
  
    return {
      ...firstItem,
      storeId: formData.value.storeId || '',
      storeName: selectedStoreName.value,
      customerId: formData.value.customerId || '',
      customerName: selectedCustomerName.value,
      warehouseId: formData.value.warehouseId || '',
      warehouseName: selectedWarehouseName.value,
      orderDate: formData.value.orderDate || '',
      orderNumber: formData.value.orderNumber || '',
      orderNo: formData.value.orderNumber || '',
      contactPerson: formData.value.contactPerson || '',
      contactPhone: formData.value.contactPhone || '',
      contactAddress: formData.value.contactAddress || '',
      projectName: formData.value.projectName || '',
      logisticsService: formData.value.logisticsService || '',
      goodsPackaging: formData.value.packaging || '',
      packaging: formData.value.packaging || '',
      salesPerson: formData.value.salesPerson || '',
      creator: currentCreatorName.value,
      orderRemark: formData.value.orderRemark || '',
      taxEnabled,
      taxRate: taxEnabled ? (Number(formData.value.taxRate) || DEFAULT_TAX_RATE) : 0,
      totalPackages: Number(totalPackages.value) || 0,
      totalQuantity: Number(totalQuantity.value) || 0,
      totalAmount: Number(totalAmount.value) || 0,
      totalTaxAmount: Number(totalTaxAmount.value) || 0,
      discountAmount,
      otherFees,
      settlementAccount: formData.value.settlementAccount || selectedStoreName.value,
      customerReceivable: Number(customerReceivable.value) || 0,
      shouldReceive: Number(shouldReceive.value) || 0,
      amountInWords: toChineseMoney(shouldReceive.value),
      currentPayment,
      currentDebt: discountAmount + otherFees - currentPayment,
      items: validItems
    }
  })
  
  const closePrintTemplateDialog = () => {
    printTemplateDialogOpen.value = false
    if (!printPreviewVisible.value) {
      selectedPrintTemplate.value = null
      selectedPrintPrinter.value = null
      printPreviewAutoPrint.value = false
      printOrderVariables.value = null
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
  
  const closeOrderPrintPreview = () => {
    printPreviewVisible.value = false
    selectedPrintTemplate.value = null
    selectedPrintPrinter.value = null
    printPreviewAutoPrint.value = false
    printOrderVariables.value = null
  }
  
  const getSaveSuccessMessage = () => (
    `${isEditMode.value ? '订单修改成功' : '订单保存成功'} · 订单编号：${formData.value.orderNumber}`
  )
  
  // 过滤商品（根据当前选择的门店和仓库）
  const filteredProducts = computed(() => {
    let result = products.value
  
    // 根据门店筛选
    if (formData.value.storeId) {
      result = result.filter(p =>
        p.storeIds && Array.isArray(p.storeIds) && p.storeIds.includes(formData.value.storeId)
      )
    }
  
    // 根据仓库筛选
    if (formData.value.warehouseId) {
      result = result.filter(p => p.warehouseId === formData.value.warehouseId)
    }
  
    return result
  })
  
  // 焦点行
  const focusedRow = ref(-1)
  const productInputRefs = new Map()
  const productDropdownStyle = ref({})
  
  const setProductInputRef = (index, element) => {
    if (element) {
      productInputRefs.set(index, element)
      setValidationFieldRef(`item-product-${index}`, element)
    } else {
      productInputRefs.delete(index)
      setValidationFieldRef(`item-product-${index}`, null)
    }
  }
  
  const activeProductRow = computed(() => {
    const item = formData.value.items[focusedRow.value]
    return item?.showDropdown && item.filteredProducts?.length ? item : null
  })
  
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
    const availableBelow = Math.max(80, window.innerHeight - rect.bottom - viewportPadding)
    const availableAbove = Math.max(80, rect.top - viewportPadding)
    const estimatedHeight = Math.min(300, item.filteredProducts.length * 42 + 42)
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
  
  // 生成订单编号
  function generateOrderNumber(orderId) {
    const now = new Date()
    const year = now.getFullYear()
    const month = String(now.getMonth() + 1).padStart(2, '0')
    const day = String(now.getDate()).padStart(2, '0')
  
    if (orderId && orderId !== 'TEMP') {
      // 有订单ID：使用三位数ID（不足三位补0）
      const id = String(orderId).padStart(3, '0')
      return `ZG${year}${month}${day}${id}`
    } else {
      // 新增模式：使用临时标识
      return `ZG${year}${month}${day}TEMP`
    }
  }
  
  // 初始化空白行
  function initEmptyRows() {
    formData.value.items = Array.from({ length: 8 }, () => ({
      productId: '',
      goodsName: '',
      spec: '',
      unit: '',
      warehouseId: '',
      warehouseName: '',
      currentStock: null,
      packages: null,
      quantity: null,
      price: null,
      taxRate: null,
      taxIncludedPrice: null,
      amount: null,
      totalAmount: null,
      remark: '',
      showDropdown: false,
      filteredProducts: [],
      unitConversions: [],
      conversionRate: null,
      historyPriceLoading: false,
      historyPriceRequestKey: ''
    }))
    // 新建订单首次显示按明细计算的合计，此时未手动修改
    totalPackages.value = totalPackagesCalculated.value
    totalPackagesManuallyEdited.value = false
  }
  
  // 加载门店
  const loadStores = async () => {
    try {
      const response = await request({ url: '/stores', method: 'GET' })
      if (response && Array.isArray(response)) {
        stores.value = response
      }
    } catch (error) {
      console.error('加载门店失败:', error)
    }
  }
  
  // 加载客户
  const loadCustomers = async () => {
    try {
      const response = await request({ url: '/customers', method: 'GET' })
      if (response && Array.isArray(response)) {
        customers.value = response
      }
    } catch (error) {
      console.error('加载客户失败:', error)
    }
  }
  
  // 加载仓库
  const loadWarehouses = async () => {
    try {
      const response = await request({ url: '/warehouses', method: 'GET' })
      if (response && Array.isArray(response)) {
        warehouses.value = response
      }
    } catch (error) {
      console.error('加载仓库失败:', error)
    }
  }
  
  // 加载商品（包含库存信息）
  const loadProducts = async () => {
    try {
      // 使用 /products/inventory 接口，返回的数据包含库存信息
      const response = await request({ url: '/products/inventory', method: 'GET' })
      if (response && Array.isArray(response)) {
        products.value = response
      }
    } catch (error) {
      console.error('加载商品失败:', error)
    }
  }
  
  // 加载单位
  const loadUnits = async () => {
    try {
      const [measurementResponse, packagingResponse] = await Promise.all([
        request({ url: '/products/units/measurements', method: 'GET' }),
        request({ url: '/products/units/packagings', method: 'GET' })
      ])
      units.value = Array.isArray(measurementResponse) ? measurementResponse : []
      packagingUnits.value = Array.isArray(packagingResponse) ? packagingResponse : []
    } catch (error) {
      console.error('加载单位失败:', error)
    }
  }
  
  const loadBankAccounts = async () => {
    try {
      const response = await request({ url: '/bank-accounts/options', method: 'GET' })
      bankAccounts.value = Array.isArray(response?.data)
        ? response.data
        : (Array.isArray(response?.items) ? response.items : [])
    } catch (error) {
      console.error('加载结算账户失败:', error)
      bankAccounts.value = []
    }
  }
  
  const loadOrderDirectory = async () => {
    try {
      const response = await request.get('/admin/directory')
      departments.value = Array.isArray(response?.departments)
        ? response.departments
        : []
      employees.value = Array.isArray(response?.employees)
        ? response.employees.map(employee => ({
            ...employee,
            departmentIds: Array.isArray(employee.departmentIds)
              ? employee.departmentIds.map(Number).filter(Number.isFinite)
              : []
          }))
        : []
    } catch (error) {
      console.warn('加载员工目录失败:', error)
      departments.value = []
      employees.value = []
    }
  }
  
  // 加载订单数据（编辑模式）
  const loadOrderData = async (orderId) => {
    console.log('loadOrderData 被调用，订单ID:', orderId)
    try {
      const response = await request({
        url: `/orders/${orderId}`,
        method: 'GET'
      })
  
      console.log('订单数据加载成功:', response)
  
      if (response) {
        if (props.action === 'edit' && response.is_audited) readOnly.value = true
        // 填充基础信息
        formData.value.storeId = response.store_id || ''
        formData.value.customerId = response.customer_id || ''
        formData.value.warehouseId = response.warehouse_id || ''
  
        // 处理日期格式：复制模式始终使用当前日期
        if (copySourceId.value) {
          // 复制订单时，使用当前日期
          formData.value.orderDate = new Date().toISOString().split('T')[0]
        } else {
          // 编辑模式时，使用源订单日期
          const rawDate = response.order_date || response.date || ''
          if (rawDate) {
            formData.value.orderDate = rawDate.split(' ')[0] // 只取日期部分
          } else {
            formData.value.orderDate = ''
          }
        }
  
        formData.value.orderNumber = response.order_number || ''
        formData.value.contactPerson = response.contact_person || response.receiver_name || ''
        formData.value.contactPhone = response.contact_phone || response.receiver_phone || ''
        formData.value.contactAddress = response.contact_address || response.receiver_address || ''
        formData.value.projectName = response.project_name || ''
        formData.value.packaging = response.goods_packaging || '桶装'
        formData.value.logisticsService = normalizeLogisticsService(response.logistics_service)
        formData.value.salesPerson = response.sales_person || ''
        formData.value.creator = currentCreatorName.value
        formData.value.orderRemark = response.remark || ''
        formData.value.discountAmount = response.discount_amount || null
        formData.value.otherFees = response.other_fees || null
        formData.value.settlementAccount = response.settlement_account || ''
        formData.value.currentPayment = response.current_payment || 0
  
        console.log('基础信息填充完成，formData:', formData.value)
  
        // 填充商品明细
        if (response.order_goods && response.order_goods.length > 0) {
          console.log('开始填充商品明细，order_goods:', response.order_goods)
          const taxEnabled = response.order_goods.some(item =>
            Number(item.tax_rate) > 0 ||
            Number(item.tax_included_price) > 0 ||
            Number(item.total_amount) > 0
          ) || Number(response.tax_amount) > 0
          const savedTaxRate = response.order_goods.find(item => Number(item.tax_rate) > 0)?.tax_rate
  
          showTaxColumns.value = taxEnabled
          formData.value.taxRate = taxEnabled
            ? (Number(savedTaxRate) || DEFAULT_TAX_RATE)
            : 0
  
          formData.value.items = response.order_goods.map(item => ({
            productId: item.product_id || '',
            goodsName: item.goods_name || '',
            spec: item.spec || '',
            unit: item.unit || '',
            warehouseId: item.warehouse_id || '',
            warehouseName: item.warehouse_name || '',
            currentStock: null, // 需要重新查询
            packages: item.packages || null,
            quantity: item.quantity || null,
            price: item.price || null,
            taxRate: taxEnabled ? (Number(item.tax_rate) || DEFAULT_TAX_RATE) : 0,
            taxIncludedPrice: taxEnabled ? (Number(item.tax_included_price) || 0) : 0,
            amount: item.amount || null,
            totalAmount: taxEnabled ? (Number(item.total_amount) || 0) : 0,
            remark: item.remark || '',
            showDropdown: false,
            filteredProducts: [],
            unitConversions: [],
            conversionRate: null
          }))
  
          console.log('商品明细填充完成，items:', formData.value.items)
  
          // 编辑模式：在已有数据基础上增加3行空行
          for (let i = 0; i < 3; i++) {
            formData.value.items.push({
              productId: '',
              goodsName: '',
              spec: '',
              unit: '',
              warehouseId: '',
              warehouseName: '',
              currentStock: null,
              packages: null,
              quantity: null,
              price: null,
              taxRate: null,
              taxIncludedPrice: null,
              amount: null,
              totalAmount: 0,
              remark: '',
              showDropdown: false,
              filteredProducts: [],
              unitConversions: [],
              conversionRate: null
            })
          }
  
          // 重新查询每个商品的当前库存
          for (let item of formData.value.items) {
            if (item.productId && item.warehouseId) {
              await updateStockInfo(item)
            }
          }
  
          normalizeTaxRows(taxEnabled, true)
        }
  
        // 保留数据库总件数，直到下一次明细件数变化。
        if (response.total_packages !== undefined && response.total_packages !== null) {
          totalPackages.value = Number(response.total_packages)
          totalPackagesManuallyEdited.value = true
        } else {
          totalPackages.value = totalPackagesCalculated.value
          totalPackagesManuallyEdited.value = false
        }
  
        // 加载客户欠款
        if (response.customer_id) {
          await loadCustomerDebt(response.customer_id)
        }
  
        console.log('订单数据加载完毕')
      }
    } catch (error) {
      console.error('加载订单数据失败:', error)
      loadFailed.value = true
      showErrorModal('加载订单数据失败，请稍后重试')
    }
  }
  
  // 根据单位ID获取单位名称
  const getUnitName = (unitId) => {
    const unit = units.value.find(u => u.id === unitId)
    return unit ? unit.name : ''
  }
  
  const handlePackagingChange = async () => {
    if (formData.value.packaging !== ADD_PACKAGING_VALUE) {
      return
    }
  
    const packagingName = window.prompt('请输入新的包装名称')
    formData.value.packaging = '桶装'
  
    if (!packagingName || !packagingName.trim()) {
      return
    }
  
    const trimmedName = packagingName.trim()
    if (packagingOptions.value.includes(trimmedName)) {
      formData.value.packaging = trimmedName
      return
    }
  
    try {
      const response = await request({
        url: '/products/units',
        method: 'POST',
        data: { name: trimmedName, type: 'packaging' }
      })
  
      if (!response?.success) {
        throw new Error(response?.message || '新增包装失败')
      }
  
      await loadUnits()
      formData.value.packaging = trimmedName
    } catch (error) {
      console.error('新增包装失败:', error)
      showErrorModal(`新增包装失败：${error.response?.data?.message || error.message}`)
    }
  }
  
  // 门店改变
  const onStoreChange = () => {
    closeCustomerDropdown()
  
    // 重置客户和仓库选择
    formData.value.customerId = ''
    formData.value.warehouseId = ''
    formData.value.contactPerson = ''
    formData.value.contactPhone = ''
    formData.value.contactAddress = ''
    formData.value.settlementAccount = getPreferredSettlementAccount(formData.value.storeId)
  
    // 清空商品列表
    clearProductItems()
  }
  
  // 仓库改变
  const onWarehouseChange = () => {
    // 仓库改变后，商品列表会通过 filteredProducts 自动筛选
    // 清空商品列表
    clearProductItems()
  }
  
  // 清空商品列表
  const clearProductItems = () => {
    formData.value.items = Array.from({ length: 8 }, () => ({
      productId: '',
      goodsName: '',
      spec: '',
      unit: '',
      warehouseId: '',
      warehouseName: '',
      currentStock: null,
      packages: null,
      quantity: null,
      price: null,
      taxRate: null,
      taxIncludedPrice: null,
      amount: null,
      totalAmount: null,
      remark: '',
      showDropdown: false,
      filteredProducts: [],
      unitConversions: [],
      conversionRate: null
    }))
  }
  
  // 加载客户欠款
  const customerReceivable = ref(0)
  const loadCustomerDebt = async (customerId) => {
    if (!customerId) {
      customerReceivable.value = 0
      return
    }
  
    try {
      const response = await request({
        url: `/customers/${customerId}`,
        method: 'GET'
      })
  
      if (String(formData.value.customerId) === String(customerId) &&
          response && response.receivable !== undefined) {
        customerReceivable.value = response.receivable || 0
      }
    } catch (error) {
      console.error('加载客户欠款失败:', error)
      if (String(formData.value.customerId) === String(customerId)) {
        customerReceivable.value = 0
      }
    }
  }
  
  // 客户改变
  const onCustomerChange = () => {
    const customer = customers.value.find(c =>
      String(c.id) === String(formData.value.customerId)
    )
    if (customer) {
      formData.value.contactPerson = customer.contactPerson || ''
      formData.value.contactPhone = customer.phone || ''
      formData.value.contactAddress = customer.address || ''
    }
  
    // 加载客户欠款
    loadCustomerDebt(formData.value.customerId)
  }
  
  // 显示商品下拉框
  const productMatchesSearch = (product, searchText) => {
    const keyword = String(searchText || '').trim().toLowerCase()
    if (!keyword) return true
  
    const productName = String(product.name || '').toLowerCase()
    const specification = String(product.specification || product.spec || '').toLowerCase()
  
    return productName.includes(keyword) || specification.includes(keyword)
  }
  
  const showProductDropdown = (index) => {
    // 如果没有选择门店和仓库，直接返回，不显示下拉框
    if (!formData.value.storeId || !formData.value.warehouseId) {
      return
    }
  
    focusedRow.value = index
    formData.value.items[index].showDropdown = true
  
    // 商品名称和规格型号都支持搜索
    const searchText = formData.value.items[index].goodsName
    formData.value.items[index].filteredProducts = filteredProducts.value.filter(product =>
      productMatchesSearch(product, searchText)
    )
  
    nextTick(updateProductDropdownPosition)
  }
  
  // 隐藏商品下拉框
  const hideProductDropdown = (index) => {
    setTimeout(() => {
      if (formData.value.items[index]) formData.value.items[index].showDropdown = false
    }, 200)
  }
  
  // 过滤商品
  const filterProducts = (index) => {
    const searchText = formData.value.items[index].goodsName
    formData.value.items[index].filteredProducts = filteredProducts.value.filter(product =>
      productMatchesSearch(product, searchText)
    )
  
    nextTick(updateProductDropdownPosition)
  }
  
  // 修改已选商品时，清空当前行的商品相关数据，保留用户正在输入的搜索内容
  const clearProductRowData = (index, goodsName = '') => {
    const item = formData.value.items[index]
    if (!item) return
  
    Object.assign(item, {
      productId: '',
      goodsName,
      spec: '',
      unit: '',
      warehouseId: '',
      warehouseName: '',
      currentStock: null,
      packages: null,
      quantity: null,
      price: null,
      taxRate: null,
      taxIncludedPrice: null,
      amount: null,
      totalAmount: null,
      remark: '',
      unitConversions: [],
      baseUnitId: '',
      conversionRate: null,
      historyPriceLoading: false,
      historyPriceRequestKey: ''
    })
  
    syncTotalPackagesFromItems()
  }
  
  const handleProductInput = (index) => {
    const item = formData.value.items[index]
    if (!item) return
  
    dismissValidationHint(`item-product-${index}`)
    const searchText = item.goodsName
    if (item.productId) {
      clearProductRowData(index, searchText)
    }
  
    filterProducts(index)
  }
  
  // 选择商品
  const selectProduct = (index, product) => {
    const item = formData.value.items[index]
    item.productId = product.id
    item.goodsName = product.name
    item.spec = product.specification || ''
  
    // 根据 unitId 查找单位名称
    if (product.unitId) {
      const unit = units.value.find(u => u.id === product.unitId)
      item.unit = unit ? unit.name : ''
    } else {
      item.unit = ''
    }
  
    item.price = product.price || 0
    item.taxRate = showTaxColumns.value ? DEFAULT_TAX_RATE : 0
    item.taxIncludedPrice = showTaxColumns.value && product.price
      ? parseFloat((product.price * (1 + DEFAULT_TAX_RATE / 100)).toFixed(2))
      : 0
  
    // 保存单位换算信息
    item.unitConversions = product.unitConversions || []
    item.baseUnitId = product.unitId
  
    // 提取换算比例（件 → 基础单位，如 1件 = 20公斤）
    if (item.unitConversions && item.unitConversions.length > 0) {
      item.conversionRate = item.unitConversions[0].value || null
    } else {
      item.conversionRate = null
    }
  
    // 自动设置仓库（使用顶部选择的仓库或商品默认仓库）
    if (formData.value.warehouseId) {
      item.warehouseId = formData.value.warehouseId
      const warehouse = warehouses.value.find(w => w.id === formData.value.warehouseId)
      item.warehouseName = warehouse ? warehouse.name : ''
    } else if (product.warehouseId) {
      item.warehouseId = product.warehouseId
      const warehouse = warehouses.value.find(w => w.id === product.warehouseId)
      item.warehouseName = warehouse ? warehouse.name : ''
    }
  
    // 获取当前库存
    item.currentStock = product.stock || 0
  
    item.showDropdown = false
    item.historyPriceLoading = false
    item.historyPriceRequestKey = ''
    calculateRowAmount(index)
    loadHistoryPrice(index, product.id)
  }
  
  const loadHistoryPrice = async (index, productId) => {
    const customerId = formData.value.customerId
    if (!customerId || !productId) return
  
    const item = formData.value.items[index]
    if (!item) return
    const requestKey = `${customerId}:${productId}`
    item.historyPriceLoading = true
    item.historyPriceRequestKey = requestKey
  
    try {
      const response = await request({
        url: '/orders/history-price',
        method: 'GET',
        params: { customerId, productId }
      })
      if (
        formData.value.items[index] !== item ||
        item.historyPriceRequestKey !== requestKey
      ) {
        return
      }
  
      const historyPrice = Number(response?.price)
      if (
        response?.success &&
        Number.isFinite(historyPrice) &&
        historyPrice >= 0 &&
        String(formData.value.customerId) === String(customerId) &&
        String(item.productId) === String(productId)
      ) {
        item.price = historyPrice
        if (showTaxColumns.value) {
          item.taxIncludedPrice = parseFloat(
            (historyPrice * (1 + (Number(item.taxRate) || DEFAULT_TAX_RATE) / 100)).toFixed(2)
          )
        }
        calculateRowAmount(index)
      }
    } catch (error) {
      console.warn('加载客户商品历史单价失败:', error)
    } finally {
      if (formData.value.items[index] === item && item.historyPriceRequestKey === requestKey) {
        item.historyPriceLoading = false
      }
    }
  }
  
  // 更新商品库存信息（编辑模式使用）
  const updateStockInfo = async (item) => {
    try {
      // 从商品列表中查找该商品
      const product = products.value.find(p => p.id === item.productId)
      if (product) {
        // 更新库存
        item.currentStock = product.stock || 0
  
        // 更新仓库名称
        if (item.warehouseId) {
          const warehouse = warehouses.value.find(w => w.id === item.warehouseId)
          item.warehouseName = warehouse ? warehouse.name : ''
        }
  
        // 更新单位换算信息
        item.unitConversions = product.unitConversions || []
        if (item.unitConversions && item.unitConversions.length > 0) {
          item.conversionRate = item.unitConversions[0].value || null
        }
      }
    } catch (error) {
      console.error('更新库存信息失败:', error)
    }
  }
  
  // 单价改变时自动计算含税单价
  const onPriceChange = (index) => {
    const item = formData.value.items[index]
  
    if (!showTaxColumns.value) {
      item.taxRate = 0
      item.taxIncludedPrice = 0
      calculateRowAmount(index)
      return
    }
  
    const taxRate = item.taxRate !== null && item.taxRate !== undefined ? item.taxRate : 0
  
    if (item.price !== null && item.price !== undefined && item.price !== '') {
      // 含税单价 = 单价 × (1 + 税率/100)，保留两位小数
      item.taxIncludedPrice = parseFloat((item.price * (1 + taxRate / 100)).toFixed(2))
    }
  
    calculateRowAmount(index)
  }
  
  // 含税单价改变时自动计算单价
  const onTaxIncludedPriceChange = (index) => {
    const item = formData.value.items[index]
  
    if (!showTaxColumns.value) {
      item.taxRate = 0
      item.taxIncludedPrice = 0
      item.totalAmount = 0
      return
    }
  
    const taxRate = item.taxRate !== null && item.taxRate !== undefined ? item.taxRate : 0
  
    if (item.taxIncludedPrice !== null && item.taxIncludedPrice !== undefined && item.taxIncludedPrice !== '') {
      // 单价 = 含税单价 ÷ (1 + 税率/100)，保留两位小数
      item.price = parseFloat((item.taxIncludedPrice / (1 + taxRate / 100)).toFixed(2))
    }
  
    calculateRowAmount(index)
  }
  
  // 行税率改变时重新计算含税单价
  const onItemTaxRateChange = (index) => {
    const item = formData.value.items[index]
  
    if (!showTaxColumns.value) {
      item.taxRate = 0
      item.taxIncludedPrice = 0
      item.totalAmount = 0
      return
    }
  
    // 如果有单价，则重新计算含税单价
    if (item.price !== null && item.price !== undefined && item.price !== '') {
      onPriceChange(index)
    }
  }
  
  // 件数改变时自动换算数量
  const onPackagesChange = (index) => {
    const item = formData.value.items[index]
  
    // 如果有换算比例，自动计算数量
    if (item.conversionRate && item.packages) {
      item.quantity = item.packages * item.conversionRate
    }
  
    syncTotalPackagesFromItems()
    calculateRowAmount(index)
  }
  
  // 数量改变时自动换算件数
  const onQuantityChange = (index) => {
    const item = formData.value.items[index]
  
    // 如果有换算比例，自动计算件数
    if (item.conversionRate && item.quantity) {
      item.packages = item.quantity / item.conversionRate
      syncTotalPackagesFromItems()
    }
  
    calculateRowAmount(index)
  }
  
  // 计算行金额
  const calculateRowAmount = (index) => {
    const item = formData.value.items[index]
    item.amount = (item.quantity || 0) * (item.price || 0)
    item.totalAmount = showTaxColumns.value
      ? (item.quantity || 0) * (item.taxIncludedPrice || 0)
      : 0
  }
  
  const normalizeTaxRows = (taxEnabled, preserveExisting = false) => {
    formData.value.taxRate = taxEnabled
      ? (Number(formData.value.taxRate) || DEFAULT_TAX_RATE)
      : 0
  
    formData.value.items.forEach((item, index) => {
      if (!item.productId) {
        item.taxRate = null
        item.taxIncludedPrice = null
        item.totalAmount = 0
        calculateRowAmount(index)
        return
      }
  
      if (!taxEnabled) {
        item.taxRate = 0
        item.taxIncludedPrice = 0
        item.totalAmount = 0
        calculateRowAmount(index)
        return
      }
  
      item.taxRate = Number(item.taxRate) || DEFAULT_TAX_RATE
      const price = Number(item.price) || 0
      const existingTaxIncludedPrice = Number(item.taxIncludedPrice)
      const hasExistingTaxIncludedPrice =
        item.taxIncludedPrice !== null &&
        item.taxIncludedPrice !== '' &&
        Number.isFinite(existingTaxIncludedPrice)
  
      if (!preserveExisting || !hasExistingTaxIncludedPrice) {
        item.taxIncludedPrice = price
          ? parseFloat((price * (1 + item.taxRate / 100)).toFixed(2))
          : 0
      }
      calculateRowAmount(index)
    })
  }
  
  // 添加行
  const addRow = (index) => {
    formData.value.items.splice(index + 1, 0, {
      productId: '',
      goodsName: '',
      spec: '',
      unit: '',
      warehouseId: '',
      warehouseName: '',
      currentStock: null,
      packages: null,
      quantity: null,
      price: null,
      taxRate: null,
      taxIncludedPrice: null,
      amount: null,
      totalAmount: null,
      remark: '',
      showDropdown: false,
      filteredProducts: [],
      unitConversions: [],
      conversionRate: null
    })
  }
  
  // 删除行
  const removeRow = (index) => {
    if (formData.value.items.length > 1) {
      const [removed] = formData.value.items.splice(index, 1)
      if (Number(removed?.packages)) {
        syncTotalPackagesFromItems()
      }
    }
  }
  
  // 计算合计
  const totalPackagesCalculated = computed(() => {
    return formData.value.items.reduce((sum, item) => sum + (item.packages || 0), 0)
  })
  
  // 总件数：稳定的数据源
  // - 首次根据明细自动初始化
  // - 手动输入优先，下一次明细件数变化后恢复自动汇总
  // - 从数据库/草稿加载时，先保留保存的值
  const totalPackages = ref(0)
  const totalPackagesManuallyEdited = ref(false) // 标记用户是否手动修改过
  const syncTotalPackagesFromItems = () => {
    totalPackagesManuallyEdited.value = false
    totalPackages.value = totalPackagesCalculated.value
  }
  
  const totalQuantity = computed(() => {
    return formData.value.items.reduce((sum, item) => sum + (item.quantity || 0), 0)
  })
  
  const totalAmount = computed(() => {
    return formData.value.items.reduce((sum, item) => sum + (item.amount || 0), 0)
  })
  
  const totalTaxAmount = computed(() => {
    if (!showTaxColumns.value) return 0
    return formData.value.items.reduce((sum, item) => sum + (item.totalAmount || 0), 0)
  })
  
  watch(showTaxColumns, (taxEnabled) => {
    normalizeTaxRows(taxEnabled)
  })
  
  // 自动模式下同步明细件数；手动模式由件数输入事件解除。
  watch(
    totalPackagesCalculated,
    (newCalculated) => {
      if (!totalPackagesManuallyEdited.value) {
        totalPackages.value = newCalculated
      }
    },
    { immediate: false }
  )
  
  // 监听含税金额变化，自动更新折扣金额
  watch(
    () => (showTaxColumns.value ? totalTaxAmount.value : totalAmount.value),
    (newTotal) => {
      // 根据含税开关状态，选择不同的金额
      formData.value.discountAmount = newTotal
    },
    { immediate: true }
  )
  
  // 应收金额 = 折扣金额 + 其他费用
  const shouldReceive = computed(() => {
    const discount = formData.value.discountAmount
    const fees = formData.value.otherFees
    if (discount === null && !fees) return null
    return (discount || 0) + (fees || 0)
  })
  
  // 本单欠款 = 折扣金额 + 其他费用 - 本次收款
  const currentDebt = computed(() => {
    const discount = formData.value.discountAmount || 0
    const fees = formData.value.otherFees || 0
    const payment = formData.value.currentPayment || 0
    return discount + fees - payment
  })
  
  // 计算最终金额
  const calculateFinal = () => {
    // 触发计算
  }
  
  // 用户手动修改总件数时的处理
  const onTotalPackagesManualInput = () => {
    totalPackagesManuallyEdited.value = true
  }
  
  // 监听客户选择变化
  watch(() => formData.value.customerId, (newCustomerId) => {
    if (newCustomerId) {
      loadCustomerDebt(newCustomerId)
    } else {
      customerReceivable.value = 0
    }
  })
  
  // 表单校验
  const validateForm = () => {
    dismissValidationHint()
  
    // 1. 检查门店
    if (!formData.value.storeId) {
      showValidationHint('storeId', '请选择门店。')
      return false
    }
  
    // 2. 检查客户
    if (!formData.value.customerId) {
      showValidationHint('customerId', '请选择客户。')
      return false
    }
  
    // 3. 检查仓库
    if (!formData.value.warehouseId) {
      showValidationHint('warehouseId', '请选择仓库。')
      return false
    }
  
    // 4. 检查联系人信息
    if (!formData.value.contactPerson) {
      showValidationHint('contactPerson', '请填写联系人。')
      return false
    }
  
    if (!formData.value.contactPhone) {
      showValidationHint('contactPhone', '请填写联系方式。')
      return false
    }
  
    // 5. 检查商品明细（商品ID和数量必填，件数、单价可以为空）
    const validItems = formData.value.items.filter(item =>
      item.productId && item.quantity && item.quantity > 0
    )
  
    // 检查是否有填了商品但没填数量的行
    const invalidItemIndex = formData.value.items.findIndex(item =>
      item.productId && (!item.quantity || item.quantity <= 0)
    )
  
    if (invalidItemIndex !== -1) {
      showValidationHint(`item-quantity-${invalidItemIndex}`, '请填写商品数量。')
      return false
    }
  
    if (validItems.length === 0) {
      const productIndexWithText = formData.value.items.findIndex(item =>
        item.goodsName && !item.productId
      )
      const firstEmptyProductIndex = formData.value.items.findIndex(item => !item.productId)
      const productIndex = productIndexWithText !== -1
        ? productIndexWithText
        : (firstEmptyProductIndex === -1 ? 0 : firstEmptyProductIndex)
      showValidationHint(`item-product-${productIndex}`, '请至少添加一条商品明细。')
      return false
    }
  
    return true
  }
  
  // 保存订单
  const saving = ref(false)
  
  const handleSave = async () => {
    if (readOnly.value || loading.value || loadFailed.value) return
    // 1. 校验表单
    if (!validateForm()) return
  
    // 2. 防止重复提交
    if (saving.value) {
      showErrorModal('正在保存中，请稍候...')
      return
    }
  
    try {
      saving.value = true
  
      // 3. 过滤有效商品（只要求填写商品ID，件数、数量、单价都可以为空）
      const validItems = formData.value.items.filter(item =>
        item.productId
      )
      const taxEnabled = showTaxColumns.value
  
      // 4. 构建请求数据
      const requestData = {
        storeId: formData.value.storeId,
        customerId: formData.value.customerId,
        warehouseId: formData.value.warehouseId,
        orderDate: formData.value.orderDate,
        orderNumber: formData.value.orderNumber,
        contactPerson: formData.value.contactPerson,
        contactPhone: formData.value.contactPhone,
        contactAddress: formData.value.contactAddress,
        projectName: formData.value.projectName,
        goodsPackaging: formData.value.packaging,
        logisticsService: formData.value.logisticsService,
        salesPerson: formData.value.salesPerson,
        creator: currentCreatorName.value,
        orderRemark: formData.value.orderRemark,
        taxEnabled,
        taxRate: taxEnabled
          ? (Number(formData.value.taxRate) || DEFAULT_TAX_RATE)
          : 0,
        discountAmount: formData.value.discountAmount || 0,
        otherFees: formData.value.otherFees || 0,
        settlementAccount: formData.value.settlementAccount,
        currentPayment: formData.value.currentPayment || 0,
        items: validItems.map(item => ({
          productId: item.productId,
          goodsName: item.goodsName || '',
          spec: item.spec || '',
          unit: item.unit || '',
          warehouseId: item.warehouseId || null,
          packages: Number(item.packages) || 0,
          quantity: Number(item.quantity) || 0,
          price: Number(item.price) || 0,
          taxRate: taxEnabled ? (Number(item.taxRate) || DEFAULT_TAX_RATE) : 0,
          taxIncludedPrice: taxEnabled ? (Number(item.taxIncludedPrice) || 0) : 0,
          amount: Number(item.amount) || 0,
          totalAmount: taxEnabled ? (Number(item.totalAmount) || 0) : 0,
          remark: item.remark || ''
        }))
      }
  
      // 直接使用用户最终看到的总件数（不管是自动计算的还是手动修改的）
      const normalizedTotalPackages = Number(totalPackages.value)
      requestData.totalPackages = Number.isFinite(normalizedTotalPackages)
        ? normalizedTotalPackages
        : 0
  
      // 5. 调用接口
      let response
      if (isEditMode.value) {
        // 编辑模式：PUT 请求
        response = await request({
          url: `/orders/${props.orderId}`,
          method: 'PUT',
          data: requestData
        })
      } else {
        // 新增模式：POST 请求
        response = await request({
          url: '/orders',
          method: 'POST',
          data: requestData
        })
      }
  
      // 6. 处理结果
      if (response && response.success) {
        persistOrderFormDefaults()
        const savedOrderNumber = response.orderNumber ||
          response.data?.order_number ||
          response.data?.orderNumber
        if (savedOrderNumber) {
          formData.value.orderNumber = savedOrderNumber
        }
  
        const successMessage = getSaveSuccessMessage()
        printOrderVariables.value = cloneDraftValue(orderPrintVariables.value)
        showSuccessToast(successMessage)
        selectedPrintTemplate.value = null
        selectedPrintPrinter.value = null
        printPreviewAutoPrint.value = false
  
        if (!isEditMode.value) {
          discardDraft()
          resetOrderFields()
          formData.value.orderNumber = ''
        }
  
        printTemplateDialogOpen.value = true
  
        if (!isEditMode.value) {
          await generateNewOrderNumber()
          draftReady.value = true
          persistDraft()
        }
      } else {
        showErrorModal('订单保存失败：' + (response?.message || '未知错误'))
      }
    } catch (error) {
      console.error('保存订单失败:', error)
  
      // 错误处理
      if (error.response && error.response.data && error.response.data.message) {
        showErrorModal('保存失败：' + error.response.data.message)
      } else if (error.message) {
        showErrorModal('保存失败：' + error.message)
      } else {
        showErrorModal('保存失败：网络错误，请检查网络连接')
      }
    } finally {
      saving.value = false
    }
  }
  
  // 保存并打印
  const handleSaveAndPrint = () => {
    handleSave()
  }
  
  // 关闭
  const showCloseConfirm = () => {
    showCloseConfirmModal.value = true
  }
  
  const cancelClose = () => {
    showCloseConfirmModal.value = false
  }
  
  const confirmClose = () => {
    showCloseConfirmModal.value = false
    discardDraft()
    router.back()
  }
  
  // 清空表单
  const handleClearForm = () => {
    showClearConfirmModal.value = true
  }
  
  const cancelClear = () => {
    showClearConfirmModal.value = false
  }
  
  const resetOrderFields = () => {
    dismissValidationHint()
    closeCustomerDropdown()
    formData.value.storeId = ''
    formData.value.customerId = ''
    customerReceivable.value = 0
    formData.value.warehouseId = ''
    formData.value.orderDate = getCurrentOrderDate()
    formData.value.contactPerson = ''
    formData.value.contactPhone = ''
    formData.value.contactAddress = ''
    formData.value.settlementAccount = ''
    formData.value.projectName = ''
    formData.value.packaging = '桶装'
    formData.value.logisticsService = logisticsServiceOptions[0]
    formData.value.salesPerson = ''
    formData.value.creator = currentCreatorName.value
    formData.value.orderRemark = ''
    formData.value.taxRate = 0
    formData.value.discountAmount = null
    formData.value.otherFees = null
    formData.value.currentPayment = 0
  
    // 清空商品列表
    initEmptyRows()
    showTaxColumns.value = false
    if (!isEditMode.value) {
      applyNewOrderDefaults()
    }
  }
  
  const confirmClear = () => {
    showClearConfirmModal.value = false
    resetOrderFields()
  }
  
  watch(
    [formData, showTaxColumns, totalPackages],
    () => {
      scheduleDraftSave()
    },
    { deep: true }
  )
  
  // 初始化
  onMounted(async () => {
    try {
    window.addEventListener('resize', updateProductDropdownPosition)
    window.addEventListener('scroll', updateProductDropdownPosition, true)
    window.addEventListener('resize', updateCustomerDropdownPosition)
    window.addEventListener('scroll', updateCustomerDropdownPosition, true)
    window.addEventListener('resize', updateValidationHintPosition)
    window.addEventListener('scroll', updateValidationHintPosition, true)
    document.addEventListener('pointerdown', handleCustomerDocumentPointerdown)
  
    console.log('OrderForm mounted, props.orderId:', props.orderId)
    console.log('isEditMode:', isEditMode.value)
  
    if (setHeaderActions) {
      setHeaderActions(null)
    }
  
    await Promise.all([
      loadStores(),
      loadCustomers(),
      loadWarehouses(),
      loadProducts(),
      loadUnits(),
      loadBankAccounts(),
      loadOrderDirectory()
    ])
  
    let savedDraft = readOnly.value ? null : orderDraftStore.draft
    if (savedDraft && savedDraft.key !== orderFormRoute.key) {
      orderDraftStore.clearDraft()
      savedDraft = null
    }
  
    if (savedDraft && savedDraft.key === orderFormRoute.key) {
      await restoreDraft(savedDraft)
  
      for (const item of formData.value.items) {
        if (item.productId && item.warehouseId) {
          await updateStockInfo(item)
        }
      }
  
      if (formData.value.customerId) {
        await loadCustomerDebt(formData.value.customerId)
      }
    } else {
      if (isEditMode.value) {
        // 编辑模式：加载订单数据
        console.log('进入编辑模式，加载订单ID:', props.orderId)
        await loadOrderData(props.orderId)
      } else {
        // 新增模式：初始化空行并生成订单编号
        console.log('进入新增模式')
        initEmptyRows()
  
        if (copySourceId.value) {
          console.log('复制订单数据，源订单ID:', copySourceId.value)
          await loadOrderData(copySourceId.value)
          // 复制后清空日期，使用当前日期
          formData.value.orderDate = getCurrentOrderDate()
        } else {
          applyNewOrderDefaults()
        }
  
        // 从订单列表中获取最大ID+1，生成正式订单编号
        await generateNewOrderNumber()
      }
    }
  
    draftReady.value = true
    persistDraft()
    } catch (error) {
      loadFailed.value = true
      showErrorModal(error?.response?.data?.message || '加载销售订单失败')
    } finally {
      loading.value = false
    }
  })
  
  onBeforeUnmount(() => {
    window.removeEventListener('resize', updateProductDropdownPosition)
    window.removeEventListener('scroll', updateProductDropdownPosition, true)
    window.removeEventListener('resize', updateCustomerDropdownPosition)
    window.removeEventListener('scroll', updateCustomerDropdownPosition, true)
    window.removeEventListener('resize', updateValidationHintPosition)
    window.removeEventListener('scroll', updateValidationHintPosition, true)
    document.removeEventListener('pointerdown', handleCustomerDocumentPointerdown)
    productInputRefs.clear()
    validationFieldRefs.clear()
    clearTimeout(validationHintTimer)
    clearTimeout(draftSaveTimer)
    clearTimeout(saveToastTimer)
    persistDraft()
  })
  
  // 生成新订单编号（从现有订单中找最大ID+1）
  async function generateNewOrderNumber() {
    try {
      const response = await request({
        url: '/orders',
        method: 'GET'
      })
  
      if (response && Array.isArray(response)) {
        // 从订单列表中找到最大的ID
        let maxId = 0
        response.forEach(order => {
          if (order.id && order.id > maxId) {
            maxId = order.id
          }
        })
  
        // 下一个订单ID = 最大ID + 1
        const nextId = maxId + 1
        formData.value.orderNumber = generateOrderNumber(nextId)
        console.log('生成订单编号:', formData.value.orderNumber, '(基于最大ID:', maxId, ')')
      } else {
        // 如果没有订单，从1开始
        formData.value.orderNumber = generateOrderNumber(1)
      }
    } catch (error) {
      console.error('获取订单列表失败:', error)
      // 不复用固定的临时编号；提交时由后端按新订单 ID 生成正式编号。
      formData.value.orderNumber = ''
    }
  }

  return {
    loading,
    loadFailed,
    readOnly,
    openPrint: () => { printTemplateDialogOpen.value = true },
    router,
    route,
    orderDraftStore,
    userStore,
    currentCreatorName,
    creatorNameStyle,
    setHeaderActions,
    showTaxColumns,
    DEFAULT_TAX_RATE,
    showCloseConfirmModal,
    showClearConfirmModal,
    printTemplateDialogOpen,
    printPreviewVisible,
    selectedPrintTemplate,
    selectedPrintPrinter,
    printPreviewAutoPrint,
    printOrderVariables,
    saveToast,
    saveToastTimer,
    isEditMode,
    copySourceId,
    draftKey,
    orderFormRoute,
    showModal,
    modalType,
    modalTitle,
    modalMessage,
    validationHint,
    validationHintStyle,
    validationHintPlacement,
    validationFieldRefs,
    validationHintTimer,
    setValidationFieldRef,
    dismissValidationHint,
    updateValidationHintPosition,
    showValidationHint,
    dismissSaveToast,
    showSuccessToast,
    showErrorModal,
    closeModal,
    stores,
    customers,
    warehouses,
    products,
    units,
    packagingUnits,
    bankAccounts,
    employees,
    departments,
    DEFAULT_PACKAGING_OPTIONS,
    ADD_PACKAGING_VALUE,
    logisticsServiceOptions,
    ORDER_FORM_DEFAULTS_STORAGE_KEY,
    SERVER_ORDER_DEFAULTS,
    readOrderFormDefaults,
    orderFormDefaults,
    getCurrentOrderDate,
    formData,
    salesPeople,
    packagingOptions,
    normalizeLogisticsService,
    getServerDefaultSettlementAccount,
    getPreferredSettlementAccount,
    applyNewOrderDefaults,
    persistOrderFormDefaults,
    draftReady,
    draftSaveTimer,
    cloneDraftValue,
    getDraftFormData,
    persistDraft,
    scheduleDraftSave,
    restoreDraft,
    discardDraft,
    filteredCustomers,
    CUSTOMER_PAGE_SIZE,
    customerSearch,
    customerPage,
    customerDropdownOpen,
    customerInputRef,
    customerDropdownRef,
    customerDropdownStyle,
    setCustomerInputRef,
    customerSearchResults,
    customerTotalPages,
    paginatedCustomers,
    updateCustomerDropdownPosition,
    openCustomerDropdown,
    closeCustomerDropdown,
    handleCustomerSearchInput,
    selectCustomer,
    changeCustomerPage,
    handleCustomerDocumentPointerdown,
    filteredWarehouses,
    selectedStoreName,
    storeBankAccounts,
    selectedCustomerName,
    selectedWarehouseName,
    orderPrintVariables,
    closePrintTemplateDialog,
    openSelectedPrintTemplate,
    previewSelectedPrintTemplate,
    printSelectedPrintTemplate,
    closeOrderPrintPreview,
    getSaveSuccessMessage,
    filteredProducts,
    focusedRow,
    productInputRefs,
    productDropdownStyle,
    setProductInputRef,
    activeProductRow,
    updateProductDropdownPosition,
    generateOrderNumber,
    initEmptyRows,
    loadStores,
    loadCustomers,
    loadWarehouses,
    loadProducts,
    loadUnits,
    loadBankAccounts,
    loadOrderDirectory,
    loadOrderData,
    getUnitName,
    handlePackagingChange,
    onStoreChange,
    onWarehouseChange,
    clearProductItems,
    customerReceivable,
    loadCustomerDebt,
    onCustomerChange,
    productMatchesSearch,
    showProductDropdown,
    hideProductDropdown,
    filterProducts,
    clearProductRowData,
    handleProductInput,
    selectProduct,
    loadHistoryPrice,
    updateStockInfo,
    onPriceChange,
    onTaxIncludedPriceChange,
    onItemTaxRateChange,
    onPackagesChange,
    onQuantityChange,
    calculateRowAmount,
    normalizeTaxRows,
    addRow,
    removeRow,
    totalPackagesCalculated,
    totalPackages,
    totalPackagesManuallyEdited,
    syncTotalPackagesFromItems,
    totalQuantity,
    totalAmount,
    totalTaxAmount,
    shouldReceive,
    currentDebt,
    calculateFinal,
    onTotalPackagesManualInput,
    validateForm,
    saving,
    handleSave,
    handleSaveAndPrint,
    showCloseConfirm,
    cancelClose,
    confirmClose,
    handleClearForm,
    cancelClear,
    resetOrderFields,
    confirmClear,
    generateNewOrderNumber
  }
}
