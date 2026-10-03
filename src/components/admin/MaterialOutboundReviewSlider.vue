<template>
  <teleport to="body">
    <div
      v-if="visible"
      class="review-slider-overlay"
      role="presentation"
      @click.self="requestClose"
    >
      <section class="review-slider-modal" role="dialog" aria-modal="true" aria-labelledby="reviewSliderTitle" @click.stop>
        <header class="review-slider-header">
          <div>
            <span class="review-slider-eyebrow">原材料出库审核</span>
            <h2 id="reviewSliderTitle">确认审核并扣减库存</h2>
          </div>
          <button type="button" class="review-slider-close" title="关闭" :disabled="loading" @click="requestClose">×</button>
        </header>

        <div class="review-slider-body">
          <p>
            审核后将从“{{ record?.warehouseName || '-' }}”扣减
            {{ formatNumber(record?.totalQuantity) }} {{ record?.primaryItem?.unit || '' }}，
            并完成成品入库。
          </p>
          <div v-if="error" class="review-slider-error" role="alert">{{ error }}</div>
          <label class="review-slider-track">
            <span class="review-slider-label">{{ loading ? '审核处理中...' : '滑动到最右侧完成审核' }}</span>
            <input
              v-model.number="progress"
              class="review-slider-input"
              type="range"
              min="0"
              max="100"
              step="1"
              :disabled="loading"
              aria-label="滑动确认审核"
              @change="handleSliderChange"
            />
            <span class="review-slider-value">{{ progress }}%</span>
          </label>
        </div>

        <footer class="review-slider-footer">
          <button type="button" class="review-slider-button secondary" :disabled="loading" @click="requestClose">
            取消
          </button>
          <span class="review-slider-hint">需要滑到 100% 才会提交审核</span>
        </footer>
      </section>
    </div>
  </teleport>
</template>

<script setup>
import { ref, watch } from 'vue'
import request from '@/api/request'

const props = defineProps({
  visible: { type: Boolean, default: false },
  record: { type: Object, default: null }
})

const emit = defineEmits(['close', 'audited'])

const progress = ref(0)
const loading = ref(false)
const error = ref('')

const formatNumber = value => Number(value || 0).toLocaleString('zh-CN', {
  maximumFractionDigits: 3
})

const requestClose = () => {
  if (!loading.value) emit('close')
}

const handleSliderChange = async () => {
  if (progress.value < 100 || loading.value || !props.record) return
  if (
    !props.record.finishedWarehouseId
    || !props.record.finishedProductId
    || Number(props.record.producedQuantity || 0) <= 0
  ) {
    progress.value = 0
    error.value = '请先点击“修改”补充成品商品、入库仓库和入库数量。'
    return
  }
  loading.value = true
  error.value = ''
  try {
    const response = await request({
      url: `/material-outbounds/${props.record.id}/audit`,
      method: 'POST',
      data: {
        finishedWarehouseId: props.record.finishedWarehouseId,
        finishedProductId: props.record.finishedProductId,
        finishedQuantity: props.record.producedQuantity,
        finishedRemark: props.record.finishedRemark || props.record.remark || ''
      }
    })
    emit('audited', response)
  } catch (requestError) {
    progress.value = 0
    error.value = requestError?.response?.data?.message || '审核失败，请检查库存和成品入库信息。'
  } finally {
    loading.value = false
  }
}

watch(
  () => props.visible,
  visible => {
    if (visible) {
      progress.value = 0
      error.value = ''
    }
  }
)
</script>

<style scoped>
.review-slider-overlay {
  position: fixed;
  inset: 0;
  z-index: 2147483200;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  background: rgba(15, 23, 42, .52);
}

.review-slider-modal {
  width: min(520px, calc(100vw - 32px));
  overflow: hidden;
  color: #17212b;
  background: #fff;
  border: 1px solid #dce5e9;
  border-radius: 7px;
  box-shadow: 0 20px 56px rgba(15, 23, 42, .28);
}

.review-slider-header,
.review-slider-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 15px 18px;
  border-bottom: 1px solid #e8edef;
}

.review-slider-footer {
  border-top: 1px solid #e8edef;
  border-bottom: 0;
}

.review-slider-eyebrow {
  color: #71808a;
  font-size: 12px;
}

.review-slider-header h2 {
  margin: 4px 0 0;
  color: #08755e;
  font-size: 18px;
}

.review-slider-close {
  width: 34px;
  height: 34px;
  color: #64717c;
  background: #fff;
  border: 1px solid #d4dde3;
  border-radius: 4px;
  cursor: pointer;
  font-size: 20px;
}

.review-slider-body {
  padding: 22px 18px 24px;
}

.review-slider-body p {
  margin: 0 0 22px;
  color: #52616c;
  line-height: 1.7;
}

.review-slider-track {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 7px 12px;
  align-items: center;
  padding: 14px;
  background: #f7faf9;
  border: 1px solid #d9ebe5;
  border-radius: 5px;
}

.review-slider-label {
  color: #08755e;
  font-weight: 600;
}

.review-slider-value {
  color: #08755e;
  font-variant-numeric: tabular-nums;
}

.review-slider-input {
  grid-column: 1 / -1;
  width: 100%;
  accent-color: #159a7c;
  cursor: grab;
}

.review-slider-input:active {
  cursor: grabbing;
}

.review-slider-error {
  margin-bottom: 14px;
  padding: 9px 11px;
  color: #b5363e;
  background: #fff6f6;
  border: 1px solid #f1cbd0;
  border-radius: 4px;
  font-size: 12px;
}

.review-slider-button {
  min-height: 36px;
  padding: 0 14px;
  border: 1px solid transparent;
  border-radius: 4px;
  cursor: pointer;
  font: inherit;
  font-weight: 600;
}

.review-slider-button.secondary {
  color: #52616c;
  background: #fff;
  border-color: #d4dde3;
}

.review-slider-button:disabled {
  cursor: default;
  opacity: .55;
}

.review-slider-hint {
  color: #7b8892;
  font-size: 12px;
}
</style>
