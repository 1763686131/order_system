<template>
  <div class="return-order-form-page">
    <form class="return-form" @submit.prevent="save(false)">
      <div class="top-info-bar">
        <div class="info-group">
          <label>门店</label>
          <select v-model="form.storeId" required @change="onStoreChange">
            <option value="">请选择门店</option>
            <option v-for="store in stores" :key="store.id" :value="String(store.id)">
              {{ store.name }}
            </option>
          </select>
        </div>
        <div class="info-group">
          <label>客户</label>
          <select v-model="form.customerId" required>
            <option value="">请选择客户</option>
            <option v-for="customer in filteredCustomers" :key="customer.id" :value="String(customer.id)">
              {{ customer.customerName }}
            </option>
          </select>
        </div>
        <div class="info-group">
          <label>仓库</label>
          <select v-model="form.warehouseId" @change="onWarehouseChange">
            <option value="">请选择仓库</option>
            <option v-for="warehouse in filteredWarehouses" :key="warehouse.id" :value="String(warehouse.id)">
              {{ warehouse.name }}
            </option>
          </select>
        </div>
        <div class="info-group">
          <label>单据日期</label>
          <input v-model="form.returnDate" type="date" required />
        </div>
        <div class="info-group">
          <label>原订单编号</label>
          <input v-model.trim="form.originalOrderNumber" type="text" placeholder="请输入原订单编号" required />
        </div>
        <div class="info-group right-actions">
          <div class="tax-switch-group">
            <label class="switch-label">含税</label>
            <label class="switch">
              <input v-model="form.taxEnabled" type="checkbox" />
              <span class="slider"></span>
            </label>
          </div>
          <button class="btn-clear" type="button" @click="clearForm">清空</button>
          <button class="btn-close" type="button" @click="close">关闭 ››</button>
        </div>
      </div>

      <div class="return-hint-bar">
        <span>{{ productType === 'raw-material' ? '原材料退货单' : '销售退货单' }}</span>
        <small>选择门店后加载对应客户、仓库和商品；商品选择后自动带出规格、单位、多单位和库存。</small>
      </div>

      <div class="products-table-wrapper">
        <table class="products-table">
          <thead>
            <tr>
              <th style="width: 42px">☀</th>
              <th style="width: 66px">操作</th>
              <th style="width: 220px">*商品信息</th>
              <th style="width: 125px">规格型号</th>
              <th style="width: 85px">单位</th>
              <th style="width: 130px">所属仓库</th>
              <th style="width: 100px">当前库存</th>
              <th style="width: 80px">件数</th>
              <th style="width: 100px">*数量</th>
              <th style="width: 110px">*单价 (元)</th>
              <th v-if="form.taxEnabled" style="width: 82px">税率 (%)</th>
              <th v-if="form.taxEnabled" style="width: 110px">含税单价</th>
              <th style="width: 120px">金额 (元)</th>
              <th v-if="form.taxEnabled" style="width: 110px">税额</th>
              <th v-if="form.taxEnabled" style="width: 120px">含税金额</th>
              <th style="width: 180px">备注信息</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(item, index) in form.items"
              :key="item.key"
              :class="{ 'row-focused': focusedRow === index }"
            >
              <td class="center">{{ index + 1 }}</td>
              <td class="center">
                <button class="btn-icon btn-add" type="button" title="在下方插入一行" @click="addRow(index)">+</button>
                <button class="btn-icon btn-remove" type="button" title="删除此行" @click="removeRow(index)">×</button>
              </td>
              <td class="product-col">
                <div class="product-select-wrapper">
                  <input
                    v-model="item.goodsName"
                    class="product-input"
                    type="text"
                    @focus="showProductDropdown(index)"
                    @blur="hideProductDropdown(index)"
                    @input="filterProducts(index)"
                  />
                  <div
                    v-if="item.showDropdown && item.filteredProducts.length"
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
                    <button
                      v-for="product in item.filteredProducts"
                      :key="product.id"
                      class="product-option"
                      type="button"
                      @click="selectProduct(index, product)"
                    >
                      <span class="col-code">{{ product.code || '-' }}</span>
                      <span class="col-name">{{ product.name }}</span>
                      <span class="col-spec">{{ product.specification || '-' }}</span>
                      <span class="col-unit">{{ getUnitName(product.unitId) || '-' }}</span>
                      <span class="col-stock">{{ number(product.stock) }}</span>
                    </button>
                  </div>
                </div>
              </td>
              <td><input v-model="item.specification" type="text" readonly class="readonly-input" /></td>
              <td class="unit-cell">
                <input v-model="item.unit" type="text" readonly class="readonly-input" />
              </td>
              <td>
                <select v-if="item.productId" v-model="item.warehouseId" @change="onItemWarehouseChange(item)">
                  <option value="">请选择仓库</option>
                  <option v-for="warehouse in filteredWarehouses" :key="warehouse.id" :value="String(warehouse.id)">
                    {{ warehouse.name }}
                  </option>
                </select>
                <span v-else class="blank-cell" aria-hidden="true"></span>
              </td>
              <td class="right"><input :value="item.productId ? number(item.currentStock) : ''" type="text" readonly class="readonly-input" /></td>
              <td><input v-model.number="item.packages" type="number" min="0" step="0.01" @input="onPackagesChange(item)" /></td>
              <td><input v-model.number="item.quantity" type="number" min="0" step="0.01" @input="onQuantityChange(item)" /></td>
              <td><input v-model.number="item.price" type="number" min="0" step="0.01" @input="calculateRow(item)" /></td>
              <td v-if="form.taxEnabled">
                <input
                  :value="item.productId ? item.taxRate : ''"
                  type="number"
                  min="0"
                  max="100"
                  step="0.01"
                  @input="item.taxRate = $event.target.value === '' ? null : Number($event.target.value); calculateRow(item)"
                />
              </td>
              <td v-if="form.taxEnabled">
                <input
                  :value="item.productId ? item.taxIncludedPrice : ''"
                  type="number"
                  min="0"
                  step="0.01"
                  @input="item.taxIncludedPrice = $event.target.value === '' ? null : Number($event.target.value); calculateFromTaxIncluded(item)"
                />
              </td>
              <td class="right"><input :value="item.productId ? money(item.amount) : ''" type="text" readonly class="readonly-input" /></td>
              <td v-if="form.taxEnabled" class="right">{{ item.productId ? money(item.taxAmount) : '' }}</td>
              <td v-if="form.taxEnabled" class="right">{{ item.productId ? money(item.taxIncludedAmount) : '' }}</td>
              <td><input v-model="item.remark" type="text" /></td>
            </tr>
            <tr class="total-row">
              <td colspan="7" class="center"><button class="btn-text-link" type="button">合计</button></td>
              <td class="right">{{ number(totalPackages) }}</td>
              <td class="right">{{ number(totalQuantity) }}</td>
              <td :colspan="form.taxEnabled ? 3 : 1"></td>
              <td class="right">
                <input v-model.number="form.returnAmount" class="editable-total" type="number" min="0" step="0.01" />
              </td>
              <td v-if="form.taxEnabled" class="right">{{ money(totalTaxAmount) }}</td>
              <td v-if="form.taxEnabled" class="right">{{ money(totalTaxIncludedAmount) }}</td>
              <td></td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="bottom-info-bar">
        <div class="finance-row-full">
          <div class="info-group">
            <label>业务员</label>
            <input v-model.trim="form.salesPerson" type="text" placeholder="请输入业务员" />
          </div>
          <div class="info-group">
            <label>制单人</label>
            <input v-model.trim="form.creator" type="text" placeholder="请输入制单人" />
          </div>
          <div class="info-group wide">
            <label>备注信息</label>
            <input v-model.trim="form.remark" type="text" placeholder="请输入备注信息" />
          </div>
          <div class="info-group">
            <label>包装</label>
            <input v-model.trim="form.packaging" type="text" placeholder="无" />
          </div>
          <div class="finance-item">
            <label>实退金额</label>
            <input v-model.number="form.returnAmount" type="number" min="0" step="0.01" />
          </div>
          <div class="finance-item">
            <label>本次退款</label>
            <input v-model.number="form.refundAmount" type="number" min="0" step="0.01" />
          </div>
          <div class="finance-item">
            <label>结算账户</label>
            <input v-model.trim="form.settlementAccount" type="text" />
          </div>
        </div>

        <div class="finance-row">
          <div class="finance-item">
            <span class="finance-label">商品合计:</span>
            <span class="finance-value">{{ money(form.taxEnabled ? totalTaxIncludedAmount : totalAmount) }}</span>
          </div>
          <div class="finance-item">
            <span class="finance-label">核销金额:</span>
            <span class="finance-value highlight">{{ money(Number(form.returnAmount || 0) - Number(form.refundAmount || 0)) }}</span>
          </div>
          <div class="finance-item">
            <span class="finance-label red">实际退款:</span>
            <span class="finance-value red">{{ money(form.refundAmount) }}</span>
          </div>
          <div class="account-tip">实退金额用于核销客户应收；本次退款为 0 时，不产生现金退款。</div>
          <div class="action-row">
            <button class="btn-save-and-print" type="button" :disabled="saving" @click="save(true)">保存后打印</button>
            <button class="btn-save-final" type="submit" :disabled="saving">{{ saving ? '保存中...' : '保存 (Ctrl+Q)' }}</button>
          </div>
        </div>
      </div>
    </form>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import request from '@/api/request'

const props = defineProps({
  productType: {
    type: String,
    default: 'finished-product'
  }
})

const router = useRouter()
const saving = ref(false)
const stores = ref([])
const customers = ref([])
const warehouses = ref([])
const products = ref([])
const units = ref([])
const stockBalances = ref([])
const focusedRow = ref(-1)
let rowKey = 0

const today = () => new Date().toISOString().slice(0, 10)
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
  taxEnabled: false,
  items: Array.from({ length: 8 }, blankItem),
  returnAmount: 0,
  refundAmount: 0,
  settlementAccount: '',
  salesPerson: '',
  creator: '',
  packaging: '无',
  remark: ''
})

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

const filteredWarehouses = computed(() => {
  if (!form.value.storeId) return []
  return warehouses.value.filter(item => idEquals(item.storeId ?? item.store_id, form.value.storeId))
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
}

const onStoreChange = () => {
  form.value.customerId = ''
  form.value.warehouseId = ''
  form.value.settlementAccount = ''
  resetItems()
}

const onWarehouseChange = () => {
  form.value.items.forEach(item => {
    item.productId = ''
    item.productCode = ''
    item.goodsName = ''
    item.specification = ''
    item.unit = ''
    item.warehouseId = form.value.warehouseId
    item.currentStock = 0
    item.unitConversions = []
    item.conversionRate = null
    item.filteredProducts = []
  })
}

const onItemWarehouseChange = item => {
  if (!item.productId) return
  const product = products.value.find(candidate => idEquals(candidate.id, item.productId))
  if (product) item.currentStock = getProductStock(product, item)
}

const showProductDropdown = index => {
  if (!form.value.storeId) return
  focusedRow.value = index
  const item = form.value.items[index]
  item.showDropdown = true
  filterProducts(index)
}

const hideProductDropdown = index => {
  window.setTimeout(() => {
    if (form.value.items[index]) form.value.items[index].showDropdown = false
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
}

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
  calculateRow(item)
}

const addRow = index => {
  const position = Math.max(0, Math.min(Number(index) + 1, form.value.items.length))
  form.value.items.splice(position, 0, blankItem())
}

const removeRow = index => {
  if (form.value.items.length <= 1) return
  form.value.items.splice(index, 1)
  syncReturnAmount()
}

const clearForm = () => {
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
  form.value.creator = ''
  form.value.packaging = '无'
  form.value.remark = ''
  resetItems()
}

const close = () => router.push({ name: 'admin-orders-returns' })

watch(() => form.value.taxEnabled, enabled => {
  form.value.items.forEach(item => {
    item.taxRate = enabled ? (Number(item.taxRate) || 13) : 0
    calculateRow(item)
  })
})

const loadData = async () => {
  try {
    const productUrl = props.productType === 'raw-material'
      ? '/raw-material-products'
      : '/products/inventory'
    const [storeData, customerData, warehouseData, productData, unitData, stockData] = await Promise.all([
      request({ url: '/stores', method: 'GET' }),
      request({ url: '/customers', method: 'GET' }),
      request({ url: '/warehouses', method: 'GET' }),
      request({ url: productUrl, method: 'GET' }),
      request({ url: '/products/units/measurements', method: 'GET' }),
      props.productType === 'raw-material'
        ? request({ url: '/stock-balances', method: 'GET', params: { type: 'raw-material' } })
        : Promise.resolve([])
    ])
    stores.value = Array.isArray(storeData) ? storeData.filter(item => item.status !== 'inactive') : []
    customers.value = Array.isArray(customerData) ? customerData.filter(item => item.status !== 'inactive') : []
    warehouses.value = Array.isArray(warehouseData) ? warehouseData : []
    products.value = Array.isArray(productData) ? productData.filter(item => item.enabled !== false) : []
    units.value = Array.isArray(unitData) ? unitData : []
    stockBalances.value = Array.isArray(stockData) ? stockData : []
  } catch (error) {
    console.error('加载退货单基础数据失败:', error)
    window.alert(error?.response?.data?.message || '加载退货单基础数据失败')
  }
}

const save = async printAfterSave => {
  if (saving.value) return
  const validItems = form.value.items.filter(item => item.productId && Number(item.quantity) > 0)
  if (!form.value.storeId || !form.value.customerId) {
    window.alert('请选择门店和客户')
    return
  }
  if (!form.value.originalOrderNumber) {
    window.alert('请输入原订单编号')
    return
  }
  if (!validItems.length) {
    window.alert('请至少选择一条商品并填写数量')
    return
  }
  if (Number(form.value.refundAmount) > Number(form.value.returnAmount)) {
    window.alert('本次退款不能超过实退金额')
    return
  }

  saving.value = true
  try {
    const response = await request({
      url: '/returns',
      method: 'POST',
      data: {
        productType: props.productType,
        storeId: Number(form.value.storeId),
        customerId: Number(form.value.customerId),
        returnDate: form.value.returnDate,
        originalOrderNumber: form.value.originalOrderNumber,
        taxEnabled: form.value.taxEnabled,
        returnAmount: Number(form.value.returnAmount) || 0,
        refundAmount: Number(form.value.refundAmount) || 0,
        settlementAccount: form.value.settlementAccount,
        salesPerson: form.value.salesPerson,
        creator: form.value.creator,
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
    if (printAfterSave) window.print()
    window.alert(response?.message || `退货单保存成功：${response?.returnNumber || ''}`)
    await router.push({ name: 'admin-orders-returns' })
  } catch (error) {
    console.error('保存退货单失败:', error)
    window.alert(error?.response?.data?.message || error.message || '保存退货单失败')
  } finally {
    saving.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.return-order-form-page { min-height: 100%; padding: 18px 20px 28px; color: #172033; background: #f5f7f9; }
.return-page-header, .info-card, .table-card, .bottom-card, .page-footer { background: #fff; border: 1px solid #dfe6ed; }
.return-page-header { display: flex; align-items: center; justify-content: space-between; padding: 18px 22px; border-radius: 6px 6px 0 0; }
.page-kicker { color: #0f9f78; font-size: 10px; font-weight: 800; letter-spacing: .1em; }
h1 { margin: 5px 0 4px; font-size: 21px; }
.return-page-header p { margin: 0; color: #7a8699; font-size: 12px; }
.header-actions, .footer-actions { display: flex; gap: 9px; }
.return-form { display: flex; flex-direction: column; gap: 12px; }
.info-card, .bottom-card { padding: 16px 18px; }
.info-row, .bottom-grid { display: grid; grid-template-columns: repeat(6, minmax(120px, 1fr)); gap: 12px 14px; align-items: end; }
.info-field { display: flex; min-width: 0; flex-direction: column; gap: 6px; }
.info-field span { color: #566176; font-size: 12px; font-weight: 700; }
.info-field em { color: #ef4444; font-style: normal; }
.info-field input, .info-field select, .info-field textarea, .product-table input, .product-table select { width: 100%; min-width: 0; height: 34px; padding: 0 8px; color: #172033; background: #fff; border: 1px solid #cbd5e1; border-radius: 4px; outline: none; box-sizing: border-box; }
.info-field textarea { height: auto; padding-top: 8px; resize: vertical; }
.info-field input:focus, .info-field select:focus, .info-field textarea:focus, .product-table input:focus, .product-table select:focus { border-color: #0f9f78; box-shadow: 0 0 0 2px rgba(15,159,120,.12); }
.order-number-field { grid-column: span 2; }
.tax-switch { display: inline-flex; align-items: center; justify-content: center; gap: 8px; height: 34px; color: #566176; font-size: 13px; font-weight: 700; }
.tax-switch input { position: absolute; opacity: 0; }
.tax-switch i { position: relative; display: block; width: 38px; height: 22px; background: #cbd5e1; border-radius: 20px; cursor: pointer; }
.tax-switch i::after { position: absolute; top: 3px; left: 3px; width: 16px; height: 16px; background: #fff; border-radius: 50%; content: ""; transition: transform .2s; }
.tax-switch input:checked + i { background: #0f9f78; }
.tax-switch input:checked + i::after { transform: translateX(16px); }
.table-card { overflow: hidden; }
.table-heading { display: flex; align-items: center; justify-content: space-between; padding: 14px 18px; border-bottom: 1px solid #e5eaf0; }
.table-heading h2 { margin: 0; font-size: 15px; }
.table-heading span { display: block; margin-top: 4px; color: #8a95a6; font-size: 11px; }
.table-scroll { overflow-x: auto; }
.product-table { width: 100%; min-width: 1660px; border-collapse: collapse; table-layout: fixed; }
.product-table th { height: 38px; padding: 0 7px; color: #566176; background: #f7f9fb; border-bottom: 1px solid #dfe6ed; font-size: 11px; text-align: left; white-space: nowrap; }
.product-table td { height: 51px; padding: 6px 7px; border-bottom: 1px solid #edf1f5; vertical-align: middle; }
.product-table input, .product-table select { height: 31px; font-size: 12px; }
.index-col { width: 42px; } .operation-col { width: 72px; } .product-col { width: 220px; } .remark-col { width: 180px; }
.center { text-align: center; } .number-cell { text-align: right; font-variant-numeric: tabular-nums; }
.readonly-input { color: #536174 !important; background: #f7f9fb !important; }
.operation-cell { white-space: nowrap; text-align: center; }
.btn-icon { width: 24px; height: 24px; margin: 0 2px; border-radius: 4px; cursor: pointer; font-size: 17px; line-height: 20px; }
.btn-add { color: #0f9f78; background: #effaf6; border: 1px solid #a6dfcd; }
.btn-remove { color: #d92d20; background: #fff6f5; border: 1px solid #f3b6b1; }
.unit-cell small { display: block; overflow: hidden; margin-top: 3px; color: #8a95a6; font-size: 10px; text-overflow: ellipsis; white-space: nowrap; }
.product-select-wrapper { position: relative; }
.product-dropdown { position: absolute; z-index: 30; top: calc(100% + 3px); left: 0; width: 620px; max-height: 300px; overflow-y: auto; background: #fff; border: 1px solid #b8c6d4; border-radius: 4px; box-shadow: 0 8px 22px rgba(15,23,42,.16); }
.product-dropdown-header, .product-option { display: grid; grid-template-columns: 90px 190px 130px 90px 70px; gap: 8px; align-items: center; padding: 8px 10px; font-size: 11px; }
.product-dropdown-header { color: #7a8699; background: #f7f9fb; border-bottom: 1px solid #e5eaf0; }
.product-option { width: 100%; color: #344054; background: #fff; border: 0; border-bottom: 1px solid #f0f2f5; cursor: pointer; text-align: left; }
.product-option:hover { background: #eefaf6; } .product-option strong { overflow: hidden; color: #172033; text-overflow: ellipsis; white-space: nowrap; }
.total-row td { background: #f7f9fb; border-top: 1px solid #cbd5e1; font-weight: 700; }
.editable-total { color: #0f9f78 !important; font-weight: 800; }
.full-width { grid-column: 1 / -1; }
.account-tip { margin-top: 14px; padding: 9px 12px; color: #596579; background: #f0faf6; border-left: 3px solid #0f9f78; font-size: 12px; line-height: 1.6; }
.page-footer { display: flex; align-items: center; justify-content: space-between; padding: 14px 18px; border-radius: 0 0 6px 6px; }
.btn { display: inline-flex; height: 36px; align-items: center; justify-content: center; padding: 0 15px; border-radius: 4px; cursor: pointer; font-size: 13px; font-weight: 700; }
.btn:disabled { cursor: not-allowed; opacity: .55; }
.btn-light { color: #445066; background: #fff; border: 1px solid #cbd5e1; } .btn-primary { color: #fff; background: #0f9f78; border: 1px solid #0f9f78; }
.close-btn { min-width: 76px; }
.row-focused td { background: #fbfffd; }
@media (max-width: 1000px) { .info-row, .bottom-grid { grid-template-columns: repeat(3, minmax(120px, 1fr)); } .order-number-field { grid-column: span 1; } }
@media (max-width: 640px) { .return-order-form-page { padding: 8px; } .return-page-header, .page-footer { align-items: flex-start; flex-direction: column; gap: 12px; } .info-row, .bottom-grid { grid-template-columns: 1fr; } .full-width, .order-number-field { grid-column: auto; } }
</style>

<style scoped>
.return-order-form-page {
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

  min-height: 100vh;
  padding: 0;
  color: var(--text);
  background: var(--page-bg);
  font-size: 14px;
}

.return-form {
  display: flex;
  gap: 0;
  min-height: 0;
  flex-direction: column;
}

.top-info-bar {
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 14px 20px;
  background: var(--panel-bg);
  border-bottom: 1px solid var(--border);
  box-shadow: 0 1px 2px rgba(15, 23, 42, .04);
  flex-wrap: wrap;
}

.info-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-group label,
.finance-item label {
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}

.info-group select,
.info-group input[type="text"],
.info-group input[type="date"],
.finance-item input {
  min-width: 150px;
  height: 38px;
  padding: 0 11px;
  color: var(--text);
  background: var(--panel-bg);
  border: 1px solid var(--border-strong);
  border-radius: 5px;
  outline: none;
  font-size: 14px;
}

.info-group.wide input {
  min-width: 260px;
}

.info-group select:focus,
.info-group input:focus,
.finance-item input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(var(--accent-rgb), .1);
}

.right-actions {
  margin-left: auto;
  gap: 10px;
}

.tax-switch-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.switch-label {
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 600;
}

.switch {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
}

.switch input {
  width: 0;
  height: 0;
  opacity: 0;
}

.slider {
  position: absolute;
  inset: 0;
  cursor: pointer;
  background: var(--border-strong);
  border-radius: 999px;
  transition: .2s ease;
}

.slider::before {
  position: absolute;
  bottom: 3px;
  left: 3px;
  width: 18px;
  height: 18px;
  background: var(--panel-bg);
  border-radius: 50%;
  box-shadow: 0 1px 3px rgba(0, 0, 0, .15);
  content: "";
  transition: .2s ease;
}

.switch input:checked + .slider {
  background: var(--accent);
}

.switch input:checked + .slider::before {
  transform: translateX(20px);
}

.btn-clear,
.btn-close {
  height: 36px;
  padding: 0 14px;
  border-radius: 5px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
}

.btn-clear {
  color: #dc2626;
  background: #fef2f2;
  border: 1px solid #fecaca;
}

.btn-close {
  color: var(--text-secondary);
  background: var(--panel-bg);
  border: 1px solid var(--border-strong);
}

.btn-clear:hover {
  background: #fee2e2;
}

.btn-close:hover {
  color: var(--accent-dark);
  background: var(--accent-soft);
  border-color: var(--accent-border);
}

.return-hint-bar {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 9px 20px;
  color: var(--text-secondary);
  background: var(--panel-bg);
  border-bottom: 1px solid var(--border);
}

.return-hint-bar span {
  color: var(--accent-dark);
  font-weight: 650;
}

.return-hint-bar small {
  color: var(--text-muted);
}

.products-table-wrapper {
  flex: none;
  overflow-x: auto;
  background: var(--panel-bg);
}

.products-table {
  width: 100%;
  min-width: 1560px;
  border-collapse: collapse;
  background: var(--panel-bg);
  table-layout: fixed;
  font-size: 13px;
}

.products-table thead {
  position: sticky;
  z-index: 10;
  top: 0;
  background: #f8fafc;
}

.products-table th {
  padding: 9px 12px;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border);
  font-size: 12px;
  font-weight: 650;
  text-align: left;
  white-space: nowrap;
}

.products-table td {
  padding: 4px;
  background: var(--panel-bg);
  border-bottom: 1px solid #edf1f5;
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

.products-table tr.row-focused td {
  background: rgba(var(--accent-rgb), .05);
}

.products-table input,
.products-table select {
  width: 100%;
  height: 28px;
  padding: 0 8px;
  color: var(--text);
  background: transparent;
  border: 1px solid transparent;
  outline: none;
  font-size: 13px;
  font-variant-numeric: tabular-nums;
}

.products-table input:focus,
.products-table select:focus {
  background: var(--panel-bg);
  border-color: var(--accent);
  box-shadow: 0 0 0 2px rgba(var(--accent-rgb), .1);
}

.products-table input[readonly],
.readonly-input {
  color: var(--text-muted) !important;
  background: #f8fafc !important;
  cursor: not-allowed;
}

.product-col,
.product-select-wrapper {
  position: relative;
}

.product-input {
  width: 100%;
  height: 28px;
  padding: 0 8px;
  color: var(--text);
  background: transparent;
  border: 1px solid transparent;
  outline: none;
  font-size: 13px;
}

.product-input:focus {
  background: var(--panel-bg);
  border-color: var(--accent);
}

.product-dropdown {
  position: absolute;
  z-index: 1000;
  top: 100%;
  left: 0;
  min-width: 600px;
  max-height: 300px;
  margin-top: 4px;
  overflow-y: auto;
  background: var(--panel-bg);
  border: 1px solid var(--border-strong);
  border-radius: 5px;
  box-shadow: 0 4px 8px rgba(15, 23, 42, .12);
}

.product-dropdown-header,
.product-option {
  display: flex;
  align-items: center;
  padding: 9px 12px;
  font-size: 11px;
}

.product-dropdown-header {
  position: sticky;
  z-index: 1;
  top: 0;
  color: var(--text-secondary);
  background: #f8fafc;
  border-bottom: 1px solid var(--border);
  font-weight: 650;
}

.product-option {
  width: 100%;
  color: var(--text-secondary);
  background: var(--panel-bg);
  border: 0;
  border-bottom: 1px solid #f8fafc;
  cursor: pointer;
  text-align: left;
  font-size: 13px;
}

.product-option:hover {
  background: rgba(var(--accent-rgb), .08);
}

.product-dropdown-header .col-code,
.product-option .col-code { width: 100px; flex-shrink: 0; }
.product-dropdown-header .col-name,
.product-option .col-name { width: 180px; flex-shrink: 0; }
.product-dropdown-header .col-spec,
.product-option .col-spec { width: 150px; flex-shrink: 0; }
.product-dropdown-header .col-unit,
.product-option .col-unit { width: 80px; flex-shrink: 0; }
.product-dropdown-header .col-stock,
.product-option .col-stock { width: 90px; flex-shrink: 0; text-align: right; }
.product-option .col-name { color: var(--text); font-weight: 600; }
.product-option .col-stock { color: var(--accent-dark); font-weight: 600; }

.unit-cell small {
  display: block;
  overflow: hidden;
  color: var(--text-muted);
  font-size: 10px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.blank-cell {
  display: block;
  min-height: 28px;
}

.btn-icon {
  width: 24px;
  height: 24px;
  padding: 0;
  color: var(--accent);
  background: transparent;
  border: 0;
  border-radius: 3px;
  cursor: pointer;
  font-size: 16px;
  font-weight: 700;
  transition: transform .18s ease, color .18s ease;
}

.btn-icon:hover {
  transform: scale(1.15);
}

.btn-icon.btn-remove {
  color: #ef4444;
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
  color: var(--text);
  background: transparent;
  border: 1px solid transparent;
  outline: none;
  font-size: 13px;
  font-weight: 650;
  text-align: right;
}

.editable-total:focus {
  background: var(--panel-bg);
  border-color: var(--accent);
}

.btn-text-link {
  color: var(--accent-dark);
  background: none;
  border: none;
  cursor: pointer;
  font-size: 13px;
  font-weight: 650;
}

.bottom-info-bar {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 14px 20px;
  background: var(--panel-bg);
  border-top: 1px solid var(--border);
  box-shadow: 0 -1px 2px rgba(15, 23, 42, .04);
}

.finance-row-full,
.finance-row,
.action-row {
  display: flex;
  align-items: center;
  gap: 14px;
}

.finance-row-full {
  flex-wrap: nowrap;
}

.finance-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.finance-item input {
  width: 120px;
}

.finance-label {
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
}

.finance-value {
  min-width: 72px;
  color: var(--text);
  font-size: 15px;
  font-weight: 650;
  font-variant-numeric: tabular-nums;
}

.finance-value.highlight {
  color: var(--accent-dark);
}

.finance-value.red,
.finance-label.red {
  color: #ef4444;
}

.account-tip {
  flex: 1;
  margin-top: 0;
  color: var(--text-muted);
  font-size: 12px;
  white-space: nowrap;
}

.action-row {
  margin-left: auto;
  justify-content: flex-end;
}

.btn-save-and-print,
.btn-save-final {
  height: 38px;
  padding: 0 20px;
  color: #fff;
  background: var(--accent);
  border: 1px solid var(--accent);
  border-radius: 5px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
}

.btn-save-final {
  background: var(--accent-dark);
  border-color: var(--accent-dark);
}

.btn-save-and-print:disabled,
.btn-save-final:disabled {
  cursor: not-allowed;
  opacity: .6;
}

@media (max-width: 1280px) {
  .top-info-bar,
  .finance-row-full {
    gap: 12px;
  }

  .finance-row-full {
    flex-wrap: wrap;
  }
}

@media (max-width: 780px) {
  .top-info-bar,
  .finance-row-full,
  .finance-row {
    align-items: stretch;
    flex-direction: column;
  }

  .info-group,
  .info-group select,
  .info-group input,
  .finance-item,
  .finance-item input {
    width: 100%;
    min-width: 100%;
  }

  .right-actions,
  .action-row {
    margin-left: 0;
  }

  .account-tip {
    white-space: normal;
  }
}
</style>
