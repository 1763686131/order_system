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
        <button class="btn-close" @click="handleClose">关闭 ››</button>
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
            <th style="width: 80px">税率(%)</th>
            <th style="width: 100px">合税单价</th>
            <th style="width: 120px">金额 (元)</th>
            <th style="width: 120px">含税金额</th>
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
            <td><input type="number" v-model.number="item.taxRate" @input="onItemTaxRateChange(index)" min="0" max="100" step="0.01" /></td>
            <td><input type="number" v-model.number="item.taxIncludedPrice" @input="onTaxIncludedPriceChange(index)" min="0" step="0.01" /></td>
            <td class="right"><input type="text" :value="item.amount ? item.amount.toFixed(2) : ''" readonly class="readonly-input" /></td>
            <td class="right"><input type="text" :value="item.totalAmount ? item.totalAmount.toFixed(2) : ''" readonly class="readonly-input" /></td>
            <td><input type="text" v-model="item.remark" /></td>
          </tr>

          <!-- 合计行 -->
          <tr class="total-row">
            <td colspan="2" class="center"><button class="btn-text-link">合计</button></td>
            <td colspan="5"></td>
            <td class="right">{{ totalPackages || '' }}</td>
            <td class="right">{{ totalQuantity ? totalQuantity.toFixed(2) : '' }}</td>
            <td colspan="3"></td>
            <td class="right">{{ totalAmount ? totalAmount.toFixed(2) : '' }}</td>
            <td class="right">{{ totalTaxAmount ? totalTaxAmount.toFixed(2) : '' }}</td>
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

    <!-- 自定义确认弹窗 -->
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
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import request from '@/api/request'

const router = useRouter()

// Props 定义
const props = defineProps({
  orderId: {
    type: Number,
    default: null
  }
})

// 判断是否为编辑模式
const isEditMode = computed(() => props.orderId !== null)

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
    router.back()
  }
}

// 基础数据
const stores = ref([])
const customers = ref([])
const warehouses = ref([])
const products = ref([])
const units = ref([]) // 新增单位数据

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
  salesPerson: '柯晓',
  creator: '下单员',
  orderRemark: '',
  taxRate: 13,
  discountAmount: null,
  otherFees: null,
  settlementAccount: '',
  currentPayment: 0,
  printAfterSave: false,
  items: []
})

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
    const response = await request({ url: '/products/units', method: 'GET' })
    if (response && Array.isArray(response)) {
      units.value = response
    }
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
      formData.value.salesPerson = response.sales_person || ''
      formData.value.creator = response.creator || ''
      formData.value.orderRemark = response.remark || ''
      formData.value.taxRate = response.tax_rate || 13
      formData.value.discountAmount = response.discount_amount || null
      formData.value.otherFees = response.other_fees || null
      formData.value.settlementAccount = response.settlement_account || ''
      formData.value.currentPayment = response.current_payment || 0

      console.log('基础信息填充完成，formData:', formData.value)

      // 填充商品明细
      if (response.order_goods && response.order_goods.length > 0) {
        console.log('开始填充商品明细，order_goods:', response.order_goods)
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
          taxRate: item.tax_rate || 13,
          taxIncludedPrice: item.tax_included_price || null,
          amount: item.amount || null,
          totalAmount: item.total_amount || null,
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
            taxRate: 13,
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

        // 重新查询每个商品的当前库存
        for (let item of formData.value.items) {
          if (item.productId && item.warehouseId) {
            await updateStockInfo(item)
          }
        }
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

// 门店改变
const onStoreChange = () => {
  // 重置客户和仓库选择
  formData.value.customerId = ''
  formData.value.warehouseId = ''
  formData.value.contactPerson = ''
  formData.value.contactPhone = ''
  formData.value.contactAddress = ''
}

// 仓库改变
const onWarehouseChange = () => {
  // 仓库改变后，商品列表会通过 filteredProducts 自动筛选
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
  formData.value.items[index].filteredProducts = filteredProducts.value
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
  item.taxRate = 13
  item.taxIncludedPrice = product.price ? parseFloat((product.price * 1.13).toFixed(2)) : 0

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
  item.totalAmount = (item.quantity || 0) * (item.taxIncludedPrice || 0)
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
const totalPackages = computed(() => {
  return formData.value.items.reduce((sum, item) => sum + (item.packages || 0), 0)
})

const totalQuantity = computed(() => {
  return formData.value.items.reduce((sum, item) => sum + (item.quantity || 0), 0)
})

const totalAmount = computed(() => {
  return formData.value.items.reduce((sum, item) => sum + (item.amount || 0), 0)
})

const totalTaxAmount = computed(() => {
  return formData.value.items.reduce((sum, item) => sum + (item.totalAmount || 0), 0)
})

// 监听含税金额变化，自动更新折扣金额
watch(totalTaxAmount, (newTotal) => {
  // 自动将折扣金额设为含税金额总计
  formData.value.discountAmount = newTotal
}, { immediate: true })

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

  // 5. 检查商品明细（只要求商品ID必填，数量、件数、单价都可以为空或0）
  const validItems = formData.value.items.filter(item =>
    item.productId
  )

  if (validItems.length === 0) {
    showErrorModal('请至少添加一条有效的商品明细（至少填写商品）')
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
      salesPerson: formData.value.salesPerson,
      creator: formData.value.creator,
      orderRemark: formData.value.orderRemark,
      taxRate: formData.value.taxRate,
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
        taxRate: Number(item.taxRate) || 13,
        taxIncludedPrice: Number(item.taxIncludedPrice) || 0,
        amount: Number(item.amount) || 0,
        totalAmount: Number(item.totalAmount) || 0,
        remark: item.remark || ''
      }))
    }

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
const handleClose = () => {
  if (confirm('确定要关闭吗？未保存的数据将丢失')) {
    router.back()
  }
}

// 初始化
onMounted(() => {
  console.log('OrderForm mounted, props.orderId:', props.orderId)
  console.log('isEditMode:', isEditMode.value)

  loadStores()
  loadCustomers()
  loadWarehouses()
  loadProducts()
  loadUnits() // 加载单位数据

  if (isEditMode.value) {
    // 编辑模式：加载订单数据
    console.log('进入编辑模式，加载订单ID:', props.orderId)
    loadOrderData(props.orderId)
  } else {
    // 新增模式：初始化空行并生成订单编号
    console.log('进入新增模式')
    initEmptyRows()
    // 从订单列表中获取最大ID+1，生成正式订单编号
    generateNewOrderNumber()
  }
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
  padding: 0;
  background: #f5f7fa;
  min-height: 100vh;
}

/* 顶部信息栏 */
.top-info-bar {
  background: white;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  gap: 16px;
  border-bottom: 1px solid #e5e7eb;
  flex-wrap: wrap;
}

.info-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-group label {
  font-size: 14px;
  color: #374151;
  white-space: nowrap;
}

.info-group select,
.info-group input[type="text"],
.info-group input[type="date"],
.info-group input[type="tel"] {
  height: 32px;
  padding: 0 10px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 14px;
  outline: none;
  min-width: 150px;
}

.info-group select:focus,
.info-group input:focus {
  border-color: #10b981;
}

.info-group.wide input {
  min-width: 300px;
}

.info-group.right-actions {
  margin-left: auto;
  gap: 8px;
}

.btn-need-delivery {
  padding: 6px 14px;
  background: white;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-need-delivery:hover {
  background: #f9fafb;
}

.btn-save-primary {
  padding: 6px 16px;
  background: #10b981;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-save-primary:hover {
  background: #059669;
}

.btn-save-success {
  padding: 6px 12px;
  background: #10b981;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
}

.btn-close {
  padding: 6px 14px;
  background: white;
  color: #6b7280;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
}

.btn-close:hover {
  background: #f9fafb;
}

/* 联系人信息栏 */
.contact-info-bar {
  background: white;
  padding: 10px 16px;
  display: flex;
  align-items: center;
  gap: 16px;
  border-bottom: 1px solid #e5e7eb;
}

/* 商品表格 */
.products-table-wrapper {
  background: white;
  overflow-x: auto;
  flex: 1;
}

.products-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.products-table thead {
  background: #f9fafb;
  position: sticky;
  top: 0;
  z-index: 10;
}

.products-table th {
  padding: 10px 8px;
  text-align: left;
  font-weight: 600;
  color: #374151;
  border: 1px solid #e5e7eb;
  white-space: nowrap;
}

.products-table td {
  padding: 4px;
  border: 1px solid #e5e7eb;
  background: white;
}

.products-table td.center {
  text-align: center;
}

.products-table td.right {
  text-align: right;
}

.products-table tr.row-focused {
  background: #f0fdf4;
}

.products-table input,
.products-table select {
  width: 100%;
  height: 28px;
  padding: 0 6px;
  border: 1px solid transparent;
  background: transparent;
  font-size: 13px;
  outline: none;
}

.products-table input:focus,
.products-table select:focus {
  border-color: #10b981;
  background: white;
}

.products-table input[readonly] {
  background: #f9fafb;
  color: #6b7280;
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
  padding: 0 6px;
  border: 1px solid transparent;
  background: transparent;
  font-size: 13px;
  outline: none;
}

.product-input:focus {
  border-color: #10b981;
  background: white;
}

.product-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  min-width: 600px;
  max-height: 300px;
  overflow-y: auto;
  background: white;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  margin-top: 2px;
}

.product-dropdown-header {
  display: flex;
  padding: 8px 12px;
  background: #f3f4f6;
  font-size: 12px;
  font-weight: 600;
  color: #374151;
  border-bottom: 1px solid #e5e7eb;
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
  padding: 8px 12px;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.15s;
  border-bottom: 1px solid #f3f4f6;
}

.product-option:last-child {
  border-bottom: none;
}

.product-option .col-code {
  width: 100px;
  flex-shrink: 0;
  color: #6b7280;
}

.product-option .col-name {
  width: 180px;
  flex-shrink: 0;
  font-weight: 500;
  color: #111827;
}

.product-option .col-spec {
  width: 150px;
  flex-shrink: 0;
  color: #6b7280;
}

.product-option .col-unit {
  width: 80px;
  flex-shrink: 0;
  color: #6b7280;
}

.product-option .col-stock {
  width: 90px;
  flex-shrink: 0;
  text-align: right;
  color: #059669;
  font-weight: 500;
}

.product-option:hover {
  background: #f0fdf4;
}

.readonly-input {
  background: #f9fafb !important;
  color: #6b7280 !important;
  cursor: not-allowed;
}

.btn-icon {
  width: 24px;
  height: 24px;
  padding: 0;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 14px;
  transition: transform 0.2s;
}

.btn-icon:hover {
  transform: scale(1.2);
}

.btn-icon.btn-add {
  color: #10b981;
}

.btn-icon.btn-remove {
  color: #ef4444;
}

.total-row {
  background: #fef3c7;
  font-weight: 600;
}

.total-row td {
  padding: 8px;
}

.btn-text-link {
  background: none;
  border: none;
  color: #3b82f6;
  cursor: pointer;
  text-decoration: underline;
  font-size: 13px;
}

/* 底部信息栏 */
.bottom-info-bar {
  background: white;
  padding: 12px 16px;
  border-top: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.finance-row-full {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: nowrap;
}

.finance-row {
  display: flex;
  align-items: center;
  gap: 12px;
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
  gap: 6px;
}

.finance-item label {
  font-size: 15px;
  font-weight: 500;
  color: #374151;
  white-space: nowrap;
}

.finance-item input,
.finance-item select {
  height: 32px;
  padding: 0 10px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 15px;
  outline: none;
  width: 120px;
}

.finance-label {
  font-size: 15px;
  font-weight: 500;
  color: #374151;
}

.finance-value {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
  min-width: 80px;
}

.finance-value.highlight {
  color: #10b981;
  font-size: 16px;
}

.finance-value.red {
  color: #ef4444;
  font-size: 16px;
}

.action-row {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 8px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #6b7280;
  cursor: pointer;
}

.btn-save-and-print,
.btn-save-final {
  padding: 8px 20px;
  background: #10b981;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-save-and-print:hover,
.btn-save-final:hover {
  background: #059669;
}

.btn-save-and-print:disabled,
.btn-save-final:disabled {
  background: #9ca3af;
  cursor: not-allowed;
  opacity: 0.6;
}

.btn-save-final {
  background: #3b82f6;
}

.btn-save-final:hover {
  background: #2563eb;
}

.btn-save-final:disabled {
  background: #9ca3af;
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
  background: rgba(0, 0, 0, 0.6);
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
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  width: 400px;
  max-width: 90%;
  animation: slideUp 0.3s ease;
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
  border-bottom: 1px solid #e5e7eb;
}

.modal-icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  font-weight: bold;
  margin: 0 auto 12px;
}

.modal-icon.success {
  background: #10b981;
  color: white;
}

.modal-icon.error {
  background: #ef4444;
  color: white;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #111827;
}

.modal-body {
  padding: 24px;
  text-align: center;
}

.modal-body p {
  margin: 0;
  font-size: 14px;
  color: #6b7280;
  line-height: 1.6;
  white-space: pre-line;
}

.modal-footer {
  padding: 16px 24px 24px;
  text-align: center;
}

.btn-modal-confirm {
  background: #3b82f6;
  color: white;
  border: none;
  padding: 10px 32px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  min-width: 120px;
}

.btn-modal-confirm:hover {
  background: #2563eb;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.btn-modal-confirm:active {
  transform: translateY(0);
}
</style>
