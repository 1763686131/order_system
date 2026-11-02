<template>
  <slot
    :form="form"
    :order="previewOrder"
    :saving="saving"
    :units-ready="unitsReady"
    :error="errorMessage"
    :add-item="addItem"
    :edit-item="editItem"
    :remove-item="removeItem"
    :change-receivable="changeReceivable"
    :save="saveOrder"
    :cancel="() => emit('cancel')"
  />
  <Teleport to="body">
    <div v-if="itemDraft" class="mobile-product-dialog-overlay" @click.self="closeItemDialog" @keydown.esc.stop.prevent="closeItemDialog">
      <section ref="dialogElement" class="mobile-product-dialog" role="dialog" aria-modal="true" :aria-label="itemDraftIndex === -1 ? '新增商品' : '修改商品明细'" tabindex="-1" @keydown.tab="keepDialogFocus">
        <header class="product-dialog-header">
          <h3>{{ itemDraftIndex === -1 ? '新增商品' : '修改商品明细' }}</h3>
          <button class="dialog-close-button" type="button" aria-label="关闭商品明细" title="关闭" @click="closeItemDialog"><X aria-hidden="true" /></button>
        </header>
        <form class="product-dialog-form" @submit.prevent="confirmItem">
          <div class="product-fields">
            <div class="product-field full-width">
              <label :for="`${productListId}-input`">商品</label>
              <div class="product-combobox" @focusout="handleProductSearchBlur">
                <div class="product-search-control">
                  <Search class="product-search-icon" aria-hidden="true" />
                  <input
                    :id="`${productListId}-input`"
                    ref="productSearchInput"
                    :value="productSearch"
                    role="combobox"
                    aria-label="商品"
                    aria-autocomplete="list"
                    aria-haspopup="listbox"
                    :aria-expanded="productSearchOpen"
                    :aria-controls="productListId"
                    :aria-activedescendant="productSearchOpen && activeProductIndex >= 0 ? `${productListId}-${filteredProducts[activeProductIndex]?.id}` : undefined"
                    :disabled="!unitsReady"
                    :aria-invalid="productSearchEdited && !!itemError"
                    autocomplete="off"
                    placeholder="搜索商品名称、规格或编码"
                    required
                    @focus="openProductSearch"
                    @click="openProductSearch"
                    @input="handleProductSearchInput"
                    @keydown="handleProductSearchKeydown"
                  />
                  <button class="product-search-toggle" type="button" aria-label="商品选项" :aria-expanded="productSearchOpen" :disabled="!unitsReady" @click="toggleProductSearch">
                    <ChevronDown aria-hidden="true" />
                  </button>
                </div>
                <div v-if="productSearchOpen" :id="productListId" class="product-search-options" role="listbox" aria-label="商品搜索结果">
                  <button
                    v-for="(product, index) in filteredProducts"
                    :id="`${productListId}-${product.id}`"
                    :key="product.id"
                    class="product-search-option"
                    :class="{ 'is-active': index === activeProductIndex }"
                    type="button"
                    role="option"
                    tabindex="-1"
                    :aria-selected="sameId(product.id, itemDraft.productId)"
                    :data-product-id="product.id"
                    @mousedown.prevent
                    @click="chooseProduct(product)"
                  >
                    <span class="product-option-name">{{ product.name }}</span>
                    <span v-if="product.code || product.specification" class="product-option-detail">{{ [product.code, product.specification].filter(Boolean).join(' · ') }}</span>
                  </button>
                  <div v-if="!filteredProducts.length" class="product-search-empty" role="status">暂无匹配商品</div>
                </div>
              </div>
            </div>
            <label><span>规格型号</span><input :value="itemDraft.spec" aria-label="规格型号" readonly /></label>
            <label><span>单位</span><input :value="itemDraft.unit" aria-label="单位" readonly /></label>
            <label class="full-width">
              <span>所属仓库</span>
              <select v-model="itemDraft.warehouseId" aria-label="所属仓库" required @change="changeWarehouse(itemDraft)">
                <option value="">请选择仓库</option>
                <option v-if="itemDraft.warehouseId && !availableWarehouses.some(warehouse => sameId(warehouse.id, itemDraft.warehouseId))" :value="itemDraft.warehouseId">{{ itemDraft.warehouseName || '历史仓库' }}</option>
                <option v-for="warehouse in availableWarehouses" :key="warehouse.id" :value="warehouse.id">{{ warehouse.name }}</option>
              </select>
            </label>
            <label><span>件数</span><input v-model.number="itemDraft.packages" aria-label="件数" type="number" min="0" step="any" inputmode="decimal" @input="changePackages(itemDraft)" /></label>
            <label><span>数量</span><input v-model.number="itemDraft.quantity" aria-label="数量" type="number" min="0.0001" step="any" inputmode="decimal" required @input="changeQuantity(itemDraft)" /></label>
            <label><span>单价</span><input v-model.number="itemDraft.price" aria-label="单价" type="number" min="0" step="any" inputmode="decimal" @input="changePrice(itemDraft)" /></label>
            <template v-if="taxEnabled">
              <label><span>税率 (%)</span><input v-model.number="itemDraft.taxRate" aria-label="税率" type="number" min="0" max="100" step="any" inputmode="decimal" @input="changePrice(itemDraft)" /></label>
              <label><span>含税单价</span><input v-model.number="itemDraft.taxIncludedPrice" aria-label="含税单价" type="number" min="0" step="any" inputmode="decimal" @input="changeIncludedPrice(itemDraft)" /></label>
            </template>
            <div class="item-amount"><span>{{ taxEnabled ? '含税金额' : '金额' }}</span><strong>¥{{ money(taxEnabled ? itemDraft.totalAmount : itemDraft.amount) }}</strong></div>
            <label class="full-width"><span>商品备注</span><input v-model="itemDraft.remark" aria-label="商品备注" /></label>
          </div>
          <p v-if="itemError" class="save-error" role="alert">{{ itemError }}</p>
          <footer class="product-dialog-actions">
            <button class="cancel-button" type="button" @click="closeItemDialog">取消</button>
            <button class="confirm-item-button" type="submit"><Check aria-hidden="true" />修改完成</button>
          </footer>
        </form>
      </section>
    </div>
  </Teleport>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { Check, ChevronDown, Search, X } from '@lucide/vue'
import request from '@/api/request'
import { money } from '@/composables/documents/documentModels'

const props = defineProps({
  order: { type: Object, required: true },
  creating: { type: Boolean, default: false },
  editing: { type: Boolean, default: false },
  products: { type: Array, default: () => [] },
  warehouses: { type: Array, default: () => [] }
})
const emit = defineEmits(['saved', 'cancel'])
const sameId = (left, right) => String(left) === String(right)
const number = value => Number(value) || 0
const round = value => Number(value.toFixed(2))
const saving = ref(false)
const errorMessage = ref('')
const dialogElement = ref(null)
const itemDraft = ref(null)
const itemDraftIndex = ref(-1)
const itemError = ref('')
const productSearchInput = ref(null)
const productSearch = ref('')
const productSearchOpen = ref(false)
const productSearchEdited = ref(false)
const activeProductIndex = ref(-1)
const productListId = computed(() => `mobile-order-product-options-${props.order.id}`)
let itemTrigger = null
let packagesChanged = false
let previousBodyOverflow = null
const units = ref([])
const unitsReady = ref(false)
let nextItemKey = 0

const taxEnabled = Boolean(props.creating && props.order.tax_enabled) || (props.order.order_goods || []).some(item =>
  number(item.tax_rate) > 0 || number(item.tax_included_price) > 0 || number(item.total_amount) > 0
) || number(props.order.tax_amount) > 0
const defaultTaxRate = taxEnabled
  ? props.creating ? number(props.order.tax_rate) : number(props.order.order_goods?.find(item => number(item.tax_rate) > 0)?.tax_rate) || 13
  : 0

const createForm = () => ({
  contactPerson: String(props.order.contact_person || props.order.receiver_name || ''),
  contactPhone: String(props.order.contact_phone || props.order.receiver_phone || ''),
  contactAddress: props.order.contact_address || props.order.receiver_address || '',
  orderRemark: props.order.remark || '',
  discountAmount: props.order.discount_amount ?? (props.order.should_receive != null
    ? round(number(props.order.should_receive) - number(props.order.other_fees))
    : (taxEnabled ? props.order.total_amount : props.order.subtotal_amount) ?? 0),
  otherFees: number(props.order.other_fees),
  currentPayment: number(props.order.current_payment),
  totalPackages: props.order.total_packages ?? (props.order.order_goods || []).reduce((sum, item) => sum + number(item.packages), 0),
  items: (props.order.order_goods || []).map(item => ({
    key: nextItemKey++,
    productId: item.product_id || '',
    goodsName: item.goods_name || props.products.find(product => sameId(product.id, item.product_id))?.name || '',
    spec: item.spec || '',
    unit: item.unit || '',
    warehouseId: item.warehouse_id || props.order.warehouse_id || '',
    warehouseName: item.warehouse_name || '',
    packages: item.packages ?? '',
    quantity: item.quantity ?? '',
    price: item.price ?? '',
    taxRate: taxEnabled ? number(item.tax_rate) : 0,
    taxIncludedPrice: taxEnabled ? (item.tax_included_price ?? round(number(item.price) * (1 + number(item.tax_rate) / 100))) : 0,
    amount: item.amount ?? number(item.quantity) * number(item.price),
    totalAmount: taxEnabled ? (item.total_amount ?? number(item.quantity) * number(item.tax_included_price)) : 0,
    remark: item.remark || ''
  }))
})
const form = ref(createForm())

const availableWarehouses = computed(() => props.warehouses.filter(warehouse =>
  sameId(warehouse.storeId ?? warehouse.store_id, props.order.store_id)
))
const productsForItem = item => props.products.filter(product =>
  product.storeIds?.some(id => sameId(id, props.order.store_id)) &&
  (!item.warehouseId || !product.warehouseId || sameId(product.warehouseId, item.warehouseId))
)
const filteredProducts = computed(() => {
  if (!itemDraft.value) return []
  const query = productSearchEdited.value ? productSearch.value.trim().toLocaleLowerCase() : ''
  return productsForItem(itemDraft.value).filter(product =>
    !query || [product.name, product.specification, product.code].some(value =>
      String(value || '').toLocaleLowerCase().includes(query)
    )
  )
})
const scrollActiveProductIntoView = () => nextTick(() => {
  if (!productSearchOpen.value || activeProductIndex.value < 0) return
  document.getElementById(`${productListId.value}-${filteredProducts.value[activeProductIndex.value]?.id}`)
    ?.scrollIntoView({ block: 'nearest' })
})
const openProductSearch = () => {
  if (!unitsReady.value || productSearchOpen.value) return
  productSearchOpen.value = true
  const selectedIndex = filteredProducts.value.findIndex(product => sameId(product.id, itemDraft.value?.productId))
  activeProductIndex.value = selectedIndex >= 0 ? selectedIndex : filteredProducts.value.length ? 0 : -1
  scrollActiveProductIntoView()
}
const closeProductSearch = () => {
  productSearchOpen.value = false
  activeProductIndex.value = -1
}
const toggleProductSearch = () => {
  if (productSearchOpen.value) {
    closeProductSearch()
    return
  }
  productSearchInput.value?.focus({ preventScroll: true })
  openProductSearch()
}
const handleProductSearchBlur = event => {
  if (!event.currentTarget.contains(event.relatedTarget)) closeProductSearch()
}
const handleProductSearchInput = event => {
  productSearch.value = event.target.value
  productSearchEdited.value = true
  productSearchOpen.value = true
  activeProductIndex.value = filteredProducts.value.length ? 0 : -1
  itemError.value = ''
}
const chooseProduct = product => {
  const item = itemDraft.value
  if (!item) return
  if (!sameId(item.productId, product.id)) {
    item.productId = product.id
    selectProduct(item)
  }
  productSearch.value = product.name
  productSearchEdited.value = false
  itemError.value = ''
  productSearchInput.value?.focus({ preventScroll: true })
  closeProductSearch()
}
const handleProductSearchKeydown = event => {
  if (event.isComposing || event.keyCode === 229) return
  if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
    event.preventDefault()
    if (!productSearchOpen.value) {
      openProductSearch()
    } else if (filteredProducts.value.length) {
      const direction = event.key === 'ArrowDown' ? 1 : -1
      activeProductIndex.value = (activeProductIndex.value + direction + filteredProducts.value.length) % filteredProducts.value.length
      scrollActiveProductIntoView()
    }
  } else if (event.key === 'Enter') {
    event.preventDefault()
    if (productSearchOpen.value && filteredProducts.value[activeProductIndex.value]) {
      chooseProduct(filteredProducts.value[activeProductIndex.value])
    } else {
      openProductSearch()
    }
  } else if (event.key === 'Escape' && (productSearchOpen.value || productSearchEdited.value)) {
    event.preventDefault()
    event.stopPropagation()
    productSearch.value = itemDraft.value?.goodsName || ''
    productSearchEdited.value = false
    itemError.value = ''
    closeProductSearch()
  }
}
const shouldReceive = computed(() => round(number(form.value.discountAmount) + number(form.value.otherFees)))
const currentDebt = computed(() => round(shouldReceive.value - number(form.value.currentPayment)))
const previewOrder = computed(() => props.editing ? {
  ...props.order,
  contact_person: form.value.contactPerson, receiver_name: form.value.contactPerson,
  contact_phone: form.value.contactPhone, receiver_phone: form.value.contactPhone,
  contact_address: form.value.contactAddress, receiver_address: form.value.contactAddress,
  remark: form.value.orderRemark,
  should_receive: shouldReceive.value, current_payment: number(form.value.currentPayment),
  current_debt: currentDebt.value,
  order_goods: form.value.items.map(item => ({
    product_id: item.productId, goods_name: item.goodsName, spec: item.spec, unit: item.unit,
    quantity: item.quantity, price: item.price, amount: item.amount,
    tax_rate: item.taxRate, tax_included_price: item.taxIncludedPrice, total_amount: item.totalAmount
  }))
} : props.order)
const changeReceivable = value => {
  form.value.discountAmount = round(number(value) - number(form.value.otherFees))
}
const syncPackages = () => {
  form.value.totalPackages = form.value.items.reduce((sum, item) => sum + number(item.packages), 0)
}
const calculateItemAmount = item => {
  item.amount = number(item.quantity) * number(item.price)
  item.totalAmount = taxEnabled ? number(item.quantity) * number(item.taxIncludedPrice) : 0
}
const syncOrderAmount = () => {
  form.value.discountAmount = round(form.value.items.reduce((sum, row) => sum + number(taxEnabled ? row.totalAmount : row.amount), 0))
}
const conversionRate = item => number(props.products.find(product => sameId(product.id, item.productId))?.unitConversions?.[0]?.value)
const changePackages = item => {
  const rate = conversionRate(item)
  if (rate) item.quantity = number(item.packages) * rate
  packagesChanged = true
  calculateItemAmount(item)
}
const changeQuantity = item => {
  const rate = conversionRate(item)
  if (rate) {
    item.packages = number(item.quantity) / rate
    packagesChanged = true
  }
  calculateItemAmount(item)
}
const changePrice = item => {
  item.taxIncludedPrice = taxEnabled ? round(number(item.price) * (1 + number(item.taxRate) / 100)) : 0
  calculateItemAmount(item)
}
const changeIncludedPrice = item => {
  item.price = round(number(item.taxIncludedPrice) / (1 + number(item.taxRate) / 100))
  calculateItemAmount(item)
}
const selectProduct = item => {
  const product = props.products.find(product => sameId(product.id, item.productId))
  Object.assign(item, {
    goodsName: product?.name || '',
    spec: product?.specification || '',
    unit: units.value.find(unit => sameId(unit.id, product?.unitId))?.name || product?.unitName || '',
    price: product?.price ?? 0,
    taxRate: defaultTaxRate,
    packages: '',
    quantity: ''
  })
  item.warehouseId ||= props.order.warehouse_id || product?.warehouseId || ''
  packagesChanged = true
  changePrice(item)
}
const changeWarehouse = item => {
  closeProductSearch()
  if (productsForItem(item).some(product => sameId(product.id, item.productId))) return
  item.productId = ''
  selectProduct(item)
  productSearch.value = ''
  productSearchEdited.value = false
}
const openItemDialog = async (index) => {
  if (!props.editing || saving.value || itemDraft.value) return
  itemDraftIndex.value = index
  itemError.value = ''
  packagesChanged = false
  itemTrigger = document.activeElement
  previousBodyOverflow = document.body.style.overflow
  document.body.style.overflow = 'hidden'
  itemDraft.value = index >= 0 ? { ...form.value.items[index] } : {
    key: nextItemKey++, productId: '', goodsName: '', spec: '', unit: '',
    warehouseId: props.order.warehouse_id || '', warehouseName: '',
    packages: '', quantity: '', price: '', taxRate: defaultTaxRate,
    taxIncludedPrice: 0, amount: 0, totalAmount: 0, remark: ''
  }
  productSearch.value = itemDraft.value.goodsName
  productSearchEdited.value = false
  closeProductSearch()
  await nextTick()
  dialogElement.value?.focus({ preventScroll: true })
}
const addItem = () => openItemDialog(-1)
const editItem = index => openItemDialog(index)
const closeItemDialog = () => {
  closeProductSearch()
  productSearch.value = ''
  productSearchEdited.value = false
  itemDraft.value = null
  if (previousBodyOverflow !== null) {
    document.body.style.overflow = previousBodyOverflow
    previousBodyOverflow = null
  }
  const trigger = itemTrigger
  itemTrigger = null
  nextTick(() => {
    if (trigger?.isConnected) trigger.focus({ preventScroll: true })
  })
}
const keepDialogFocus = event => {
  const controls = [...(dialogElement.value?.querySelectorAll('button:not(:disabled):not([tabindex="-1"]), input:not([readonly]):not(:disabled), select:not(:disabled)') || [])]
  const first = controls[0]
  const last = controls.at(-1)
  if ((event.shiftKey && (document.activeElement === first || document.activeElement === dialogElement.value)) ||
    (!event.shiftKey && (document.activeElement === last || document.activeElement === dialogElement.value))) {
    event.preventDefault()
    const target = event.shiftKey ? last : first
    target?.focus()
  }
}
const validItem = item => Boolean(item.productId && item.warehouseId && Number.isFinite(Number(item.quantity)) && number(item.quantity) > 0)
const validItemAmounts = item => ['packages', 'price', ...(taxEnabled ? ['taxRate', 'taxIncludedPrice'] : [])]
  .every(field => Number.isFinite(Number(item[field])) && Number(item[field]) >= 0) && number(item.taxRate) <= 100
const confirmItem = () => {
  if (productSearchEdited.value) {
    itemError.value = '请从搜索结果中选择商品。'
    productSearchInput.value?.focus({ preventScroll: true })
    return
  }
  const item = itemDraft.value
  if (!item || !validItem(item) || !validItemAmounts(item)) {
    itemError.value = '请选择商品和仓库，数量必须大于 0，单价和件数须为非负数，税率须在 0 到 100 之间。'
    return
  }
  const previous = form.value.items[itemDraftIndex.value]
  const amountChanged = !previous || previous.amount !== item.amount || previous.totalAmount !== item.totalAmount
  if (itemDraftIndex.value === -1) {
    form.value.items.push({ ...item })
  } else {
    form.value.items[itemDraftIndex.value] = { ...item }
  }
  if (packagesChanged || itemDraftIndex.value === -1) syncPackages()
  if (amountChanged) syncOrderAmount()
  closeItemDialog()
}
const removeItem = index => {
  if (!props.editing || saving.value || (!props.creating && form.value.items.length === 1)) return
  form.value.items.splice(index, 1)
  syncPackages()
  syncOrderAmount()
}

watch(() => props.editing, async editing => {
  closeItemDialog()
  if (!editing) return
  form.value = createForm()
  errorMessage.value = ''
  if (unitsReady.value) return
  try {
    const response = await request({ url: '/products/units/measurements', method: 'GET' })
    if (!Array.isArray(response)) throw new Error('Invalid measurement units')
    units.value = response
    unitsReady.value = true
  } catch {
    errorMessage.value = '计量单位加载失败，请重新打开订单后再新增商品。'
  }
}, { immediate: true })
onBeforeUnmount(closeItemDialog)

const saveOrder = async () => {
  if (!props.editing || saving.value || itemDraft.value) return
  errorMessage.value = ''
  if (!form.value.contactPerson.trim() || !form.value.contactPhone.trim()) {
    errorMessage.value = '请填写收货人和收货电话。'
    return
  }
  if (!props.creating && Number(props.order.audit_state) === 1) {
    errorMessage.value = '已审核订单请先反审核再修改。'
    return
  }
  if (!props.order.customer_id || !props.order.store_id) {
    errorMessage.value = '订单缺少客户或门店信息，无法保存。'
    return
  }
  if (!form.value.items.length || form.value.items.some(item => !validItem(item))) {
    errorMessage.value = '请为每项商品选择商品、仓库并填写大于 0 的数量。'
    return
  }
  if (form.value.items.some(item => !validItemAmounts(item)) ||
    ['discountAmount', 'otherFees', 'currentPayment', 'totalPackages'].some(field => !Number.isFinite(Number(form.value[field])) || Number(form.value[field]) < 0)) {
    errorMessage.value = '金额、件数必须为非负数，税率必须在 0 到 100 之间。'
    return
  }
  saving.value = true
  try {
    // Keep creation local until this single final submission.
    const response = await request({
      url: props.creating ? '/orders' : `/orders/${props.order.id}`,
      method: props.creating ? 'POST' : 'PUT',
      data: {
        storeId: props.order.store_id,
        customerId: props.order.customer_id,
        warehouseId: props.order.warehouse_id,
        orderDate: (props.order.order_date || props.order.date || '').substring(0, 10),
        orderNumber: props.order.order_number,
        contactPerson: form.value.contactPerson,
        contactPhone: form.value.contactPhone,
        contactAddress: form.value.contactAddress,
        projectName: props.order.project_name || '',
        goodsPackaging: props.order.goods_packaging || '',
        logisticsService: props.order.logistics_service || '',
        salesPerson: props.order.sales_person || '',
        ...(props.creating ? { creator: props.order.creator || '' } : {}),
        orderRemark: form.value.orderRemark,
        settlementAccount: props.order.settlement_account || '',
        taxEnabled,
        taxRate: defaultTaxRate,
        discountAmount: number(form.value.discountAmount),
        otherFees: number(form.value.otherFees),
        currentPayment: number(form.value.currentPayment),
        totalPackages: number(form.value.totalPackages),
        items: form.value.items.map(item => ({
          productId: item.productId,
          goodsName: item.goodsName,
          spec: item.spec,
          unit: item.unit,
          warehouseId: item.warehouseId,
          packages: number(item.packages),
          quantity: number(item.quantity),
          price: number(item.price),
          taxRate: taxEnabled ? number(item.taxRate) : 0,
          taxIncludedPrice: taxEnabled ? number(item.taxIncludedPrice) : 0,
          amount: number(item.amount),
          totalAmount: taxEnabled ? number(item.totalAmount) : 0,
          remark: item.remark
        }))
      }
    })
    if (!response?.success || !response.data) throw new Error(response?.message || '订单保存失败，请重试。')
    emit('saved', response.data)
  } catch (error) {
    errorMessage.value = error.response?.data?.message || error.message || '订单保存失败，请重试。'
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.mobile-product-dialog-overlay {
  position: fixed;
  inset: 0;
  z-index: 100000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  background: rgba(15, 23, 42, 0.42);
}

.mobile-product-dialog {
  display: flex;
  width: 440px;
  max-width: 100%;
  max-height: calc(100dvh - 32px);
  min-width: 0;
  flex-direction: column;
  overflow: hidden;
  color: #2f3946;
  background: #fff;
  border: 1px solid #dfe5ec;
  border-radius: 7px;
  box-shadow: 0 12px 32px rgba(15, 23, 42, 0.16);
}

.product-dialog-header {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid #e5eaf0;
}

.product-dialog-header h3 {
  margin: 0;
  font-size: 16px;
}

.product-dialog-form {
  min-height: 0;
  overflow-y: auto;
  overscroll-behavior: contain;
}

.product-fields {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px 12px;
  padding: 16px;
}

label,
.product-field,
.item-amount {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 4px;
  color: #7a8492;
  font-size: 12px;
}

.full-width {
  grid-column: 1 / -1;
}

input,
select,
textarea {
  box-sizing: border-box;
  width: 100%;
  min-width: 0;
  min-height: 40px;
  padding: 8px;
  color: #2f3946;
  background: #fff;
  border: 1px solid var(--border, #dfe5ec);
  border-radius: 5px;
  font: inherit;
  font-size: 16px;
}

input[readonly] {
  color: #647086;
  background: #f7f9fb;
}

input:focus,
select:focus,
textarea:focus,
button:focus-visible {
  outline: 2px solid var(--accent, #0f9f78);
  outline-offset: 1px;
}

button {
  display: inline-flex;
  min-height: 40px;
  align-items: center;
  justify-content: center;
  gap: 5px;
  padding: 0 10px;
  border: 1px solid var(--border, #dfe5ec);
  border-radius: 5px;
  font: inherit;
  font-size: 14px;
  cursor: pointer;
}

button svg {
  width: 16px;
  height: 16px;
  flex: 0 0 auto;
}

button:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.product-combobox {
  position: relative;
  min-width: 0;
}

.product-search-control {
  position: relative;
}

.product-search-control input {
  padding-right: 40px;
  padding-left: 32px;
}

.product-search-icon {
  position: absolute;
  top: 12px;
  left: 10px;
  width: 16px;
  height: 16px;
  color: #7a8492;
  pointer-events: none;
}

.product-search-toggle {
  position: absolute;
  top: 1px;
  right: 1px;
  width: 38px;
  min-height: 38px;
  padding: 0;
  color: #647086;
  background: transparent;
  border: 0;
}

.product-search-options {
  position: absolute;
  top: calc(100% + 4px);
  right: 0;
  left: 0;
  z-index: 2;
  max-height: 220px;
  overflow-y: auto;
  overscroll-behavior: contain;
  background: #fff;
  border: 1px solid #dfe5ec;
  border-radius: 5px;
  box-shadow: 0 5px 16px rgba(15, 23, 42, 0.12);
}

.product-search-option {
  display: flex;
  width: 100%;
  min-height: 48px;
  flex-direction: column;
  align-items: flex-start;
  gap: 3px;
  padding: 9px 10px;
  color: #2f3946;
  text-align: left;
  background: #fff;
  border: 0;
  border-bottom: 1px solid #f0f2f4;
  border-radius: 0;
}

.product-search-option.is-active,
.product-search-option:hover {
  background: #edf8f4;
}

.product-option-name,
.product-option-detail {
  max-width: 100%;
  overflow-wrap: anywhere;
}

.product-option-detail {
  color: #7a8492;
  font-size: 12px;
}

.product-search-empty {
  padding: 16px 10px;
  color: #7a8492;
  text-align: center;
  font-size: 13px;
}

.dialog-close-button {
  width: 32px;
  min-height: 32px;
  padding: 0;
  color: #647086;
  background: #fff;
  border: 0;
}

.item-amount strong {
  padding-top: 9px;
  color: #2f3946;
  font-size: 15px;
  overflow-wrap: anywhere;
}

.save-error {
  margin: 12px;
  color: #b4232f;
  font-size: 13px;
  overflow-wrap: anywhere;
}

.product-dialog-actions {
  position: sticky;
  bottom: 0;
  display: flex;
  gap: 8px;
  padding: 12px;
  padding-bottom: max(12px, env(safe-area-inset-bottom));
  background: #fff;
  border-top: 1px solid #f0f2f4;
}

.cancel-button {
  flex: 1;
  color: #4b5563;
  background: #fff;
}

.confirm-item-button {
  flex: 2;
  color: #fff;
  background: #0f9f78;
  border-color: #0f9f78;
}
</style>
