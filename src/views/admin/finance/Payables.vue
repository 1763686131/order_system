<template>
  <section class="supplier-finance-page">
    <header class="sf-header"><h1>供应商应付账款</h1><div class="sf-actions"><button v-if="user.hasPerm('admin.finance.payable.initial')" class="sf-button" @click="openInitial"><Plus :size="16" />录入期初</button><button class="sf-button icon" title="刷新" aria-label="刷新" :disabled="loading" @click="load"><RefreshCw :size="18" /></button></div></header>
    <form class="sf-toolbar" @submit.prevent="load"><label class="sf-field">供应商<input v-model.trim="filters.keyword" type="search" /></label><label class="sf-field">门店<select v-model="filters.storeId"><option value="">全部授权门店</option><option v-for="store in stores" :key="store.id" :value="store.id">{{ store.name }}</option></select></label><label class="sf-field">截止日期<input v-model="filters.asOf" type="date" /></label><label class="sf-field">账龄<select v-model="filters.aging"><option value="">全部</option><option value="0-30">0-30 天</option><option value="31-60">31-60 天</option><option value="61-90">61-90 天</option><option value="90+">90 天以上</option></select></label><button class="sf-button primary" :disabled="loading"><Search :size="16" />查询</button></form>
    <p v-if="error" class="sf-error" role="alert">{{ error }}</p>
    <div class="sf-summary"><span>应付余额<strong>{{ formatMoney(total('payableBalance')) }}</strong></span><span>供应商预付款<strong>{{ formatMoney(total('prepaymentBalance')) }}</strong></span><span>供应商贷项<strong>{{ formatMoney(total('creditBalance')) }}</strong></span><span>净结算额<strong>{{ formatMoney(total('netSettlement')) }}</strong></span></div>
    <div class="sf-table-scroll"><table class="sf-table" style="min-width: 1200px"><thead><tr><th>供应商</th><th>已确认应付</th><th>已核销</th><th>未付应付</th><th>已开票</th><th>未开票</th><th>预付款</th><th>贷项</th><th>付款状态</th><th>结算操作</th></tr></thead><tbody><tr v-if="loading"><td colspan="10" class="sf-empty">加载中...</td></tr><tr v-else-if="!records.length"><td colspan="10" class="sf-empty">暂无供应商账务记录</td></tr><tr v-for="row in records" :key="row.supplierId"><td>{{ row.supplierName }}<div class="sf-muted">{{ row.supplierCode }}</div></td><td class="sf-number">{{ formatMoney(row.confirmedPayable) }}</td><td class="sf-number">{{ formatMoney(row.allocatedAmount) }}</td><td class="sf-number">{{ formatMoney(row.payableBalance) }}</td><td class="sf-number">{{ formatMoney(row.billedAmount) }}</td><td class="sf-number">{{ formatMoney(row.unbilledAmount) }}</td><td class="sf-number">{{ formatMoney(row.prepaymentBalance) }}</td><td class="sf-number">{{ formatMoney(row.creditBalance) }}</td><td>{{ paymentLabels[row.paymentStatus] }}<div v-if="row.hasAvailableBalance" class="sf-muted">有可用供应商余额</div></td><td><div class="sf-actions"><button v-if="user.hasPerm('admin.finance.supplier_statement.read')" class="sf-link" @click="router.push({ name: 'admin-supplier-statement', params: { supplierId: row.supplierId }, query: { storeId: filters.storeId || undefined } })">对账明细</button><button v-if="canAllocate" class="sf-button icon" title="余额核销及记录" aria-label="余额核销及记录" @click="balanceSupplier = row"><WalletCards :size="16" /></button></div></td></tr></tbody></table></div>
    <SupplierBalanceDialog v-if="balanceSupplier" :supplier="balanceSupplier" :stores="stores" :default-store="filters.storeId || route.query.storeId || ''" @close="closeBalance" @updated="load" />
    <Teleport to="body"><div v-if="initialOpen" class="sf-modal-layer" @click.self="!saving && (initialOpen = false)"><form class="supplier-finance-dialog" style="max-width: 620px" @submit.prevent="saveInitial" role="dialog" aria-modal="true" aria-label="供应商期初余额"><header class="sf-header"><h2>录入供应商期初余额</h2><button type="button" class="sf-button icon" :disabled="saving" title="关闭" @click="initialOpen = false"><X :size="18" /></button></header><div class="sf-dialog-body"><p v-if="initialError" class="sf-error" role="alert">{{ initialError }}</p><div class="sf-form-grid"><label class="sf-field">供应商<select v-model="initial.supplierId" required><option value="">请选择</option><option v-for="row in suppliers" :key="row.id" :value="row.id">{{ row.supplierName }}</option></select></label><label class="sf-field">门店<select v-model="initial.storeId" required><option value="">请选择</option><option v-for="store in stores" :key="store.id" :value="store.id">{{ store.name }}</option></select></label><label class="sf-field">业务日期<input v-model="initial.businessDate" type="date" required /></label><label v-for="field in initialFields" :key="field.key" class="sf-field">{{ field.label }}<input v-model.number="initial[field.key]" type="number" min="0" step="0.01" required /></label><label class="sf-field wide">备注<textarea v-model="initial.remark" maxlength="500" /></label></div></div><footer class="sf-footer"><span /><button class="sf-button primary" :disabled="saving"><Check :size="16" />{{ saving ? '保存中...' : '确认录入' }}</button></footer></form></div></Teleport>
  </section>
</template>
<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Check, Plus, RefreshCw, Search, WalletCards, X } from '@lucide/vue'
import request from '@/api/request'
import { useUserStore } from '@/stores/user'
import { localDate } from '@/composables/documents/documentModels'
import { formatMoney, operationKey, paymentLabels } from '@/utils/supplierFinance'
import SupplierBalanceDialog from '@/components/admin/purchase/SupplierBalanceDialog.vue'
import '@/assets/styles/supplier-finance.css'
const user = useUserStore()
const router = useRouter()
const route = useRoute()
const canAllocate = user.hasPerm('admin.route.finance.payables')
const balanceSupplier = ref(null)
const records = ref([])
const stores = ref([])
const suppliers = ref([])
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const initialError = ref('')
const initialOpen = ref(false)
const filters = reactive({ keyword: '', storeId: '', asOf: '', aging: '' })
const initial = reactive({})
const initialFields = [{ key: 'payableAmount', label: '期初应付' }, { key: 'prepaymentAmount', label: '期初预付款' }, { key: 'creditAmount', label: '期初贷项' }]
const total = key => records.value.reduce((sum, row) => sum + Number(row[key] || 0), 0)
async function load() {
  loading.value = true; error.value = ''
  try { records.value = await request({ url: '/suppliers/payables', params: filters }) }
  catch (err) { error.value = err.response?.data?.message || err.message }
  finally { loading.value = false }
}
function openInitial() { Object.assign(initial, { supplierId: '', storeId: '', businessDate: localDate(), payableAmount: 0, prepaymentAmount: 0, creditAmount: 0, remark: '', idempotencyKey: operationKey() }); initialError.value = ''; initialOpen.value = true }
async function saveInitial() {
  saving.value = true; initialError.value = ''
  try { await request({ url: `/suppliers/${initial.supplierId}/initial-balances`, method: 'POST', data: initial }); initialOpen.value = false; await load() }
  catch (err) { initialError.value = err.response?.data?.message || err.message }
  finally { saving.value = false }
}
function closeBalance() {
  balanceSupplier.value = null
  if (route.query.balanceSupplierId) {
    const query = { ...route.query }
    delete query.balanceSupplierId
    router.replace({ query })
  }
}
onMounted(async () => {
  try {
    const options = await request.get('/supplier-finance/options')
    stores.value = options.stores
    suppliers.value = options.suppliers
  }
  catch (err) { error.value = err.response?.data?.message || err.message }
  await load()
  if (canAllocate && route.query.balanceSupplierId) {
    balanceSupplier.value = records.value.find(row => row.supplierId === Number(route.query.balanceSupplierId)) || null
  }
})
</script>
