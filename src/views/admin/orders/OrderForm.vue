<template>
  <div class="order-form-page">
    <!-- 顶部信息区 -->
    <div class="top-info-bar">
      <div class="info-group">
        <label>🏪 门店</label>
        <select v-model="formData.storeId" @change="onStoreChange">
          <option value="">请选择门店</option>
          <option v-for="store in stores" :key="store.id" :value="store.id">
            {{ store.name }}
          </option>
        </select>
      </div>

      <div class="info-group">
        <label>👤 客户</label>
        <select v-model="formData.customerId" @change="onCustomerChange">
          <option value="">请选择客户</option>
          <option v-for="customer in filteredCustomers" :key="customer.id" :value="customer.id">
            {{ customer.customerName }}
          </option>
        </select>
      </div>

      <div class="info-group">
        <label>📦 仓库</label>
        <select v-model="formData.warehouseId">
          <option value="">请选择仓库</option>
          <option v-for="warehouse in filteredWarehouses" :key="warehouse.id" :value="warehouse.id">
            {{ warehouse.name }}
          </option>
        </select>
      </div>

      <div class="info-group">
        <label>📅 单据日期</label>
        <input type="date" v-model="formData.orderDate" />
      </div>

      <div class="info-group">
        <label>🔖 单据编号</label>
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
        <input type="text" v-model="formData.contactPerson" readonly />
      </div>

      <div class="info-group">
        <label>联系方式:</label>
        <input type="tel" v-model="formData.contactPhone" readonly />
      </div>

      <div class="info-group wide">
        <label>联系地址:</label>
        <input type="text" v-model="formData.contactAddress" placeholder="请输入联系地址" />
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
            <th style="width: 100px">合税单价</th>
            <th style="width: 120px">金额 (元)</th>
            <th style="width: 120px">价税合计</th>
            <th style="width: 180px">备注信息</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(item, index) in formData.items" :key="index" :class="{ 'row-focused': focusedRow === index }">
            <td class="center">{{ index + 1 }}</td>
            <td class="center">
              <button class="btn-icon btn-add" @click="addRow(index)" title="在下方插入一行">➕</button>
              <button class="btn-icon btn-remove" @click="removeRow(index)" title="删除此行">❌</button>
            </td>
            <td class="product-col">
              <div class="product-select-wrapper">
                <input
                  type="text"
                  v-model="item.productName"
                  @focus="showProductDropdown(index)"
                  @blur="hideProductDropdown(index)"
                  @input="filterProducts(index)"
                  placeholder="请选择商品"
                  class="product-input"
                />
                <div
                  v-if="item.showDropdown && item.filteredProducts && item.filteredProducts.length > 0"
                  class="product-dropdown"
                  @mousedown.prevent
                >
                  <div
                    v-for="product in item.filteredProducts"
                    :key="product.id"
                    class="product-option"
                    @click="selectProduct(index, product)"
                  >
                    {{ product.name }}
                  </div>
                </div>
              </div>
            </td>
            <td><input type="text" v-model="item.spec" readonly class="readonly-input" /></td>
            <td><input type="text" v-model="item.unit" readonly class="readonly-input" /></td>
            <td><input type="text" v-model="item.warehouseName" readonly class="readonly-input" /></td>
            <td class="right"><input type="text" :value="item.currentStock" readonly class="readonly-input" /></td>
            <td><input type="number" v-model.number="item.packages" min="0" /></td>
            <td><input type="number" v-model.number="item.quantity" @input="calculateRowAmount(index)" min="0" step="0.01" /></td>
            <td><input type="number" v-model.number="item.price" @input="calculateRowAmount(index)" min="0" step="0.01" /></td>
            <td><input type="number" v-model.number="item.taxIncludedPrice" min="0" step="0.01" /></td>
            <td class="right"><input type="text" :value="item.amount.toFixed(2)" readonly class="readonly-input" /></td>
            <td class="right"><input type="text" :value="item.totalAmount.toFixed(2)" readonly class="readonly-input" /></td>
            <td><input type="text" v-model="item.remark" placeholder="备注" /></td>
          </tr>

          <!-- 合计行 -->
          <tr class="total-row">
            <td colspan="2" class="center"><button class="btn-text-link">合计</button></td>
            <td colspan="5"></td>
            <td class="right">{{ totalPackages }}</td>
            <td class="right">{{ totalQuantity.toFixed(2) }}</td>
            <td colspan="2"></td>
            <td class="right">{{ totalAmount.toFixed(2) }}</td>
            <td class="right">{{ totalTaxAmount.toFixed(2) }}</td>
            <td></td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 底部信息区 -->
    <div class="bottom-info-bar">
      <div class="left-section">
        <div class="info-group">
          <label>业务员</label>
          <select v-model="formData.salesPerson">
            <option value="">威小全💰</option>
          </select>
        </div>

        <div class="info-group">
          <label>制单人</label>
          <select v-model="formData.creator">
            <option value="">总经理🔒</option>
          </select>
        </div>

        <div class="info-group wide">
          <label>备注信息</label>
          <input type="text" v-model="formData.orderRemark" placeholder="请输入备注信息" />
        </div>
      </div>

      <div class="right-section">
        <div class="finance-row">
          <div class="finance-item">
            <label>折扣率(%)</label>
            <input type="number" v-model.number="formData.discountRate" @input="calculateDiscount" min="0" max="100" />
          </div>
          <div class="finance-item">
            <label>折后金额</label>
            <input type="text" :value="discountedAmount.toFixed(2)" readonly />
          </div>
          <div class="finance-item">
            <label>折后金额</label>
            <input type="text" value="折后金额" readonly />
          </div>
          <div class="finance-item">
            <label>其他费用</label>
            <input type="number" v-model.number="formData.otherFees" @input="calculateFinal" min="0" />
          </div>
          <div class="finance-item">
            <label>结算账户</label>
            <select v-model="formData.settlementAccount">
              <option value="">现金账户</option>
            </select>
          </div>
        </div>

        <div class="finance-row">
          <div class="finance-item">
            <span class="finance-label">积分:</span>
            <span class="finance-value">{{ formData.points || 0 }}</span>
          </div>
          <div class="finance-item">
            <span class="finance-label">客户欠款:</span>
            <span class="finance-value">{{ customerDebt.toFixed(2) }}</span>
          </div>
          <div class="finance-item">
            <span class="finance-label">本单应收:</span>
            <span class="finance-value">{{ shouldReceive.toFixed(2) }}</span>
          </div>
          <div class="finance-item">
            <span class="finance-label highlight">本次收款:</span>
            <span class="finance-value highlight">{{ finalAmount.toFixed(2) }}</span>
          </div>
          <div class="finance-item">
            <span class="finance-label red">本单欠款:</span>
            <span class="finance-value red">{{ currentDebt.toFixed(2) }}</span>
          </div>
          <div class="finance-item">
            <span class="finance-label">未收金额:</span>
            <span class="finance-value">{{ unpaidAmount || 0 }}</span>
          </div>
          <div class="finance-item">
            <span class="finance-label">未收:</span>
            <span class="finance-value">{{ unpaidAmount || 0 }}</span>
          </div>
        </div>

        <div class="action-row">
          <label class="checkbox-label">
            <input type="checkbox" v-model="formData.printAfterSave" />
            保存后打印
          </label>
          <button class="btn-save-and-print" @click="handleSaveAndPrint">💾 保存并打印</button>
          <button class="btn-save-final" @click="handleSaveFinal">保存(ctrl+Q)</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import request from '@/api/request'

const router = useRouter()

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
  salesPerson: '',
  creator: '',
  orderRemark: '',
  discountRate: 100,
  otherFees: 0,
  settlementAccount: '',
  points: 0,
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

// 焦点行
const focusedRow = ref(-1)

// 生成订单编号
function generateOrderNumber(orderId) {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  const id = orderId || 'NEW'
  return `ZG${year}${month}${day}${id}`
}

// 初始化空白行
function initEmptyRows() {
  formData.value.items = Array.from({ length: 8 }, () => ({
    productId: '',
    productName: '',
    spec: '',
    unit: '',
    warehouseId: '',
    warehouseName: '',
    currentStock: 0,
    packages: 0,
    quantity: 0,
    price: 0,
    taxIncludedPrice: 0,
    amount: 0,
    totalAmount: 0,
    remark: '',
    showDropdown: false,
    filteredProducts: []
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

// 加载商品
const loadProducts = async () => {
  try {
    const response = await request({ url: '/products', method: 'GET' })
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

// 门店改变
const onStoreChange = () => {
  // 重置客户和仓库选择
  formData.value.customerId = ''
  formData.value.warehouseId = ''
  formData.value.contactPerson = ''
  formData.value.contactPhone = ''
  formData.value.contactAddress = ''
}

// 客户改变
const onCustomerChange = () => {
  const customer = customers.value.find(c => c.id === formData.value.customerId)
  if (customer) {
    formData.value.contactPerson = customer.contactPerson || ''
    formData.value.contactPhone = customer.phone || ''
    formData.value.contactAddress = customer.address || ''
  }
}

// 显示商品下拉框
const showProductDropdown = (index) => {
  focusedRow.value = index
  formData.value.items[index].showDropdown = true
  formData.value.items[index].filteredProducts = products.value
}

// 隐藏商品下拉框
const hideProductDropdown = (index) => {
  setTimeout(() => {
    formData.value.items[index].showDropdown = false
  }, 200)
}

// 过滤商品
const filterProducts = (index) => {
  const searchText = formData.value.items[index].productName.toLowerCase()
  if (searchText) {
    formData.value.items[index].filteredProducts = products.value.filter(p =>
      p.name.toLowerCase().includes(searchText)
    )
  } else {
    formData.value.items[index].filteredProducts = products.value
  }
}

// 选择商品
const selectProduct = (index, product) => {
  const item = formData.value.items[index]
  item.productId = product.id
  item.productName = product.name
  item.spec = product.specification || ''

  // 根据 unitId 查找单位名称
  if (product.unitId) {
    const unit = units.value.find(u => u.id === product.unitId)
    item.unit = unit ? unit.name : ''
  } else {
    item.unit = ''
  }

  item.price = product.price || 0
  item.taxIncludedPrice = product.price || 0

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
    productName: '',
    spec: '',
    unit: '',
    warehouseId: '',
    warehouseName: '',
    currentStock: 0,
    packages: 0,
    quantity: 0,
    price: 0,
    taxIncludedPrice: 0,
    amount: 0,
    totalAmount: 0,
    remark: '',
    showDropdown: false,
    filteredProducts: []
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

// 折扣后金额
const discountedAmount = computed(() => {
  return totalAmount.value * (formData.value.discountRate / 100)
})

// 应收金额
const shouldReceive = computed(() => {
  return discountedAmount.value + (formData.value.otherFees || 0)
})

// 本次收款
const finalAmount = computed(() => {
  return shouldReceive.value
})

// 客户欠款
const customerDebt = ref(0)

// 本单欠款
const currentDebt = computed(() => {
  return 0
})

// 未收金额
const unpaidAmount = ref(0)

// 计算折扣
const calculateDiscount = () => {
  // 触发计算
}

// 计算最终金额
const calculateFinal = () => {
  // 触发计算
}

// 保存
const handleSave = () => {
  console.log('保存订单:', formData.value)
}

// 保存并打印
const handleSaveAndPrint = () => {
  console.log('保存并打印')
  handleSave()
}

// 最终保存
const handleSaveFinal = () => {
  handleSave()
}

// 关闭
const handleClose = () => {
  if (confirm('确定要关闭吗？未保存的数据将丢失')) {
    router.back()
  }
}

// 初始化
onMounted(() => {
  loadStores()
  loadCustomers()
  loadWarehouses()
  loadProducts()
  loadUnits() // 加载单位数据
  initEmptyRows()
  // 生成默认订单编号（临时）
  formData.value.orderNumber = generateOrderNumber('NEW')
})
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
  right: 0;
  max-height: 200px;
  overflow-y: auto;
  background: white;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  margin-top: 2px;
}

.product-option {
  padding: 8px 12px;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.15s;
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
  display: flex;
  justify-content: space-between;
  border-top: 1px solid #e5e7eb;
  gap: 20px;
}

.left-section {
  display: flex;
  align-items: center;
  gap: 16px;
}

.right-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 700px;
}

.finance-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.finance-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.finance-item label {
  font-size: 13px;
  color: #6b7280;
  white-space: nowrap;
}

.finance-item input,
.finance-item select {
  height: 28px;
  padding: 0 8px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 13px;
  outline: none;
  width: 100px;
}

.finance-label {
  font-size: 13px;
  color: #6b7280;
}

.finance-value {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
}

.finance-value.highlight {
  color: #10b981;
  font-size: 14px;
}

.finance-value.red {
  color: #ef4444;
  font-size: 14px;
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

.btn-save-final {
  background: #3b82f6;
}

.btn-save-final:hover {
  background: #2563eb;
}
</style>
