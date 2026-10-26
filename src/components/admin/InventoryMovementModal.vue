<template>
  <Teleport to="body">
    <div v-if="item" class="inventory-detail-layer" @click.self="$emit('close')" @keydown.esc="$emit('close')">
      <section class="inventory-detail-modal" role="dialog" aria-modal="true" aria-labelledby="inventoryMovementTitle">
        <header class="inventory-detail-header">
          <div class="inventory-detail-title">
            <span class="inventory-detail-icon"><Package :size="22" aria-hidden="true" /></span>
            <div>
              <span>库存流水</span>
              <h2 id="inventoryMovementTitle">{{ item.productName }}库存明细</h2>
              <p>{{ item.storeName || '全部门店' }} · {{ item.warehouseName || '全部仓库' }}</p>
            </div>
          </div>
          <button class="inventory-detail-close" type="button" title="关闭" aria-label="关闭库存流水" @click="$emit('close')">
            <X :size="20" aria-hidden="true" />
          </button>
        </header>
        <div class="inventory-detail-body">
          <div class="movement-summary">
            <span>当前库存</span><strong>{{ formatNumber(item.stock) }}</strong><small>{{ item.unit }}</small>
          </div>
          <div v-if="loading" class="movement-state">正在加载入库与出库记录...</div>
          <div v-else-if="error" class="movement-state error" role="alert">{{ error }}</div>
          <div v-else-if="records.length === 0" class="movement-state">暂无已审核的入库或出库记录</div>
          <div v-else class="movement-table-wrap">
            <table
              class="movement-table"
              v-table-layout="{ storageKey: 'inventory-movement-detail-v2', resizeMode: 'fit', minWidth: 64 }"
            >
              <colgroup>
                <col style="width: 22%" />
                <col style="width: 18%" />
                <col style="width: 9%" />
                <col style="width: 18%" />
                <col style="width: 13%" />
                <col style="width: 10%" />
                <col style="width: 10%" />
              </colgroup>
              <thead>
                <tr>
                  <th data-column-key="documentNo" data-min-width="120">单据编号</th>
                  <th data-column-key="date" data-min-width="100">日期</th>
                  <th data-column-key="type" data-min-width="64">类型</th>
                  <th class="movement-number" data-column-key="quantity" data-min-width="90">数量</th>
                  <th data-column-key="warehouse" data-min-width="90">仓库</th>
                  <th data-column-key="purpose" data-min-width="90">用途</th>
                  <th class="movement-produced-quantity" data-column-key="producedQuantity" data-min-width="80">成品数量</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="movement in records" :key="movementKey(movement)">
                  <td class="movement-document">{{ movement.documentNo || '-' }}</td>
                  <td>{{ formatMovementDate(movement.documentDate || movement.createdAt) }}</td>
                  <td><span :class="['movement-type', `movement-${movement.movementType}`]">{{ movement.movementType === 'in' ? '入库' : '出库' }}</span></td>
                  <td :class="['movement-number', `movement-${movement.movementType}`]">
                    {{ movement.movementType === 'in' ? '+' : '-' }}{{ formatNumber(movement.quantity) }}<small>{{ item.unit }}</small>
                  </td>
                  <td>{{ movement.warehouseName || '-' }}</td>
                  <td class="movement-note">{{ String(movement.remark || '').trim() || '-' }}</td>
                  <td class="movement-produced-quantity">
                    <template v-if="hasProducedQuantity(movement)">
                      {{ formatNumber(movement.producedQuantity) }}<small>公斤</small>
                    </template>
                    <template v-else-if="movement.producedQuantity === null || movement.producedQuantity === undefined">-</template>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </div>
  </Teleport>
</template>

<script setup>
import { Package, X } from '@lucide/vue'

defineProps({
  item: { type: Object, default: null },
  records: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' }
})
defineEmits(['close'])
const formatNumber = value => Number(value || 0).toLocaleString('zh-CN', { maximumFractionDigits: 3 })
const formatMovementDate = value => String(value || '').slice(0, 16) || '-'
const movementKey = movement => [movement.movementType, movement.sourceDocumentId, movement.documentNo, movement.warehouseId, movement.storeId].join('-')
const hasProducedQuantity = movement => (
  movement.movementType === 'out'
  && Number.isFinite(Number(movement.producedQuantity))
  && Number(movement.producedQuantity) > 0
)
</script>

<style scoped>
.inventory-detail-layer {
  --accent: #0f9f78;
  --accent-dark: #08745a;
  --accent-soft: #e9f8f3;
  --border: #dfe5ec;
  position: fixed;
  inset: 0;
  z-index: 2147483000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  color: #172033;
  background: rgba(15, 23, 42, 0.42);
}
.inventory-detail-modal {
  display: flex;
  width: min(1180px, calc(100vw - 48px));
  max-height: min(680px, calc(100vh - 48px));
  flex-direction: column;
  overflow: hidden;
  background: #f4f7f9;
  border: 1px solid var(--border);
  border-radius: 7px;
  box-shadow: 0 20px 60px rgba(15, 23, 42, 0.22);
}
.inventory-detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 14px 20px;
  background: #fff;
  border-bottom: 1px solid var(--border);
}
.inventory-detail-title { display: flex; min-width: 0; align-items: center; gap: 12px; }
.inventory-detail-icon { display: inline-flex; width: 40px; height: 40px; flex: 0 0 auto; align-items: center; justify-content: center; color: var(--accent-dark); background: var(--accent-soft); border-radius: 7px; }
.inventory-detail-title > div { min-width: 0; }
.inventory-detail-title span:not(.inventory-detail-icon) { color: var(--accent-dark); font-size: 12px; font-weight: 700; }
.inventory-detail-title h2 { margin: 3px 0 2px; overflow: hidden; font-size: 18px; font-weight: 700; text-overflow: ellipsis; white-space: nowrap; }
.inventory-detail-title p { margin: 0; color: #475569; font-size: 14px; overflow-wrap: anywhere; }
.inventory-detail-close { display: inline-flex; width: 34px; height: 34px; flex: 0 0 auto; align-items: center; justify-content: center; padding: 0; color: #68758a; background: transparent; border: 0; border-radius: 5px; cursor: pointer; }
.inventory-detail-close:hover { color: #273245; background: #f0f3f6; }
.inventory-detail-close:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.inventory-detail-body { min-height: 0; flex: 1; overflow-y: auto; padding: 16px; }
.movement-summary { display: flex; align-items: baseline; gap: 7px; padding: 13px 15px; background: #fff; border: 1px solid var(--border); border-radius: 7px; }
.movement-summary span { color: #334155; font-size: 15px; font-weight: 700; }
.movement-summary strong { margin-left: 4px; color: var(--accent-dark); font-size: 25px; font-weight: 800; font-variant-numeric: tabular-nums; }
.movement-summary small { color: #475569; font-size: 14px; font-weight: 700; }
.movement-state { display: flex; min-height: 180px; align-items: center; justify-content: center; margin-top: 13px; color: #475569; background: #fff; border: 1px solid var(--border); border-radius: 7px; font-size: 15px; font-weight: 600; padding: 16px; }
.movement-state.error { color: #b42318; }
.movement-table-wrap { margin-top: 13px; overflow-x: auto; background: #fff; border: 1px solid var(--border); border-radius: 7px; }
.movement-table { width: 100%; min-width: 835px; border-collapse: collapse; table-layout: fixed; font-size: 15px; }
.movement-table th { height: 46px; padding: 0 12px; color: #334155; background: #f8fafc; border-bottom: 1px solid var(--border); font-size: 14px; font-weight: 700; text-align: left; white-space: nowrap; }
.movement-table td { height: 56px; padding: 8px 12px; overflow: hidden; color: #1f2937; border-bottom: 1px solid #edf1f5; font-weight: 600; text-overflow: ellipsis; white-space: nowrap; }
.movement-table tbody tr:last-child td { border-bottom: 0; }
.movement-document { color: var(--accent-dark) !important; font-weight: 800; }
.movement-number { font-variant-numeric: tabular-nums; text-align: right !important; }
.movement-table td.movement-number { font-size: 16px; font-weight: 800; }
.movement-number small, .movement-produced-quantity small { margin-left: 3px; font-size: 13px; }
.movement-type { display: inline-flex; min-height: 29px; align-items: center; padding: 0 10px; border-radius: 5px; font-size: 14px; font-weight: 700; }
.movement-in { color: #13734f !important; }
.movement-type.movement-in { background: #eaf8f1; }
.movement-out { color: #dc2626 !important; }
.movement-type.movement-out { background: #fef2f2; }
.movement-note { color: #334155 !important; line-height: 1.55; overflow-wrap: anywhere; white-space: normal !important; }
.movement-produced-quantity { color: #334155 !important; font-variant-numeric: tabular-nums; text-align: left; }
.movement-table td.movement-produced-quantity { font-size: 16px; font-weight: 800; }
@media (max-width: 640px) {
  .inventory-detail-layer { padding: 0; }
  .inventory-detail-modal { width: 100vw; max-height: 100vh; height: 100vh; border-radius: 0; }
}
</style>
