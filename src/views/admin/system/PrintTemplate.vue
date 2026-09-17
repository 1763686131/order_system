<template>
  <div class="print-template-page">
    <Teleport to="body">
      <Transition name="notice">
        <div
          v-if="notice.visible"
          :class="['page-notice', `notice-${notice.type}`]"
          :role="notice.type === 'error' ? 'alert' : 'status'"
          :aria-live="notice.type === 'error' ? 'assertive' : 'polite'"
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="12" cy="12" r="9"></circle>
            <path v-if="notice.type === 'success'" d="m8 12 2.7 2.7L16.5 9"></path>
            <path v-else d="M12 8v5M12 17h.01"></path>
          </svg>
          <span>{{ notice.message }}</span>
        </div>
      </Transition>
    </Teleport>

    <!-- 搜索面板 -->
    <section class="search-panel">
      <div class="search-grid">
        <div class="search-field">
          <label class="search-label">模板名称</label>
          <input
            v-model="searchForm.templateName"
            type="text"
            class="search-input"
            placeholder="请输入模板名称"
            @keyup.enter="handleSearch"
          />
        </div>

        <div class="search-field">
          <label class="search-label">业务类型</label>
          <select v-model="searchForm.businessType" class="search-select">
            <option value="">全部类型</option>
            <option value="sale">销售</option>
            <option value="purchase">采购</option>
            <option value="return">退货</option>
            <option value="transfer">调拨</option>
            <option value="inventory">盘点</option>
            <option value="receipt">收款</option>
            <option value="payment">付款</option>
          </select>
        </div>

        <div class="search-field">
          <label class="search-label" style="opacity: 0">占位</label>
          <div class="search-checkbox-wrapper">
            <label class="search-checkbox">
              <input v-model="searchForm.showDisabled" type="checkbox" />
              <span>显示停用</span>
            </label>
          </div>
        </div>

        <div class="search-actions">
          <button type="button" class="btn-search" @click="handleSearch">
            <svg class="btn-icon" viewBox="0 0 24 24" aria-hidden="true">
              <circle cx="11" cy="11" r="8" />
              <path d="m21 21-4.35-4.35" />
            </svg>
            搜索
          </button>
        </div>
      </div>
    </section>

    <!-- 记录面板 -->
    <section class="records-panel">
      <!-- 工具栏 -->
      <div class="records-toolbar">
        <div class="toolbar-left"></div>
        <div class="toolbar-right">
          <button type="button" class="btn-icon-only" title="刷新" @click="handleRefresh">
            <svg class="icon-svg" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M21 2v6h-6" />
              <path d="M3 12a9 9 0 0 1 15-6.7L21 8" />
              <path d="M3 22v-6h6" />
              <path d="M21 12a9 9 0 0 1-15 6.7L3 16" />
            </svg>
          </button>
          <button type="button" class="btn-primary" @click="handleCreate">
            <svg class="btn-icon" viewBox="0 0 24 24" aria-hidden="true">
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            新增
          </button>
        </div>
      </div>

      <!-- 表格容器 -->
      <div class="table-scroll">
        <table class="data-table">
          <thead>
            <tr>
              <th style="width: 200px">模板名称</th>
              <th style="width: 120px">业务类型</th>
              <th style="width: 120px">纸张</th>
              <th style="width: 110px">纸张宽mm</th>
              <th style="width: 110px">纸张高mm</th>
              <th style="width: 80px">默认</th>
              <th style="width: 80px">启用</th>
              <th style="width: 450px; text-align: center">相关操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td colspan="8" class="loading-cell">
                <div class="loading-content">
                  <div class="loading-spinner"></div>
                  <span>加载中...</span>
                </div>
              </td>
            </tr>
            <tr v-else-if="!filteredTemplates.length">
              <td colspan="8" class="empty-cell">
                <div class="empty-content">
                  <div class="empty-icon">📄</div>
                  <div class="empty-text">暂无模板数据</div>
                  <div class="empty-hint">点击右上角"新增"按钮创建打印模板</div>
                </div>
              </td>
            </tr>
            <template v-else>
              <tr
                v-for="template in filteredTemplates"
                :key="template.id"
                class="data-row"
              >
                <td>
                  <button
                    type="button"
                    class="link-button"
                    @click="handleView(template)"
                  >
                    {{ template.name }}
                  </button>
                </td>
                <td>{{ getBusinessTypeLabel(template.businessType) }}</td>
                <td>{{ template.paperType || '自定义' }}</td>
                <td style="text-align: right; font-variant-numeric: tabular-nums">
                  {{ template.pageWidth }}
                </td>
                <td style="text-align: right; font-variant-numeric: tabular-nums">
                  {{ template.pageHeight }}
                </td>
                <td style="text-align: center">
                  <span v-if="template.isDefault" class="status-tag success-tag">是</span>
                  <span v-else class="status-tag muted-tag">否</span>
                </td>
                <td style="text-align: center">
                  <span v-if="template.enabled" class="status-tag success-tag">是</span>
                  <span v-else class="status-tag muted-tag">否</span>
                </td>
                <td style="text-align: center">
                  <div class="action-buttons">
                    <button
                      type="button"
                      class="btn-action btn-primary-action"
                      @click="handleDesign(template)"
                    >
                      设计
                    </button>
                    <button
                      type="button"
                      class="btn-action btn-secondary-action"
                      @click="handlePreview(template)"
                    >
                      查看设计
                    </button>
                    <button
                      type="button"
                      class="btn-action btn-secondary-action"
                      :disabled="copyingTemplateId !== null"
                      @click="handleCopy(template)"
                    >
                      {{
                        String(copyingTemplateId) === String(template.id)
                          ? '复制中'
                          : '复制'
                      }}
                    </button>
                    <button
                      v-if="!template.isDefault"
                      type="button"
                      class="btn-action btn-secondary-action"
                      @click="handleSetDefault(template)"
                    >
                      设为默认
                    </button>
                    <button
                      type="button"
                      class="btn-action btn-secondary-action"
                      @click="handleUse(template)"
                    >
                      使用
                    </button>
                    <button
                      type="button"
                      class="btn-action btn-danger-action"
                      @click="handleDelete(template)"
                    >
                      删除
                    </button>
                  </div>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>

      <!-- 分页 -->
      <div class="table-footer">
        <div class="footer-info">
          共 <strong>{{ filteredTemplates.length }}</strong> 条记录
        </div>
      </div>
    </section>

    <!-- 新增/编辑模板弹窗 -->
    <Teleport to="body">
      <Transition name="modal">
        <div
          v-if="showTemplateModal"
          class="modal-overlay"
          @click.self="showTemplateModal = false"
        >
          <div class="modal-container">
            <div class="modal-header">
              <h3>{{ isEditing ? '编辑模板' : '新增模板' }}</h3>
              <button
                type="button"
                class="modal-close"
                @click="showTemplateModal = false"
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>
            <div class="modal-body">
              <div class="form-grid">
                <div class="form-field">
                  <label class="form-label">模板名称 <span class="required">*</span></label>
                  <input
                    v-model="templateForm.name"
                    type="text"
                    class="form-input"
                    placeholder="请输入模板名称"
                  />
                </div>
                <div class="form-field">
                  <label class="form-label">业务类型 <span class="required">*</span></label>
                  <select v-model="templateForm.businessType" class="form-select">
                    <option value="">请选择</option>
                    <option value="sale">销售</option>
                    <option value="purchase">采购</option>
                    <option value="return">退货</option>
                    <option value="transfer">调拨</option>
                    <option value="inventory">盘点</option>
                    <option value="receipt">收款</option>
                    <option value="payment">付款</option>
                  </select>
                </div>
                <div class="form-field">
                  <label class="form-label">纸张类型</label>
                  <select v-model="templateForm.paperType" class="form-select">
                    <option value="">自定义</option>
                    <option value="二等分">二等分</option>
                    <option value="A4">A4</option>
                    <option value="小票">小票 (58mm)</option>
                    <option value="标签">标签</option>
                  </select>
                </div>
                <div class="form-field">
                  <label class="form-label">纸张宽度(mm) <span class="required">*</span></label>
                  <input
                    v-model.number="templateForm.pageWidth"
                    type="number"
                    class="form-input"
                    placeholder="210"
                  />
                </div>
                <div class="form-field">
                  <label class="form-label">纸张高度(mm) <span class="required">*</span></label>
                  <input
                    v-model.number="templateForm.pageHeight"
                    type="number"
                    class="form-input"
                    placeholder="140"
                  />
                </div>
                <div class="form-field form-field-full">
                  <label class="form-checkbox">
                    <input v-model="templateForm.enabled" type="checkbox" />
                    <span>启用模板</span>
                  </label>
                </div>
              </div>
            </div>
            <div class="modal-footer">
              <button
                type="button"
                class="btn-secondary"
                @click="showTemplateModal = false"
              >
                取消
              </button>
              <button type="button" class="btn-primary" @click="handleSaveTemplate">
                确定
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <PrintDesignerEditor
      :visible="showDesigner"
      :template="designerTemplate"
      :templates="templates"
      @save="handleDesignerSave"
      @close="closeDesigner"
    />
  </div>
</template>

<script setup>
import { ref, computed, onBeforeUnmount, onMounted } from 'vue'
import {
  getTemplates,
  createTemplate,
  updateTemplate,
  deleteTemplate,
  setDefaultTemplate,
  migrateTemplates
} from '@/api/printTemplate'
import PrintDesignerEditor from '@/components/print/PrintDesignerEditor.vue'

// ==================== 数据 ====================
const loading = ref(false)
const templates = ref([])
const copyingTemplateId = ref(null)
const templateStorageKey = 'order-system-print-templates'
const notice = ref({
  visible: false,
  type: 'success',
  message: ''
})
let noticeTimer = null

const showNotice = (message, type = 'success') => {
  if (noticeTimer !== null) {
    window.clearTimeout(noticeTimer)
  }

  notice.value = {
    visible: true,
    type,
    message: String(message || '')
  }
  noticeTimer = window.setTimeout(() => {
    notice.value.visible = false
    noticeTimer = null
  }, type === 'error' ? 5000 : 3000)
}

const searchForm = ref({
  templateName: '',
  businessType: '',
  showDisabled: false
})

const showTemplateModal = ref(false)
const showDesigner = ref(false)
const designerTemplate = ref(null)
const isEditing = ref(false)
const templateForm = ref({
  id: null,
  name: '',
  businessType: '',
  paperType: '',
  pageWidth: 210,
  pageHeight: 140,
  enabled: true,
  isDefault: false
})

// ==================== 计算属性 ====================
const filteredTemplates = computed(() => {
  let result = templates.value

  // 按名称筛选
  if (searchForm.value.templateName) {
    const keyword = searchForm.value.templateName.toLowerCase()
    result = result.filter((t) => t.name.toLowerCase().includes(keyword))
  }

  // 按业务类型筛选
  if (searchForm.value.businessType) {
    result = result.filter((t) => t.businessType === searchForm.value.businessType)
  }

  // 是否显示停用
  if (!searchForm.value.showDisabled) {
    result = result.filter((t) => t.enabled)
  }

  return result
})

// ==================== 方法 ====================
const getBusinessTypeLabel = (type) => {
  const map = {
    sale: '销售',
    purchase: '采购',
    return: '退货',
    transfer: '调拨',
    inventory: '盘点',
    receipt: '收款',
    payment: '付款'
  }
  return map[type] || type
}

const handleSearch = () => {
  // 搜索逻辑已通过 computed 实现
  console.log('执行搜索')
}

const handleRefresh = async () => {
  await loadTemplates()
}

const handleCreate = () => {
  designerTemplate.value = {
    id: null,
    name: '销售三联单',
    businessType: 'sale',
    paperType: '三联单',
    pageWidth: 210,
    pageHeight: 140,
    enabled: true,
    isDefault: false,
    content: null
  }
  showDesigner.value = true
}

const handleDesign = async (template) => {
  try {
    // 保存模板的设计内容
    const response = await updateTemplate(template.id, {
      ...template,
      content: designerTemplate.value?.content || template.content
    })

    if (response.success) {
      designerTemplate.value = template
      showDesigner.value = true

      // 触发全局事件
      window.dispatchEvent(new CustomEvent('order-system-print-templates-updated', {
        detail: { id: template.id, updatedAt: new Date().toISOString() }
      }))
    } else {
      alert(response.message || '加载设计器失败')
    }
  } catch (error) {
    console.error('加载设计器失败:', error)
    alert('加载设计器失败，请稍后重试')
  }
}

const handleView = (template) => {
  handleDesign(template)
}

const closeDesigner = () => {
  showDesigner.value = false
  designerTemplate.value = null
}

const handleDesignerSave = async (template) => {
  try {
    const savedTemplate = {
      ...template,
      updatedAt: new Date().toISOString()
    }

    let response
    const existingIndex = templates.value.findIndex((item) => (
      template?.id !== undefined &&
      template?.id !== null &&
      String(item.id) === String(template.id)
    ))

    if (existingIndex >= 0) {
      // 更新现有模板
      response = await updateTemplate(template.id, savedTemplate)
    } else {
      // 新增模板
      const { id, ...createPayload } = savedTemplate
      response = await createTemplate(createPayload)
    }

    if (response.success) {
      const savedId = existingIndex >= 0
        ? template.id
        : response.data?.id
      await loadTemplates()
      window.dispatchEvent(new CustomEvent('order-system-print-templates-updated', {
        detail: { id: savedId, updatedAt: savedTemplate.updatedAt }
      }))
      closeDesigner()
      showNotice(`模板“${savedTemplate.name || '未命名模板'}”保存成功`)
    } else {
      showNotice(response.message || '保存模板失败', 'error')
    }
  } catch (error) {
    console.error('保存模板失败:', error)
    showNotice(error?.message || '保存模板失败，请稍后重试', 'error')
  }
}

const handlePreview = (template) => {
  designerTemplate.value = template
  showDesigner.value = true
}

const handleCopy = async (template) => {
  if (!template || copyingTemplateId.value !== null) return

  copyingTemplateId.value = template.id

  try {
    const copiedTemplate = {
      name: `${template.name}复制版`,
      businessType: template.businessType,
      paperType: template.paperType || '',
      pageWidth: template.pageWidth,
      pageHeight: template.pageHeight,
      enabled: template.enabled !== false,
      isDefault: false,
      content: template.content
        ? JSON.parse(JSON.stringify(template.content))
        : null
    }

    const response = await createTemplate(copiedTemplate)
    if (!response?.success) {
      throw new Error(response?.message || '复制模板失败')
    }

    await loadTemplates()
    window.dispatchEvent(new CustomEvent('order-system-print-templates-updated', {
      detail: {
        id: response.data?.id,
        copiedFromId: template.id,
        updatedAt: new Date().toISOString()
      }
    }))
  } catch (error) {
    console.error('复制模板失败:', error)
    alert(error?.message || '复制模板失败，请稍后重试')
  } finally {
    copyingTemplateId.value = null
  }
}

const handleSetDefault = async (template) => {
  try {
    const response = await setDefaultTemplate(template.id)
    if (response.success) {
      // 更新本地状态
      templates.value.forEach((t) => {
        if (t.businessType === template.businessType) {
          t.isDefault = t.id === template.id
        }
      })
      console.log('已设为默认:', template)
    } else {
      alert(response.message || '设置默认模板失败')
    }
  } catch (error) {
    console.error('设置默认模板失败:', error)
    alert('设置默认模板失败，请稍后重试')
  }
}

const handleUse = (template) => {
  console.log('使用模板:', template)
  // TODO: 打开打印预览
}

const handleDelete = async (template) => {
  if (template.isDefault) {
    alert('默认模板不能删除，请先设置其他模板为默认')
    return
  }

  if (!confirm(`确定要删除模板"${template.name}"吗？`)) {
    return
  }

  try {
    const response = await deleteTemplate(template.id)
    if (response.success) {
      const index = templates.value.findIndex((t) => t.id === template.id)
      if (index > -1) {
        templates.value.splice(index, 1)
      }
      console.log('已删除:', template)
    } else {
      alert(response.message || '删除模板失败')
    }
  } catch (error) {
    console.error('删除模板失败:', error)
    alert('删除模板失败，请稍后重试')
  }
}

const handleSaveTemplate = async () => {
  if (!templateForm.value.name) {
    alert('请输入模板名称')
    return
  }
  if (!templateForm.value.businessType) {
    alert('请选择业务类型')
    return
  }
  if (!templateForm.value.pageWidth || !templateForm.value.pageHeight) {
    alert('请输入纸张尺寸')
    return
  }

  try {
    let response
    if (isEditing.value) {
      // 编辑模板
      response = await updateTemplate(templateForm.value.id, templateForm.value)
    } else {
      // 新增模板
      response = await createTemplate(templateForm.value)
    }

    if (response.success) {
      showTemplateModal.value = false
      // 重新加载模板列表
      await loadTemplates()
      console.log('保存模板成功:', response.data)
    } else {
      alert(response.message || '保存模板失败')
    }
  } catch (error) {
    console.error('保存模板失败:', error)
    alert('保存模板失败，请稍后重试')
  }
}

const loadTemplates = async () => {
  loading.value = true
  try {
    const response = await getTemplates()
    if (response.success) {
      templates.value = response.data || []

      // 如果数据库没有数据，尝试从 localStorage 迁移
      if (templates.value.length === 0) {
        await migrateFromLocalStorage()
      }
    } else {
      console.error('加载模板失败:', response.message)
      templates.value = []
    }
  } catch (error) {
    console.error('加载模板失败:', error)
    // 如果后端请求失败，尝试从 localStorage 加载
    await migrateFromLocalStorage()
  } finally {
    loading.value = false
  }
}

const migrateFromLocalStorage = async () => {
  const storedTemplates = localStorage.getItem(templateStorageKey)
  if (storedTemplates) {
    try {
      const parsedTemplates = JSON.parse(storedTemplates)
      if (Array.isArray(parsedTemplates) && parsedTemplates.length > 0) {
        // 迁移到数据库
        const response = await migrateTemplates(parsedTemplates)
        if (response.success) {
          console.log('数据迁移成功:', response.data)
          templates.value = parsedTemplates
          // 清除 localStorage 中的数据
          localStorage.removeItem(templateStorageKey)
        }
      }
    } catch (error) {
      console.error('数据迁移失败:', error)
    }
  }
}

// ==================== 生命周期 ====================
onMounted(() => {
  loadTemplates()
})

onBeforeUnmount(() => {
  if (noticeTimer !== null) {
    window.clearTimeout(noticeTimer)
  }
})
</script>

<style scoped>
/* CSS变量定义 */
.print-template-page {
  --accent: #0f9f78;
  --accent-rgb: 15, 159, 120;
  --accent-dark: #08745a;
  --accent-soft: #e9f8f3;
  --accent-border: #a9e5d2;
  --page-bg: #f4f7f8;
  --panel-bg: #ffffff;
  --border: #e2e8f0;
  --border-strong: #cbd5e1;
  --text: #172033;
  --text-secondary: #596579;
  --text-muted: #8a96a8;

  min-height: 100vh;
  background: var(--page-bg);
  color: var(--text);
  font-size: 14px;
  padding: 18px 20px;
}

.page-notice {
  position: fixed;
  top: 24px;
  left: 50%;
  z-index: 30000;
  display: flex;
  min-width: 0;
  max-width: min(520px, calc(100vw - 32px));
  min-height: 44px;
  align-items: center;
  gap: 9px;
  padding: 10px 16px;
  overflow-wrap: anywhere;
  color: #172033;
  background: #fff;
  border: 1px solid #dfe5ec;
  border-radius: 6px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.16);
  transform: translateX(-50%);
  font-size: 13px;
  font-weight: 600;
  line-height: 1.5;
  box-sizing: border-box;
}

.page-notice svg {
  flex: 0 0 19px;
  width: 19px;
  height: 19px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.notice-success svg {
  color: #0f9f78;
}

.notice-error svg {
  color: #dc3545;
}

.notice-enter-active,
.notice-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.notice-enter-from,
.notice-leave-to {
  opacity: 0;
  transform: translate(-50%, -8px);
}

/* ==================== 搜索面板 ==================== */
.search-panel {
  background: var(--panel-bg);
  border: 1px solid var(--border);
  border-radius: 7px;
  padding: 18px 20px;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
  margin-bottom: 14px;
}

.search-grid {
  display: grid;
  grid-template-columns: minmax(200px, 1fr) minmax(200px, 1fr) minmax(160px, 0.8fr) auto;
  gap: 14px;
  align-items: end;
}

.search-field {
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.search-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text);
}

.search-input,
.search-select {
  height: 38px;
  padding: 0 11px;
  border: 1px solid var(--border-strong);
  border-radius: 5px;
  font-size: 14px;
  color: var(--text);
  background: var(--panel-bg);
  transition: all 0.18s ease;
}

.search-input:focus,
.search-select:focus {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(var(--accent-rgb), 0.1);
}

.search-input::placeholder {
  color: var(--text-muted);
}

.search-checkbox-wrapper {
  height: 38px;
  display: flex;
  align-items: center;
}

.search-checkbox {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 13px;
  color: var(--text-secondary);
  cursor: pointer;
  user-select: none;
}

.search-checkbox input[type='checkbox'] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.search-actions {
  display: flex;
  gap: 10px;
}

.btn-search {
  height: 38px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  padding: 0 20px;
  background: var(--accent);
  color: #ffffff;
  border: 1px solid var(--accent);
  border-radius: 5px;
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
  cursor: pointer;
  transition: all 0.18s ease;
}

.btn-search:hover {
  background: var(--accent-dark);
  border-color: var(--accent-dark);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(var(--accent-rgb), 0.25);
}

.btn-search .btn-icon {
  width: 16px;
  height: 16px;
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}

/* ==================== 记录面板 ==================== */
.records-panel {
  background: var(--panel-bg);
  border: 1px solid var(--border);
  border-radius: 7px;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
  overflow: hidden;
}

.records-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 62px;
  padding: 11px 16px;
  border-bottom: 1px solid var(--border);
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.btn-icon-only {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: var(--panel-bg);
  border: 1px solid var(--border-strong);
  border-radius: 5px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.18s ease;
}

.btn-icon-only:hover {
  background: var(--accent-soft);
  border-color: var(--accent-border);
  color: var(--accent-dark);
}

.btn-icon-only .icon-svg {
  width: 18px;
  height: 18px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.btn-primary {
  height: 38px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  padding: 0 15px;
  background: var(--accent);
  color: #ffffff;
  border: 1px solid var(--accent);
  border-radius: 5px;
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
  cursor: pointer;
  transition: all 0.18s ease;
}

.btn-primary:hover {
  background: var(--accent-dark);
  border-color: var(--accent-dark);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(var(--accent-rgb), 0.25);
}

.btn-primary .btn-icon {
  width: 16px;
  height: 16px;
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}

/* ==================== 表格 ==================== */
.table-scroll {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  min-width: 1200px;
  table-layout: fixed;
  border-collapse: collapse;
}

.data-table thead {
  background: #f8fafc;
}

.data-table th {
  height: 45px;
  padding: 9px 12px;
  font-size: 12px;
  font-weight: 650;
  color: var(--text-secondary);
  text-align: left;
  border-bottom: 1px solid var(--border);
}

.data-table td {
  height: 57px;
  padding: 9px 12px;
  font-size: 14px;
  color: var(--text);
  border-bottom: 1px solid #edf1f5;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.data-row:hover {
  background: rgba(var(--accent-rgb), 0.04);
}

.link-button {
  color: var(--accent-dark);
  font-weight: 600;
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  text-decoration: none;
  transition: all 0.18s ease;
}

.link-button:hover {
  text-decoration: underline;
  color: var(--accent);
}

.status-tag {
  display: inline-flex;
  align-items: center;
  min-height: 25px;
  padding: 3px 9px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 650;
  white-space: nowrap;
}

.success-tag {
  color: #13734f;
  background: #eaf8f1;
}

.muted-tag {
  color: var(--text-muted);
  background: #f1f2f4;
}

.action-buttons {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  flex-wrap: wrap;
}

.btn-action {
  height: 30px;
  padding: 0 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
  cursor: pointer;
  transition: all 0.18s ease;
  border: 1px solid transparent;
}

.btn-action:disabled {
  cursor: wait;
  opacity: 0.55;
}

.btn-primary-action {
  background: var(--accent);
  color: #ffffff;
  border-color: var(--accent);
}

.btn-primary-action:hover {
  background: var(--accent-dark);
  border-color: var(--accent-dark);
}

.btn-secondary-action {
  background: var(--panel-bg);
  color: var(--text-secondary);
  border-color: var(--border-strong);
}

.btn-secondary-action:hover {
  background: var(--accent-soft);
  border-color: var(--accent-border);
  color: var(--accent-dark);
}

.btn-danger-action {
  background: var(--panel-bg);
  color: #b4232f;
  border-color: var(--border-strong);
}

.btn-danger-action:hover {
  background: #fff1f2;
  border-color: #f0a5ad;
  color: #a12635;
}

/* 加载和空状态 */
.loading-cell,
.empty-cell {
  text-align: center;
  height: 290px;
}

.loading-content,
.empty-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 12px;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.empty-icon {
  font-size: 48px;
  opacity: 0.3;
}

.empty-text {
  font-size: 14px;
  color: var(--text);
  font-weight: 600;
}

.empty-hint {
  font-size: 12px;
  color: var(--text-muted);
}

/* ==================== 表格页脚 ==================== */
.table-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 58px;
  padding: 10px 16px;
  border-top: 1px solid var(--border);
  background: var(--panel-bg);
}

.footer-info {
  font-size: 12px;
  color: var(--text-secondary);
}

.footer-info strong {
  font-weight: 700;
  color: var(--text);
  font-variant-numeric: tabular-nums;
}

/* ==================== 弹窗 ==================== */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.42);
  backdrop-filter: blur(1px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.modal-container {
  background: var(--panel-bg);
  border-radius: 7px;
  border: 1px solid var(--border);
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.15);
  width: 600px;
  max-width: 90%;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border);
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 650;
  color: var(--text);
}

.modal-close {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: transparent;
  border: none;
  border-radius: 5px;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.18s ease;
}

.modal-close:hover {
  background: #f1f5f9;
  color: var(--text);
}

.modal-close svg {
  width: 18px;
  height: 18px;
  stroke: currentColor;
  stroke-width: 2;
  stroke-linecap: round;
}

.modal-body {
  padding: 24px;
  overflow-y: auto;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.form-field-full {
  grid-column: 1 / -1;
}

.form-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
}

.required {
  color: #ef4444;
}

.form-input,
.form-select {
  height: 38px;
  padding: 0 11px;
  border: 1px solid var(--border-strong);
  border-radius: 5px;
  font-size: 14px;
  color: var(--text);
  background: var(--panel-bg);
  transition: all 0.18s ease;
}

.form-input:focus,
.form-select:focus {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(var(--accent-rgb), 0.1);
}

.form-checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--text-secondary);
  cursor: pointer;
  user-select: none;
}

.form-checkbox input[type='checkbox'] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.modal-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid var(--border);
}

.btn-secondary {
  height: 38px;
  padding: 0 20px;
  background: var(--panel-bg);
  color: var(--text-secondary);
  border: 1px solid var(--border-strong);
  border-radius: 5px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.18s ease;
}

.btn-secondary:hover {
  background: var(--accent-soft);
  border-color: var(--accent-border);
  color: var(--accent-dark);
}

/* 弹窗动画 */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: all 0.25s ease;
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: translateY(20px);
  opacity: 0;
}

/* ==================== 响应式 ==================== */
@media (max-width: 1280px) {
  .search-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .search-actions {
    grid-column: 1 / -1;
  }
}

@media (max-width: 780px) {
  .page-notice {
    top: 12px;
    max-width: calc(100vw - 32px);
  }

  .print-template-page {
    padding: 12px;
  }

  .search-grid {
    grid-template-columns: 1fr;
  }

  .toolbar-right {
    flex-wrap: wrap;
  }

  .action-buttons {
    flex-direction: column;
    gap: 6px;
  }

  .btn-action {
    width: 100%;
  }

  .modal-container {
    width: calc(100vw - 32px);
  }

  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
