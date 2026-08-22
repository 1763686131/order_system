<template>
  <div class="timeline-container">
    <div v-if="loading" style="color: #999; width:100%; text-align:center; padding:60px 20px; font-size:16px;">
      加载中...
    </div>

    <div v-else-if="materialGroups.length === 0" style="color: #999; width:100%; text-align:center; padding:60px 20px; font-size:16px;">
      {{ emptyMessage }}
    </div>

    <div v-else v-for="group in materialGroups" :key="group.date" class="timeline-group">
      <div class="timeline-date">{{ group.date }}</div>
      <div class="timeline-items">
        <div
          v-for="record in group.records"
          :key="record.id"
          class="material-card"
          :id="`mat-card-${record.id}`"
        >
          <!-- 查看模式 -->
          <div
            :id="`mat-view-${record.id}`"
            v-show="editingId !== record.id"
            style="display: flex; align-items: center; width: 100%; box-sizing: border-box;"
          >
            <div class="m-data-group">
              <div class="m-item">
                <span class="m-label-black">使用树脂：</span>
                <span class="m-val-pink">{{ record.used }}kg</span>
              </div>
              <div class="m-item">
                <span class="m-label-black">成品：</span>
                <span class="m-val-green">{{ record.produced }}kg</span>
              </div>
              <div class="m-item">
                <span class="m-label-blue">剩余树脂：</span>
                <span class="m-val-blue">{{ record.remaining.toFixed(1) }}kg</span>
              </div>
            </div>
            <div class="m-divider"></div>
            <div class="m-note">
              <span class="m-note-label">备注：</span>
              <span class="m-note-val">{{ record.remark || '无' }}</span>
            </div>

            <div v-if="userStore.hasPerm('material.edit')" style="margin-left: auto; padding-left: 10px;">
              <button
                class="btn-default"
                style="padding: 6px 16px; font-size: 13px; border-radius: 20px; border: 1px solid #d9d9d9; height: 34px; font-weight: bold; cursor: pointer;"
                @click="startEdit(record)"
              >
                修改
              </button>
            </div>
          </div>

          <!-- 编辑模式 -->
          <div
            :id="`mat-edit-${record.id}`"
            v-show="editingId === record.id"
            style="display: flex; align-items: center; width: 100%; flex-wrap: wrap; gap: 12px; box-sizing: border-box;"
          >
            <div class="m-data-group" style="flex-wrap: wrap; gap: 8px;">
              <div class="m-item" style="display: flex; align-items: center;">
                <span class="m-label-black" style="font-size: 13px;">使用树脂：</span>
                <input
                  v-model.number="editForm.used"
                  type="number"
                  style="width: 70px; height: 28px; padding: 0 4px; border: 1px solid #eb2f96; border-radius: 8px; outline: none; font-weight: bold; color: #eb2f96; text-align: center; background: #fff0f6;"
                />
                <span class="m-val-pink" style="margin-left: 2px; font-size: 13px;">kg</span>
              </div>
              <div class="m-item" style="display: flex; align-items: center;">
                <span class="m-label-black" style="font-size: 13px;">成品：</span>
                <input
                  v-model.number="editForm.produced"
                  type="number"
                  style="width: 70px; height: 28px; padding: 0 4px; border: 1px solid #52c41a; border-radius: 8px; outline: none; font-weight: bold; color: #52c41a; text-align: center; background: #f6ffed;"
                />
                <span class="m-val-green" style="margin-left: 2px; font-size: 13px;">kg</span>
              </div>
              <div class="m-item" style="font-size: 13px;">
                <span class="m-label-blue">剩余：</span>
                <span class="m-val-blue">{{ record.remaining.toFixed(1) }} kg</span>
              </div>
            </div>
            <div style="flex-grow: 1; min-width: 10px;"></div>
            <div class="m-note" style="display: flex; align-items: center; flex: 1; min-width: 140px; max-width: 260px;">
              <span class="m-note-label" style="white-space: nowrap; font-size: 13px;">备注：</span>
              <input
                v-model="editForm.remark"
                type="text"
                placeholder="备注..."
                style="width: 100%; height: 28px; padding: 0 6px; border: 1px solid #b3d8ff; border-radius: 8px; outline: none; color: #111; font-size: 13px; background: #f0f7ff;"
              />
            </div>

            <div style="margin-left: auto; display: flex; align-items: center; gap: 6px; padding-left: 10px;">
              <button
                v-if="userStore.hasPerm('material.delete')"
                class="btn-danger"
                style="padding: 4px 14px; font-size: 12px; border-radius: 20px; border: none; height: 32px; font-weight: bold; color: white; cursor: pointer;"
                @click="deleteRecord(record.id)"
              >
                删除
              </button>
              <button
                class="btn-default"
                style="padding: 4px 14px; font-size: 12px; border-radius: 20px; border: 1px solid #d9d9d9; height: 32px; font-weight: bold; cursor: pointer;"
                @click="cancelEdit"
              >
                取消
              </button>
              <button
                class="btn-primary"
                style="padding: 4px 16px; font-size: 12px; border-radius: 20px; border: none; height: 32px; font-weight: bold; background: linear-gradient(135deg, #52c41a 0%, #389e0d 100%); color: white; cursor: pointer;"
                @click="submitEdit"
              >
                完成
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useUserStore } from '@/stores/user'
import request from '@/api/request'

const userStore = useUserStore()

const loading = ref(false)
const allRecords = ref([])
const editingId = ref(null)
const editForm = ref({
  used: 0,
  produced: 0,
  remark: ''
})

// 日期过滤范围
const filterStartDate = ref(null)
const filterEndDate = ref(null)

// 空状态提示信息
const emptyMessage = computed(() => {
  if (filterStartDate.value && filterEndDate.value) {
    return `没有找到 ${filterStartDate.value} 到 ${filterEndDate.value} 的原材料记录`
  }
  return '最近 30 天内暂无原材料（树脂）使用记录'
})

// 按日期分组的数据
const materialGroups = computed(() => {
  if (allRecords.value.length === 0) return []

  const groups = {}
  allRecords.value.forEach(record => {
    const day = record.date.substring(0, 10)
    if (!groups[day]) {
      groups[day] = []
    }
    groups[day].push(record)
  })

  // 转换为数组并按日期倒序排列
  const result = Object.keys(groups)
    .sort((a, b) => b.localeCompare(a))
    .map(date => ({
      date,
      records: groups[date].sort((a, b) => b.date.localeCompare(a.date))
    }))

  return result
})

// 加载原材料数据
const fetchMaterials = async () => {
  loading.value = true
  try {
    console.log('开始加载原材料数据...')
    const response = await request({ url: '/materials', method: 'GET' })
    console.log('原材料数据响应:', response)

    const matData = response || {}
    let records = matData.records || []
    let currentStock = parseFloat(matData.total_stock) || 0

    console.log('原始记录数:', records.length, '总库存:', currentStock)

    // 按时间正序排列计算剩余库存
    records.sort((a, b) => a.date.localeCompare(b.date))
    records.forEach(r => {
      currentStock -= parseFloat(r.used) || 0
      r.remaining = currentStock
    })

    // 应用日期过滤
    let filteredRecords = []
    if (filterStartDate.value && filterEndDate.value) {
      const startT = new Date(filterStartDate.value.replace(/-/g, '/')).getTime()
      const endT = new Date(filterEndDate.value.replace(/-/g, '/')).getTime() + 86400000 - 1
      filteredRecords = records.filter(r => {
        const dateStr = r.date || ''
        if (!dateStr) return false
        const t = new Date(dateStr.substring(0, 10).replace(/-/g, '/')).getTime()
        return t >= startT && t <= endT
      })
      console.log('日期过滤后记录数:', filteredRecords.length)
    } else {
      // 默认显示最近30天
      const now = new Date()
      const thirtyDaysAgo = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 29).getTime()
      filteredRecords = records.filter(r => {
        const dateStr = r.date || ''
        if (!dateStr) return false
        const t = new Date(dateStr.substring(0, 10).replace(/-/g, '/')).getTime()
        return t >= thirtyDaysAgo
      })
      console.log('默认过滤(最近30天)后记录数:', filteredRecords.length)
    }

    allRecords.value = filteredRecords
    console.log('最终展示记录数:', allRecords.value.length)
  } catch (error) {
    console.error('拉取原材料数据异常:', error)
    alert('加载原材料数据失败，请检查网络连接')
  } finally {
    loading.value = false
  }
}

// 开始编辑
const startEdit = (record) => {
  editingId.value = record.id
  editForm.value = {
    used: record.used,
    produced: record.produced,
    remark: record.remark || ''
  }
}

// 取消编辑
const cancelEdit = () => {
  editingId.value = null
  editForm.value = {
    used: 0,
    produced: 0,
    remark: ''
  }
}

// 提交编辑
const submitEdit = async () => {
  if (isNaN(editForm.value.used) || isNaN(editForm.value.produced)) {
    return alert('保存失败：消耗量与产出量必须输入有效的数字！')
  }

  try {
    await request({
      url: `/materials/${editingId.value}`,
      method: 'PUT',
      data: {
        used: editForm.value.used,
        produced: editForm.value.produced,
        remark: editForm.value.remark
      }
    })
    editingId.value = null
    await fetchMaterials()
  } catch (error) {
    alert('修改失败：底层鉴权拦截或服务器异常')
  }
}

// 删除记录
const deleteRecord = async (id) => {
  if (!confirm('安全警告：您确定要彻底物理删除这条原材料使用流水记录吗？\n删除后所有剩余树脂库存将自动动态重算，此操作不可撤销！')) {
    return
  }

  try {
    await request({
      url: `/materials/${id}`,
      method: 'DELETE'
    })
    await fetchMaterials()
  } catch (error) {
    alert('删除失败：底层权限不足')
  }
}

// 监听日期过滤事件
const handleDateFilter = (event) => {
  filterStartDate.value = event.detail.startDate
  filterEndDate.value = event.detail.endDate
  fetchMaterials()
}

// 监听刷新事件
const handleRefresh = () => {
  fetchMaterials()
}

onMounted(() => {
  // 立即加载数据
  fetchMaterials()

  // 监听日期过滤事件
  window.addEventListener('filter-material-date', handleDateFilter)
  window.addEventListener('refresh-materials', handleRefresh)

  // 监听 Tab 切换事件，当切换到原材料 Tab 时刷新数据
  const handleTabSwitch = (e) => {
    if (e.detail && e.detail.index === 3) {
      fetchMaterials()
    }
  }
  window.addEventListener('switch-tab', handleTabSwitch)
})

onUnmounted(() => {
  window.removeEventListener('filter-material-date', handleDateFilter)
  window.removeEventListener('refresh-materials', handleRefresh)
})

// 暴露刷新方法
defineExpose({
  refresh: fetchMaterials
})
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

/* 时间轴项目网格 */
.timeline-items {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}

/* 原材料卡片 */
.material-card {
  display: flex;
  align-items: center;
  background: #ffffff;
  border-radius: 50px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.03);
  padding: 24px 40px;
  width: 100%;
  border: 1px solid #f0f0f0;
}

/* 数据分组 */
.m-data-group {
  display: flex;
  align-items: center;
  gap: 40px;
  flex-wrap: wrap;
}

/* 数据项 */
.m-item {
  font-size: 18px;
  letter-spacing: 0.5px;
}

/* 标签样式 */
.m-label-black {
  color: #111;
  font-weight: bold;
}

.m-label-blue {
  color: #1A4B84;
  font-weight: bold;
}

/* 值样式 */
.m-val-pink {
  color: #F47B8B;
  font-weight: bold;
}

.m-val-green {
  color: #61D081;
  font-weight: bold;
}

.m-val-blue {
  color: #5C91C5;
  font-weight: bold;
}

/* 分隔符 */
.m-divider {
  width: 1px;
  height: 40px;
  background-color: #e8e8e8;
  margin: 0 24px;
  flex-shrink: 0;
}

/* 备注 */
.m-note {
  font-size: 18px;
}

.m-note-label {
  color: #111;
}

.m-note-val {
  color: #111;
  font-weight: bold;
}

/* 按钮样式 */
.btn-default {
  background: #f5f5f5;
  color: #555;
  border: 1px solid #d9d9d9;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-default:hover {
  background: #e8e8e8;
}

.btn-primary {
  background: #1890ff;
  color: white;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary:hover {
  background: #40a9ff;
}

.btn-danger {
  background: #ff4d4f;
  color: white;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-danger:hover {
  background: #ff7875;
}

/* 响应式 */
@media (max-width: 768px) {
  .timeline-items {
    grid-template-columns: 1fr !important;
  }

  .material-card {
    flex-direction: column !important;
    align-items: flex-start !important;
    border-radius: 20px !important;
    padding: 24px !important;
    width: 100% !important;
  }

  .m-data-group {
    flex-direction: column !important;
    align-items: flex-start !important;
    gap: 16px !important;
  }
}
</style>
