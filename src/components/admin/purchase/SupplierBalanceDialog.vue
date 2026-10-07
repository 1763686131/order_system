<template>
  <Teleport to="body">
    <div class="sf-modal-layer" @click.self="!saving && emit('close')">
      <section class="supplier-finance-dialog" role="dialog" aria-modal="true" aria-label="供应商余额核销">
        <header class="sf-header"><h2>{{ supplier.supplierName }} · 余额核销</h2><button class="sf-button icon" title="关闭" aria-label="关闭" :disabled="saving" @click="emit('close')"><X :size="18" /></button></header>
        <div class="sf-dialog-body">
          <p v-if="error" class="sf-error" role="alert">{{ error }}</p>
          <form class="sf-toolbar" @submit.prevent="load">
            <fieldset class="sf-inline-fields" :disabled="saving || loading">
            <label class="sf-field">门店<select v-model="storeId" required @change="reset"><option value="">请选择</option><option v-for="store in stores" :key="store.id" :value="store.id">{{ store.name }}</option></select></label>
            <label v-if="canPrepay || canCredit" class="sf-field">余额类型<select v-model="kind" @change="reset"><option v-if="canPrepay" value="prepayments">供应商预付款</option><option v-if="canCredit" value="credits">供应商贷项</option></select></label>
            <button class="sf-button" :disabled="loading || !storeId"><RefreshCw :size="16" />查询</button>
            </fieldset>
          </form>
          <form v-if="canPrepay || canCredit" id="supplier-balance-form" @submit.prevent="allocate">
            <fieldset class="sf-plain-fieldset" :disabled="saving || loading">
            <div class="sf-form-grid">
              <label class="sf-field wide">余额来源<select v-model="sourceId" required @change="allocations = []"><option value="">请选择</option><option v-for="source in sources" :key="source.id" :value="source.id">{{ source.documentNo }} · 可用 {{ formatMoney(source.availableAmount) }}</option></select></label>
              <label class="sf-field">业务日期<input v-model="date" type="date" required /></label>
              <label class="sf-field wide">未开票核销原因<textarea v-model="unbilledReason" maxlength="500" /></label>
              <label v-if="user.hasPerm('admin.finance.supplier_payment.invoice_override')" class="sf-check wide"><input v-model="invoiceOverride" type="checkbox" />财务豁免见票付款</label>
              <label class="sf-field wide">备注<textarea v-model="remark" maxlength="500" /></label>
            </div>
            <div class="sf-header sf-section-title"><h3>应付核销明细</h3></div>
            <PayableAllocationTable v-model="allocations" :sources="payables" :loading="loading" />
            <div class="sf-summary"><span>来源可用余额<strong>{{ formatMoney(selectedSource?.availableAmount) }}</strong></span><span>本次核销<strong>{{ formatMoney(total) }}</strong></span></div>
            </fieldset>
          </form>
          <div class="sf-header sf-section-title"><h3>余额核销记录</h3></div>
          <div class="sf-table-scroll"><table class="sf-table"><thead><tr><th>核销单号</th><th>余额类型</th><th>业务日期</th><th>核销金额</th><th>状态</th><th>操作人</th><th>操作</th></tr></thead><tbody><tr v-if="!history.length"><td colspan="7" class="sf-empty">暂无余额核销记录</td></tr><tr v-for="row in history" :key="row.id"><td><button class="sf-link" @click="selectedHistory = row">{{ row.documentNo }}</button></td><td>{{ row.kind === 'prepayment' ? '预付款' : '贷项' }}</td><td>{{ row.businessDate }}</td><td class="sf-number">{{ formatMoney(row.amount) }}</td><td>{{ row.status === 'audited' ? '已核销' : '已撤销' }}</td><td>{{ row.createdBy }}</td><td><button v-if="row.status === 'audited' && user.hasPerm(`admin.finance.supplier_${row.kind}.allocate`)" class="sf-button icon danger" title="撤销核销" aria-label="撤销核销" :disabled="saving" @click="pendingReverse = row"><RotateCcw :size="16" /></button></td></tr></tbody></table></div>
          <template v-if="selectedHistory">
            <div class="sf-header sf-section-title"><h3>{{ selectedHistory.documentNo }} · 核销明细</h3><button class="sf-button icon" title="收起明细" aria-label="收起明细" @click="selectedHistory = null"><X :size="16" /></button></div>
            <p class="sf-muted">余额来源：{{ selectedHistory.sourceDocumentNo }} · {{ selectedHistory.auditedAt }} · {{ selectedHistory.createdBy }}</p>
            <p v-if="selectedHistory.unbilledReason">未开票核销原因：{{ selectedHistory.unbilledReason }}</p>
            <p v-if="selectedHistory.invoiceOverride">财务豁免见票付款</p>
            <p v-if="selectedHistory.remark">备注：{{ selectedHistory.remark }}</p>
            <PayableAllocationTable :model-value="selectedHistory.allocations" readonly />
          </template>
        </div>
        <footer class="sf-footer"><button class="sf-button" :disabled="saving" @click="emit('close')">关闭</button><button v-if="canPrepay || canCredit" form="supplier-balance-form" class="sf-button primary" :disabled="saving || loading || !selectedSource || total <= 0 || total > selectedSource.availableAmount"><Check :size="16" />{{ saving ? '处理中...' : '确认余额核销' }}</button></footer>
      </section>
    </div>
    <div v-if="pendingReverse" class="sf-modal-layer sf-confirm-layer"><section class="supplier-finance-dialog sf-confirm-dialog" role="dialog" aria-modal="true" aria-label="撤销余额核销"><header class="sf-header"><h2>撤销余额核销</h2></header><div class="sf-dialog-body"><p>将冲销 {{ pendingReverse.documentNo }}，恢复应付和可用供应商余额。银行余额不变。</p></div><footer class="sf-footer"><button class="sf-button" :disabled="saving" @click="pendingReverse = null">取消</button><button class="sf-button danger" :disabled="saving" @click="reverse">确认撤销</button></footer></section></div>
  </Teleport>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { Check, RefreshCw, RotateCcw, X } from '@lucide/vue'
import request from '@/api/request'
import { useUserStore } from '@/stores/user'
import { localDate } from '@/composables/documents/documentModels'
import { formatMoney, operationKey, sumMoney } from '@/utils/supplierFinance'
import PayableAllocationTable from './PayableAllocationTable.vue'
const props = defineProps({ supplier: { type: Object, required: true }, stores: { type: Array, required: true }, defaultStore: { type: [String, Number], default: '' } })
const emit = defineEmits(['close', 'updated'])
const user = useUserStore()
const canPrepay = user.hasPerm('admin.finance.supplier_prepayment.allocate')
const canCredit = user.hasPerm('admin.finance.supplier_credit.allocate')
const kind = ref(canPrepay ? 'prepayments' : 'credits')
const storeId = ref(props.defaultStore || props.supplier.storeId || '')
const date = ref(localDate())
const sourceId = ref('')
const sources = ref([])
const payables = ref([])
const allocations = ref([])
const history = ref([])
const selectedHistory = ref(null)
const remark = ref('')
const unbilledReason = ref('')
const invoiceOverride = ref(false)
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const pendingReverse = ref(null)
const key = ref(operationKey())
const selectedSource = computed(() => sources.value.find(row => Number(row.id) === Number(sourceId.value)))
const total = computed(() => sumMoney(allocations.value, 'amount'))
function reset() { sourceId.value = ''; allocations.value = []; selectedHistory.value = null; key.value = operationKey(); load() }
async function load() {
  if (!storeId.value) return
  loading.value = true
  error.value = ''
  try {
    const params = { storeId: storeId.value }
    const [balance, debts, records] = await Promise.all([
      request.get(`/suppliers/${props.supplier.supplierId}/${kind.value}/allocatable`, { params }),
      request.get(`/suppliers/${props.supplier.supplierId}/payables/allocatable`, { params }),
      request.get('/supplier-balance-allocations', { params: { ...params, supplierId: props.supplier.supplierId } })
    ])
    sources.value = balance.items; payables.value = debts.items; history.value = records.items
    if (selectedHistory.value) selectedHistory.value = history.value.find(row => row.id === selectedHistory.value.id) || null
    if (sourceId.value && !selectedSource.value) { sourceId.value = ''; allocations.value = [] }
  } catch (err) { error.value = err.response?.data?.message || err.message }
  finally { loading.value = false }
}
async function allocate() {
  saving.value = true
  error.value = ''
  try {
    await request.post(`/suppliers/${props.supplier.supplierId}/${kind.value}/${sourceId.value}/allocate`, {
      version: selectedSource.value.version, businessDate: date.value, unbilledReason: unbilledReason.value,
      invoiceOverride: invoiceOverride.value, remark: remark.value, idempotencyKey: key.value,
      allocations: allocations.value.filter(row => Number(row.amount) > 0)
    })
    sourceId.value = ''; allocations.value = []; key.value = operationKey(); emit('updated'); await load()
  } catch (err) { error.value = err.response?.data?.message || err.message }
  finally { saving.value = false }
}
async function reverse() {
  saving.value = true
  try {
    await request.post(`/supplier-balance-allocations/${pendingReverse.value.id}/reverse`, { version: pendingReverse.value.version, idempotencyKey: operationKey() })
    pendingReverse.value = null; emit('updated'); await load()
  } catch (err) { pendingReverse.value = null; error.value = err.response?.data?.message || err.message }
  finally { saving.value = false }
}
onMounted(load)
</script>
