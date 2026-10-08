<template>
  <Teleport to="body">
    <div class="sf-modal-layer" @click.self="!busy && $emit('close')" @keydown.esc="!busy && $emit('close')">
      <section class="supplier-finance-dialog" role="dialog" aria-modal="true" aria-labelledby="assignment-title">
        <header class="sf-header"><h2 id="assignment-title">采购审核 · {{ document?.documentNo }}</h2><button class="sf-button icon" :disabled="busy" title="关闭" aria-label="关闭" @click="$emit('close')"><X :size="18" /></button></header>
        <form @submit.prevent="assign">
        <div class="sf-dialog-body">
          <p v-if="error" class="sf-error" role="alert">{{ error }}</p>
          <div v-if="loading" class="sf-empty">加载中...</div>
          <template v-else-if="document">
            <div class="sf-summary"><span>入库日期<strong>{{ document.documentDate }}</strong></span><span>采购状态<strong>{{ settlementLabels[document.financialStatus] }}</strong></span><span>已确认应付<strong>{{ formatMoney(document.confirmedPayable) }}</strong></span></div>
            <label class="sf-field settlement-field">结算归属
              <select v-model="document.settlementType" :disabled="!canEdit"><option value="pending_supplier">供应商结算</option><option value="none">无需结算</option></select>
            </label>
            <div class="sf-table-scroll">
              <table class="sf-table assignment-table">
                <thead><tr><th>商品 / 批次</th><th>实收数量</th><th>采购单价</th><th>税率 (%)</th><th>未税金额</th><th>税额</th><th>含税金额</th><th>供应商</th><th>归属状态</th></tr></thead>
                <tbody><tr v-for="item in document.items" :key="item.id">
                  <td>{{ item.productName }}<div class="sf-muted">{{ item.batchNo }}</div></td>
                  <td class="sf-number">{{ item.receivedQty }} {{ item.unit }}</td>
                  <td><input v-model.number="item.unitPrice" type="number" min="0" step="0.0001" :required="requiresSupplier" :disabled="!canEdit" :aria-label="`${item.productName}采购单价`" /></td>
                  <td><input v-model.number="item.taxRate" type="number" min="0" max="100" step="0.01" :disabled="!canEdit" :aria-label="`${item.productName}税率`" /></td>
                  <td class="sf-number">{{ formatMoney(amounts(item).amount) }}</td><td class="sf-number">{{ formatMoney(amounts(item).taxAmount) }}</td><td class="sf-number">{{ formatMoney(amounts(item).taxIncludedAmount) }}</td>
                  <td><select v-model="item.supplierId" :required="requiresSupplier" :disabled="!canEdit || !requiresSupplier" :aria-label="`${item.productName}供应商`">
                    <option :value="null">请选择供应商</option>
                    <option v-if="item.supplierId && !suppliers.some(supplier => supplier.id === item.supplierId)" :value="item.supplierId">{{ item.supplierName || '历史供应商' }}</option>
                    <option v-for="supplier in suppliers" :key="supplier.id" :value="supplier.id">{{ supplier.supplierName }}</option>
                  </select></td>
                  <td>{{ item.payableTransactionId ? '应付已确认' : !requiresSupplier ? '无需结算' : item.supplierId && hasValue(item.unitPrice) ? '采购信息已补齐' : '待补采购信息' }}</td>
                </tr></tbody>
              </table>
            </div>
            <label class="sf-field settlement-field">结算备注<textarea v-model="document.settlementRemark" maxlength="500" :disabled="!canEdit" /></label>
          </template>
        </div>
        <footer class="sf-footer">
          <span>{{ document?.storeName }}</span>
          <div class="sf-actions">
            <button type="button" class="sf-button" :disabled="busy" @click="$emit('close')">关闭</button>
            <button v-if="user.hasPerm('admin.purchase.inbound.assign_supplier')" type="submit" class="sf-button" :disabled="!canEdit"><Save :size="16" />保存采购信息</button>
            <button v-if="user.hasPerm('admin.purchase.inbound.confirm_payable')" type="button" class="sf-button primary" :disabled="loading || busy || !canConfirm" @click="confirm"><Check :size="16" />{{ busy ? '处理中...' : '审核并确认应付' }}</button>
          </div>
        </footer>
        </form>
      </section>
    </div>
  </Teleport>
</template>
<script setup>
import { computed, onMounted, ref } from 'vue'
import { Check, Save, X } from '@lucide/vue'
import request from '@/api/request'
import { useUserStore } from '@/stores/user'
import { inboundAmounts } from '@/composables/documents/documentModels'
import { formatMoney, operationKey, settlementLabels } from '@/utils/supplierFinance'
import '@/assets/styles/supplier-finance.css'
const props = defineProps({ inboundId: { type: Number, required: true } })
const emit = defineEmits(['close', 'updated'])
const user = useUserStore()
const document = ref(null)
const suppliers = ref([])
const loading = ref(true)
const busy = ref(false)
const error = ref('')
const savedAssignments = ref('')
const hasValue = value => value !== '' && value != null
const requiresSupplier = computed(() => document.value?.settlementType === 'pending_supplier')
const posted = computed(() => ['reviewed', 'posted'].includes(document.value?.status))
const canEdit = computed(() => !loading.value && !busy.value && posted.value
  && document.value?.financialStatus !== 'payable_confirmed'
  && user.hasPerm('admin.purchase.inbound.assign_supplier'))
const assignmentSignature = () => JSON.stringify({
  settlementType: document.value?.settlementType,
  settlementRemark: document.value?.settlementRemark,
  items: document.value?.items.map(item => [item.id, item.supplierId, item.unitPrice, item.taxRate])
})
const canConfirm = computed(() => posted.value && document.value?.financialStatus === 'supplier_assigned' && savedAssignments.value === assignmentSignature())
const amounts = item => inboundAmounts({ quantity: item.receivedQty, price: item.unitPrice, taxRate: item.taxRate }, true)
async function load() {
  document.value = await request({ url: `/stock-inbounds/${props.inboundId}/settlement` })
  savedAssignments.value = assignmentSignature()
  const data = await request({ url: '/suppliers', params: { storeId: document.value.storeId, status: 'active' } })
  suppliers.value = Array.isArray(data) ? data : []
}
async function perform(action, data) {
  if (busy.value) return
  busy.value = true
  error.value = ''
  try {
    const result = await request({ url: `/stock-inbounds/${props.inboundId}/${action}`, method: 'POST', data: { version: document.value.version, idempotencyKey: operationKey(), ...data } })
    document.value = result.stockIn
    savedAssignments.value = assignmentSignature()
    emit('updated')
  } catch (err) { error.value = err.response?.data?.message || err.message }
  finally { busy.value = false }
}
function assign() {
  if (!canEdit.value) return
  if (requiresSupplier.value && document.value.items.some(item => !item.supplierId || !hasValue(item.unitPrice))) { error.value = '请为每条明细补齐供应商和采购单价'; return }
  return perform('assign-supplier', {
    settlementType: document.value.settlementType,
    settlementRemark: document.value.settlementRemark,
    items: document.value.items.map(item => ({
      inboundItemId: item.id, supplierId: requiresSupplier.value ? item.supplierId : null,
      unitPrice: hasValue(item.unitPrice) ? Number(item.unitPrice) : null, taxRate: Number(item.taxRate || 0)
    }))
  })
}
const confirm = () => canConfirm.value && perform('confirm-payable', {})
onMounted(async () => { try { await load() } catch (err) { error.value = err.response?.data?.message || err.message } finally { loading.value = false } })
</script>
<style scoped>
form { display: flex; flex-direction: column; min-height: 0; }
.settlement-field { margin: 14px 0; }
.assignment-table { min-width: 1160px; table-layout: fixed; }
.assignment-table th:first-child { width: 180px; }
.assignment-table th:nth-child(3) { width: 115px; }
.assignment-table th:nth-child(4) { width: 90px; }
.assignment-table th:nth-child(8) { width: 200px; }
.assignment-table input { width: 100%; min-width: 0; height: 32px; padding: 0 6px; border: 1px solid #d4dde3; border-radius: 4px; text-align: right; font: inherit; font-variant-numeric: tabular-nums; }
.assignment-table input:disabled { color: #596579; background: #f8fafb; }
@media (max-width: 780px) {
  .sf-footer, .sf-actions { flex-wrap: wrap; gap: 8px; }
}
</style>
