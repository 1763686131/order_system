<template>
  <section class="supplier-finance-page">
    <header class="sf-header"><h1>员工采购 / 费用报销 <span class="sf-badge warning">临时原型</span></h1><button class="sf-button primary" @click="openForm()"><Plus :size="16" />新增费用</button></header>
    <div class="sf-toolbar"><label class="sf-field">关键词<input v-model.trim="keyword" type="search" placeholder="报销人、商户、费用类型" /></label></div>
    <div class="sf-table-scroll"><table class="sf-table"><thead><tr><th>日期</th><th>费用类型</th><th>商户</th><th>报销人</th><th>金额</th><th>付款方式</th><th>附件</th><th>操作</th></tr></thead><tbody><tr v-if="!filtered.length"><td colspan="8" class="sf-empty">暂无临时费用记录</td></tr><tr v-for="row in filtered" :key="row.id"><td>{{ row.date }}</td><td>{{ row.type }}</td><td>{{ row.merchant }}</td><td>{{ row.employee }}</td><td class="sf-number">{{ formatMoney(row.amount) }}</td><td>{{ row.paymentMethod }}</td><td>{{ row.attachments.length }} 份</td><td><div class="sf-actions"><button class="sf-button icon" title="查看费用" aria-label="查看费用" @click="openForm(row, true)"><Eye :size="16" /></button><button class="sf-button icon" title="修改费用" aria-label="修改费用" @click="openForm(row)"><Pencil :size="16" /></button><button class="sf-button icon danger" title="删除费用" aria-label="删除费用" @click="deleteTarget = row.id"><Trash2 :size="16" /></button></div></td></tr></tbody></table></div>
    <footer class="sf-footer"><span>共 {{ filtered.length }} 笔</span><span>费用合计 {{ formatMoney(filtered.reduce((sum, row) => sum + Number(row.amount), 0)) }}</span></footer>
    <Teleport to="body"><div v-if="formOpen" class="sf-modal-layer" @click.self="formOpen = false"><form class="supplier-finance-dialog" style="max-width: 720px" @submit.prevent="save" role="dialog" aria-modal="true" aria-label="临时员工费用"><header class="sf-header"><h2>{{ readOnly ? '费用详情' : form.id ? '修改费用' : '新增费用' }}</h2><button class="sf-button icon" type="button" title="关闭" @click="formOpen = false"><X :size="18" /></button></header><div class="sf-dialog-body"><fieldset :disabled="readOnly" style="border: 0; padding: 0"><div class="sf-form-grid"><label class="sf-field">日期<input v-model="form.date" type="date" required /></label><label class="sf-field">费用类型<select v-model="form.type"><option>办公用品</option><option>五金</option><option>零星采购</option><option>差旅</option><option>其它费用</option></select></label><label class="sf-field">金额<input v-model.number="form.amount" type="number" min="0.01" step="0.01" required /></label><label class="sf-field">商户名称<input v-model.trim="form.merchant" maxlength="120" required /></label><label class="sf-field">报销人<input v-model.trim="form.employee" maxlength="80" required /></label><label class="sf-field">付款方式<select v-model="form.paymentMethod"><option>员工垫付</option><option>现金</option><option>银行卡</option><option>微信</option><option>支付宝</option></select></label><label class="sf-field wide">备注<textarea v-model="form.remark" maxlength="500" /></label><label v-if="!readOnly" class="sf-field wide">发票 / 收据<input type="file" multiple accept="image/*,.pdf" @change="selectFiles" /></label></div></fieldset><div v-for="(file, index) in form.attachments" :key="`${file.name}-${index}`" class="sf-actions" style="margin-top: 10px"><a class="sf-link" :href="file.url" target="_blank" rel="noopener">{{ file.name }}</a><button v-if="!readOnly" class="sf-button icon" type="button" title="移除附件" @click="form.attachments.splice(index, 1)"><X :size="16" /></button></div></div><footer class="sf-footer"><span class="sf-badge warning">临时记录</span><button v-if="!readOnly" class="sf-button primary"><Save :size="16" />保存临时费用</button><button v-else class="sf-button" type="button" @click="formOpen = false">关闭</button></footer></form></div></Teleport>
    <CustomModal :visible="Boolean(deleteTarget)" title="删除临时费用" message="确定删除这条临时费用？" type="warning" @confirm="remove" @cancel="deleteTarget = null" />
  </section>
</template>
<script setup>
import { computed, onBeforeUnmount, reactive, ref } from 'vue'
import { Eye, Pencil, Plus, Save, Trash2, X } from '@lucide/vue'
import CustomModal from '@/components/CustomModal.vue'
import { localDate } from '@/composables/documents/documentModels'
import { formatMoney } from '@/utils/supplierFinance'
import '@/assets/styles/supplier-finance.css'
const records = ref([])
const form = reactive({})
const formOpen = ref(false)
const readOnly = ref(false)
const keyword = ref('')
const deleteTarget = ref(null)
const objectUrls = new Set()
const filtered = computed(() => records.value.filter(row => `${row.employee} ${row.merchant} ${row.type}`.includes(keyword.value)))
function openForm(row, view = false) { Object.assign(form, row ? { ...row, attachments: [...row.attachments] } : { id: null, date: localDate(), type: '办公用品', amount: '', merchant: '', employee: '', paymentMethod: '员工垫付', remark: '', attachments: [] }); readOnly.value = view; formOpen.value = true }
function selectFiles(event) { for (const file of event.target.files) { const url = URL.createObjectURL(file); objectUrls.add(url); form.attachments.push({ name: file.name, url }) } event.target.value = '' }
function save() { const record = { ...form, attachments: [...form.attachments], id: form.id || crypto.randomUUID() }; const index = records.value.findIndex(row => row.id === record.id); if (index < 0) records.value.unshift(record); else records.value[index] = record; formOpen.value = false }
function remove() { records.value = records.value.filter(row => row.id !== deleteTarget.value); deleteTarget.value = null }
onBeforeUnmount(() => objectUrls.forEach(url => URL.revokeObjectURL(url)))
</script>
