<template>
  <div class="timeline-container" v-if="groupedOrders.length > 0">
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
          :class="order.type == 1 ? 'card-insulation' : ''"
        >
          <!-- 右上角状态标签 -->
          <div
            class="ribbon"
            :style="order.audit_state === 1
              ? 'background: #D5EFE3; color: #4CBCA0;'
              : 'background: #FDECEE; color: #F46E83;'"
          >
            {{ order.audit_state === 1 ? '已发货' : '未审核' }}
          </div>

          <!-- 左侧区域 -->
          <div class="shipped-left">
            <div class="shipped-title">{{ order.goods_name || '无货物名称' }}</div>
            <div class="expand-list-text" @click="toggleExpand($event)">展开列表</div>

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
              >
                单号: {{ order.logistics_no || '暂无记录' }}
              </div>
            </div>

            <div class="shipped-bottom" style="margin-top: 12px;">
              <div>
                <div class="s-time-label">出库发货时间</div>
                <div class="s-time-value">{{ order.shipped_date || order.completed_date || '未知' }}</div>
              </div>
              <div
                v-if="userStore.hasPerm('shipped.view_detail')"
                class="s-detail-btn"
                @click="$emit('view-detail', order.id)"
              >
                查看
              </div>
            </div>
          </div>

          <!-- 右侧区域 -->
          <div class="shipped-right">
            <div class="s-sub-title">{{ order.type == 1 ? '绝缘订单' : '中固订单' }}</div>
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
import { computed } from 'vue'
import { useUserStore } from '@/stores/user'

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

const isEmployee = computed(() => {
  return userStore.role === 'employee' || userStore.role === 'operator'
})

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
/* 样式已在全局 CSS 中定义 */
</style>
