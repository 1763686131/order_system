<template>
  <div v-if="groupedMaterials.length > 0" class="timeline-container">
    <div
      v-for="group in groupedMaterials"
      :key="group.date"
      class="timeline-group"
    >
      <div class="timeline-date">{{ group.date }}</div>
      <div class="timeline-items">
        <div
          v-for="item in group.items"
          :key="item.id"
          class="material-card"
          style="box-sizing: border-box; width: 100%;"
        >
          <!-- 查看模式 -->
          <div
            v-if="!item.editing"
            style="display: flex; align-items: center; width: 100%; flex-wrap: wrap; gap: 12px; box-sizing: border-box;"
          >
            <div class="m-data-group">
              <div class="m-item">
                <span class="m-label-black">使用树脂：</span>
                <span class="m-val-pink">{{ item.used }} kg</span>
              </div>
              <div class="m-item">
                <span class="m-label-black">成品：</span>
                <span class="m-val-green">{{ item.produced }} kg</span>
              </div>
              <div class="m-item">
                <span class="m-label-blue">剩余树脂：</span>
                <span class="m-val-blue">{{ item.remaining ? item.remaining.toFixed(1) : '0.0' }} kg</span>
              </div>
            </div>
            <div style="flex-grow: 1; min-width: 10px;"></div>
            <div class="m-note">
              <span class="m-note-label">备注：</span>
              <span class="m-note-val">{{ item.remark || '无' }}</span>
            </div>

            <div
              v-if="userStore.hasPerm('material.edit')"
              style="margin-left: auto; padding-left: 10px;"
            >
              <button
                class="btn-default"
                style="padding: 6px 16px; font-size: 13px; border-radius: 20px; border: 1px solid #d9d9d9; height: 34px; font-weight: bold; cursor: pointer;"
                @click="startEdit(item)"
              >
                修改
              </button>
            </div>
          </div>

          <!-- 编辑模式 -->
          <div
            v-else
            style="display: flex; align-items: center; width: 100%; flex-wrap: wrap; gap: 12px; box-sizing: border-box;"
          >
            <div class="m-data-group" style="flex-wrap: wrap; gap: 8px;">
              <div class="m-item" style="display: flex; align-items: center;">
                <span class="m-label-black" style="font-size: 13px;">使用树脂：</span>
                <input
                  v-model="item.editUsed"
                  type="number"
                  style="width: 70px; height: 28px; padding: 0 4px; border: 1px solid #eb2f96; border-radius: 8px; outline: none; font-weight: bold; color: #eb2f96; text-align: center; background: #fff0f6;"
                />
                <span class="m-val-pink" style="margin-left: 2px; font-size: 13px;">kg</span>
              </div>
              <div class="m-item" style="display: flex; align-items: center;">
                <span class="m-label-black" style="font-size: 13px;">成品：</span>
                <input
                  v-model="item.editProduced"
                  type="number"
                  style="width: 70px; height: 28px; padding: 0 4px; border: 1px solid #52c41a; border-radius: 8px; outline: none; font-weight: bold; color: #52c41a; text-align: center; background: #f6ffed;"
                />
                <span class="m-val-green" style="margin-left: 2px; font-size: 13px;">kg</span>
              </div>
              <div class="m-item" style="font-size: 13px;">
                <span class="m-label-blue">剩余：</span>
                <span class="m-val-blue">{{ item.remaining ? item.remaining.toFixed(1) : '0.0' }} kg</span>
              </div>
            </div>

            <div style="flex-grow: 1; min-width: 10px;"></div>

            <div class="m-item" style="display: flex; align-items: center;">
              <span class="m-label-black" style="font-size: 13px; margin-right: 4px;">备注：</span>
              <input
                v-model="item.editRemark"
                style="width: 120px; height: 28px; padding: 0 8px; border: 1px solid #1890ff; border-radius: 8px; outline: none; font-size: 13px; background: #e6f7ff;"
              />
            </div>

            <div style="margin-left: auto; padding-left: 10px; display: flex; gap: 8px;">
              <button
                class="btn-default"
                style="padding: 6px 16px; font-size: 13px; border-radius: 20px; height: 34px; font-weight: bold; cursor: pointer;"
                @click="cancelEdit(item)"
              >
                取消
              </button>
              <button
                class="btn-primary"
                style="padding: 6px 16px; font-size: 13px; border-radius: 20px; height: 34px; font-weight: bold; cursor: pointer; background: #52c41a; border: none; color: white;"
                @click="saveEdit(item)"
              >
                保存
              </button>
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
import { ref, computed, watch, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { getMaterials, updateMaterial } from '@/api/materials'

const props = defineProps({
  filterStart: {
    type: String,
    default: null
  },
  filterEnd: {
    type: String,
    default: null
  }
})

const userStore = useUserStore()

const materials = ref([])
const loading = ref(false)

// 空数据提示
const emptyMessage = computed(() => {
  if (props.filterStart) {
    return `没有找到 ${props.filterStart} 到 ${props.filterEnd} 的原材料记录`
  }
  return '最近 3 天内暂无原材料（树脂）使用记录'
})

// 按日期分组
const groupedMaterials = computed(() => {
  const groups = {}

  materials.value.forEach(item => {
    const day = item.date ? item.date.substring(0, 10) : '未知日期'
    if (!groups[day]) {
      groups[day] = []
    }
    groups[day].push(item)
  })

  return Object.keys(groups)
    .sort((a, b) => b.localeCompare(a))
    .map(date => ({
      date,
      items: groups[date].sort((a, b) => b.date.localeCompare(a.date))
    }))
})

// 加载原材料数据
const loadMaterials = async () => {
  loading.value = true
  try {
    const resData = await getMaterials()

    let allRecords = resData.records || []
    let currentStock = parseFloat(resData.total_stock) || 0

    // 计算剩余库存
    allRecords.sort((a, b) => a.date.localeCompare(b.date))
    allRecords.forEach(r => {
      currentStock -= (parseFloat(r.used) || 0)
      r.remaining = currentStock
      r.editing = false
    })

    // 日期筛选
    let filteredRecords = []

    if (props.filterStart && props.filterEnd) {
      const startT = new Date(props.filterStart.replace(/-/g, '/')).getTime()
      const endT = new Date(props.filterEnd.replace(/-/g, '/')).getTime() + 86400000 - 1

      filteredRecords = allRecords.filter(r => {
        const dateStr = r.date || ''
        if (!dateStr) return false
        const t = new Date(dateStr.substring(0, 10).replace(/-/g, '/')).getTime()
        return t >= startT && t <= endT
      })
    } else {
      const now = new Date()
      const threeDaysAgo = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 2).getTime()

      filteredRecords = allRecords.filter(r => {
        const dateStr = r.date || ''
        if (!dateStr) return false
        const t = new Date(dateStr.substring(0, 10).replace(/-/g, '/')).getTime()
        return t >= threeDaysAgo
      })
    }

    materials.value = filteredRecords
  } catch (error) {
    console.error('Failed to load materials:', error)
  } finally {
    loading.value = false
  }
}

// 开始编辑
const startEdit = (item) => {
  item.editing = true
  item.editUsed = item.used
  item.editProduced = item.produced
  item.editRemark = item.remark || ''
}

// 取消编辑
const cancelEdit = (item) => {
  item.editing = false
}

// 保存编辑
const saveEdit = async (item) => {
  try {
    const updateData = {
      used: item.editUsed,
      produced: item.editProduced,
      remark: item.editRemark
    }

    await updateMaterial(item.id, updateData)

    item.used = item.editUsed
    item.produced = item.editProduced
    item.remark = item.editRemark
    item.editing = false

    // 重新加载以更新剩余库存
    loadMaterials()
  } catch (error) {
    console.error('Failed to save material:', error)
    alert('保存失败')
  }
}

// 监听筛选条件变化
watch([() => props.filterStart, () => props.filterEnd], () => {
  loadMaterials()
})

onMounted(() => {
  loadMaterials()
})
</script>

<style scoped>
/* 样式已在全局 CSS 中定义 */
</style>
