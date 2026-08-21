<template>
  <div class="nav-bar">
    <div
      v-for="(tab, index) in tabs"
      :key="index"
      class="nav-item"
      :class="{ active: currentTab === index, 'ml-auto': tab.align === 'right' }"
      @click="$emit('switch-tab', index)"
    >
      {{ tab.label }}
    </div>
  </div>
</template>

<script setup>
defineProps({
  currentTab: {
    type: Number,
    default: 0
  }
})

defineEmits(['switch-tab'])

const tabs = [
  { label: '未完成订单', align: 'left' },
  { label: '已完成订单', align: 'left' },
  { label: '已出库订单', align: 'left' },
  { label: '原材料数据', align: 'right' }
]
</script>

<style scoped>
.nav-bar {
  display: flex;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 0 20px;
}

.nav-item {
  padding: 18px 24px;
  cursor: pointer;
  font-size: 15px;
  font-weight: 500;
  color: #666;
  transition: all 0.3s;
  border-bottom: 3px solid transparent;
  user-select: none;
}

.nav-item:hover {
  color: #1890ff;
  background: rgba(24, 144, 255, 0.05);
}

.nav-item.active {
  color: #1890ff;
  border-bottom-color: #1890ff;
}

.ml-auto {
  margin-left: auto;
}
</style>
