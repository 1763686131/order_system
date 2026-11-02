<template>
  <Teleport to="body">
    <div class="order-create-overlay" @click.self="emit('cancel')" @keydown.esc.stop.prevent="emit('cancel')">
      <section ref="dialogElement" class="order-create-dialog" role="dialog" aria-modal="true" aria-labelledby="order-create-title" tabindex="-1" @keydown.tab="keepDialogFocus">
        <header class="wizard-header">
          <div>
            <span class="wizard-step">新增订单 · {{ step }} / 2</span>
            <h3 id="order-create-title">{{ step === 1 ? '选择门店' : '选择客户和仓库' }}</h3>
          </div>
          <button type="button" class="close-button" aria-label="取消新增订单" title="取消" @click="emit('cancel')"><X aria-hidden="true" /></button>
        </header>
        <form class="wizard-form" @submit.prevent="nextStep">
          <div class="wizard-body">
            <template v-if="step === 1">
              <fieldset class="store-options">
                <legend class="sr-only">选择门店</legend>
                <label v-for="store in availableStores" :key="store.id" class="choice-option">
                  <input v-model="form.storeId" type="radio" name="create-store" :value="store.id" :aria-label="store.name" />
                  <strong>{{ store.name }}</strong>
                </label>
              </fieldset>
              <p v-if="!availableStores.length" class="empty-message" role="status">暂无可用门店，请确认门店状态和访问权限。</p>
            </template>
            <template v-else>
              <div class="selected-store">{{ selectedStore?.name }}</div>
              <p v-if="loading" class="empty-message" role="status">正在加载客户和单据信息...</p>
              <div v-if="loadError" class="load-error" role="alert">
                <span>{{ loadError }}</span>
                <button type="button" :disabled="loading" @click="loadOptions"><RefreshCw aria-hidden="true" />重试</button>
              </div>
              <div v-if="!loading && !loadError" class="customer-field">
                <label for="create-customer-search">客户</label>
                <div class="customer-search">
                  <Search aria-hidden="true" />
                  <input id="create-customer-search" v-model="customerSearch" type="search" autocomplete="off" aria-label="搜索客户" placeholder="搜索客户名称、联系人或电话" />
                </div>
                <fieldset class="customer-options">
                  <legend class="sr-only">选择客户</legend>
                  <label v-for="customer in filteredCustomers" :key="customer.id" class="choice-option">
                    <input v-model="form.customerId" type="radio" name="create-customer" :value="customer.id" :aria-label="customer.customerName || customer.name" />
                    <span>
                      <strong>{{ customer.customerName || customer.name }}</strong>
                      <small v-if="customer.contactPerson || customer.phone">{{ [customer.contactPerson, customer.phone].filter(Boolean).join(' · ') }}</small>
                    </span>
                  </label>
                </fieldset>
                <p v-if="!filteredCustomers.length" class="empty-message" role="status">{{ customerSearch ? '暂无匹配客户' : '该门店暂无客户，请先添加客户。' }}</p>
              </div>
              <label class="field">
                <span>仓库</span>
                <select v-model="form.warehouseId" aria-label="仓库" required>
                  <option value="">请选择仓库</option>
                  <option v-for="warehouse in availableWarehouses" :key="warehouse.id" :value="warehouse.id">{{ warehouse.name }}</option>
                </select>
              </label>
              <p v-if="!availableWarehouses.length" class="empty-message" role="status">该门店暂无可访问的仓库。</p>
              <details class="order-settings">
                <summary>单据信息</summary>
                <div class="settings-fields">
                  <label class="field"><span>订单日期</span><input v-model="form.orderDate" aria-label="订单日期" type="date" required /></label>
                  <label class="field"><span>项目名称</span><input v-model.trim="form.projectName" aria-label="项目名称" /></label>
                  <label class="field"><span>商品包装</span><input v-model.trim="form.packaging" aria-label="商品包装" list="create-packaging-options" /></label>
                  <datalist id="create-packaging-options"><option v-for="packaging in packagingOptions" :key="packaging" :value="packaging" /></datalist>
                  <label class="field">
                    <span>物流服务</span>
                    <select v-model="form.logisticsService" aria-label="物流服务"><option v-for="service in logisticsOptions" :key="service" :value="service">{{ service }}</option></select>
                  </label>
                  <label class="field">
                    <span>业务员</span>
                    <select v-model="form.salesPerson" aria-label="业务员"><option value="">未指定</option><option v-for="employee in salesPeople" :key="employee.id" :value="employee.displayName">{{ employee.displayName }}</option></select>
                  </label>
                  <label class="field">
                    <span>结算账户</span>
                    <select v-model="form.settlementAccount" aria-label="结算账户"><option value="">默认结算账户</option><option v-for="account in availableAccounts" :key="account.id || account.value || account.accountName" :value="account.value || account.accountName">{{ account.label || account.accountName || account.value }}</option></select>
                  </label>
                  <label class="tax-toggle"><input v-model="form.taxEnabled" aria-label="含税订单" type="checkbox" />含税订单</label>
                  <label v-if="form.taxEnabled" class="field"><span>税率 (%)</span><input v-model.number="form.taxRate" aria-label="订单税率" type="number" min="0" max="100" step="any" required inputmode="decimal" /></label>
                </div>
              </details>
              <p v-if="optionsWarning" class="options-warning" role="status">{{ optionsWarning }}</p>
            </template>
            <p v-if="validationError" class="validation-error" role="alert">{{ validationError }}</p>
          </div>
          <footer class="wizard-actions">
            <button type="button" class="secondary-button" @click="emit('cancel')">取消</button>
            <button v-if="step === 2" type="button" class="secondary-button back-button" @click="step = 1; validationError = ''"><ArrowLeft aria-hidden="true" />上一步</button>
            <button class="primary-button" type="submit" :disabled="step === 1 ? !selectedStore : loading || !!loadError || !selectedCustomer || !selectedWarehouse">
              {{ step === 1 ? '下一步' : '开始填写' }}<ArrowRight aria-hidden="true" />
            </button>
          </footer>
        </form>
      </section>
    </div>
  </Teleport>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ArrowLeft, ArrowRight, RefreshCw, Search, X } from '@lucide/vue'
import request from '@/api/request'
import { useUserStore } from '@/stores/user'
import { filterAccessibleOptions } from '@/utils/accessControl'

const props = defineProps({
  stores: { type: Array, default: () => [] },
  warehouses: { type: Array, default: () => [] }
})
const emit = defineEmits(['ready', 'cancel'])
const userStore = useUserStore()
const sameId = (left, right) => String(left) === String(right)
const step = ref(1)
const dialogElement = ref(null)
const loading = ref(false)
const loadError = ref('')
const optionsWarning = ref('')
const validationError = ref('')
const customers = ref([])
const accounts = ref([])
const employees = ref([])
const departments = ref([])
const customerSearch = ref('')
const logisticsOptions = ['送货上门+回单拍照回传', '送货上门+回单邮回', '送货上门', '用户自提', '无']
let defaults = {}
try {
  defaults = JSON.parse(localStorage.getItem('admin_order_form_default_selections') || '{}') || {}
} catch {
  // Invalid saved preferences must not block a new order.
}
const now = new Date()
const form = ref({
  storeId: '', customerId: '', warehouseId: '',
  orderDate: [now.getFullYear(), String(now.getMonth() + 1).padStart(2, '0'), String(now.getDate()).padStart(2, '0')].join('-'),
  projectName: '', packaging: String(defaults.packaging || '桶装'),
  logisticsService: logisticsOptions.includes(defaults.logisticsService) ? defaults.logisticsService : logisticsOptions[0],
  salesPerson: '', settlementAccount: '', taxEnabled: false, taxRate: 13
})
const availableStores = computed(() => filterAccessibleOptions(props.stores.filter(store => store.status === 'active'), userStore, 'store'))
const selectedStore = computed(() => availableStores.value.find(store => sameId(store.id, form.value.storeId)))
const availableWarehouses = computed(() => filterAccessibleOptions(props.warehouses, userStore, 'warehouse')
  .filter(warehouse => sameId(warehouse.storeId ?? warehouse.store_id, form.value.storeId)))
const selectedWarehouse = computed(() => availableWarehouses.value.find(warehouse => sameId(warehouse.id, form.value.warehouseId)))
const storeCustomers = computed(() => customers.value.filter(customer => sameId(customer.storeId ?? customer.store_id, form.value.storeId)))
const selectedCustomer = computed(() => storeCustomers.value.find(customer => sameId(customer.id, form.value.customerId)))
const filteredCustomers = computed(() => {
  const query = customerSearch.value.trim().toLocaleLowerCase()
  return storeCustomers.value.filter(customer => !query || [customer.customerName, customer.name, customer.contactPerson, customer.phone]
    .some(value => String(value || '').toLocaleLowerCase().includes(query)))
})
const availableAccounts = computed(() => accounts.value.filter(account => sameId(account.storeId ?? account.store_id, form.value.storeId)))
const salesPeople = computed(() => {
  const salesDepartments = new Set(departments.value.filter(department => department.name === '销售部').map(department => String(department.id)))
  return employees.value.filter(employee => employee.displayName && employee.departmentIds?.some(id => salesDepartments.has(String(id))))
})
const packagingOptions = computed(() => [...new Set(['无', '桶装', '纸箱', '托盘', '袋装', form.value.packaging].filter(Boolean))])
const setDefaultAccount = () => {
  const saved = defaults.settlementAccountsByStore?.[String(form.value.storeId)]
  if (saved === '' || availableAccounts.value.some(account => (account.value || account.accountName) === saved)) {
    form.value.settlementAccount = saved
    return
  }
  const account = availableAccounts.value.find(account => account.isDefault) || availableAccounts.value[0]
  form.value.settlementAccount = account?.value || account?.accountName || ''
}
watch(() => form.value.storeId, () => {
  form.value.customerId = ''
  form.value.warehouseId = ''
  customerSearch.value = ''
  validationError.value = ''
  setDefaultAccount()
})
const loadOptions = async () => {
  if (loading.value) return
  loading.value = true
  loadError.value = ''
  optionsWarning.value = ''
  try {
    const [customerData, accountData, directory] = await Promise.all([
      request({ url: '/customers', method: 'GET' }),
      request({ url: '/bank-accounts/options', method: 'GET' }).catch(() => {
        optionsWarning.value = '结算账户暂未加载，提交时使用门店默认账户。'
        return null
      }),
      request({ url: '/admin/directory', method: 'GET' }).catch(() => {
        optionsWarning.value = '业务员信息暂未加载，可稍后在完整订单页面修改。'
        return null
      })
    ])
    if (!Array.isArray(customerData)) throw new Error('客户数据加载失败，请重试。')
    customers.value = customerData
    accounts.value = Array.isArray(accountData?.data) ? accountData.data : Array.isArray(accountData?.items) ? accountData.items : []
    employees.value = Array.isArray(directory?.employees) ? directory.employees : []
    departments.value = Array.isArray(directory?.departments) ? directory.departments : []
    form.value.salesPerson = salesPeople.value.some(employee => employee.displayName === defaults.salesPerson) ? defaults.salesPerson : ''
    setDefaultAccount()
  } catch (error) {
    loadError.value = error.response?.data?.message || error.message || '客户数据加载失败，请重试。'
  } finally {
    loading.value = false
  }
}
const nextStep = async () => {
  validationError.value = ''
  if (!selectedStore.value) {
    validationError.value = '请选择可访问的门店。'
    return
  }
  if (step.value === 1) {
    step.value = 2
    await nextTick()
    dialogElement.value?.focus({ preventScroll: true })
    return
  }
  if (loading.value || loadError.value || !selectedCustomer.value || !selectedWarehouse.value) {
    validationError.value = '请选择该门店的客户和仓库。'
    return
  }
  if (!form.value.orderDate || (form.value.taxEnabled && (!Number.isFinite(Number(form.value.taxRate)) || form.value.taxRate < 0 || form.value.taxRate > 100))) {
    validationError.value = '请填写订单日期，税率须在 0 到 100 之间。'
    return
  }
  emit('ready', {
    store: selectedStore.value, customer: selectedCustomer.value, warehouse: selectedWarehouse.value,
    ...form.value, taxRate: form.value.taxEnabled ? Number(form.value.taxRate) : 0
  })
}
const keepDialogFocus = event => {
  const controls = [...(dialogElement.value?.querySelectorAll('button:not(:disabled), input:not(:disabled), select:not(:disabled), summary') || [])]
    .filter(element => element.getClientRects().length)
  const first = controls[0]
  const last = controls.at(-1)
  if ((event.shiftKey && (document.activeElement === first || document.activeElement === dialogElement.value)) ||
      (!event.shiftKey && (document.activeElement === last || document.activeElement === dialogElement.value))) {
    event.preventDefault()
    const target = event.shiftKey ? last : first
    target?.focus()
  }
}
let previousOverflow
let trigger
onMounted(() => {
  trigger = document.activeElement
  previousOverflow = document.body.style.overflow
  document.body.style.overflow = 'hidden'
  dialogElement.value?.focus({ preventScroll: true })
  loadOptions()
})
onBeforeUnmount(() => {
  document.body.style.overflow = previousOverflow
  if (trigger?.isConnected) trigger.focus({ preventScroll: true })
})
</script>

<style scoped>
.order-create-overlay {
  position: fixed;
  inset: 0;
  z-index: 100000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  background: rgba(15, 23, 42, 0.42);
}
.order-create-dialog {
  display: flex;
  flex-direction: column;
  width: 440px;
  max-width: 100%;
  max-height: calc(100dvh - 32px);
  min-width: 0;
  overflow: hidden;
  color: #2f3946;
  background: #fff;
  border: 1px solid #dfe5ec;
  border-radius: 7px;
  box-shadow: 0 12px 32px rgba(15, 23, 42, 0.16);
  outline: none;
}
.wizard-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 16px; border-bottom: 1px solid #e5eaf0; }
.wizard-header h3 { margin: 5px 0 0; font-size: 17px; }
.wizard-step, .selected-store { color: #647086; font-size: 12px; }
.selected-store { padding-bottom: 2px; }
.wizard-form { display: flex; min-height: 0; flex-direction: column; }
.wizard-body { display: flex; min-height: 0; flex-direction: column; gap: 14px; padding: 16px; overflow-y: auto; overscroll-behavior: contain; }
.store-options, .customer-options { display: flex; min-width: 0; flex-direction: column; gap: 0; margin: 0; padding: 0; border: 1px solid #dfe5ec; border-radius: 5px; }
.store-options { max-height: 300px; overflow-y: auto; }
.customer-options { max-height: 170px; overflow-y: auto; overscroll-behavior: contain; }
.choice-option { display: flex; flex: 0 0 auto; align-items: center; gap: 10px; min-height: 46px; padding: 10px; border-bottom: 1px solid #eef1f4; cursor: pointer; }
.choice-option:last-child { border-bottom: 0; }
.choice-option:has(input:checked) { background: #edf8f4; }
.choice-option > span { display: flex; min-width: 0; flex-direction: column; gap: 4px; }
.choice-option strong { font-size: 14px; font-weight: 500; overflow-wrap: anywhere; }
.choice-option small { color: #647086; font-size: 12px; overflow-wrap: anywhere; }
.choice-option input, .tax-toggle input { width: 16px; height: 16px; flex: 0 0 auto; margin: 0; accent-color: #0f9f78; }
.customer-field, .field { display: flex; min-width: 0; flex-direction: column; gap: 6px; font-size: 13px; }
.customer-search { position: relative; }
.customer-search > svg { position: absolute; top: 13px; left: 10px; width: 16px; height: 16px; color: #7a8492; pointer-events: none; }
input:not([type="radio"]):not([type="checkbox"]), select { box-sizing: border-box; width: 100%; min-width: 0; min-height: 42px; padding: 8px; color: #2f3946; background: #fff; border: 1px solid #dfe5ec; border-radius: 5px; font: inherit; font-size: 16px; }
.customer-search input[type="search"] { padding-left: 33px; }
input:focus-visible, select:focus-visible, button:focus-visible, summary:focus-visible { outline: 2px solid #0f9f78; outline-offset: 1px; }
.order-settings { min-width: 0; border-top: 1px solid #e5eaf0; padding-top: 12px; font-size: 13px; }
.order-settings summary { min-height: 28px; cursor: pointer; }
.settings-fields { display: flex; flex-direction: column; gap: 12px; padding-top: 8px; }
.tax-toggle { display: flex; align-items: center; gap: 8px; min-height: 36px; }
.wizard-actions { display: flex; flex: 0 0 auto; gap: 8px; padding: 12px; padding-bottom: max(12px, env(safe-area-inset-bottom)); border-top: 1px solid #e5eaf0; }
.wizard-actions button { white-space: nowrap; }
button { display: inline-flex; align-items: center; justify-content: center; gap: 4px; min-width: 0; min-height: 40px; padding: 8px 10px; border: 1px solid #dfe5ec; border-radius: 5px; font: inherit; font-size: 14px; cursor: pointer; }
button svg { width: 16px; height: 16px; flex: 0 0 auto; }
button:disabled { opacity: 0.5; cursor: not-allowed; }
.close-button { width: 32px; min-height: 32px; padding: 0; color: #647086; background: #fff; border: 0; }
.primary-button { flex: 1.3; color: #fff; background: #0f9f78; border-color: #0f9f78; }
.secondary-button { flex: 1; color: #4b5563; background: #fff; }
.back-button { flex: 1.2; }
.empty-message { margin: 0; color: #7a8492; font-size: 13px; line-height: 1.6; }
.load-error { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.load-error, .validation-error { margin: 0; color: #b4232f; font-size: 13px; overflow-wrap: anywhere; }
.load-error button { flex: 0 0 auto; color: #4b5563; background: #fff; }
.options-warning { margin: 0; color: #8c641c; font-size: 12px; line-height: 1.6; }
.sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0, 0, 0, 0); }
@media (max-width: 360px) {
  .wizard-actions button { padding-right: 6px; padding-left: 6px; font-size: 13px; }
}
</style>
