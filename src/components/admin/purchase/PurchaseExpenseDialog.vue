<template>
  <Teleport to="body"><div class="sf-modal-layer" @click.self="!busy && $emit('close')">
    <section class="supplier-finance-dialog" role="dialog" aria-modal="true" aria-labelledby="expense-title">
      <header class="sf-header"><h2 id="expense-title">采购费用归属</h2><button class="sf-button icon" :disabled="busy" title="关闭" aria-label="关闭" @click="$emit('close')"><X :size="18" /></button></header>
      <div class="sf-dialog-body">
        <p v-if="error" class="sf-error" role="alert">{{ error }}</p>
        <div v-if="loading" class="sf-empty">加载中...</div>
        <template v-else>
          <form v-if="user.hasPerm('admin.purchase.expense.create')" class="sf-form-grid" @submit.prevent="save">
            <label class="sf-field wide">实际入库批次 / 商品<select v-model="form.inboundItemId" required><option value="">请选择未审核入库商品</option><option v-for="item in sourceItems" :key="item.id" :value="item.id">{{ item.documentDate }} · {{ item.productName }} · {{ item.batchNo }} · {{ item.supplierName }}</option></select></label>
            <label class="sf-field">费用类型<select v-model="form.expenseType"><option>运费</option><option>包装费</option><option>加工费</option><option>其它费用</option></select></label>
            <label class="sf-field">未税金额<input v-model.number="form.amountExcludingTax" type="number" min="0" step="0.01" required /></label>
            <label class="sf-field">税额<input v-model.number="form.taxAmount" type="number" min="0" step="0.01" required /></label>
            <label><input v-model="form.includeInPayable" type="checkbox" />计入供应商应付</label>
            <label><input v-model="form.includeInInventoryCost" type="checkbox" />计入库存成本</label>
            <span>价税合计 {{ formatMoney(Number(form.amountExcludingTax) + Number(form.taxAmount)) }}</span>
            <label class="sf-field wide">备注<input v-model="form.remark" maxlength="500" /></label>
            <div class="sf-actions wide"><button type="submit" class="sf-button primary" :disabled="busy || !sourceItems.length"><Save :size="16" />保存费用草稿</button></div>
          </form>
          <div class="sf-table-scroll" style="margin-top: 14px"><table class="sf-table"><thead><tr><th>费用 / 商品</th><th>供应商</th><th>未税金额</th><th>税额</th><th>含税金额</th><th>归属</th><th>状态</th><th style="width: 170px">操作</th></tr></thead><tbody><tr v-if="!expenses.length"><td colspan="8" class="sf-empty">暂无已归属费用</td></tr><tr v-for="line in expenses" :key="line.id"><td>{{ line.expenseType }}<div class="sf-muted">{{ orderItems.find(item => item.orderItemId === line.purchaseOrderItemId)?.productName }}</div></td><td>{{ orderItems.find(item => item.orderItemId === line.purchaseOrderItemId)?.supplierName }}</td><td class="sf-number">{{ formatMoney(line.amountExcludingTax) }}</td><td class="sf-number">{{ formatMoney(line.taxAmount) }}</td><td class="sf-number">{{ formatMoney(line.amountIncludingTax) }}</td><td>{{ [line.includeInPayable ? '应付' : '', line.includeInInventoryCost ? '库存成本' : ''].filter(Boolean).join('、') || '备注' }}</td><td>{{ line.status === 'confirmed' ? '已确认' : '草稿' }}</td><td><div class="sf-actions"><button v-if="user.hasPerm('admin.purchase.expense.confirm')" class="sf-button icon" :disabled="busy || !isDraftBatch(line)" :title="line.status === 'confirmed' ? '撤销费用确认' : '确认费用归属'" :aria-label="line.status === 'confirmed' ? '撤销费用确认' : '确认费用归属'" @click="toggleConfirm(line)"><Undo2 v-if="line.status === 'confirmed'" :size="16" /><Check v-else :size="16" /></button><button v-if="line.status === 'draft' && user.hasPerm('admin.purchase.expense.delete')" class="sf-button icon danger" :disabled="busy" title="删除费用草稿" aria-label="删除费用草稿" @click="deleteTarget = line"><Trash2 :size="16" /></button></div></td></tr></tbody></table></div>
        </template>
      </div>
      <footer class="sf-footer"><span>费用含税合计 {{ formatMoney(expenses.reduce((sum, line) => sum + line.amountIncludingTax, 0)) }}</span><button class="sf-button" :disabled="busy" @click="$emit('close')">关闭</button></footer>
    </section>
  </div></Teleport>
  <CustomModal :visible="Boolean(deleteTarget)" title="删除费用草稿" message="确定删除这条费用草稿？" type="warning" @confirm="remove" @cancel="deleteTarget = null" />
</template>
<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { Check, Save, Trash2, Undo2, X } from '@lucide/vue'
import CustomModal from '@/components/CustomModal.vue'
import { useUserStore } from '@/stores/user'
import request from '@/api/request'
import { formatMoney, operationKey } from '@/utils/supplierFinance'
import '@/assets/styles/supplier-finance.css'
const props = defineProps({ orderId: { type: Number, required: true } })
const emit = defineEmits(['close', 'updated'])
const user = useUserStore()
const loading = ref(true)
const busy = ref(false)
const error = ref('')
const batches = ref([])
const orderItems = ref([])
const expenses = ref([])
const deleteTarget = ref(null)
const form = reactive({ inboundItemId: '', expenseType: '运费', amountExcludingTax: 0, taxAmount: 0, includeInPayable: true, includeInInventoryCost: false, remark: '' })
const sourceItems = computed(() => batches.value.filter(batch => batch.status === 'draft').flatMap(batch => batch.items.map(item => ({ ...item, documentDate: batch.documentDate }))))
const isDraftBatch = line => batches.value.some(batch => batch.status === 'draft' && batch.items.some(item => item.id === line.inboundItemId))
async function load() {
  const [order, inboundData, expenseData] = await Promise.all([request({ url: `/purchase-orders/${props.orderId}` }), request({ url: '/stock-inbounds', params: { businessType: 'purchase' } }), request({ url: `/purchase-orders/${props.orderId}/expenses` })])
  orderItems.value = order.items
  batches.value = inboundData.filter(batch => batch.purchaseOrderId === props.orderId)
  expenses.value = expenseData
}
async function perform(fn) {
  busy.value = true; error.value = ''
  try { await fn(); await load(); emit('updated') } catch (err) { error.value = err.response?.data?.message || err.message } finally { busy.value = false }
}
function save() {
  const source = sourceItems.value.find(item => item.id === form.inboundItemId)
  if (!source) return
  perform(() => request({ url: `/purchase-orders/${props.orderId}/expenses`, method: 'POST', data: { ...form, supplierId: source.supplierId, purchaseOrderItemId: source.purchaseOrderItemId } }))
}
function toggleConfirm(line) { perform(() => request({ url: `/purchase-expenses/${line.id}/confirm`, method: line.status === 'confirmed' ? 'DELETE' : 'POST', data: { version: line.version, idempotencyKey: operationKey() } })) }
function remove() { const id = deleteTarget.value.id; deleteTarget.value = null; perform(() => request({ url: `/purchase-expenses/${id}`, method: 'DELETE' })) }
onMounted(async () => { try { await load() } catch (err) { error.value = err.response?.data?.message || err.message } finally { loading.value = false } })
</script>
