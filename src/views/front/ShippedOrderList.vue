<template>
  <div v-if="groupedOrders.length > 0" class="timeline-container">
    <div
      v-for="group in groupedOrders"
      :key="group.date"
      class="timeline-group"
    >
      <div class="timeline-date">{{ group.date }}</div>
      <div class="shipped-grid">
        <div
          v-for="order in group.orders"
          :key="order.id"
          class="shipped-card"
          :class="{ 'card-insulation': isInsulationStore(order) }"
        >
        >
          <!-- 右上角状态标签 -->
          <div
            class="ribbon"
            :style="order.audit_state === 1
              ? 'background: #D5EFE3; color: #4CBCA0; border: none; font-weight: bold; box-shadow: none;'
              : 'background: #FDECEE; color: #F46E83; border: none; font-weight: bold; box-shadow: none;'"
          >
            {{ order.audit_state === 1 ? '已发货' : '未审核' }}
          </div>

          <!-- 左侧区域 -->
          <div class="shipped-left" style="display: flex; flex-direction: column;">
            <div class="shipped-title">{{ order.goods_name || '无货物名称' }}</div>
            <div class="expand-list-text" @click="toggleExpand">展开列表</div>

            <div class="s-tags-wrapper">
              <div v-if="order.goods_packaging" class="s-tag s-tag-purple">包装:{{ order.goods_packaging }}</div>
              <div v-if="order.goods_quantity" class="s-tag s-tag-green">件数:{{ order.goods_quantity }}</div>
              <div v-if="order.goods_weight" class="s-tag s-tag-cyan">货物总重量:{{ order.goods_weight }}</div>
            </div>

            <div v-if="order.remark" class="s-tags-wrapper">
              <div class="s-tag s-tag-pink">备注信息:{{ order.remark }}</div>
            </div>

            <div class="s-tags-wrapper" style="margin-top: auto; padding-top: 24px;">
              <div
                class="s-tag"
                :style="getMethodTagStyle(order)"
                :title="getMethodTagTitle(order)"
                @click="handleMethodClick(order)"
                @mouseover="e => handleTagHover(e, true)"
                @mouseout="e => handleTagHover(e, false)"
              >
                发货方式: {{ getShippingMethod(order) }}
              </div>
              <span
                v-if="order.receipt_img_url && String(order.receipt_img_url).trim() !== ''"
                class="receipt-pure-tag"
                style="cursor: pointer;"
                title="点击查看回单详情"
                @click="$emit('view-receipt', order.id)"
              >
                回单
              </span>
              <div
                class="s-tag"
                :style="getLogisticsTagStyle(order)"
                :title="getLogisticsTagTitle(order)"
                @click="handleLogisticsClick(order)"
                @mouseover="e => handleTagHover(e, true)"
                @mouseout="e => handleTagHover(e, false)"
              >
                单号: {{ order.logistics_no || '暂无记录' }}
              </div>
            </div>

            <div class="shipped-bottom" style="margin-top: 12px;">
              <div>
                <div class="s-time-label">出库发货时间</div>
                <div class="s-time-value">{{ order.shipped_date || order.completed_date || '未知' }}</div>
              </div>
            </div>
          </div>

          <!-- 右侧区域 -->
          <div class="shipped-right">
            <div class="s-sub-title">{{ getStoreName(order) }}订单</div>
            <div class="s-main-title">{{ order.order_client || '未命名' }}</div>
            <div class="s-info-list">
              <div>收货姓名：{{ order.receiver_name || '未填' }}</div>
              <div>联系电话：{{ isEmployee ? '***' : (order.receiver_phone || '未填') }}</div>
              <div
                style="display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;"
                :title="order.receiver_address || ''"
              >
                收货地址：{{ order.receiver_address || '未填' }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div v-else style="color: #999; width:100%; text-align:center; padding:60px 20px; font-size:16px;">
    {{ emptyMessage }}
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { getStores } from '@/utils/storeHelper'

const props = defineProps({
  orders: {
    type: Array,
    required: true
  },
  filterStart: {
    type: String,
    default: null
  },
  filterEnd: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['refresh', 'view-detail', 'view-receipt', 'audit', 'manage-receipt'])

const userStore = useUserStore()
const stores = ref([])

const isEmployee = computed(() => {
  return userStore.role === 'employee' || userStore.role === 'operator'
})

// 加载门店列表
onMounted(async () => {
  try {
    stores.value = await getStores()
    console.log('ShippedOrderList - 门店数据加载完成:', stores.value)
    console.log('ShippedOrderList - 订单数据:', props.orders)
  } catch (error) {
    console.error('ShippedOrderList - 加载门店失败:', error)
  }
})

// 根据 store_id 或 type 获取门店名称
const getStoreName = (order) => {
  const storeId = order.store_id || (order.type === 1 ? 1 : 2)
  const store = stores.value.find(s => s.id === storeId)
  return store ? store.name : '未知门店'
}

// 根据 store_id 或 type 判断是否为绝缘（用于样式）
const isInsulationStore = (order) => {
  const storeId = order.store_id || (order.type === 1 ? 1 : 2)
  return storeId === 1
}

// 空数据提示信息
const emptyMessage = computed(() => {
  if (props.filterStart) {
    return `没有找到 ${props.filterStart} 到 ${props.filterEnd} 的出库记录`
  }
  return '最近 3 天内暂无任何已出库的物流记录'
})

// 按日期分组并排序
const groupedOrders = computed(() => {
  const groups = {}

  props.orders.forEach(order => {
    const day = order.shipped_date
      ? order.shipped_date.substring(0, 10)
      : (order.completed_date ? order.completed_date.substring(0, 10) : '未知日期')

    if (!groups[day]) {
      groups[day] = []
    }
    groups[day].push(order)
  })

  // 日期倒序，同一天内订单按时间倒序
  return Object.keys(groups)
    .sort((a, b) => b.localeCompare(a))
    .map(date => ({
      date,
      orders: groups[date].sort((a, b) => {
        const timeA = a.shipped_date || a.completed_date || ''
        const timeB = b.shipped_date || b.completed_date || ''
        return timeB.localeCompare(timeA)
      })
    }))
})

// 获取发货方式文本
const getShippingMethod = (order) => {
  const methodMap = { 0: '物流', 1: '零担快运', 2: '快递', 3: '专车', 4: '其它' }

  if (order.shipping_method !== undefined && order.shipping_method !== '') {
    let method = methodMap[order.shipping_method] || '其它'
    if (order.shipping_method === 4 && order.shipping_custom) {
      method = order.shipping_custom
    }
    return method
  } else if (order.logistics_type) {
    return order.logistics_type
  }
  return '其它'
}

// 获取发货方式标签样式
const getMethodTagStyle = (order) => {
  const isAudited = order.audit_state === 1

  if (isAudited) {
    return 'background:#f0f5ff; color:#2f54eb; border:1px solid #adc6ff; cursor: not-allowed;'
  } else {
    if (userStore.hasPerm('shipped.audit')) {
      return 'background:#e6f4ff; color:#1677ff; border:1px solid #91caff; cursor: pointer; transition: all 0.2s;'
    } else {
      return 'background:#f5f5f5; color:#bfbfbf; border:1px solid #d9d9d9; cursor: not-allowed; opacity: 0.7;'
    }
  }
}

// 获取发货方式标签提示
const getMethodTagTitle = (order) => {
  const isAudited = order.audit_state === 1

  if (isAudited) {
    return '该订单已通过最终审核确认，系统已锁死'
  } else {
    if (userStore.hasPerm('shipped.audit')) {
      return '点击此处进行出库审核操作'
    } else {
      return '暂无权限进行出库审核操作'
    }
  }
}

// 获取物流单号标签样式
const getLogisticsTagStyle = (order) => {
  const isAudited = order.audit_state === 1

  if (isAudited) {
    return 'background:#fff0f6; color:#eb2f96; border:1px solid #ffadd2; cursor: pointer; transition: all 0.2s;'
  } else {
    return 'background:#e6f7ff; color:#1890ff; border:1px solid #b7e1ff; cursor: not-allowed;'
  }
}

// 获取物流单号标签提示
const getLogisticsTagTitle = (order) => {
  const isAudited = order.audit_state === 1

  if (isAudited) {
    return '点击管理回单图片'
  } else {
    return '请先完成【确认审核】后再上传回单图片'
  }
}

// 处理标签悬停
const handleTagHover = (event, isEntering) => {
  if (isEntering) {
    event.target.style.transform = 'scale(1.05)'
  } else {
    event.target.style.transform = 'scale(1)'
  }
}

// 处理发货方式点击
const handleMethodClick = (order) => {
  const isAudited = order.audit_state === 1

  if (!isAudited && userStore.hasPerm('shipped.audit')) {
    emit('audit', order.id)
  }
}

// 处理物流单号点击
const handleLogisticsClick = (order) => {
  const isAudited = order.audit_state === 1

  if (isAudited) {
    emit('manage-receipt', order.id)
  }
}

// 展开/收起货物列表
const toggleExpand = (event) => {
  const titleEl = event.target.previousElementSibling
  if (titleEl && titleEl.classList.contains('shipped-title')) {
    titleEl.classList.toggle('expanded')
  }
}
</script>

<style scoped>
/* 时间轴容器 */
.timeline-container {
  display: flex;
  flex-direction: column;
  gap: 40px;
  width: 100%;
}

/* 时间轴分组 */
.timeline-group {
  display: flex;
  flex-direction: column;
}

/* 时间轴日期 */
.timeline-date {
  font-size: 26px;
  font-weight: 900;
  color: #111;
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  gap: 14px;
}

.timeline-date::before {
  content: '';
  display: block;
  width: 8px;
  height: 28px;
  background-color: #1890ff;
  border-radius: 4px;
}

/* 已出库订单网格 */
.shipped-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(480px, 1fr));
  gap: 32px;
  width: 100%;
}

/* 已出库订单卡片 */
.shipped-card {
  display: flex;
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
  overflow: hidden;
  position: relative;
  border: 1px solid #ebedf0;
  transition: transform 0.2s, box-shadow 0.2s;
}

.shipped-card:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

/* 右上角状态标签 */
.ribbon {
  position: absolute;
  top: 12px;
  right: -42px;
  background-color: #D5EFE3;
  color: #4CBCA0;
  padding: 4px 44px;
  font-size: 12px;
  font-weight: bold;
  transform: rotate(45deg);
  text-align: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  z-index: 10;
}

/* 左侧区域 */
.shipped-left {
  flex: 1.4;
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  border-right: 1px dashed #e8e8e8;
  min-width: 0;
}

/* 货物名称标题 */
.shipped-title {
  font-size: 18px;
  font-weight: 800;
  color: #111;
  margin-bottom: 8px;
  line-height: 1.5;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.shipped-title.expanded {
  white-space: normal;
  word-break: break-all;
}

/* 展开列表文本 */
.expand-list-text {
  display: none;
  font-size: 13px;
  color: #8A7BFE;
  text-align: right;
  margin-top: 0;
  margin-bottom: 12px;
  cursor: pointer;
  font-weight: bold;
  position: relative;
  z-index: 11;
}

/* 标签包装器 */
.s-tags-wrapper {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 8px;
}

.shipped-left .s-tags-wrapper:last-of-type {
  margin-bottom: 16px;
}

/* 回单纯标签 */
.receipt-pure-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 3px 10px;
  font-size: 11px;
  font-weight: bold;
  background-color: #FDECEE;
  border: 1px solid #FDECEE;
  color: #F26E83;
  border-radius: 3px;
  user-select: none;
}

/* 标签样式 */
.s-tag {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
}

/* 标签颜色变体 */
.s-tag-purple {
  background-color: #EDEBFF;
  color: #8A7BFE;
}

.s-tag-cyan {
  background-color: #DDF8F6;
  color: #2BCBC7;
}

.s-tag-green {
  background-color: #E2F6ED;
  color: #69D5A5;
}

.s-tag-pink {
  background-color: #FDECEE;
  color: #F26E83;
}

/* 底部时间区域 */
.shipped-bottom {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-top: auto;
}

/* 时间标签和值 */
.s-time-label {
  font-size: 12px;
  color: #999;
  margin-bottom: 4px;
}

.s-time-value {
  font-size: 18px;
  font-weight: bold;
  color: #111;
  letter-spacing: 0.5px;
}

/* 查看详情按钮 */
.s-detail-btn {
  background-color: #EDEBFF;
  color: #8A7BFE;
  padding: 6px 16px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: bold;
  cursor: pointer;
  transition: background-color 0.2s;
}

.s-detail-btn:hover {
  background-color: #E2E0FB;
}

/* 右侧区域 */
.shipped-right {
  flex: 1;
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  background-color: #FAFAFA;
}

/* 副标题 */
.s-sub-title {
  font-size: 13px;
  color: #8C99A8;
  text-align: center;
  font-weight: bold;
  margin-bottom: 6px;
}

/* 主标题 */
.s-main-title {
  font-size: 20px;
  font-weight: bold;
  color: #222;
  text-align: center;
  margin-bottom: 16px;
}

/* 信息列表 */
.s-info-list {
  font-size: 14px;
  color: #666;
  line-height: 1.6;
}

.s-info-list div {
  margin-bottom: 4px;
}

/* 响应式布局 */
@media (max-width: 768px) {
  .shipped-grid {
    grid-template-columns: 1fr !important;
    gap: 16px !important;
  }

  .shipped-card {
    flex-direction: column !important;
  }

  .shipped-left {
    border-right: none !important;
    border-bottom: 1px dashed #e8e8e8 !important;
    padding: 16px !important;
  }

  .shipped-right {
    padding: 16px !important;
    align-items: flex-start !important;
  }

  .s-sub-title,
  .s-main-title {
    text-align: left !important;
  }

  .ribbon {
    top: 10px !important;
    right: -40px !important;
    padding: 4px 44px !important;
    font-size: 11px !important;
  }

  .shipped-title,
  .expand-list-text {
    margin-right: 65px !important;
  }
}
</style>
