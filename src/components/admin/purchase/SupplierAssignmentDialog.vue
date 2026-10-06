<template>
  <Teleport to="body">
    <div class="sf-modal-layer" @click.self="!busy && $emit('close')" @keydown.esc="!busy && $emit('close')">
      <section class="supplier-finance-dialog" role="dialog" aria-modal="true" aria-labelledby="assignment-title">
        <header class="sf-header"><h2 id="assignment-title">供应商归属确认 · {{ document?.documentNo }}</h2><button class="sf-button icon" :disabled="busy" title="关闭" aria-label="关闭" @click="$emit('close')"><X :size="18" /></button></header>
        <div class="sf-dialog-body">
          <p v-if="error" class="sf-error" role="alert">{{ error }}</p>
          <div v-if="loading" class="sf-empty">加载中...</div>
          <template v-else-if="document">
            <div class="sf-summary"><span>入库日期<strong>{{ document.documentDate }}</strong></span><span>财务状态<strong>{{ settlementLabels[document.financialStatus] }}</strong></span><span>已确认应付<strong>{{ formatMoney(document.confirmedPayable) }}</strong></span></div>
            <div class="sf-table-scroll">
              <table class="sf-table">
                <thead><tr><th>商品 / 批次</th><th>实收数量</th><th>未税金额</th><th>税额</th><th>含税金额</th><th style="width: 220px">供应商</th><th>归属状态</th></tr></thead>
                <tbody><tr v-for="item in document.items" :key="item.id"><td>{{ item.productName }}<div class="sf-muted">{{ item.batchNo }}</div></td><td>{{ item.receivedQty }} {{ item.unit }}</td><td class="sf-number">{{ formatMoney(Number(item.totalAmount) - Number(item.taxAmount)) }}</td><td class="sf-number">{{ formatMoney(item.taxAmount) }}</td><td class="sf-number">{{ formatMoney(item.totalAmount) }}</td><td><select v-model="item.supplierId" :disabled="busy || Boolean(item.payableTransactionId) || !user.hasPerm('admin.purchase.inbound.assign_supplier')" :aria-label="`${item.productName}供应商`"><option :value="null">请选择供应商</option><option v-for="supplier in suppliers" :key="supplier.id" :value="supplier.id">{{ supplier.supplierName }}</option></select></td><td>{{ item.payableTransactionId ? '应付已确认' : item.supplierAssignedAt ? '已补供应商' : '待补供应商' }}</td></tr></tbody>
              </table>
            </div>
            <label class="sf-field" style="margin-top: 14px">结算备注<textarea v-model="document.settlementRemark" maxlength="500" :disabled="busy || document.financialStatus === 'payable_confirmed'" /></label>
          </template>
        </div>
        <footer class="sf-footer">
          <span>{{ document?.storeName }}</span>
          <div class="sf-actions">
            <button class="sf-button" :disabled="busy" @click="$emit('close')">取消</button>
            <button v-if="user.hasPerm('admin.purchase.inbound.assign_supplier')" class="sf-button" :disabled="loading || busy || document?.financialStatus === 'payable_confirmed'" @click="assign"><Save :size="16" />保存供应商归属</button>
            <button v-if="user.hasPerm('admin.purchase.inbound.confirm_payable')" class="sf-button primary" :disabled="loading || busy || !canConfirm" @click="confirm"><Check :size="16" />{{ busy ? '处理中...' : '确认应付' }}</button>
          </div>
        </footer>
      </section>
    </div>
  </Teleport>
</template>
<script setup>
import { computed, onMounted, ref } from 'vue'
import { Check, Save, X } from '@lucide/vue'
import request from '@/api/request'
import { useUserStore } from '@/stores/user'
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
const assignmentSignature = () => JSON.stringify(document.value?.items.map(item => [item.id, item.supplierId]))
const canConfirm = computed(() => document.value?.financialStatus === 'supplier_assigned' && savedAssignments.value === assignmentSignature())
async function load() {
  document.value = await request({ url: `/stock-inbounds/${props.inboundId}/settlement` })
  savedAssignments.value = assignmentSignature()
  const data = await request({ url: '/suppliers', params: { storeId: document.value.storeId, status: 'active' } })
  suppliers.value = Array.isArray(data) ? data : []
}
async function perform(action, data) {
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
  if (document.value.items.some(item => !item.supplierId)) { error.value = '请为每条明细选择供应商'; return }
  return perform('assign-supplier', { items: document.value.items.map(item => ({ inboundItemId: item.id, supplierId: item.supplierId })), settlementRemark: document.value.settlementRemark })
}
const confirm = () => perform('confirm-payable', {})
onMounted(async () => { try { await load() } catch (err) { error.value = err.response?.data?.message || err.message } finally { loading.value = false } })
</script>
