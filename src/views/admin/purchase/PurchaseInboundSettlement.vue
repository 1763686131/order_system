<template>
  <section class="supplier-finance-page">
    <header class="sf-header"><h1>独立入库结算</h1><button class="sf-button icon" title="刷新" aria-label="刷新" :disabled="loading" @click="load"><RefreshCw :size="18" /></button></header>
    <div class="sf-toolbar">
      <label class="sf-field">关键词<input v-model.trim="keyword" type="search" placeholder="单号、商品、供应商" /></label>
      <label class="sf-field">财务状态<select v-model="status"><option value="">全部</option><option value="pending_supplier">待补供应商</option><option value="supplier_assigned">已补供应商/待确认</option><option value="payable_confirmed">应付已确认</option></select></label>
      <span class="sf-badge warning">待处理 {{ records.filter(row => row.financialStatus !== 'payable_confirmed').length }} 张</span>
    </div>
    <p v-if="error" class="sf-error" role="alert">{{ error }}</p>
    <div class="sf-table-scroll"><table class="sf-table"><thead><tr><th>入库单号</th><th>日期 / 门店</th><th>商品明细</th><th>供应商</th><th>含税金额</th><th>财务状态</th><th>操作</th></tr></thead><tbody>
      <tr v-if="loading"><td colspan="7" class="sf-empty">加载中...</td></tr>
      <tr v-else-if="!filtered.length"><td colspan="7" class="sf-empty">暂无待补供应商入库记录</td></tr>
      <tr v-for="row in filtered" :key="row.id"><td><button class="sf-link" @click="router.push(`/admin/purchase/inbound/${row.id}`)">{{ row.documentNo }}</button></td><td>{{ row.documentDate }}<div class="sf-muted">{{ row.storeName }}</div></td><td>{{ row.items.map(item => item.productName).join('、') }}</td><td>{{ row.supplierName || '待补录' }}</td><td class="sf-number">{{ formatMoney(row.totalAmount) }}</td><td><span class="sf-badge" :class="{ warning: row.financialStatus !== 'payable_confirmed' }">{{ settlementLabels[row.financialStatus] }}</span></td><td><button class="sf-button" :disabled="!['reviewed', 'posted'].includes(row.status)" @click="selectedId = row.id">{{ row.financialStatus === 'payable_confirmed' ? '查看' : '归属确认' }}</button></td></tr>
    </tbody></table></div>
    <footer class="sf-footer">共 {{ filtered.length }} 张</footer>
    <SupplierAssignmentDialog v-if="selectedId" :inbound-id="selectedId" @close="selectedId = null" @updated="load" />
  </section>
</template>
<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { RefreshCw } from '@lucide/vue'
import request from '@/api/request'
import SupplierAssignmentDialog from '@/components/admin/purchase/SupplierAssignmentDialog.vue'
import { formatMoney, settlementLabels } from '@/utils/supplierFinance'
import '@/assets/styles/supplier-finance.css'
const router = useRouter()
const records = ref([])
const selectedId = ref(null)
const loading = ref(false)
const error = ref('')
const keyword = ref('')
const status = ref('')
const filtered = computed(() => records.value.filter(row => (!status.value || row.financialStatus === status.value) && (!keyword.value || `${row.documentNo} ${row.supplierName} ${row.items.map(item => item.productName).join(' ')}`.toLowerCase().includes(keyword.value.toLowerCase()))))
async function load() {
  loading.value = true
  error.value = ''
  try { records.value = await request({ url: '/stock-inbounds', params: { businessType: 'purchase', settlementType: 'pending_supplier' } }) }
  catch (err) { error.value = err.response?.data?.message || err.message }
  finally { loading.value = false }
}
onMounted(load)
</script>
