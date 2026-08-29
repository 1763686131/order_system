<template>
  <div v-for="order in processedOrders" :key="order.id + '-' + order.cardIndex">
    <!-- 未完成订单卡片 (Tab 0) -->
    <div v-if="statusType === 'pending'" class="flip-container">
      <div class="flipper" :class="{ 'no-flip': !order.isFirstCard }">
        <!-- 正面 -->
        <div class="order-card front" :style="{ backgroundColor: order.storeColor, color: order.storeTextColor }">
          <div class="order-title">{{ order.order_client || '未命名归属' }}订单</div>
          <div class="order-header">
            <span><strong>{{ order.typeName }}</strong> 产品列表 {{ order.isFirstCard ? '' : '(续集)' }}</span>
            <span>{{ order.isFirstCard ? (order.date || '未知时间') : '' }}</span>
          </div>

          <div class="product-list" :class="order.compactClass">
            <div
              v-for="(line, idx) in order.chunkLines"
              :key="idx"
              class="product-item"
              :style="getLineStyle(line, order.isMobile)"
              v-html="formatLine(line, order.isMobile)"
            ></div>
            <div v-if="order.indicatorHtml" class="card-part-indicator" v-html="order.partLetter"></div>
          </div>

          <div v-if="order.isFirstCard && order.tagsHtml" class="tags-wrapper">
            <div class="tags-label">标签&备注</div>
            <div class="tags-container">
              <div v-if="order.goods_packaging" class="tag tag-blue">包装:{{ order.goods_packaging }}</div>
              <div v-if="order.goods_weight" class="tag tag-cyan">重量:{{ order.goods_weight }}</div>
              <div v-if="order.remark" class="tag tag-red">备注:{{ order.remark }}</div>
              <div v-if="order.goods_quantity" class="tag tag-green">件数:{{ order.goods_quantity }}</div>
            </div>
          </div>

          <div v-if="order.isFirstCard" class="actions">
            <button
              v-if="userStore.hasPerm('pending.complete')"
              class="btn btn-primary"
              @click="$emit('complete', order.id)"
            >
              确定完成
            </button>
            <button
              v-if="userStore.hasPerm('pending.view_detail')"
              class="btn btn-default"
              @click="toggleCard($event)"
            >
              详情页面
            </button>
          </div>
        </div>

        <!-- 背面 -->
        <div v-if="order.isFirstCard" class="order-card back" :style="{ backgroundColor: order.storeColor, color: order.storeTextColor }">
          <div class="order-title">{{ order.order_client || '未命名归属' }}订单</div>
          <div class="order-header">
            <span><strong>{{ order.typeName }}</strong> 产品列表</span>
            <span>{{ order.date || '未知时间' }}</span>
          </div>

          <div class="product-list">
            <div class="info-row" style="display: flex; justify-content: space-between;">
              <span>收货姓名：{{ order.receiver_name || '未填' }}</span>
              <span>联系电话：{{ isEmployee ? '***' : (order.receiver_phone || '未填') }}</span>
            </div>
            <div class="info-row">收货地址：{{ order.receiver_address || '未填' }}</div>
            <div class="info-row info-label" style="margin-top: 12px;">货物全量信息：</div>
            <div
              v-for="(line, idx) in order.allGoodsLines"
              :key="idx"
              class="info-row text-red text-bold"
              :style="getBackLineStyle(line)"
            >
              {{ line }}
            </div>
            <div style="display: flex; gap: 24px; margin-top: 16px;">
              <div class="info-row"><span class="info-label">包装：</span>{{ order.goods_packaging || '无' }}</div>
              <div class="info-row"><span class="info-label">数量：</span><span class="text-red text-bold">{{ order.goods_weight || '无' }}</span></div>
            </div>
            <div style="display: flex; gap: 24px;">
              <div class="info-row"><span class="info-label">件数：</span>{{ order.goods_quantity || '无' }}</div>
              <div class="info-row"><span class="info-label">物流服务：</span>{{ isEmployee ? '***' : (order.logistics_service || '无') }}</div>
            </div>
            <div v-if="order.remark" class="info-row">
              <span class="info-label">备注：</span>
              <span class="text-red text-bold">{{ order.remark }}</span>
            </div>
          </div>

          <div class="actions-back">
            <button
              v-if="userStore.hasPerm('pending.view_detail')"
              class="btn btn-default"
              @click="toggleCard($event)"
            >
              ⇦返回
            </button>
            <button
              v-if="userStore.hasPerm('pending.complete')"
              class="btn btn-primary"
              @click="$emit('complete', order.id)"
            >
              确定完成
            </button>
            <button
              v-if="userStore.hasPerm('pending.edit')"
              class="btn btn-danger"
              @click="$emit('edit', order.id)"
            >
              修改
            </button>
            <button
              v-if="userStore.hasPerm('pending.copy')"
              class="btn btn-success"
              @click="$emit('copy', order.id)"
            >
              复制
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 已完成订单卡片 (Tab 1) -->
    <div v-else-if="statusType === 'completed'" class="completed-card" :style="{ backgroundColor: order.storeColor, color: order.storeTextColor, padding: '20px 24px', fontSize: '15px' }">
      <div class="order-title" style="font-size: 28px; margin-bottom: 8px;">{{ order.order_client || '未命名归属' }}订单</div>
      <div class="order-header" style="font-size: 15px; padding-bottom: 8px; margin-bottom: 12px;">
        <span><strong>{{ order.typeName }}</strong> 发货核对明细 {{ order.isFirstCard ? '' : '(续)' }}</span>
        <span>{{ order.isFirstCard ? order.shortDate : '' }}</span>
      </div>

      <div class="product-list" :class="order.compactClass" style="position:relative;">
        <template v-if="order.isFirstCard">
          <div class="info-row" style="display: flex; justify-content: space-between;">
            <span>收货姓名：{{ order.receiver_name || '未填' }}</span>
            <span>电话：{{ isEmployee ? '***' : (order.receiver_phone || '未填') }}</span>
          </div>
          <div class="info-row">收货地址：{{ order.receiver_address || '未填' }}</div>
          <div class="info-row info-label" style="margin-top: 6px;">货物信息：</div>
        </template>

        <div
          v-for="(line, idx) in order.chunkLines"
          :key="idx"
          class="info-row text-red text-bold"
          :style="getCompletedLineStyle(line)"
        >
          {{ line }}
        </div>

        <div v-if="order.indicatorHtml && !order.isMobile" class="card-part-indicator" style="font-size:70px;">{{ order.partLetter }}</div>

        <template v-if="order.isFirstCard">
          <div style="margin-top: auto; padding-top: 12px; display: flex; flex-direction: column; gap: 4px; flex-shrink: 0;">
            <div style="display: flex; gap: 24px;">
              <div class="info-row"><span class="info-label">包装：</span>{{ order.goods_packaging || '无' }}</div>
              <div class="info-row"><span class="info-label">数量：</span><span class="text-red text-bold">{{ order.goods_weight || '无' }}</span></div>
            </div>
            <div style="display: flex; gap: 24px;">
              <div class="info-row"><span class="info-label">件数：</span>{{ order.goods_quantity || '无' }}</div>
              <div class="info-row"><span class="info-label">物流：</span>{{ isEmployee ? '***' : (order.logistics_service || '无') }}</div>
            </div>
            <div v-if="order.remark" class="info-row">
              <span class="info-label">备注信息：</span>
              <span class="text-red text-bold">{{ order.remark }}</span>
            </div>
            <div class="info-row" style="color: #888; border-top: 1px dashed #f0f0f0; padding-top: 8px; margin-top: 4px;">
              <span class="info-label" style="color: #333;">完成时间：</span>{{ order.completed_date || '未知' }}
            </div>
          </div>
        </template>
      </div>

      <div v-if="order.isFirstCard" class="actions-back" style="margin-top: 12px; padding-top: 12px;">
        <button
          v-if="userStore.hasPerm('completed.uncomplete')"
          class="btn btn-default"
          @click="$emit('uncomplete', order.id)"
        >
          撤销
        </button>
        <button
          v-if="userStore.hasPerm('completed.ship')"
          class="btn btn-primary"
          @click="$emit('ship', order.id)"
        >
          出库
        </button>
        <button
          v-if="userStore.hasPerm('completed.delete')"
          class="btn btn-danger"
          @click="$emit('delete', order.id)"
        >
          删除
        </button>
        <button
          v-if="userStore.hasPerm('completed.copy')"
          class="btn btn-success"
          @click="$emit('copy', order.id)"
        >
          复制
        </button>
      </div>
    </div>
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
  statusType: {
    type: String,
    required: true // 'pending' 或 'completed'
  }
})

defineEmits(['complete', 'uncomplete', 'ship', 'delete', 'edit', 'copy'])

const userStore = useUserStore()
const stores = ref([])

const isEmployee = computed(() => {
  return userStore.role === 'employee' || userStore.role === 'operator'
})

// 加载门店列表
onMounted(async () => {
  stores.value = await getStores()
})

// 根据 store_id 或 type 获取门店名称
const getStoreName = (order) => {
  const storeId = order.store_id || (order.type === 1 ? 1 : 2)
  const store = stores.value.find(s => s.id === storeId)
  return store ? store.name : '未知门店'
}

// 根据 store_id 或 type 获取门店背景颜色
const getStoreColor = (order) => {
  const storeId = order.store_id || (order.type === 1 ? 1 : 2)
  const store = stores.value.find(s => s.id === storeId)
  return store?.color || '#f5f5f5'
}

// 根据 store_id 或 type 获取门店字体颜色
const getStoreTextColor = (order) => {
  const storeId = order.store_id || (order.type === 1 ? 1 : 2)
  const store = stores.value.find(s => s.id === storeId)
  return store?.textColor || '#333333'
}

// 根据 store_id 或 type 获取样式类名（已废弃，保留用于兼容）
const getStoreClass = (order) => {
  const storeId = order.store_id || (order.type === 1 ? 1 : 2)
  return storeId === 1 ? 'card-insulation' : ''
}

// 处理订单数据，拆分卡片
const processedOrders = computed(() => {
  const result = []
  const isMobile = window.innerWidth <= 768

  props.orders.forEach(order => {
    const goodsLines = (order.goods_name || '').split('\n').filter(l => l.trim() !== '')

    let chunks = []
    if (isMobile) {
      chunks = [goodsLines]
    } else {
      // 每9行一组
      for (let i = 0; i < goodsLines.length; i += 9) {
        chunks.push(goodsLines.slice(i, i + 9))
      }
      if (chunks.length === 0) chunks.push([])
    }

    chunks.forEach((chunkLines, chunkIndex) => {
      const isFirstCard = chunkIndex === 0
      const isSplit = chunks.length > 1
      const partLetter = String.fromCharCode(65 + chunkIndex)
      const compactClass = (!isMobile && chunkLines.length >= 8) ? 'compact' : ''
      const typeClass = getStoreClass(order)
      const storeColor = getStoreColor(order)
      const storeTextColor = getStoreTextColor(order)
      const typeName = getStoreName(order) + '订单'
      const shortDate = order.completed_date ? order.completed_date.split(' ')[0] : '未知日期'

      result.push({
        ...order,
        cardIndex: chunkIndex,
        chunkLines,
        allGoodsLines: goodsLines,
        isFirstCard,
        isSplit,
        partLetter,
        compactClass,
        typeClass,
        storeColor,
        storeTextColor,
        typeName,
        shortDate,
        isMobile,
        indicatorHtml: (!isMobile && isSplit),
        tagsHtml: isFirstCard && (order.goods_packaging || order.goods_weight || order.remark || order.goods_quantity)
      })
    })
  })

  return result
})

// 计算文本缩放比例
const calculateTextScale = (text, maxChars = 12, isHighlightMode = false) => {
  if (!text) return 1
  let len = 0

  for (let i = 0; i < text.length; i++) {
    const char = text[i]

    if (char.match(/[一-龥]/)) {
      len += 1
    } else if (isHighlightMode && char.match(/[a-zA-Z0-9.]/)) {
      if (char.match(/[A-Z]/)) len += 1.8
      else if (char.match(/[0-9]/)) len += 1.4
      else len += 1.1
    } else {
      if (char.match(/[A-Z]/)) len += 0.9
      else if (char.match(/[0-9]/)) len += 0.7
      else len += 0.55
    }
  }

  if (len <= maxChars) return 1
  const scale = maxChars / len
  return Math.max(scale, 0.35)
}

// 格式化行内容（高亮数字和字母）
const formatLine = (line, isMobile) => {
  if (isMobile) {
    return line
  }
  return line.replace(/([a-zA-Z0-9.]+)/g, '<span class="text-red-large">$1</span>')
}

// 获取行样式
const getLineStyle = (line, isMobile) => {
  if (isMobile) {
    return 'white-space: pre-wrap; word-break: break-all; line-height: 1.5; padding-bottom: 6px; color: #333;'
  }
  const lineScale = calculateTextScale(line, 14.5, true)
  const renderScale = Math.min(lineScale, 1.15)
  return `zoom: ${renderScale}; white-space: nowrap; height: calc(var(--red-size, 42px) * 1.1); display: flex; align-items: center;`
}

// 获取背面行样式
const getBackLineStyle = (line) => {
  const lineScale = calculateTextScale(line, 15)
  const renderScale = Math.min(lineScale, 1.15)
  return `font-size: calc(15px * ${renderScale}); white-space: nowrap; height: 24px; display: flex; align-items: center;`
}

// 获取已完成订单行样式
const getCompletedLineStyle = (line) => {
  const lineScale = calculateTextScale(line, 14.5)
  const renderScale = Math.min(lineScale, 1.15)
  return `font-size: calc(var(--base-size, 24px) * ${renderScale}); white-space: nowrap; flex-shrink: 0; height: calc(var(--base-size, 24px) * 1.4); display: flex; align-items: center;`
}

// 切换卡片翻转
const toggleCard = (event) => {
  const card = event.target.closest('.flip-container') || event.target.closest('.completed-card')
  if (!card) return

  const flipper = card.querySelector('.flipper')
  if (flipper) {
    flipper.classList.toggle('flipped')
  }
}
</script>

<style scoped>
/* 样式已在全局 CSS 中定义 */
</style>
