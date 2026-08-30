<template>
  <div v-if="visible" class="modal-overlay" @click="handleOverlayClick">
    <div class="modal-container" @click.stop>
      <!-- 弹窗头部 -->
      <div class="modal-header">
        <h3 class="modal-title">{{ isEdit ? '编辑商品' : '新增商品' }}</h3>
        <button class="btn-close" @click="handleClose">×</button>
      </div>

      <!-- Tab 选项卡 -->
      <div class="modal-tabs">
        <div
          v-for="(tab, index) in tabs"
          :key="index"
          :class="['tab-item', { active: currentTab === index }]"
          @click="currentTab = index"
        >
          {{ tab }}
        </div>
      </div>

      <!-- 弹窗内容 -->
      <div class="modal-body">
        <!-- Tab 0: 基本信息 -->
        <div v-show="currentTab === 0" class="tab-content">
          <!-- 第一行：门店 + 状态 -->
          <div class="form-row">
            <div class="form-group half">
              <label class="required">门店:</label>
              <div class="checkbox-group">
                <label v-for="store in stores" :key="store.id" class="checkbox-item">
                  <input
                    type="checkbox"
                    :value="store.id"
                    v-model="formData.storeIds"
                  />
                  <span class="checkbox-label">{{ store.name }}</span>
                </label>
              </div>
            </div>
            <div class="form-group half">
              <label>状态:</label>
              <ToggleSwitch v-model="formData.enabled" />
            </div>
          </div>

          <!-- 第二行：仓库 + 分类 -->
          <div class="form-row">
            <div class="form-group half">
              <label class="required">仓库:</label>
              <select
                v-model="formData.warehouse"
                class="form-select"
                :disabled="!formData.storeIds || formData.storeIds.length === 0"
              >
                <option value="">请选择默认仓库</option>
                <option
                  v-for="warehouse in filteredWarehouses"
                  :key="warehouse.id"
                  :value="warehouse.id"
                >
                  {{ warehouse.name }}
                </option>
              </select>
            </div>
            <div class="form-group half">
              <label class="required">分类:</label>
              <select
                v-model="formData.category"
                class="form-select"
                :disabled="!formData.warehouse"
              >
                <option value="">请选择商品分类</option>
                <option
                  v-for="category in filteredCategories"
                  :key="category.id"
                  :value="category.id"
                >
                  {{ category.name }}
                </option>
              </select>
            </div>
          </div>

          <!-- 第三行：商品名称 + 编号 -->
          <div class="form-row">
            <div class="form-group half">
              <label class="required">商品名称:</label>
              <input
                v-model="formData.name"
                type="text"
                placeholder="请输入商品名称"
                class="form-input"
              />
            </div>
            <div class="form-group half">
              <label>编号:</label>
              <input
                v-model="formData.code"
                type="text"
                placeholder="请输入编号"
                class="form-input"
              />
            </div>
          </div>

          <!-- 第四行：规格型号 + 备注 -->
          <div class="form-row">
            <div class="form-group half">
              <label>规格型号:</label>
              <input
                v-model="formData.specification"
                type="text"
                placeholder="请输入规格型号"
                class="form-input"
              />
            </div>
            <div class="form-group half">
              <label>备注:</label>
              <input
                v-model="formData.notes"
                type="text"
                placeholder="请输入备注"
                class="form-input"
              />
            </div>
          </div>

          <!-- 第五行：单位 -->
          <div class="form-row">
            <div class="form-group full">
              <label class="required">单位:</label>
              <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
                <label
                  v-for="unit in units"
                  :key="unit.id"
                  :class="['unit-tag', { active: formData.unitId === unit.id }]"
                  @click="formData.unitId = unit.id"
                >
                  {{ unit.name }}
                </label>
                <button type="button" class="btn-add-unit" @click="handleAddUnit">+ 新增</button>
              </div>
            </div>
          </div>

          <!-- 第六行：添加多单位 -->
          <div class="form-row">
            <div class="form-group full">
              <label>添加多单位:</label>
              <div style="display: flex; flex-direction: column; gap: 16px;">
                <!-- 已添加的多单位列表 -->
                <div
                  v-for="(conversion, index) in formData.unitConversions"
                  :key="index"
                  style="display: flex; flex-direction: column; gap: 10px; padding: 12px; border: 1px solid #e5e7eb; border-radius: 8px; background: #f9fafb;"
                >
                  <!-- 第一行：单位换算 -->
                  <div style="display: flex; align-items: center; gap: 10px;">
                    <select v-model="conversion.fromUnitId" class="form-select" style="width: 150px;">
                      <option value="">请选择单位</option>
                      <option v-for="unit in units" :key="unit.id" :value="unit.id">{{ unit.name }}</option>
                    </select>
                    <span>=</span>
                    <input
                      v-model="conversion.value"
                      type="number"
                      step="0.01"
                      placeholder="数量"
                      class="form-input"
                      style="width: 120px;"
                    />
                    <span>{{ getUnitName(formData.unitId) }}</span>
                    <button type="button" class="btn-delete-conversion" @click="removeUnitConversion(index)" title="删除">×</button>
                  </div>

                  <!-- 分裂区域 -->
                  <div v-if="conversion.fromUnitId" style="margin-left: 20px; display: flex; flex-direction: column; gap: 8px;">
                    <div style="font-size: 13px; color: #6b7280; font-weight: 500;">
                      分裂（1{{ getUnitName(conversion.fromUnitId) }} 可分裂成）:
                    </div>

                    <!-- 分裂项列表 -->
                    <div
                      v-for="(split, idx) in conversion.splits"
                      :key="idx"
                      style="display: flex; align-items: center; gap: 10px;"
                    >
                      <input
                        v-model="split.quantity"
                        type="number"
                        step="1"
                        placeholder="数量"
                        class="form-input"
                        style="width: 100px;"
                      />
                      <select v-model="split.unitId" class="form-select" style="width: 120px;">
                        <option value="">请选择单位</option>
                        <option v-for="unit in units" :key="unit.id" :value="unit.id">{{ unit.name }}</option>
                      </select>
                      <button type="button" class="btn-delete-split" @click="removeSplit(index, idx)">×</button>
                    </div>

                    <!-- 添加分裂项按钮 -->
                    <button type="button" class="btn-add-split" @click="addSplit(index)">+ 添加分裂项</button>
                  </div>
                </div>

                <!-- 添加多单位按钮 -->
                <button
                  type="button"
                  class="btn-add-conversion"
                  @click="addUnitConversion"
                  :disabled="!formData.unitId"
                >
                  + 继续添加单位
                </button>
              </div>
            </div>
          </div>

          <!-- 属性展开区域 -->
          <div class="form-row">
            <div class="form-group full">
              <div class="attributes-section">
                <!-- 展开/收起按钮 -->
                <div class="attributes-toggle" @click="toggleAttributes">
                  <span style="color: #3b82f6; font-size: 14px;">属性</span>
                  <span style="color: #3b82f6; font-size: 12px; margin-left: 6px;">{{ attributesExpanded ? '▲' : '▼' }}</span>
                </div>

                <!-- 属性内容区（可展开） -->
                <div v-if="attributesExpanded" class="attributes-content">
                  <!-- 顶部标题栏 -->
                  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <div style="display: flex; align-items: center; gap: 12px;">
                      <span style="font-size: 15px; font-weight: 600; color: #374151;">属性</span>
                      <label style="display: flex; align-items: center; gap: 6px; cursor: pointer;">
                        <input type="checkbox" v-model="formData.enableAttributes" class="checkbox-green" id="enableAttr" />
                        <span style="font-size: 14px; color: #10b981;">启用属性</span>
                      </label>
                      <span style="color: #9ca3af; font-size: 14px; cursor: help;" title="启用属性后可以设置商品的不同规格">?</span>
                    </div>
                    <div style="display: flex; gap: 16px;">
                      <button type="button" class="btn-text-link-add" @click="addNewAttribute">
                        + 新增属性
                      </button>
                    </div>
                  </div>

                  <!-- 属性配置区域（只有启用后才显示） -->
                  <div v-if="formData.enableAttributes">
                    <div style="display: grid; grid-template-columns: 220px 1fr; gap: 30px; margin-bottom: 20px;">
                      <!-- 左侧：属性名称 -->
                      <div>
                        <div style="font-size: 13px; color: #6b7280; font-weight: 600; margin-bottom: 12px;">
                          属性名称
                        </div>
                        <div style="display: flex; flex-direction: column; gap: 8px;">
                          <div
                            v-for="attr in attributesList"
                            :key="attr.id"
                            :class="['attribute-checkbox-item', { checked: attr.selected }]"
                          >
                            <input type="checkbox" v-model="attr.selected" class="checkbox-green" />
                            <span
                              @dblclick="editAttributeName(attr)"
                              style="flex: 1; cursor: text;"
                              :title="'双击编辑'"
                            >{{ attr.name }}</span>
                            <button
                              type="button"
                              class="btn-delete-attr"
                              @click="deleteAttributeById(attr.id)"
                              title="删除属性"
                            >×</button>
                          </div>
                        </div>
                      </div>

                      <!-- 右侧：属性选项 -->
                      <div>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                          <span style="font-size: 13px; color: #6b7280; font-weight: 600;">属性选项</span>
                          <button type="button" class="btn-text-link-cancel" @click="addAttributeOption">
                            + 新增属性选项
                          </button>
                        </div>

                        <!-- 显示已选属性的选项 -->
                        <div v-if="selectedAttributes.length === 0" style="color: #9ca3af; font-size: 13px; padding: 40px 20px; text-align: center; background: #f9fafb; border: 1px dashed #d1d5db; border-radius: 6px;">
                          请先在左侧选择属性名称
                        </div>
                        <div v-else style="display: flex; flex-direction: column; gap: 16px;">
                          <div
                            v-for="attr in selectedAttributes"
                            :key="attr.id"
                            style="display: flex; flex-direction: column; gap: 8px;"
                          >
                            <div style="font-size: 13px; font-weight: 600; color: #374151;">{{ attr.name }}</div>
                            <div style="display: flex; flex-wrap: wrap; gap: 10px;">
                              <label
                                v-for="option in attr.options"
                                :key="option.id"
                                :class="['option-checkbox-tag', { checked: option.selected }]"
                              >
                                <input type="checkbox" v-model="option.selected" style="display: none;" />
                                <span
                                  @dblclick="editAttributeOption(attr, option)"
                                  :title="'双击编辑'"
                                >{{ option.name }}</span>
                                <button
                                  type="button"
                                  class="btn-delete-option"
                                  @click.stop="deleteAttributeOption(attr.id, option.id)"
                                  title="删除选项"
                                >×</button>
                              </label>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>

                    <!-- 价格&条码表格 -->
                    <div v-if="selectedAttributeCombinations.length > 0" style="margin-top: 30px; border-top: 1px solid #e5e7eb; padding-top: 20px;">
                      <div style="font-size: 15px; font-weight: 600; color: #374151; margin-bottom: 16px;">价格&条码</div>

                      <div style="overflow-x: auto;">
                        <table class="attribute-price-table">
                          <thead>
                            <tr>
                              <th style="min-width: 150px;">属性名称</th>
                              <th style="min-width: 120px;">
                                进货价
                                <button type="button" class="btn-batch-link">批量</button>
                              </th>
                              <th style="min-width: 120px;">
                                批发价
                                <button type="button" class="btn-batch-link">批量</button>
                              </th>
                              <th style="min-width: 120px;">
                                零售价
                                <button type="button" class="btn-batch-link">批量</button>
                              </th>
                              <th style="min-width: 120px;">
                                条形码
                                <button type="button" class="btn-batch-link">批量</button>
                              </th>
                              <th style="width: 80px;">启用</th>
                            </tr>
                          </thead>
                          <tbody>
                            <tr v-for="(combo, index) in selectedAttributeCombinations" :key="index">
                              <td>{{ combo.name }}</td>
                              <td>
                                <input
                                  v-model="combo.purchasePrice"
                                  type="number"
                                  step="0.01"
                                  placeholder="进货价"
                                  class="table-input"
                                />
                              </td>
                              <td>
                                <input
                                  v-model="combo.wholesalePrice"
                                  type="number"
                                  step="0.01"
                                  placeholder="批发价"
                                  class="table-input"
                                />
                              </td>
                              <td>
                                <input
                                  v-model="combo.retailPrice"
                                  type="number"
                                  step="0.01"
                                  placeholder="零售价"
                                  class="table-input"
                                />
                              </td>
                              <td>
                                <input
                                  v-model="combo.barcode"
                                  type="text"
                                  placeholder="条形码"
                                  class="table-input"
                                />
                              </td>
                              <td style="text-align: center;">
                                <input type="checkbox" v-model="combo.enabled" class="checkbox-green" />
                              </td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Tab 1: 属性 -->
        <div v-show="currentTab === 1" class="tab-content">
          <p class="empty-tip">属性设置</p>
        </div>

        <!-- Tab 2: 价格&条码 -->
        <div v-show="currentTab === 2" class="tab-content">
          <p class="empty-tip">价格和条码设置</p>
        </div>

        <!-- Tab 3: 库存设置 -->
        <div v-show="currentTab === 3" class="tab-content">
          <div class="warehouse-section">
            <div class="section-header">
              <div>
                <h4 class="section-title">仓库管理</h4>
                <p class="section-desc">管理仓库及其分类，为商品选择所属仓库及分类</p>
              </div>
              <button class="btn-add-warehouse" @click="handleAddWarehouse">
                <span>+</span> 新增仓库
              </button>
            </div>

            <div class="warehouse-list">
              <div v-for="warehouse in warehouses" :key="warehouse.id" class="warehouse-item">
                <div class="warehouse-header">
                  <label class="warehouse-checkbox">
                    <input
                      type="checkbox"
                      :value="warehouse.id"
                      @change="handleWarehouseChange(warehouse.id, $event.target.checked)"
                      :checked="isWarehouseSelected(warehouse.id)"
                    />
                    <span class="warehouse-name">{{ warehouse.name }}</span>
                  </label>
                  <div class="warehouse-actions">
                    <button class="btn-icon" @click="handleEditWarehouse(warehouse)" title="修改仓库">
                      <span>✏️</span>
                    </button>
                    <button class="btn-icon btn-danger" @click="handleDeleteWarehouse(warehouse.id)" title="删除仓库">
                      <span>🗑️</span>
                    </button>
                  </div>
                </div>

                <div v-if="isWarehouseSelected(warehouse.id)" class="category-section">
                  <div class="category-header">
                    <span class="category-title">分类列表</span>
                    <button class="btn-add-category" @click="handleAddCategory(warehouse.id)">
                      <span>+</span> 新增分类
                    </button>
                  </div>

                  <div class="category-list">
                    <div
                      v-for="category in warehouse.categories"
                      :key="category.id"
                      class="category-item"
                    >
                      <label class="category-checkbox">
                        <input
                          type="checkbox"
                          :value="category.id"
                          v-model="formData.warehouseCategories[warehouse.id]"
                        />
                        <span class="category-label">{{ category.name }}</span>
                      </label>
                      <div class="category-actions">
                        <button class="btn-icon-sm" @click="handleEditCategory(warehouse.id, category)" title="修改分类">
                          ✏️
                        </button>
                        <button class="btn-icon-sm btn-danger" @click="handleDeleteCategory(warehouse.id, category.id)" title="删除分类">
                          ×
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div v-if="warehouses.length === 0" class="empty-tip">
                暂无仓库，请点击"新增仓库"添加
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 弹窗底部 -->
      <div class="modal-footer">
        <button class="btn-cancel" @click="handleClose">取消</button>
        <button class="btn-save" @click="handleSave">保存</button>
        <button class="btn-save-continue" @click="handleSaveAndContinue">保存并继续新增</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue'
import request from '@/api/request'
import ToggleSwitch from '@/components/common/ToggleSwitch.vue'

const visible = ref(false)
const isEdit = ref(false)
const currentTab = ref(0)
const stores = ref([])
const allWarehouses = ref([]) // 所有仓库数据
const units = ref([]) // 单位列表
const attributesExpanded = ref(false) // 属性区域是否展开
const attributesList = ref([]) // 属性列表（从数据库加载）

const tabs = ['基本信息', '仓库', '价格&条码', '库存设置']

const formData = reactive({
  code: '',
  name: '',
  specification: '',
  category: '',
  unitId: null,
  enableMultiUnit: false,
  notes: '',
  enabled: true,
  warehouse: '',
  storeIds: [],
  warehouseCategories: {}, // 格式: { 仓库ID: [分类ID数组] }
  unitConversions: [], // 单位换算关系: [{ fromUnitId: 1, value: 10 }] 表示 1个fromUnit = 10个baseUnit
  enableAttributes: false, // 是否启用属性
  attributes: [] // 选中的属性和选项
})

const emit = defineEmits(['save', 'refresh'])

// 根据选择的门店筛选仓库
const filteredWarehouses = computed(() => {
  if (!formData.storeIds || formData.storeIds.length === 0) {
    return []
  }

  // 筛选属于选中门店的仓库
  return allWarehouses.value.filter(warehouse =>
    formData.storeIds.includes(warehouse.storeId)
  )
})

// 根据选择的仓库获取分类列表
const filteredCategories = computed(() => {
  if (!formData.warehouse) {
    return []
  }

  // 找到选中的仓库
  const selectedWarehouse = allWarehouses.value.find(w => w.id === formData.warehouse)
  return selectedWarehouse?.categories || []
})

// 用于"库存设置" Tab 的仓库列表（和以前一样）
const warehouses = computed(() => filteredWarehouses.value)

// 已选中的属性
const selectedAttributes = computed(() => {
  return attributesList.value.filter(attr => attr.selected)
})

// 生成属性组合用于价格表格
const selectedAttributeCombinations = computed(() => {
  const selected = selectedAttributes.value
  if (selected.length === 0) return []

  // 获取所有已选中的属性选项
  const selectedOptions = selected.map(attr => {
    return attr.options.filter(opt => opt.selected)
  })

  // 如果有任何属性没有选中选项，返回空
  if (selectedOptions.some(opts => opts.length === 0)) return []

  // 生成笛卡尔积组合
  const combinations = cartesianProduct(selectedOptions)

  return combinations.map((combo, index) => {
    const name = combo.map(opt => opt.name).join(' / ')
    return {
      id: index,
      name: name,
      purchasePrice: '',
      wholesalePrice: '',
      retailPrice: '',
      barcode: '',
      enabled: true
    }
  })
})

// 笛卡尔积辅助函数
const cartesianProduct = (arrays) => {
  if (arrays.length === 0) return []
  if (arrays.length === 1) return arrays[0].map(item => [item])

  const result = []
  const restProduct = cartesianProduct(arrays.slice(1))

  for (const item of arrays[0]) {
    for (const rest of restProduct) {
      result.push([item, ...rest])
    }
  }

  return result
}

// 监听门店选择变化，清空仓库选择
watch(() => formData.storeIds, (newStoreIds, oldStoreIds) => {
  if (JSON.stringify(newStoreIds) !== JSON.stringify(oldStoreIds)) {
    // 门店变化时，如果当前选择的仓库不在新的筛选结果中，则清空
    const filteredIds = filteredWarehouses.value.map(w => w.id)
    if (formData.warehouse && !filteredIds.find(w => w.id === formData.warehouse)) {
      formData.warehouse = ''
      formData.category = ''
    }
  }
})

// 监听仓库选择变化，清空分类选择
watch(() => formData.warehouse, (newWarehouse, oldWarehouse) => {
  if (newWarehouse !== oldWarehouse) {
    formData.category = ''
  }
})

// 加载门店数据
const loadStores = async () => {
  try {
    const response = await request({
      url: '/stores',
      method: 'GET'
    })
    if (response && Array.isArray(response)) {
      stores.value = response.filter(s => s.status === 'active')
    }
  } catch (error) {
    console.error('加载门店失败:', error)
  }
}

// 加载仓库数据
const loadWarehouses = async () => {
  try {
    const response = await request({
      url: '/warehouses',
      method: 'GET'
    })
    if (response && Array.isArray(response)) {
      allWarehouses.value = response
    }
  } catch (error) {
    console.error('加载仓库失败:', error)
  }
}

// 加载单位数据
const loadUnits = async () => {
  try {
    const response = await request({
      url: '/products/units',
      method: 'GET'
    })
    if (response && Array.isArray(response)) {
      units.value = response
    }
  } catch (error) {
    console.error('加载单位失败:', error)
  }
}

// 加载属性数据
const loadAttributes = async () => {
  try {
    const response = await request({
      url: '/products/attributes',
      method: 'GET'
    })
    if (response && Array.isArray(response)) {
      // 添加 selected 状态
      attributesList.value = response.map(attr => ({
        ...attr,
        selected: false,
        options: attr.options.map(opt => ({
          ...opt,
          selected: false
        }))
      }))
    }
  } catch (error) {
    console.error('加载属性失败:', error)
  }
}

// 新增单位
const handleAddUnit = async () => {
  const unitName = prompt('请输入新单位名称：')
  if (!unitName || !unitName.trim()) return

  try {
    const response = await request({
      url: '/products/units',
      method: 'POST',
      data: { name: unitName.trim() }
    })
    if (response.success) {
      alert('单位添加成功')
      await loadUnits()
    }
  } catch (error) {
    alert('添加单位失败：' + (error.response?.data?.message || error.message))
  }
}

// 获取单位名称
const getUnitName = (unitId) => {
  const unit = units.value.find(u => u.id === unitId)
  return unit ? unit.name : ''
}

// 添加单位换算
const addUnitConversion = () => {
  if (!formData.unitId) {
    alert('请先选择基础单位')
    return
  }
  formData.unitConversions.push({
    fromUnitId: null,
    value: '',
    splits: [] // 分裂项: [{ quantity: 10, unitId: 5 }]
  })
}

// 删除单位换算
const removeUnitConversion = (index) => {
  formData.unitConversions.splice(index, 1)
}

// 添加分裂项
const addSplit = (conversionIndex) => {
  const conversion = formData.unitConversions[conversionIndex]
  if (!conversion.splits) {
    conversion.splits = []
  }
  conversion.splits.push({
    quantity: '',
    unitId: null
  })
}

// 删除分裂项
const removeSplit = (conversionIndex, splitIndex) => {
  formData.unitConversions[conversionIndex].splits.splice(splitIndex, 1)
}

// 切换属性展开状态
const toggleAttributes = () => {
  attributesExpanded.value = !attributesExpanded.value
}

// 清空所有属性选择
const clearAllAttributes = () => {
  attributesList.value.forEach(attr => {
    attr.selected = false
    attr.options.forEach(opt => {
      opt.selected = false
    })
  })
}

// 清空选中的属性选项
const clearSelectedOptions = () => {
  attributesList.value.forEach(attr => {
    attr.options.forEach(opt => {
      opt.selected = false
    })
  })
}

// 双击编辑属性选项
const editAttributeOption = async (attr, option) => {
  const newName = prompt('修改选项名称：', option.name)
  if (!newName || !newName.trim() || newName === option.name) return

  try {
    // 更新选项列表
    const updatedOptions = attr.options.map(opt =>
      opt.id === option.id ? { ...opt, name: newName.trim() } : opt
    )

    const response = await request({
      url: `/products/attributes/${attr.id}`,
      method: 'PUT',
      data: { options: updatedOptions }
    })
    if (response.success) {
      option.name = newName.trim()
    }
  } catch (error) {
    alert('修改失败：' + (error.response?.data?.message || error.message))
  }
}

// 删除属性选项
const deleteAttributeOption = async (attrId, optionId) => {
  if (!confirm('确定要删除这个选项吗？')) return

  try {
    const response = await request({
      url: `/products/attributes/${attrId}/options/${optionId}`,
      method: 'DELETE'
    })
    if (response.success) {
      await loadAttributes()
    }
  } catch (error) {
    alert('删除失败：' + (error.response?.data?.message || error.message))
  }
}

// 双击编辑属性名称
const editAttributeName = async (attr) => {
  const newName = prompt('修改属性名称：', attr.name)
  if (!newName || !newName.trim() || newName === attr.name) return

  try {
    const response = await request({
      url: `/products/attributes/${attr.id}`,
      method: 'PUT',
      data: { name: newName.trim() }
    })
    if (response.success) {
      attr.name = newName.trim()
    }
  } catch (error) {
    alert('修改失败：' + (error.response?.data?.message || error.message))
  }
}

// 删除属性（通过ID）
const deleteAttributeById = async (attrId) => {
  const attr = attributesList.value.find(a => a.id === attrId)
  if (!attr) return

  if (!confirm(`确定要删除属性"${attr.name}"吗？`)) return

  try {
    const response = await request({
      url: `/products/attributes/${attrId}`,
      method: 'DELETE'
    })
    if (response.success) {
      await loadAttributes()
    }
  } catch (error) {
    alert('删除失败：' + (error.response?.data?.message || error.message))
  }
}

// 刷新属性（重新加载）
const deleteAttribute = async () => {
  if (confirm('确定要刷新属性列表吗？这将重新加载所有属性数据。')) {
    await loadAttributes()
  }
}

// 新增属性选项
const addAttributeOption = async () => {
  const selected = selectedAttributes.value
  if (selected.length === 0) {
    alert('请先选择一个属性')
    return
  }
  if (selected.length > 1) {
    alert('请只选择一个属性来添加选项')
    return
  }

  const attr = selected[0]
  const optionName = prompt(`为"${attr.name}"添加新选项：`)
  if (!optionName || !optionName.trim()) return

  try {
    const response = await request({
      url: `/products/attributes/${attr.id}/options`,
      method: 'POST',
      data: { name: optionName.trim() }
    })
    if (response.success) {
      alert('选项添加成功')
      await loadAttributes()
    }
  } catch (error) {
    alert('添加选项失败：' + (error.response?.data?.message || error.message))
  }
}

// 新增属性
const addNewAttribute = async () => {
  const attrName = prompt('请输入新属性名称：')
  if (!attrName || !attrName.trim()) return

  try {
    const response = await request({
      url: '/products/attributes',
      method: 'POST',
      data: { name: attrName.trim() }
    })
    if (response.success) {
      alert('属性添加成功')
      await loadAttributes()
    }
  } catch (error) {
    alert('添加属性失败：' + (error.response?.data?.message || error.message))
  }
}

onMounted(() => {
  loadStores()
  loadWarehouses()
  loadUnits()
  loadAttributes()
})

// 打开弹窗
const open = (product = null) => {
  visible.value = true
  currentTab.value = 0

  if (product) {
    isEdit.value = true
    Object.assign(formData, product)
  } else {
    isEdit.value = false
    resetForm()
  }
}

// 关闭弹窗
const handleClose = () => {
  visible.value = false
}

// 点击遮罩层关闭
const handleOverlayClick = () => {
  handleClose()
}

// 重置表单
const resetForm = () => {
  Object.assign(formData, {
    code: '',
    name: '',
    specification: '',
    category: '',
    unit: '',
    enableMultiUnit: false,
    notes: '',
    enabled: true,
    warehouse: '',
    storeIds: [],
    warehouseCategories: {}
  })
}

// 新增分类
const handleNewCategory = () => {
  console.log('新增分类')
}

// 处理仓库选择
const handleWarehouseChange = (warehouseId, checked) => {
  if (checked) {
    // 选中仓库时，初始化为空数组
    if (!formData.warehouseCategories[warehouseId]) {
      formData.warehouseCategories[warehouseId] = []
    }
  } else {
    // 取消选中时，删除该仓库的分类数据
    delete formData.warehouseCategories[warehouseId]
  }
}

// 判断仓库是否被选中
const isWarehouseSelected = (warehouseId) => {
  return warehouseId in formData.warehouseCategories
}

// 新增仓库
const handleAddWarehouse = () => {
  const name = prompt('请输入仓库名称:')
  if (!name || !name.trim()) return

  const newId = Math.max(...warehouses.value.map(w => w.id), 0) + 1
  warehouses.value.push({
    id: newId,
    name: name.trim(),
    categories: []
  })
}

// 修改仓库
const handleEditWarehouse = (warehouse) => {
  const newName = prompt('请输入新的仓库名称:', warehouse.name)
  if (!newName || !newName.trim()) return

  warehouse.name = newName.trim()
}

// 删除仓库
const handleDeleteWarehouse = (warehouseId) => {
  if (!confirm('确定要删除该仓库吗？删除后将无法恢复。')) return

  const index = warehouses.value.findIndex(w => w.id === warehouseId)
  if (index > -1) {
    warehouses.value.splice(index, 1)
    // 同时删除该仓库的选择数据
    delete formData.warehouseCategories[warehouseId]
  }
}

// 新增分类
const handleAddCategory = (warehouseId) => {
  const name = prompt('请输入分类名称:')
  if (!name || !name.trim()) return

  const warehouse = warehouses.value.find(w => w.id === warehouseId)
  if (!warehouse) return

  const newId = Math.max(...warehouse.categories.map(c => c.id), warehouseId * 100) + 1
  warehouse.categories.push({
    id: newId,
    name: name.trim()
  })
}

// 修改分类
const handleEditCategory = (warehouseId, category) => {
  const newName = prompt('请输入新的分类名称:', category.name)
  if (!newName || !newName.trim()) return

  category.name = newName.trim()
}

// 删除分类
const handleDeleteCategory = (warehouseId, categoryId) => {
  if (!confirm('确定要删除该分类吗？')) return

  const warehouse = warehouses.value.find(w => w.id === warehouseId)
  if (!warehouse) return

  const index = warehouse.categories.findIndex(c => c.id === categoryId)
  if (index > -1) {
    warehouse.categories.splice(index, 1)
    // 如果该分类被选中，从选择中移除
    if (formData.warehouseCategories[warehouseId]) {
      const catIndex = formData.warehouseCategories[warehouseId].indexOf(categoryId)
      if (catIndex > -1) {
        formData.warehouseCategories[warehouseId].splice(catIndex, 1)
      }
    }
  }
}

// 保存
const handleSave = async () => {
  // 验证必填项
  if (!formData.storeIds || formData.storeIds.length === 0) {
    alert('请至少选择一个门店')
    return
  }

  if (!formData.warehouse) {
    alert('请选择仓库')
    return
  }

  if (!formData.category) {
    alert('请选择分类')
    return
  }

  if (!formData.name) {
    alert('请输入商品名称')
    return
  }

  if (!formData.unitId) {
    alert('请选择单位')
    return
  }

  try {
    // 准备提交数据
    const submitData = {
      storeIds: formData.storeIds,
      warehouse: formData.warehouse,
      category: formData.category,
      name: formData.name,
      code: formData.code,
      specification: formData.specification,
      notes: formData.notes,
      unitId: formData.unitId,
      unitConversions: formData.unitConversions,
      enableAttributes: formData.enableAttributes,
      enabled: formData.enabled
    }

    // 如果启用了属性，添加属性组合数据
    if (formData.enableAttributes && selectedAttributeCombinations.value.length > 0) {
      submitData.attributeCombinations = selectedAttributeCombinations.value
    }

    // 调用API保存
    const url = isEdit.value ? `/products/${formData.id}` : '/products'
    const method = isEdit.value ? 'PUT' : 'POST'

    const response = await request({
      url,
      method,
      data: submitData
    })

    if (response.success) {
      alert(isEdit.value ? '更新成功' : '添加成功')
      emit('save', response.product)
      handleClose()
    }
  } catch (error) {
    alert('保存失败：' + (error.response?.data?.message || error.message))
  }
}

// 保存并继续新增
const handleSaveAndContinue = async () => {
  // 验证必填项
  if (!formData.storeIds || formData.storeIds.length === 0) {
    alert('请至少选择一个门店')
    return
  }

  if (!formData.warehouse) {
    alert('请选择仓库')
    return
  }

  if (!formData.category) {
    alert('请选择分类')
    return
  }

  if (!formData.name) {
    alert('请输入商品名称')
    return
  }

  if (!formData.unitId) {
    alert('请选择单位')
    return
  }

  try {
    // 准备提交数据
    const submitData = {
      storeIds: formData.storeIds,
      warehouse: formData.warehouse,
      category: formData.category,
      name: formData.name,
      code: formData.code,
      specification: formData.specification,
      notes: formData.notes,
      unitId: formData.unitId,
      unitConversions: formData.unitConversions,
      enableAttributes: formData.enableAttributes,
      enabled: formData.enabled
    }

    // 如果启用了属性，添加属性组合数据
    if (formData.enableAttributes && selectedAttributeCombinations.value.length > 0) {
      submitData.attributeCombinations = selectedAttributeCombinations.value
    }

    // 调用API保存
    const response = await request({
      url: '/products',
      method: 'POST',
      data: submitData
    })

    if (response.success) {
      alert('添加成功')
      emit('save', response.product)
      resetForm()
    }
  } catch (error) {
    alert('保存失败：' + (error.response?.data?.message || error.message))
  }
}

defineExpose({
  open
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-container {
  width: 90%;
  max-width: 960px;
  max-height: 90vh;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
}

/* 头部 */
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e5e7eb;
}

.modal-title {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.btn-close {
  font-size: 28px;
  color: #9ca3af;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.3s;
}

.btn-close:hover {
  background: #f3f4f6;
  color: #1f2937;
}

/* Tab 选项卡 */
.modal-tabs {
  display: flex;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
}

.tab-item {
  flex: 1;
  padding: 12px 16px;
  text-align: center;
  font-size: 14px;
  color: #6b7280;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.3s;
}

.tab-item:hover {
  color: #10b981;
  background: #f3f4f6;
}

.tab-item.active {
  color: #10b981;
  border-bottom-color: #10b981;
  font-weight: 600;
  background: white;
}

/* 内容区 */
.modal-body {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

.tab-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-row {
  display: flex;
  gap: 16px;
}

.form-group {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  min-width: 0;
}

.form-group.half {
  flex: 1;
}

.form-group.full {
  flex: 1;
  width: 100%;
}

.form-group label {
  font-size: 14px;
  color: #374151;
  white-space: nowrap;
  min-width: 80px;
  text-align: right;
  padding-top: 8px;
}

.form-group label.required::before {
  content: '*';
  color: #ef4444;
  margin-right: 4px;
}

.form-input,
.form-select,
.form-textarea {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 14px;
  outline: none;
  transition: all 0.3s;
  font-family: inherit;
}

.form-input:focus,
.form-select:focus,
.form-textarea:focus {
  border-color: #10b981;
  box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.1);
}

.form-input::placeholder,
.form-textarea::placeholder {
  color: #9ca3af;
}

.form-select {
  cursor: pointer;
}

.form-textarea {
  resize: vertical;
  min-height: 80px;
}

/* 复选框组 */
.checkbox-group {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  padding: 8px 0;
}

.checkbox-item {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  font-size: 14px;
  color: #374151;
  user-select: none;
}

.checkbox-item input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: #10b981;
}

.checkbox-label {
  cursor: pointer;
}

.checkbox-item:hover .checkbox-label {
  color: #10b981;
}

.input-with-link {
  flex: 1;
  display: flex;
  gap: 8px;
  align-items: center;
}

.link-new {
  color: #10b981;
  text-decoration: none;
  font-size: 14px;
  white-space: nowrap;
  cursor: pointer;
}

.link-new:hover {
  text-decoration: underline;
}

.unit-group {
  flex: 1;
  display: flex;
  gap: 12px;
  align-items: center;
}

.checkbox-inline {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: #6b7280;
  cursor: pointer;
  white-space: nowrap;
}

.checkbox-inline input[type="checkbox"] {
  cursor: pointer;
  accent-color: #10b981;
}

.empty-tip {
  text-align: center;
  color: #9ca3af;
  padding: 40px 0;
  font-size: 14px;
}

/* 仓库分类设置 */
.warehouse-section {
  padding: 16px 0;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 8px 0;
}

.section-desc {
  font-size: 13px;
  color: #6b7280;
  margin: 0;
}

.btn-add-warehouse {
  padding: 8px 16px;
  background: #10b981;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.3s;
  font-weight: 500;
}

.btn-add-warehouse:hover {
  background: #059669;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(16, 185, 129, 0.3);
}

.btn-add-warehouse span {
  font-size: 18px;
}

.warehouse-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.warehouse-item {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
  background: #f9fafb;
  transition: all 0.3s;
}

.warehouse-item:hover {
  border-color: #10b981;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.1);
}

.warehouse-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.warehouse-checkbox {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  user-select: none;
}

.warehouse-checkbox input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: #10b981;
}

.warehouse-name {
  font-size: 15px;
  font-weight: 600;
  color: #374151;
}

.warehouse-actions {
  display: flex;
  gap: 8px;
}

.btn-icon {
  padding: 6px 10px;
  background: white;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
}

.btn-icon:hover {
  background: #f3f4f6;
  border-color: #9ca3af;
  transform: scale(1.05);
}

.btn-icon.btn-danger:hover {
  background: #fee2e2;
  border-color: #ef4444;
}

.category-section {
  padding: 12px;
  background: white;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
}

.category-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e5e7eb;
}

.category-title {
  font-size: 13px;
  font-weight: 600;
  color: #6b7280;
}

.btn-add-category {
  padding: 4px 12px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: all 0.2s;
}

.btn-add-category:hover {
  background: #2563eb;
}

.category-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 8px;
}

.category-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-radius: 4px;
  border: 1px solid #e5e7eb;
  transition: all 0.2s;
  background: #f9fafb;
}

.category-item:hover {
  background: #f3f4f6;
  border-color: #10b981;
}

.category-checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
  flex: 1;
}

.category-checkbox input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: #10b981;
}

.category-label {
  font-size: 14px;
  color: #374151;
}

.category-actions {
  display: flex;
  gap: 4px;
  margin-left: 8px;
}

.btn-icon-sm {
  padding: 2px 6px;
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 14px;
  color: #6b7280;
  border-radius: 3px;
  transition: all 0.2s;
}

.btn-icon-sm:hover {
  background: #e5e7eb;
  color: #374151;
}

.btn-icon-sm.btn-danger {
  font-size: 18px;
  font-weight: bold;
}

.btn-icon-sm.btn-danger:hover {
  background: #fee2e2;
  color: #ef4444;
}

/* 底部 */
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #e5e7eb;
  background: #f9fafb;
}

.btn-cancel,
.btn-save,
.btn-save-continue {
  padding: 8px 20px;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-cancel {
  background: white;
  color: #6b7280;
  border: 1px solid #d1d5db;
}

.btn-cancel:hover {
  background: #f3f4f6;
  border-color: #9ca3af;
}

.btn-save {
  background: #10b981;
  color: white;
}

.btn-save:hover {
  background: #059669;
}

.btn-save-continue {
  background: #3b82f6;
  color: white;
}

.btn-save-continue:hover {
  background: #2563eb;
}

/* 单位标签样式 */
.unit-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 8px 16px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  color: #374151;
  background: white;
  cursor: pointer;
  transition: all 0.3s;
  user-select: none;
}

.unit-tag:hover {
  border-color: #10b981;
  color: #10b981;
  background: #f0fdf4;
}

.unit-tag.active {
  border-color: #10b981;
  background: #10b981;
  color: white;
  font-weight: 600;
}

.btn-add-unit {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 8px 16px;
  border: 1px dashed #9ca3af;
  border-radius: 6px;
  background: white;
  color: #6b7280;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-add-unit:hover {
  border-color: #10b981;
  color: #10b981;
  background: #f0fdf4;
}

/* 多单位换算样式 */
.btn-add-conversion {
  padding: 8px 16px;
  border: 1px dashed #9ca3af;
  border-radius: 6px;
  background: white;
  color: #6b7280;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
  align-self: flex-start;
}

.btn-add-conversion:hover:not(:disabled) {
  border-color: #10b981;
  color: #10b981;
  background: #f0fdf4;
}

.btn-add-conversion:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-delete-conversion {
  width: 28px;
  height: 28px;
  border: 1px solid #ef4444;
  border-radius: 4px;
  background: white;
  color: #ef4444;
  font-size: 20px;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  line-height: 1;
}

.btn-delete-conversion:hover {
  background: #ef4444;
  color: white;
}

/* 分裂按钮样式 */
.btn-split {
  padding: 6px 14px;
  border: 1px solid #3b82f6;
  border-radius: 4px;
  background: white;
  color: #3b82f6;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-split:hover {
  background: #3b82f6;
  color: white;
}

/* 分裂弹窗样式 */
.split-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
}

.split-modal {
  background: white;
  border-radius: 8px;
  width: 480px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
}

.split-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
}

.split-modal-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.btn-close-split {
  font-size: 24px;
  color: #9ca3af;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.3s;
}

.btn-close-split:hover {
  background: #f3f4f6;
  color: #1f2937;
}

.split-modal-body {
  padding: 20px;
  overflow-y: auto;
}

.split-modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 16px 20px;
  border-top: 1px solid #e5e7eb;
  background: #f9fafb;
}

.btn-add-split {
  padding: 8px 16px;
  border: 1px dashed #9ca3af;
  border-radius: 6px;
  background: white;
  color: #6b7280;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
  margin-top: 10px;
}

.btn-add-split:hover {
  border-color: #3b82f6;
  color: #3b82f6;
  background: #eff6ff;
}

.btn-delete-split {
  width: 28px;
  height: 28px;
  border: 1px solid #ef4444;
  border-radius: 4px;
  background: white;
  color: #ef4444;
  font-size: 20px;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  line-height: 1;
}

.btn-delete-split:hover {
  background: #ef4444;
  color: white;
}

/* 属性区域样式 */
.attributes-section {
  width: 100%;
}

.attributes-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
  user-select: none;
}

.attributes-toggle:hover {
  background: #dbeafe;
  border-color: #93c5fd;
}

.attributes-content {
  margin-top: 16px;
  padding: 20px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.checkbox-green {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: #10b981;
}

.attribute-checkbox-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  transition: all 0.3s;
  font-size: 14px;
  color: #374151;
}

.attribute-checkbox-item:hover {
  border-color: #10b981;
  background: #f0fdf4;
}

.attribute-checkbox-item.checked {
  border-color: #10b981;
  background: #f0fdf4;
}

.btn-delete-attr {
  width: 20px;
  height: 20px;
  border: none;
  background: none;
  color: #ef4444;
  font-size: 18px;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  line-height: 1;
  opacity: 0;
}

.attribute-checkbox-item:hover .btn-delete-attr {
  opacity: 1;
}

.btn-delete-attr:hover {
  color: #dc2626;
  transform: scale(1.2);
}

.option-checkbox-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  background: white;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 13px;
  color: #374151;
  user-select: none;
  position: relative;
}

.option-checkbox-tag:hover {
  border-color: #10b981;
  background: #f0fdf4;
}

.option-checkbox-tag.checked {
  border-color: #10b981;
  background: #10b981;
  color: white;
  font-weight: 500;
}

.btn-delete-option {
  position: absolute;
  top: -6px;
  right: -6px;
  width: 18px;
  height: 18px;
  border: none;
  background: #ef4444;
  color: white;
  font-size: 14px;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  line-height: 1;
  opacity: 0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.option-checkbox-tag:hover .btn-delete-option {
  opacity: 1;
}

.btn-delete-option:hover {
  background: #dc2626;
  transform: scale(1.1);
}

.btn-text-link-refresh {
  padding: 0;
  border: none;
  background: none;
  color: #3b82f6;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-text-link-refresh:hover {
  color: #2563eb;
}

.btn-text-link-add {
  padding: 0;
  border: none;
  background: none;
  color: #3b82f6;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-text-link-add:hover {
  color: #2563eb;
}

.btn-text-link-cancel {
  padding: 0;
  border: none;
  background: none;
  color: #3b82f6;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-text-link-cancel:hover {
  color: #2563eb;
}

/* 价格表格样式 */
.attribute-price-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  overflow: hidden;
}

.attribute-price-table thead {
  background: #f9fafb;
}

.attribute-price-table th {
  padding: 12px;
  text-align: left;
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  border-bottom: 1px solid #e5e7eb;
}

.attribute-price-table td {
  padding: 10px 12px;
  border-bottom: 1px solid #f3f4f6;
  font-size: 13px;
  color: #374151;
}

.attribute-price-table tbody tr:hover {
  background: #f9fafb;
}

.table-input {
  width: 100%;
  padding: 6px 10px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 13px;
  transition: all 0.3s;
}

.table-input:focus {
  outline: none;
  border-color: #10b981;
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1);
}

.btn-batch-link {
  padding: 2px 8px;
  margin-left: 6px;
  border: none;
  background: none;
  color: #3b82f6;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-batch-link:hover {
  color: #2563eb;
  text-decoration: underline;
}

.btn-text-link {
  padding: 0;
  border: none;
  background: none;
  color: #6b7280;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-text-link:hover {
  color: #374151;
}

.btn-text-link-primary {
  padding: 0;
  border: none;
  background: none;
  color: #3b82f6;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-text-link-primary:hover {
  color: #2563eb;
}

.btn-refresh {
  padding: 4px 10px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  background: white;
  color: #6b7280;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-refresh:hover {
  border-color: #10b981;
  color: #10b981;
  background: #f0fdf4;
}

.btn-link-sm {
  padding: 4px 10px;
  border: none;
  background: none;
  color: #3b82f6;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s;
  text-decoration: none;
}

.btn-link-sm:hover {
  color: #2563eb;
  text-decoration: underline;
}
</style>
