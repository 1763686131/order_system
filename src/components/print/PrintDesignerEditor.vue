<template>
  <div v-if="visible" class="print-designer-shell">
    <div class="print-designer-toolbar">
      <div class="designer-title">
        <input
          v-model="templateName"
          class="designer-name-input"
          aria-label="模板名称"
          placeholder="模板名称"
        />
        <small>210mm × 140mm · 三联单打印 1 份</small>
      </div>
      <div class="designer-actions">
        <button type="button" class="designer-btn" @click="handlePreview">预览</button>
        <button type="button" class="designer-btn designer-btn-primary" @click="handleSave">
          保存模板
        </button>
        <button type="button" class="designer-btn" @click="handleClose">退出</button>
      </div>
    </div>
    <div class="print-designer-canvas">
      <print-designer ref="designerRef" @ready="configureDesigner"></print-designer>
    </div>
  </div>
</template>

<script setup>
import { nextTick, ref, watch } from 'vue'
import 'vue-print-designer'
import 'vue-print-designer/style.css'

const props = defineProps({
  visible: { type: Boolean, default: false },
  template: { type: Object, default: null }
})

const emit = defineEmits(['save', 'close'])
const designerRef = ref(null)
const templateName = ref('')
const configured = ref(false)

const defaultVariables = {
  orderNo: 'XS20260913001',
  orderDate: '2026-09-13',
  customerName: '示例客户',
  warehouseName: '默认仓库',
  totalAmount: '0.00',
  items: [
    {
      productName: '示例商品',
      spec: '标准规格',
      quantity: 1,
      unitPrice: '0.00',
      amount: '0.00'
    }
  ]
}

const defaultTemplateData = {
  canvasSize: { width: 794, height: 529 },
  pages: [{ id: 'sale-page', elements: [] }],
  unit: 'mm',
  testData: defaultVariables,
  ext: {
    availableVariables: [
      { id: 'orderNo', label: '订单号' },
      { id: 'orderDate', label: '订单日期' },
      { id: 'customerName', label: '客户名称' },
      { id: 'warehouseName', label: '仓库名称' },
      { id: 'totalAmount', label: '合计金额' },
      { id: 'items', label: '商品明细', isArray: true }
    ]
  }
}

const configureDesigner = async () => {
  const designer = designerRef.value
  if (!designer || configured.value || !designer.getTemplateData?.()) return

  configured.value = true
  designer.setBranding({
    title: '订单打印模板设计器',
    showLogo: false,
    showTitle: true
  })
  designer.setLanguage('zh')
  await designer.setTestData(defaultVariables, { merge: false })
  await designer.setTemplateVariables(defaultVariables, { merge: false })
  designer.loadTemplateData(props.template?.design || defaultTemplateData)
}

const openDesigner = async () => {
  configured.value = false
  templateName.value = props.template?.name || '销售三联单'
  await nextTick()
  const designer = designerRef.value
  if (designer?.getTemplateData?.()) {
    configureDesigner()
  }
}

watch(
  () => props.visible,
  (visible) => {
    if (visible) openDesigner()
  }
)

const handlePreview = async () => {
  const designer = designerRef.value
  if (!designer) return
  await designer.setVariables(defaultVariables, { merge: false })
  await designer.preview()
}

const handleSave = () => {
  const designer = designerRef.value
  if (!designer) return
  emit('save', {
    ...props.template,
    name: templateName.value || props.template?.name || '销售三联单',
    businessType: props.template?.businessType || 'sale',
    paperType: props.template?.paperType || '三联单',
    pageWidth: 210,
    pageHeight: 140,
    enabled: props.template?.enabled !== false,
    design: designer.getTemplateData()
  })
}

const handleClose = () => emit('close')
</script>

<style scoped>
.print-designer-shell {
  position: fixed;
  inset: 0;
  z-index: 10000;
  display: flex;
  flex-direction: column;
  background: #eef1f5;
}

.print-designer-toolbar {
  height: 58px;
  flex: 0 0 58px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 18px;
  background: #fff;
  border-bottom: 1px solid #d9e0e8;
}

.designer-title {
  display: flex;
  align-items: baseline;
  gap: 14px;
  color: #172033;
  font-size: 16px;
  font-weight: 650;
}

.designer-name-input {
  width: 220px;
  height: 32px;
  padding: 0 9px;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  color: #172033;
  font-size: 15px;
  font-weight: 650;
}

.designer-name-input:focus {
  outline: 2px solid rgba(15, 159, 120, 0.2);
  border-color: #0f9f78;
}

.designer-title small {
  color: #7b8798;
  font-size: 12px;
  font-weight: 400;
}

.designer-actions {
  display: flex;
  gap: 8px;
}

.designer-btn {
  height: 34px;
  padding: 0 14px;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  background: #fff;
  color: #475569;
  cursor: pointer;
}

.designer-btn-primary {
  border-color: #0f9f78;
  background: #0f9f78;
  color: #fff;
}

.print-designer-canvas {
  min-height: 0;
  flex: 1;
}

.print-designer-canvas print-designer {
  display: block;
  width: 100%;
  height: 100%;
}
</style>
