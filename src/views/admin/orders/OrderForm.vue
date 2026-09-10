<template>
  <div class="order-form-page">
    <!-- 顶部信息区 -->
    <div class="top-info-bar">
      <div class="info-group">
        <label>门店</label>
        <select v-model="formData.storeId" @change="onStoreChange">
          <option value="">请选择门店</option>
          <option v-for="store in stores" :key="store.id" :value="store.id">
            {{ store.name }}
          </option>
        </select>
      </div>

      <div class="info-group">
        <label>客户</label>
        <select v-model="formData.customerId" @change="onCustomerChange">
          <option value="">请选择客户</option>
          <option v-for="customer in filteredCustomers" :key="customer.id" :value="customer.id">
            {{ customer.customerName }}
          </option>
        </select>
      </div>

      <div class="info-group">
        <label>仓库</label>
        <select v-model="formData.warehouseId" @change="onWarehouseChange">
          <option value="">请选择仓库</option>
          <option v-for="warehouse in filteredWarehouses" :key="warehouse.id" :value="warehouse.id">
            {{ warehouse.name }}
          </option>
        </select>
      </div>

      <div class="info-group">
        <label>单据日期</label>
        <input type="date" v-model="formData.orderDate" />
      </div>

      <div class="info-group">
        <label>单据编号</label>
        <input type="text" v-model="formData.orderNumber" placeholder="ZG+日期+ID" />
      </div>

      <div class="info-group right-actions">
        <div class="tax-switch-group">
          <label class="switch-label">含税</label>
          <label class="switch">
            <input type="checkbox" v-model="showTaxColumns" />
            <span class="slider"></span>
          </label>
        </div>
        <button class="btn-clear" @click="handleClearForm">清空</button>
        <button class="btn-close" @click="showCloseConfirm">关闭 ››</button>
      </div>
    </div>

    <!-- 联系人信息区 -->
    <div class="contact-info-bar">
      <div class="info-group">
        <label>联系人:</label>
        <input type="text" v-model="formData.contactPerson" placeholder="请输入联系人" />
      </div>

      <div class="info-group">
        <label>联系方式:</label>
        <input type="tel" v-model="formData.contactPhone" placeholder="请输入联系方式" />
      </div>

      <div class="info-group wide">
        <label>联系地址:</label>
        <input type="text" v-model="formData.contactAddress" placeholder="请输入联系地址" />
      </div>

      <div class="info-group">
        <label>工程项目:</label>
        <input type="text" v-model="formData.projectName" placeholder="选填" />
      </div>

      <div class="info-group">
        <label>物流服务:</label>
        <select v-model="formData.logisticsService">
          <option
            v-for="service in logisticsServiceOptions"
            :key="service"
            :value="service"
          >
            {{ service }}
          </option>
        </select>
      </div>
    </div>

    <!-- 商品表格区 -->
    <div class="products-table-wrapper">
      <table class="products-table">
        <thead>
          <tr>
            <th style="width: 40px">☀</th>
            <th style="width: 60px">操作</th>
            <th style="width: 180px">*商品信息</th>
            <th style="width: 120px">规格型号</th>
            <th style="width: 80px">单位</th>
            <th style="width: 120px">所属仓库</th>
            <th style="width: 100px">当前库存</th>
            <th style="width: 80px">件数</th>
            <th style="width: 100px">*数量</th>
            <th style="width: 100px">*单价 (元)</th>
            <th v-if="showTaxColumns" style="width: 80px">税率(%)</th>
            <th v-if="showTaxColumns" style="width: 100px">含税单价</th>
            <th style="width: 120px">金额 (元)</th>
            <th v-if="showTaxColumns" style="width: 120px">含税金额</th>
            <th style="width: 180px">备注信息</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(item, index) in formData.items" :key="index" :class="{ 'row-focused': focusedRow === index }">
            <td class="center">{{ index + 1 }}</td>
            <td class="center">
              <button class="btn-icon btn-add" @click="addRow(index)" title="在下方插入一行">+</button>
              <button class="btn-icon btn-remove" @click="removeRow(index)" title="删除此行">×</button>
            </td>
            <td class="product-col">
              <div class="product-select-wrapper">
                <input
                  type="text"
                  v-model="item.goodsName"
                  @focus="showProductDropdown(index)"
                  @blur="hideProductDropdown(index)"
                  @input="filterProducts(index)"
                  class="product-input"
                />
                <div
                  v-if="item.showDropdown && item.filteredProducts && item.filteredProducts.length > 0"
                  class="product-dropdown"
                  @mousedown.prevent
                >
                  <div class="product-dropdown-header">
                    <span class="col-code">编号</span>
                    <span class="col-name">名称</span>
                    <span class="col-spec">规格</span>
                    <span class="col-unit">单位</span>
                    <span class="col-stock">库存</span>
                  </div>
                  <div
                    v-for="product in item.filteredProducts"
                    :key="product.id"
                    class="product-option"
                    @click="selectProduct(index, product)"
                  >
                    <span class="col-code">{{ product.code || '-' }}</span>
                    <span class="col-name">{{ product.name }}</span>
                    <span class="col-spec">{{ product.specification || '-' }}</span>
                    <span class="col-unit">{{ getUnitName(product.unitId) || '-' }}</span>
                    <span class="col-stock">{{ product.stock || 0 }}</span>
                  </div>
                </div>
              </div>
            </td>
            <td><input type="text" v-model="item.spec" readonly class="readonly-input" /></td>
            <td><input type="text" v-model="item.unit" readonly class="readonly-input" /></td>
            <td><input type="text" v-model="item.warehouseName" readonly class="readonly-input" /></td>
            <td class="right"><input type="text" :value="item.currentStock || ''" readonly class="readonly-input" /></td>
            <td><input type="number" v-model.number="item.packages" @input="onPackagesChange(index)" min="0" /></td>
            <td><input type="number" v-model.number="item.quantity" @input="onQuantityChange(index)" min="0" step="0.01" /></td>
            <td><input type="number" v-model.number="item.price" @input="onPriceChange(index)" min="0" step="0.01" /></td>
            <td v-if="showTaxColumns"><input type="number" v-model.number="item.taxRate" @input="onItemTaxRateChange(index)" min="0" max="100" step="0.01" /></td>
            <td v-if="showTaxColumns"><input type="number" v-model.number="item.taxIncludedPrice" @input="onTaxIncludedPriceChange(index)" min="0" step="0.01" /></td>
            <td class="right"><input type="text" :value="item.amount ? item.amount.toFixed(2) : ''" readonly class="readonly-input" /></td>
            <td v-if="showTaxColumns" class="right"><input type="text" :value="item.totalAmount ? item.totalAmount.toFixed(2) : ''" readonly class="readonly-input" /></td>
            <td><input type="text" v-model="item.remark" /></td>
          </tr>

          <!-- 合计行 -->
          <tr class="total-row">
            <td colspan="2" class="center"><button class="btn-text-link">合计</button></td>
            <td colspan="5"></td>
            <td class="right">
              <input
                type="number"
                :value="manualTotalPackages !== null ? manualTotalPackages : totalPackagesCalculated"
                @focus="onTotalPackagesFocus"
                @input="onManualTotalPackagesInput"
                class="editable-total"
                min="0"
              />
            </td>
            <td class="right">{{ totalQuantity ? totalQuantity.toFixed(2) : '' }}</td>
            <td :colspan="showTaxColumns ? 3 : 1"></td>
            <td class="right">{{ totalAmount ? totalAmount.toFixed(2) : '' }}</td>
            <td v-if="showTaxColumns" class="right">{{ totalTaxAmount ? totalTaxAmount.toFixed(2) : '' }}</td>
            <td></td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 底部信息区 -->
    <div class="bottom-info-bar">
      <div class="finance-row-full">
        <div class="info-group">
          <label>业务员</label>
          <select v-model="formData.salesPerson">
            <option value="柯晓">柯晓</option>
          </select>
        </div>

        <div class="info-group">
          <label>制单人</label>
          <select v-model="formData.creator">
            <option value="下单员">下单员</option>
          </select>
        </div>

        <div class="info-group wide">
          <label>备注信息</label>
          <input type="text" v-model="formData.orderRemark" placeholder="请输入备注信息" />
        </div>

        <div class="info-group">
          <label>包装</label>
          <select v-model="formData.packaging" @change="handlePackagingChange">
            <option
              v-for="packaging in packagingOptions"
              :key="packaging"
              :value="packaging"
            >
              {{ packaging }}
            </option>
            <option :value="ADD_PACKAGING_VALUE">新增包装...</option>
          </select>
        </div>

        <div class="finance-item">
          <label>折扣金额</label>
          <input type="number" v-model.number="formData.discountAmount" @input="calculateFinal" min="0" step="0.01" />
        </div>
        <div class="finance-item">
          <label>其他费用</label>
          <input type="number" v-model.number="formData.otherFees" @input="calculateFinal" min="0" />
        </div>
        <div class="finance-item">
          <label>结算账户</label>
          <input type="text" :value="selectedStoreName" readonly class="readonly-input" />
        </div>
      </div>

      <div class="finance-row">
        <div class="finance-item">
          <span class="finance-label">客户欠款:</span>
          <span class="finance-value">{{ customerReceivable ? customerReceivable.toFixed(2) : '0.00' }}</span>
        </div>
        <div class="finance-item">
          <span class="finance-label">本单应收:</span>
          <span class="finance-value">{{ shouldReceive ? shouldReceive.toFixed(2) : '0.00' }}</span>
        </div>
        <div class="finance-item">
          <label>本次收款:</label>
          <input type="number" v-model.number="formData.currentPayment" @input="calculateFinal" min="0" step="0.01" />
        </div>
        <div class="finance-item">
          <span class="finance-label red">本单欠款:</span>
          <span class="finance-value red">{{ currentDebt ? currentDebt.toFixed(2) : '0.00' }}</span>
        </div>
      </div>

      <div class="action-row">
        <label class="checkbox-label">
          <input type="checkbox" v-model="formData.printAfterSave" />
          保存后打印
        </label>
        <button class="btn-save-and-print" @click="handleSaveAndPrint" :disabled="saving">
          {{ saving ? '⏳ 保存中...' : '💾 保存并打印' }}
        </button>
        <button class="btn-save-final" @click="handleSaveFinal" :disabled="saving">
          {{ saving ? '⏳ 保存中...' : '保存(ctrl+Q)' }}
        </button>
      </div>
    </div>

    <!-- 清空确认弹窗 -->
    <div v-if="showClearConfirmModal" class="custom-modal-overlay" @click.self="cancelClear">
      <div class="custom-modal">
        <div class="modal-header">
          <div class="modal-icon warning">!</div>
          <h3>确认清空</h3>
        </div>
        <div class="modal-body">
          <p>确定要清空所有数据吗？此操作不可恢复</p>
        </div>
        <div class="modal-footer">
          <button class="btn-modal-cancel" @click="cancelClear">取消</button>
          <button class="btn-modal-confirm danger" @click="confirmClear">确定清空</button>
        </div>
      </div>
    </div>

    <!-- 关闭确认弹窗 -->
    <div v-if="showCloseConfirmModal" class="custom-modal-overlay" @click.self="cancelClose">
      <div class="custom-modal">
        <div class="modal-header">
          <div class="modal-icon warning">!</div>
          <h3>确认关闭</h3>
        </div>
        <div class="modal-body">
          <p>确定要关闭吗？未保存的数据将丢失</p>
        </div>
        <div class="modal-footer">
          <button class="btn-modal-cancel" @click="cancelClose">取消</button>
          <button class="btn-modal-confirm danger" @click="confirmClose">确定关闭</button>
        </div>
      </div>
    </div>

    <!-- 成功/错误提示弹窗 -->
    <div v-if="showModal" class="custom-modal-overlay" @click.self="closeModal">
      <div class="custom-modal">
        <div class="modal-header">
          <div class="modal-icon" :class="modalType">
            {{ modalType === 'success' ? '✓' : '✕' }}
          </div>
          <h3>{{ modalTitle }}</h3>
        </div>
        <div class="modal-body">
          <p>{{ modalMessage }}</p>
        </div>
        <div class="modal-footer">
          <button class="btn-modal-confirm" @click="closeModal">确定</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, inject, nextTick, onBeforeUnmount, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import request from '@/api/request'
import { useOrderDraftStore } from '@/stores/orderDraft'

const router = useRouter()
const route = useRoute()
const orderDraftStore = useOrderDraftStore()
const setHeaderActions = inject('setHeaderActions', null)

// 含税开关状态
const showTaxColumns = ref(false)
const DEFAULT_TAX_RATE = 13

// 手动修改的合计件数
const manualTotalPackages = ref(null)

// 关闭确认弹窗
const showCloseConfirmModal = ref(false)

// 清空确认弹窗
const showClearConfirmModal = ref(false)

// Props 定义
const props = defineProps({
  orderId: {
    type: Number,
    default: null
  }
})

// 判断是否为编辑模式
const isEditMode = computed(() => props.orderId !== null)
const copySourceId = computed(() => {
  const orderId = Number(route.query.copyFrom)
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

const showSuccessModal = (message) => {
  modalType.value = 'success'
  modalTitle.value = '操作成功'
  modalMessage.value = message
  showModal.value = true
}

const showErrorModal = (message) => {
  modalType.value = 'error'
  modalTitle.value = '操作失败'
  modalMessage.value = message
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
  // 如果是成功提示，关闭弹窗后返回列表
  if (modalType.value === 'success') {
    discardDraft()
    router.back()
  }
}

// 基础数据
const stores = ref([])
const customers = ref([])
const warehouses = ref([])
const products = ref([])
const units = ref([])
const packagingUnits = ref([])

const DEFAULT_PACKAGING_OPTIONS = ['无', '桶装', '纸箱', '托盘', '袋装']
const ADD_PACKAGING_VALUE = '__add_packaging__'
const logisticsServiceOptions = [
  '送货上门+回单拍照回传',
  '送货上门+回单邮回',
  '送货上门',
  '用户自提',
  '无'
]

// 表单数据
const formData = ref({
  storeId: '',
  customerId: '',
  warehouseId: '',
  orderDate: new Date().toISOString().split('T')[0],
  orderNumber: '',
  contactPerson: '',
  contactPhone: '',
  contactAddress: '',
  projectName: '',
  packaging: '无',
  logisticsService: '送货上门+回单拍照回传',
  salesPerson: '柯晓',
  creator: '下单员',
  orderRemark: '',
  taxRate: 0,
  discountAmount: null,
  otherFees: null,
  settlementAccount: '',
  currentPayment: 0,
  printAfterSave: false,
  items: []
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
  if (!draftReady.value) {
    return
  }

  orderDraftStore.saveDraft({
    key: orderFormRoute.key,
    mode: isEditMode.value ? 'edit' : 'create',
    orderId: props.orderId,
    formData: getDraftFormData(),
    showTaxColumns: showTaxColumns.value,
    manualTotalPackages: manualTotalPackages.value,
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
  formData.value.items = (formData.value.items || []).map(item => ({
    ...item,
    showDropdown: false,
    filteredProducts: []
  }))
  showTaxColumns.value = Boolean(draft.showTaxColumns)
  normalizeTaxRows(showTaxColumns.value, true)
  manualTotalPackages.value = draft.manualTotalPackages ?? null

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
  return customers.value.filter(c => c.storeId === formData.value.storeId)
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
  const store = stores.value.find(s => s.id === formData.value.storeId)
  return store ? store.name : ''
})

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
    conversionRate: null
  }))
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
      // 填充基础信息
      formData.value.storeId = response.store_id || ''
      formData.value.customerId = response.customer_id || ''
      formData.value.warehouseId = response.warehouse_id || ''

      // 处理日期格式：从 "2026-09-05 02:23" 提取 "2026-09-05"
      const rawDate = response.order_date || response.date || ''
      if (rawDate) {
        formData.value.orderDate = rawDate.split(' ')[0] // 只取日期部分
      } else {
        formData.value.orderDate = ''
      }

      formData.value.orderNumber = response.order_number || ''
      formData.value.contactPerson = response.contact_person || response.receiver_name || ''
      formData.value.contactPhone = response.contact_phone || response.receiver_phone || ''
      formData.value.contactAddress = response.contact_address || response.receiver_address || ''
      formData.value.projectName = response.project_name || ''
      formData.value.packaging = response.goods_packaging || '无'
      formData.value.logisticsService = normalizeLogisticsService(response.logistics_service)
      formData.value.salesPerson = response.sales_person || ''
      formData.value.creator = response.creator || ''
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
            taxRate: taxEnabled ? DEFAULT_TAX_RATE : 0,
            taxIncludedPrice: 0,
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

      // 加载客户欠款
      if (response.customer_id) {
        await loadCustomerDebt(response.customer_id)
      }

      console.log('订单数据加载完毕')
    }
  } catch (error) {
    console.error('加载订单数据失败:', error)
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
  formData.value.packaging = '无'

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
  // 重置客户和仓库选择
  formData.value.customerId = ''
  formData.value.warehouseId = ''
  formData.value.contactPerson = ''
  formData.value.contactPhone = ''
  formData.value.contactAddress = ''

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

    if (response && response.receivable !== undefined) {
      customerReceivable.value = response.receivable || 0
    }
  } catch (error) {
    console.error('加载客户欠款失败:', error)
    customerReceivable.value = 0
  }
}

// 客户改变
const onCustomerChange = () => {
  const customer = customers.value.find(c => c.id === formData.value.customerId)
  if (customer) {
    formData.value.contactPerson = customer.contactPerson || ''
    formData.value.contactPhone = customer.phone || ''
    formData.value.contactAddress = customer.address || ''
  }

  // 加载客户欠款
  loadCustomerDebt(formData.value.customerId)
}

// 显示商品下拉框
const showProductDropdown = (index) => {
  // 如果没有选择门店和仓库，直接返回，不显示下拉框
  if (!formData.value.storeId || !formData.value.warehouseId) {
    return
  }

  focusedRow.value = index
  formData.value.items[index].showDropdown = true

  // 获取相同名称的商品，按规格型号分组
  const currentName = formData.value.items[index].goodsName
  if (currentName) {
    const sameNameProducts = filteredProducts.value.filter(p =>
      p.name.toLowerCase().includes(currentName.toLowerCase())
    )
    formData.value.items[index].filteredProducts = sameNameProducts
  } else {
    formData.value.items[index].filteredProducts = filteredProducts.value
  }
}

// 隐藏商品下拉框
const hideProductDropdown = (index) => {
  setTimeout(() => {
    formData.value.items[index].showDropdown = false
  }, 200)
}

// 过滤商品
const filterProducts = (index) => {
  const searchText = formData.value.items[index].goodsName.toLowerCase()
  if (searchText) {
    formData.value.items[index].filteredProducts = filteredProducts.value.filter(p =>
      p.name.toLowerCase().includes(searchText)
    )
  } else {
    formData.value.items[index].filteredProducts = filteredProducts.value
  }
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
  calculateRowAmount(index)
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

  calculateRowAmount(index)
}

// 数量改变时自动换算件数
const onQuantityChange = (index) => {
  const item = formData.value.items[index]

  // 如果有换算比例，自动计算件数
  if (item.conversionRate && item.quantity) {
    item.packages = item.quantity / item.conversionRate
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
    formData.value.items.splice(index, 1)
  }
}

// 计算合计
const totalPackagesCalculated = computed(() => {
  return formData.value.items.reduce((sum, item) => sum + (item.packages || 0), 0)
})

const totalPackages = computed(() => {
  // 如果有手动修改的值，使用手动值
  if (manualTotalPackages.value !== null) {
    return manualTotalPackages.value
  }
  // 否则返回计算值
  return totalPackagesCalculated.value
})

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

// 合计件数获得焦点
const onTotalPackagesFocus = () => {
  // 聚焦时如果没有手动值，设置当前计算值
  if (manualTotalPackages.value === null) {
    manualTotalPackages.value = totalPackagesCalculated.value
  }
}

// 手动输入合计件数
const onManualTotalPackagesInput = (event) => {
  const value = event.target.value
  manualTotalPackages.value = value === '' ? null : Number(value)
}

// 监听商品明细变化，如果没有手动修改过，自动更新
watch(() => formData.value.items.map(item => item.packages), () => {
  // 如果没有手动修改过（或手动值为null），则自动跟随计算
  if (manualTotalPackages.value === null) {
    // 不需要做任何事，计算属性会自动更新
  } else {
    // 如果有手动修改，当表格数据变化时重新计算
    manualTotalPackages.value = totalPackagesCalculated.value
  }
}, { deep: true })

watch(showTaxColumns, (taxEnabled) => {
  normalizeTaxRows(taxEnabled)
})

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
  // 1. 检查门店
  if (!formData.value.storeId) {
    showErrorModal('请选择门店')
    return false
  }

  // 2. 检查客户
  if (!formData.value.customerId) {
    showErrorModal('请选择客户')
    return false
  }

  // 3. 检查仓库
  if (!formData.value.warehouseId) {
    showErrorModal('请选择仓库')
    return false
  }

  // 4. 检查联系人信息
  if (!formData.value.contactPerson) {
    showErrorModal('请填写联系人')
    return false
  }

  if (!formData.value.contactPhone) {
    showErrorModal('请填写联系方式')
    return false
  }

  // 5. 检查商品明细（商品ID和数量必填，件数、单价可以为空）
  const validItems = formData.value.items.filter(item =>
    item.productId && item.quantity && item.quantity > 0
  )

  if (validItems.length === 0) {
    showErrorModal('请至少添加一条商品明细，并填写数量')
    return false
  }

  // 检查是否有填了商品但没填数量的行
  const hasInvalidItems = formData.value.items.some(item =>
    item.productId && (!item.quantity || item.quantity <= 0)
  )

  if (hasInvalidItems) {
    showErrorModal('已选择商品的行必须填写数量')
    return false
  }

  return true
}

// 保存订单
const saving = ref(false)

const handleSave = async (printAfterSave = false) => {
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
      creator: formData.value.creator,
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

    // 添加手动修改的合计件数
    const finalTotalPackages = manualTotalPackages.value !== null
      ? manualTotalPackages.value
      : validItems.reduce((sum, item) => sum + (Number(item.packages) || 0), 0)
    requestData.totalPackages = finalTotalPackages

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
      // 新增模式：用后端返回的真实订单编号更新
      if (!isEditMode.value && response.orderNumber) {
        formData.value.orderNumber = response.orderNumber
      }

      showSuccessModal(isEditMode.value
        ? `订单修改成功！\n订单编号：${formData.value.orderNumber}`
        : `订单保存成功！\n订单编号：${formData.value.orderNumber}`
      )

      if (printAfterSave) {
        // TODO: 打印逻辑
        console.log('执行打印操作...')
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
  handleSave(true)
}

// 最终保存
const handleSaveFinal = () => {
  handleSave(false)
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

const confirmClear = () => {
  showClearConfirmModal.value = false

  // 重置基础信息
  formData.value.storeId = ''
  formData.value.customerId = ''
  formData.value.warehouseId = ''
  formData.value.orderDate = new Date().toISOString().split('T')[0]
  formData.value.contactPerson = ''
  formData.value.contactPhone = ''
  formData.value.contactAddress = ''
  formData.value.projectName = ''
  formData.value.packaging = '无'
  formData.value.logisticsService = logisticsServiceOptions[0]
  formData.value.salesPerson = '柯晓'
  formData.value.creator = '下单员'
  formData.value.orderRemark = ''
  formData.value.taxRate = 0
  formData.value.discountAmount = null
  formData.value.otherFees = null
  formData.value.currentPayment = 0

  // 清空商品列表
  initEmptyRows()
  showTaxColumns.value = false

  // 重置手动合计
  manualTotalPackages.value = null
}

watch(
  [formData, showTaxColumns, manualTotalPackages],
  () => {
    scheduleDraftSave()
  },
  { deep: true }
)

// 初始化
onMounted(async () => {
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
    loadUnits()
  ])

  let savedDraft = orderDraftStore.draft
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
      }

      // 从订单列表中获取最大ID+1，生成正式订单编号
      await generateNewOrderNumber()
    }
  }

  draftReady.value = true
  persistDraft()
})

onBeforeUnmount(() => {
  clearTimeout(draftSaveTimer)
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
    // 出错时使用临时编号
    formData.value.orderNumber = generateOrderNumber('TEMP')
  }
}

</script>

<style scoped>
.order-form-page {
  --accent: #0f9f78;
  --accent-rgb: 15, 159, 120;
  --accent-dark: #08745a;
  --accent-soft: #e9f8f3;
  --accent-border: #a9e5d2;
  --page-bg: #f4f7f8;
  --panel-bg: #ffffff;
  --border: #e2e8f0;
  --border-strong: #cbd5e1;
  --text: #172033;
  --text-secondary: #596579;
  --text-muted: #8a96a8;

  padding: 0;
  background: var(--page-bg);
  min-height: 100vh;
  color: var(--text);
  font-size: 14px;
}

/* 顶部信息栏 */
.top-info-bar {
  background: var(--panel-bg);
  padding: 14px 20px;
  display: flex;
  align-items: center;
  gap: 18px;
  border-bottom: 1px solid var(--border);
  flex-wrap: wrap;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.info-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-group label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  white-space: nowrap;
}

.info-group select,
.info-group input[type="text"],
.info-group input[type="date"],
.info-group input[type="tel"] {
  height: 38px;
  padding: 0 11px;
  border: 1px solid var(--border-strong);
  border-radius: 5px;
  font-size: 14px;
  color: var(--text);
  background: var(--panel-bg);
  outline: none;
  min-width: 150px;
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}

.info-group select:focus,
.info-group input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(var(--accent-rgb), 0.1);
}

.info-group.wide input {
  min-width: 300px;
}

.info-group.right-actions {
  margin-left: auto;
  gap: 10px;
  display: flex;
  align-items: center;
}

.tax-switch-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.switch-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  white-space: nowrap;
}

.switch {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--border-strong);
  transition: 0.2s ease;
  border-radius: 999px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: var(--panel-bg);
  transition: 0.2s ease;
  border-radius: 50%;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
}

input:checked + .slider {
  background-color: var(--accent);
}

input:checked + .slider:before {
  transform: translateX(20px);
}

.btn-clear {
  height: 36px;
  padding: 0 14px;
  background: #fef2f2;
  color: #dc2626;
  border: 1px solid #fecaca;
  border-radius: 5px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.18s ease;
}

.btn-clear:hover {
  background: #fee2e2;
  border-color: #fca5a5;
}

.btn-clear:focus-visible {
  outline: 2px solid #dc2626;
  outline-offset: 2px;
}

.btn-close {
  height: 36px;
  padding: 0 14px;
  background: var(--panel-bg);
  color: var(--text-secondary);
  border: 1px solid var(--border-strong);
  border-radius: 5px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.18s ease;
}

.btn-close:hover {
  background: var(--accent-soft);
  border-color: var(--accent-border);
  color: var(--accent-dark);
}

.btn-close:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

/* 联系人信息栏 */
.contact-info-bar {
  background: var(--panel-bg);
  padding: 12px 20px;
  display: flex;
  align-items: center;
  gap: 18px;
  border-bottom: 1px solid var(--border);
}

/* 商品表格 */
.products-table-wrapper {
  background: var(--panel-bg);
  overflow-x: auto;
  flex: 1;
}

.products-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  table-layout: fixed;
  min-width: 1320px;
}

.products-table thead {
  background: #f8fafc;
  position: sticky;
  top: 0;
  z-index: 10;
}

.products-table th {
  padding: 9px 12px;
  text-align: left;
  font-size: 12px;
  font-weight: 650;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border);
  white-space: nowrap;
}

.products-table td {
  padding: 4px;
  border-bottom: 1px solid #edf1f5;
  background: var(--panel-bg);
}

.products-table tbody tr:last-child td {
  border-bottom: none;
}

.products-table td.center {
  text-align: center;
}

.products-table td.right {
  text-align: right;
}

.products-table tr.row-focused {
  background: rgba(var(--accent-rgb), 0.05);
}

.products-table input,
.products-table select {
  width: 100%;
  height: 28px;
  padding: 0 8px;
  border: 1px solid transparent;
  background: transparent;
  font-size: 13px;
  color: var(--text);
  outline: none;
  transition: border-color 0.18s ease, background 0.18s ease;
  font-variant-numeric: tabular-nums;
}

.products-table input:focus,
.products-table select:focus {
  border-color: var(--accent);
  background: var(--panel-bg);
  box-shadow: 0 0 0 2px rgba(var(--accent-rgb), 0.1);
}

.products-table input[readonly] {
  background: #f8fafc;
  color: var(--text-muted);
  cursor: not-allowed;
}

/* 商品下拉框样式 */
.product-col {
  position: relative;
}

.product-select-wrapper {
  position: relative;
  width: 100%;
}

.product-input {
  width: 100%;
  height: 28px;
  padding: 0 8px;
  border: 1px solid transparent;
  background: transparent;
  font-size: 13px;
  outline: none;
}

.product-input:focus {
  border-color: var(--accent);
  background: var(--panel-bg);
}

.product-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  min-width: 600px;
  max-height: 300px;
  overflow-y: auto;
  background: var(--panel-bg);
  border: 1px solid var(--border-strong);
  border-radius: 5px;
  box-shadow: 0 4px 8px rgba(15, 23, 42, 0.12);
  z-index: 1000;
  margin-top: 4px;
}

.product-dropdown-header {
  display: flex;
  padding: 10px 12px;
  background: #f8fafc;
  font-size: 11px;
  font-weight: 650;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 1;
}

.product-dropdown-header .col-code {
  width: 100px;
  flex-shrink: 0;
}

.product-dropdown-header .col-name {
  width: 180px;
  flex-shrink: 0;
}

.product-dropdown-header .col-spec {
  width: 150px;
  flex-shrink: 0;
}

.product-dropdown-header .col-unit {
  width: 80px;
  flex-shrink: 0;
}

.product-dropdown-header .col-stock {
  width: 90px;
  flex-shrink: 0;
  text-align: right;
}

.product-option {
  display: flex;
  padding: 10px 12px;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.18s ease;
  border-bottom: 1px solid #f8fafc;
}

.product-option:last-child {
  border-bottom: none;
}

.product-option .col-code {
  width: 100px;
  flex-shrink: 0;
  color: var(--text-muted);
}

.product-option .col-name {
  width: 180px;
  flex-shrink: 0;
  font-weight: 600;
  color: var(--text);
}

.product-option .col-spec {
  width: 150px;
  flex-shrink: 0;
  color: var(--text-secondary);
}

.product-option .col-unit {
  width: 80px;
  flex-shrink: 0;
  color: var(--text-secondary);
}

.product-option .col-stock {
  width: 90px;
  flex-shrink: 0;
  text-align: right;
  color: var(--accent-dark);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.product-option:hover {
  background: rgba(var(--accent-rgb), 0.08);
}

.readonly-input {
  background: #f8fafc !important;
  color: var(--text-muted) !important;
  cursor: not-allowed;
}

.btn-icon {
  width: 24px;
  height: 24px;
  padding: 0;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 16px;
  font-weight: 700;
  transition: transform 0.18s ease, color 0.18s ease;
  border-radius: 3px;
}

.btn-icon:hover {
  transform: scale(1.15);
}

.btn-icon.btn-add {
  color: var(--accent);
}

.btn-icon.btn-add:hover {
  background: var(--accent-soft);
}

.btn-icon.btn-remove {
  color: #ef4444;
}

.btn-icon.btn-remove:hover {
  background: #fef2f2;
}

.total-row {
  background: #fef3c7;
  font-weight: 650;
}

.total-row td {
  padding: 10px 12px;
  border-top: 2px solid #f59e0b;
  border-bottom: 2px solid #f59e0b;
}

.editable-total {
  width: 100%;
  height: 28px;
  padding: 0 8px;
  border: 1px solid transparent;
  background: transparent;
  font-size: 13px;
  font-weight: 650;
  outline: none;
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.editable-total:focus {
  border-color: var(--accent);
  background: var(--panel-bg);
}

.btn-text-link {
  background: none;
  border: none;
  color: var(--accent-dark);
  cursor: pointer;
  font-size: 13px;
  font-weight: 650;
  text-decoration: none;
  transition: color 0.18s ease;
}

.btn-text-link:hover {
  color: var(--accent);
  text-decoration: underline;
}

/* 底部信息栏 */
.bottom-info-bar {
  background: var(--panel-bg);
  padding: 14px 20px;
  border-top: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 12px;
  box-shadow: 0 -1px 2px rgba(15, 23, 42, 0.04);
}

.finance-row-full {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: nowrap;
}

.finance-row {
  display: flex;
  align-items: center;
  gap: 14px;
}

.action-row {
  display: flex;
  align-items: center;
  gap: 12px;
  justify-content: flex-end;
}

.finance-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.finance-item label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  white-space: nowrap;
}

.finance-item input,
.finance-item select {
  height: 38px;
  padding: 0 11px;
  border: 1px solid var(--border-strong);
  border-radius: 5px;
  font-size: 14px;
  color: var(--text);
  background: var(--panel-bg);
  outline: none;
  width: 120px;
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
  font-variant-numeric: tabular-nums;
}

.finance-item input:focus,
.finance-item select:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(var(--accent-rgb), 0.1);
}

.finance-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
}

.finance-value {
  font-size: 15px;
  font-weight: 650;
  color: var(--text);
  min-width: 80px;
  font-variant-numeric: tabular-nums;
}

.finance-value.highlight {
  color: var(--accent-dark);
  font-size: 15px;
}

.finance-value.red {
  color: #ef4444;
  font-size: 15px;
}

.finance-label.red {
  color: #ef4444;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: var(--accent);
}

.btn-save-and-print,
.btn-save-final {
  height: 38px;
  padding: 0 20px;
  background: var(--accent);
  color: #ffffff;
  border: 1px solid var(--accent);
  border-radius: 5px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.18s ease;
  white-space: nowrap;
}

.btn-save-and-print:hover,
.btn-save-final:hover {
  background: var(--accent-dark);
  border-color: var(--accent-dark);
  box-shadow: 0 2px 4px rgba(var(--accent-rgb), 0.2);
}

.btn-save-and-print:focus-visible,
.btn-save-final:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.btn-save-and-print:disabled,
.btn-save-final:disabled {
  background: var(--border-strong);
  border-color: var(--border-strong);
  color: var(--text-muted);
  cursor: not-allowed;
  opacity: 0.6;
}

.btn-save-final {
  background: var(--accent-dark);
  border-color: var(--accent-dark);
}

.btn-save-final:hover {
  background: #06634a;
  border-color: #06634a;
}

/* 隐藏数字输入框的上下箭头 */
input[type="number"]::-webkit-outer-spin-button,
input[type="number"]::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

input[type="number"] {
  -moz-appearance: textfield;
}

/* 自定义弹窗样式 */
.custom-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(15, 23, 42, 0.42);
  backdrop-filter: blur(1px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 99999;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.custom-modal {
  background: var(--panel-bg);
  border-radius: 7px;
  border: 1px solid var(--border);
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.15);
  width: 400px;
  max-width: 90%;
  animation: slideUp 0.25s ease;
}

@keyframes slideUp {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.modal-header {
  padding: 24px 24px 16px;
  text-align: center;
  border-bottom: 1px solid var(--border);
}

.modal-icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  font-weight: 700;
  margin: 0 auto 12px;
}

.modal-icon.success {
  background: var(--accent);
  color: #ffffff;
}

.modal-icon.error {
  background: #ef4444;
  color: #ffffff;
}

.modal-icon.warning {
  background: #f59e0b;
  color: #ffffff;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 650;
  color: var(--text);
}

.modal-body {
  padding: 24px;
  text-align: center;
}

.modal-body p {
  margin: 0;
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;
  white-space: pre-line;
}

.modal-footer {
  padding: 16px 24px 24px;
  text-align: center;
  display: flex;
  gap: 12px;
  justify-content: center;
}

.btn-modal-cancel {
  height: 38px;
  background: var(--panel-bg);
  color: var(--text-secondary);
  border: 1px solid var(--border-strong);
  padding: 0 32px;
  border-radius: 5px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.18s ease;
  min-width: 120px;
}

.btn-modal-cancel:hover {
  background: var(--accent-soft);
  border-color: var(--accent-border);
  color: var(--accent-dark);
}

.btn-modal-cancel:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.btn-modal-confirm {
  height: 38px;
  background: var(--accent);
  color: #ffffff;
  border: 1px solid var(--accent);
  padding: 0 32px;
  border-radius: 5px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.18s ease;
  min-width: 120px;
}

.btn-modal-confirm:hover {
  background: var(--accent-dark);
  border-color: var(--accent-dark);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(var(--accent-rgb), 0.25);
}

.btn-modal-confirm:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.btn-modal-confirm:active {
  transform: translateY(0);
}

.btn-modal-confirm.danger {
  background: #ef4444;
  border-color: #ef4444;
}

.btn-modal-confirm.danger:hover {
  background: #dc2626;
  border-color: #dc2626;
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.25);
}

.btn-modal-confirm.danger:focus-visible {
  outline: 2px solid #ef4444;
  outline-offset: 2px;
}

/* 响应式 */
@media (max-width: 1280px) {
  .top-info-bar,
  .contact-info-bar,
  .finance-row-full {
    gap: 12px;
  }
}

@media (max-width: 780px) {
  .top-info-bar,
  .contact-info-bar {
    flex-direction: column;
    align-items: stretch;
  }

  .info-group {
    width: 100%;
  }

  .info-group select,
  .info-group input {
    width: 100%;
    min-width: 100%;
  }

  .custom-modal {
    width: 100vw;
    height: 100vh;
    max-height: 100vh;
    border-radius: 0;
  }
}
</style>
