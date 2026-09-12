<template>
  <Teleport to="body">
    <Transition name="return-form-modal">
      <div class="return-modal-layer">
        <div class="return-modal-backdrop" @click="close"></div>
        <section
          class="return-modal"
          role="dialog"
          aria-modal="true"
          aria-label="录入退货单"
          @keydown.esc="close"
        >
          <header class="return-modal-header">
            <div>
              <span class="eyebrow">退货管理</span>
              <h2>{{ productType === 'raw-material' ? '录入原材料退货单' : '录入退货单' }}</h2>
            </div>
            <button class="close-button" type="button" title="关闭" @click="close">×</button>
          </header>

          <form class="return-form" @submit.prevent="save">
            <div class="return-form-body">
              <section class="form-section">
                <div class="section-heading">
                  <div>
                    <span class="section-kicker">DOCUMENT</span>
                    <h3>基本信息</h3>
                  </div>
                  <label class="tax-switch">
                    <span>含税</span>
                    <input v-model="form.taxEnabled" type="checkbox" />
                    <i></i>
                  </label>
                </div>

                <div class="form-grid">
                  <label class="form-field">
                    <span>门店 <em>*</em></span>
                    <select v-model="form.storeId" required @change="onStoreChange">
                      <option value="">请选择门店</option>
                      <option v-for="store in stores" :key="store.id" :value="String(store.id)">
                        {{ store.name }}
                      </option>
                    </select>
                  </label>
                  <label class="form-field">
                    <span>客户 <em>*</em></span>
                    <select v-model="form.customerId" required>
                      <option value="">请选择客户</option>
                      <option v-for="customer in filteredCustomers" :key="customer.id" :value="String(customer.id)">
                        {{ customer.customerName }}
                      </option>
                    </select>
                  </label>
                  <label class="form-field">
                    <span>日期 <em>*</em></span>
                    <input v-model="form.returnDate" type="date" required />
                  </label>
                  <label class="form-field">
                    <span>原订单编号 <em>*</em></span>
                    <input v-model.trim="form.originalOrderNumber" type="text" placeholder="请输入原订单编号" required />
                  </label>
                </div>
              </section>

              <section class="form-section product-section">
                <div class="section-heading">
                  <div>
                    <span class="section-kicker">ITEMS</span>
                    <h3>商品信息</h3>
                  </div>
                  <button class="text-button" type="button" @click="addRow">＋ 添加商品</button>
                </div>

                <div class="products-table-wrapper">
                  <table class="products-table">
                    <thead>
                      <tr>
                        <th class="operation-col">操作</th>
                        <th class="product-col">商品信息 <em>*</em></th>
                        <th>规格型号</th>
                        <th>单位</th>
                        <th>所属仓库</th>
                        <th>件数</th>
                        <th>数量 <em>*</em></th>
                        <th>单价 (元)</th>
                        <th>总金额 (元)</th>
                        <th v-if="form.taxEnabled">含税单价</th>
                        <th v-if="form.taxEnabled">税额</th>
                        <th v-if="form.taxEnabled">含税金额</th>
                        <th class="remark-col">备注信息</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(item, index) in form.items" :key="item.key">
                        <td class="operation-cell">
                          <button type="button" title="删除" @click="removeRow(index)">×</button>
                        </td>
                        <td class="product-col">
                          <select v-model="item.productId" @change="selectProduct(item)">
                            <option value="">请选择商品</option>
                            <option v-for="product in products" :key="product.id" :value="String(product.id)">
                              {{ product.code ? `${product.code} · ` : '' }}{{ product.name }}
                            </option>
                          </select>
                        </td>
                        <td><input v-model="item.specification" type="text" /></td>
                        <td><input v-model="item.unit" type="text" /></td>
                        <td>
                          <select v-model="item.warehouseId">
                            <option value="">请选择</option>
                            <option v-for="warehouse in filteredWarehouses" :key="warehouse.id" :value="String(warehouse.id)">
                              {{ warehouse.name }}
                            </option>
                          </select>
                        </td>
                        <td><input v-model.number="item.packages" type="number" min="0" step="0.01" /></td>
                        <td><input v-model.number="item.quantity" type="number" min="0" step="0.01" @input="calculateRow(item)" /></td>
                        <td><input v-model.number="item.price" type="number" min="0" step="0.01" @input="calculateRow(item)" /></td>
                        <td><input v-model.number="item.amount" type="number" min="0" step="0.01" @input="markAmountTouched" /></td>
                        <td v-if="form.taxEnabled"><input v-model.number="item.taxIncludedPrice" type="number" min="0" step="0.01" @input="calculateTaxRow(item)" /></td>
                        <td v-if="form.taxEnabled" class="readonly-number">{{ money(item.taxAmount) }}</td>
                        <td v-if="form.taxEnabled" class="readonly-number">{{ money(item.taxIncludedAmount) }}</td>
                        <td class="remark-col"><input v-model="item.remark" type="text" /></td>
                      </tr>
                      <tr class="total-row">
                        <td colspan="5"><strong>合计</strong></td>
                        <td>{{ number(totalPackages) }}</td>
                        <td>{{ number(totalQuantity) }}</td>
                        <td></td>
                        <td>
                          <input v-model.number="form.returnAmount" class="total-input" type="number" min="0" step="0.01" />
                        </td>
                        <td v-if="form.taxEnabled"></td>
                        <td v-if="form.taxEnabled">{{ money(totalTaxAmount) }}</td>
                        <td v-if="form.taxEnabled">{{ money(totalTaxIncludedAmount) }}</td>
                        <td></td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </section>

              <section class="form-section">
                <div class="section-heading">
                  <div>
                    <span class="section-kicker">SETTLEMENT</span>
                    <h3>结算信息</h3>
                  </div>
                </div>
                <div class="bottom-grid">
                  <label class="form-field">
                    <span>业务员</span>
                    <input v-model.trim="form.salesPerson" type="text" />
                  </label>
                  <label class="form-field">
                    <span>制单人</span>
                    <input v-model.trim="form.creator" type="text" />
                  </label>
                  <label class="form-field">
                    <span>包装</span>
                    <input v-model.trim="form.packaging" type="text" placeholder="无" />
                  </label>
                  <label class="form-field settlement-field">
                    <span>结算账户</span>
                    <input v-model.trim="form.settlementAccount" type="text" />
                  </label>
                  <label class="form-field">
                    <span>实退金额</span>
                    <input :value="money(form.returnAmount)" type="text" readonly class="readonly-input" />
                  </label>
                  <label class="form-field">
                    <span>本次退款</span>
                    <input v-model.number="form.refundAmount" type="number" min="0" step="0.01" />
                  </label>
                  <label class="form-field full-width">
                    <span>备注信息</span>
                    <textarea v-model.trim="form.remark" rows="2" placeholder="请输入备注信息"></textarea>
                  </label>
                </div>
                <div class="account-tip">
                  实退金额会核销客户应收；本次退款默认 0，表示不现金退款，仅将客户应付金额减少相应金额。
                </div>
              </section>
            </div>

            <footer class="return-modal-footer">
              <button class="button button-secondary" type="button" @click="close">取消</button>
              <div class="footer-actions">
                <button class="button button-secondary" type="button" :disabled="saving" @click="save(true)">保存并打印</button>
                <button class="button button-primary" type="submit" :disabled="saving">
                  {{ saving ? '保存中...' : '保存' }}
                </button>
              </div>
            </footer>
          </form>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import request from '@/api/request'

const props = defineProps({
  productType: {
    type: String,
    default: 'finished-product'
  }
})

const emit = defineEmits(['close', 'saved'])
const saving = ref(false)
const stores = ref([])
const customers = ref([])
const warehouses = ref([])
const products = ref([])
const amountTouched = ref(false)
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
  packages: 0,
  quantity: 0,
  price: 0,
  amount: 0,
  taxRate: 13,
  taxIncludedPrice: 0,
  taxAmount: 0,
  taxIncludedAmount: 0,
  remark: ''
})

const form = ref({
  storeId: '',
  customerId: '',
  returnDate: today(),
  originalOrderNumber: '',
  taxEnabled: false,
  items: [blankItem(), blankItem(), blankItem()],
  returnAmount: 0,
  refundAmount: 0,
  settlementAccount: '',
  salesPerson: '',
  creator: '',
  packaging: '无',
  remark: ''
})

const filteredCustomers = computed(() => {
  if (!form.value.storeId) return customers.value
  return customers.value.filter(item => String(item.storeId ?? '') === String(form.value.storeId))
})

const filteredWarehouses = computed(() => {
  if (!form.value.storeId) return warehouses.value
  return warehouses.value.filter(item => String(item.storeId ?? '') === String(form.value.storeId))
})

const totalPackages = computed(() => form.value.items.reduce((sum, item) => sum + (Number(item.packages) || 0), 0))
const totalQuantity = computed(() => form.value.items.reduce((sum, item) => sum + (Number(item.quantity) || 0), 0))
const totalAmount = computed(() => form.value.items.reduce((sum, item) => sum + (Number(item.amount) || 0), 0))
const totalTaxAmount = computed(() => form.value.items.reduce((sum, item) => sum + (Number(item.taxAmount) || 0), 0))
const totalTaxIncludedAmount = computed(() => form.value.items.reduce((sum, item) => sum + (Number(item.taxIncludedAmount) || 0), 0))

const money = value => Number(value || 0).toFixed(2)
const number = value => Number(value || 0).toFixed(2)

const calculateTaxRow = item => {
  const rate = Number(item.taxRate) || 0
  const includedPrice = Number(item.taxIncludedPrice) || 0
  item.price = Number((includedPrice / (1 + rate / 100)).toFixed(2))
  item.amount = Number(((Number(item.quantity) || 0) * item.price).toFixed(2))
  item.taxAmount = Number((item.amount * rate / 100).toFixed(2))
  item.taxIncludedAmount = Number((item.amount + item.taxAmount).toFixed(2))
  syncReturnAmount()
}

const calculateRow = item => {
  item.amount = Number(((Number(item.quantity) || 0) * (Number(item.price) || 0)).toFixed(2))
  const rate = Number(item.taxRate) || 0
  item.taxIncludedPrice = Number((Number(item.price || 0) * (1 + rate / 100)).toFixed(2))
  item.taxAmount = Number((item.amount * rate / 100).toFixed(2))
  item.taxIncludedAmount = Number((item.amount + item.taxAmount).toFixed(2))
  syncReturnAmount()
}

const syncReturnAmount = () => {
  if (!amountTouched.value) {
    form.value.returnAmount = Number(
      (form.value.taxEnabled ? totalTaxIncludedAmount.value : totalAmount.value).toFixed(2)
    )
  }
}

const markAmountTouched = () => {
  amountTouched.value = true
}

watch(() => form.value.taxEnabled, enabled => {
  form.value.items.forEach(item => {
    item.taxRate = enabled ? (Number(item.taxRate) || 13) : 0
    calculateRow(item)
  })
  amountTouched.value = false
  syncReturnAmount()
})

const onStoreChange = () => {
  form.value.customerId = ''
  form.value.settlementAccount = stores.value.find(item => String(item.id) === String(form.value.storeId))
    ? `${stores.value.find(item => String(item.id) === String(form.value.storeId)).name}结算账户`
    : ''
  form.value.items.forEach(item => {
    item.warehouseId = ''
  })
}

const selectProduct = item => {
  const product = products.value.find(candidate => String(candidate.id) === String(item.productId))
  if (!product) return
  item.productCode = product.code || ''
  item.goodsName = product.name || ''
  item.specification = product.specification || ''
  item.unit = product.unit || ''
  item.price = Number(product.price || 0)
  item.taxRate = form.value.taxEnabled ? 13 : 0
  item.taxIncludedPrice = form.value.taxEnabled
    ? Number((item.price * 1.13).toFixed(2))
    : 0
  calculateRow(item)
}

const addRow = () => form.value.items.push(blankItem())
const removeRow = index => {
  if (form.value.items.length > 1) form.value.items.splice(index, 1)
  syncReturnAmount()
}

const close = () => emit('close')

const loadData = async () => {
  try {
    const productUrl = props.productType === 'raw-material'
      ? '/raw-material-products'
      : '/products/inventory'
    const [storeData, customerData, warehouseData, productData] = await Promise.all([
      request({ url: '/stores', method: 'GET' }),
      request({ url: '/customers', method: 'GET' }),
      request({ url: '/warehouses', method: 'GET' }),
      request({ url: productUrl, method: 'GET' })
    ])
    stores.value = Array.isArray(storeData) ? storeData.filter(item => item.status !== 'inactive') : []
    customers.value = Array.isArray(customerData) ? customerData.filter(item => item.status !== 'inactive') : []
    warehouses.value = Array.isArray(warehouseData) ? warehouseData : []
    products.value = Array.isArray(productData) ? productData.filter(item => item.enabled !== false) : []
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
    emit('saved', response)
    if (printAfterSave) window.print()
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
.return-modal-layer {
  position: fixed;
  z-index: 1200;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.return-modal-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(15, 23, 42, 0.52);
  backdrop-filter: blur(2px);
}

.return-modal {
  position: relative;
  display: flex;
  width: min(1540px, 100%);
  max-height: calc(100vh - 48px);
  flex-direction: column;
  overflow: hidden;
  color: #172033;
  background: #f4f7f8;
  border: 1px solid #d8e1e8;
  border-radius: 8px;
  box-shadow: 0 20px 60px rgba(15, 23, 42, 0.22);
}

.return-modal-header,
.return-modal-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 22px;
  background: #fff;
}

.return-modal-header {
  border-bottom: 1px solid #e2e8f0;
}

.eyebrow,
.section-kicker {
  color: #0f9f78;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.08em;
}

.return-modal h2,
.return-modal h3 {
  margin: 4px 0 0;
}

.return-modal h2 {
  font-size: 20px;
}

.return-modal h3 {
  font-size: 15px;
}

.close-button {
  width: 34px;
  height: 34px;
  color: #667085;
  background: #fff;
  border: 1px solid #cbd5e1;
  border-radius: 5px;
  cursor: pointer;
  font-size: 25px;
  line-height: 1;
}

.return-form {
  display: flex;
  min-height: 0;
  flex: 1;
  flex-direction: column;
}

.return-form-body {
  min-height: 0;
  overflow: auto;
  padding: 18px 22px;
}

.form-section {
  margin-bottom: 16px;
  padding: 16px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
}

.section-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.form-grid,
.bottom-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(150px, 1fr));
  gap: 13px 16px;
}

.form-field {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 6px;
}

.form-field > span {
  color: #596579;
  font-size: 12px;
  font-weight: 650;
}

.form-field em,
th em {
  color: #ef4444;
  font-style: normal;
}

.form-field input,
.form-field select,
.form-field textarea,
.products-table input,
.products-table select {
  width: 100%;
  min-width: 0;
  height: 36px;
  padding: 0 9px;
  color: #172033;
  background: #fff;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  outline: none;
}

.form-field textarea {
  height: auto;
  padding-top: 8px;
  resize: vertical;
}

.form-field input:focus,
.form-field select:focus,
.form-field textarea:focus,
.products-table input:focus,
.products-table select:focus {
  border-color: #0f9f78;
  box-shadow: 0 0 0 3px rgba(15, 159, 120, 0.1);
}

.full-width {
  grid-column: 1 / -1;
}

.tax-switch {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #596579;
  font-size: 13px;
  font-weight: 650;
}

.tax-switch input {
  position: absolute;
  opacity: 0;
}

.tax-switch i {
  position: relative;
  display: inline-block;
  width: 38px;
  height: 22px;
  background: #cbd5e1;
  border-radius: 12px;
  cursor: pointer;
  transition: background 0.2s ease;
}

.tax-switch i::after {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 16px;
  height: 16px;
  background: #fff;
  border-radius: 50%;
  content: "";
  transition: transform 0.2s ease;
}

.tax-switch input:checked + i {
  background: #0f9f78;
}

.tax-switch input:checked + i::after {
  transform: translateX(16px);
}

.text-button {
  color: #08745a;
  background: transparent;
  border: 0;
  cursor: pointer;
  font-size: 13px;
  font-weight: 700;
}

.products-table-wrapper {
  overflow-x: auto;
}

.products-table {
  width: 100%;
  min-width: 1400px;
  border-collapse: collapse;
  table-layout: fixed;
}

.products-table th {
  height: 42px;
  padding: 0 8px;
  color: #566176;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  font-size: 11px;
  text-align: left;
  white-space: nowrap;
}

.products-table td {
  height: 52px;
  padding: 7px 8px;
  border-bottom: 1px solid #edf1f5;
  vertical-align: middle;
}

.products-table input,
.products-table select {
  height: 32px;
  font-size: 12px;
}

.operation-col,
.operation-cell {
  width: 54px;
  text-align: center;
}

.product-col {
  width: 190px;
}

.remark-col {
  width: 170px;
}

.operation-cell button {
  width: 26px;
  height: 26px;
  color: #b42318;
  background: #fff;
  border: 1px solid #f2b8b5;
  border-radius: 4px;
  cursor: pointer;
  font-size: 18px;
  line-height: 1;
}

.readonly-number {
  color: #344054;
  font-variant-numeric: tabular-nums;
  text-align: right;
}

.total-row td {
  color: #172033;
  background: #f8fafc;
  border-top: 1px solid #cbd5e1;
  font-weight: 700;
}

.total-input {
  color: #0f9f78 !important;
  font-weight: 800;
}

.settlement-field {
  grid-column: span 2;
}

.account-tip {
  margin-top: 12px;
  padding: 10px 12px;
  color: #596579;
  background: #f1f8f5;
  border-left: 3px solid #0f9f78;
  font-size: 12px;
  line-height: 1.6;
}

.return-modal-footer {
  border-top: 1px solid #e2e8f0;
}

.footer-actions {
  display: flex;
  gap: 9px;
}

.button {
  display: inline-flex;
  height: 38px;
  align-items: center;
  justify-content: center;
  padding: 0 16px;
  border: 1px solid transparent;
  border-radius: 5px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 700;
}

.button:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.button-primary {
  color: #fff;
  background: #0f9f78;
  border-color: #0f9f78;
}

.button-secondary {
  color: #445066;
  background: #fff;
  border-color: #cbd5e1;
}

.return-form-modal-enter-active,
.return-form-modal-leave-active {
  transition: opacity 0.2s ease;
}

.return-form-modal-enter-from,
.return-form-modal-leave-to {
  opacity: 0;
}

@media (max-width: 900px) {
  .return-modal-layer {
    padding: 0;
  }

  .return-modal {
    width: 100%;
    max-height: 100vh;
    border-radius: 0;
  }

  .form-grid,
  .bottom-grid {
    grid-template-columns: repeat(2, minmax(140px, 1fr));
  }
}

@media (max-width: 560px) {
  .return-form-body {
    padding: 12px;
  }

  .form-grid,
  .bottom-grid {
    grid-template-columns: 1fr;
  }

  .settlement-field {
    grid-column: auto;
  }
}
</style>
