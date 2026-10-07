<template>
  <div class="sf-table-scroll">
    <table class="sf-table sf-allocation-table">
      <thead><tr><th>来源单号 / 商品</th><th>业务日期</th><th>应付金额</th><th>可分配金额</th><th>开票状态</th><template v-if="invoice"><th>开票数量</th><th>未税金额</th><th>税额</th></template><th>{{ invoice ? '价税合计' : '本次核销' }}</th></tr></thead>
      <tbody>
        <tr v-if="loading"><td :colspan="invoice ? 9 : 6" class="sf-empty">加载来源应付中...</td></tr>
        <tr v-else-if="!rows.length"><td :colspan="invoice ? 9 : 6" class="sf-empty">暂无可分配应付</td></tr>
        <tr v-for="row in rows" :key="row.id">
          <td>{{ row.documentNo }}<div class="sf-muted">{{ row.productName }}</div></td>
          <td>{{ row.businessDate || '-' }}</td>
          <td class="sf-number">{{ formatMoney(row.payableAmount ?? row.amountIncludingTax) }}</td>
          <td class="sf-number">{{ readonly ? '-' : formatMoney(row.availableAmount) }}</td>
          <td>{{ invoiceLabels[row.invoiceStatus] || '-' }}</td>
          <template v-if="invoice">
            <td><input v-if="!readonly" :value="entry(row.id).quantity ?? ''" type="number" min="0" step="0.0001" :aria-label="`${row.documentNo}开票数量`" @input="update(row.id, 'quantity', $event.target.value)" /><span v-else>{{ entry(row.id).quantity || '-' }}</span></td>
            <td><input v-if="!readonly" :value="entry(row.id).amountExcludingTax ?? ''" type="number" min="0" step="0.01" :aria-label="`${row.documentNo}未税金额`" @input="update(row.id, 'amountExcludingTax', $event.target.value)" /><span v-else>{{ formatMoney(entry(row.id).amountExcludingTax) }}</span></td>
            <td><input v-if="!readonly" :value="entry(row.id).taxAmount ?? ''" type="number" min="0" step="0.01" :aria-label="`${row.documentNo}税额`" @input="update(row.id, 'taxAmount', $event.target.value)" /><span v-else>{{ formatMoney(entry(row.id).taxAmount) }}</span></td>
          </template>
          <td class="sf-number">
            <template v-if="invoice">{{ formatMoney(Number(entry(row.id).amountExcludingTax || 0) + Number(entry(row.id).taxAmount || 0)) }}</template>
            <input v-else-if="!readonly" :value="entry(row.id).amount ?? ''" type="number" min="0" step="0.01" :max="row.availableAmount" :aria-label="`${row.documentNo}本次核销`" @input="update(row.id, 'amount', $event.target.value)" />
            <span v-else>{{ formatMoney(entry(row.id).amount) }}</span>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { formatMoney, invoiceLabels } from '@/utils/supplierFinance'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  sources: { type: Array, default: () => [] },
  invoice: Boolean,
  readonly: Boolean,
  loading: Boolean
})
const emit = defineEmits(['update:modelValue'])
const entry = id => props.modelValue.find(row => Number(row.payableTransactionId) === Number(id)) || {}
const rows = computed(() => {
  if (props.readonly) return props.modelValue.map(row => ({
    ...props.sources.find(source => Number(source.id) === Number(row.payableTransactionId)),
    ...row,
    id: row.payableTransactionId,
    availableAmount: 0
  }))
  const result = [...props.sources]
  props.modelValue.forEach(row => {
    if (!result.some(source => Number(source.id) === Number(row.payableTransactionId))) {
      result.push({ ...row, id: row.payableTransactionId, availableAmount: 0 })
    }
  })
  return result
})
function update(id, field, value) {
  const entries = props.modelValue.map(row => ({ ...row }))
  let target = entries.find(row => Number(row.payableTransactionId) === Number(id))
  if (!target) {
    const source = props.sources.find(row => row.id === id) || {}
    target = { payableTransactionId: id, documentNo: source.documentNo, productName: source.productName }
    entries.push(target)
  }
  target[field] = value === '' ? '' : Number(value)
  emit('update:modelValue', entries)
}
</script>
