<template>
  <Teleport to="body">
    <Transition name="logistics-copy-settings">
      <div
        v-if="visible"
        class="logistics-copy-settings-overlay"
        @click.self="handleClose"
        @keydown.esc.prevent="handleClose"
      >
        <section
          class="logistics-copy-settings-dialog"
          role="dialog"
          aria-modal="true"
          aria-labelledby="logistics-copy-settings-title"
        >
          <header class="settings-header">
            <div>
              <span class="settings-eyebrow">物流工具</span>
              <h2 id="logistics-copy-settings-title">复制字段设置</h2>
              <p>自定义物流列表复制内容的字段、名称和排列顺序。</p>
            </div>
            <button
              type="button"
              class="icon-close"
              title="关闭"
              aria-label="关闭"
              @click="handleClose"
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="m6 6 12 12M18 6 6 18"></path>
              </svg>
            </button>
          </header>

          <div v-if="settingsError" class="settings-error" role="alert">{{ settingsError }}</div>
          <div class="settings-body" :class="{ 'settings-body-disabled': loadingSettings || loadFailed || savingSettings }" :inert="loadingSettings || loadFailed || savingSettings">
            <aside class="variable-panel" aria-label="变量工具">
              <div class="variable-panel-tabs" role="tablist" aria-label="变量工具">
                <button
                  type="button"
                  class="variable-panel-tab"
                  :class="{ active: activeVariablePanelTab === 'variables' }"
                  role="tab"
                  :aria-selected="activeVariablePanelTab === 'variables'"
                  @click="activeVariablePanelTab = 'variables'"
                >
                  变量字段
                </button>
                <button
                  type="button"
                  class="variable-panel-tab"
                  :class="{ active: activeVariablePanelTab === 'templates' }"
                  role="tab"
                  :aria-selected="activeVariablePanelTab === 'templates'"
                  @click="activeVariablePanelTab = 'templates'"
                >
                  保存模板
                </button>
              </div>
              <div
                v-if="activeVariablePanelTab === 'variables'"
                class="variable-library"
                role="tabpanel"
              >
                <div
                  v-for="group in variableGroups"
                  :key="group.id"
                  class="variable-group"
                >
                  <div class="variable-group-title">
                    <span class="variable-group-label">{{ group.label }}</span>
                  </div>
                  <div class="variable-chips">
                    <button
                      v-for="variable in group.variables"
                      :key="variable.key"
                      type="button"
                      class="variable-chip"
                      draggable="true"
                      :title="`插入 @${variable.key}`"
                      @dragstart="handleVariableDragStart($event, variable.key)"
                      @dragend="handleVariableDragEnd"
                      @click="insertVariable(variable.key)"
                    >
                      {{ variable.label }}
                    </button>
                  </div>
                </div>
              </div>
              <div v-else class="saved-template-panel" role="tabpanel">
                <div class="saved-template-list">
                  <div v-if="!savedTemplates.length" class="saved-template-empty">
                    暂无保存模板，点击下方“新增模板”创建。
                  </div>
                  <article
                    v-for="template in savedTemplates"
                    :key="template.id"
                    class="saved-template-item"
                    :class="{ active: selectedTemplateId === template.id }"
                    tabindex="0"
                    @pointerdown="handleTemplatePointerDown($event, template)"
                    @keydown.enter.prevent="selectTemplate(template)"
                    @keydown.space.prevent="selectTemplate(template)"
                  >
                    <button
                      type="button"
                      class="template-select-button"
                      :aria-pressed="selectedTemplateId === template.id"
                      @pointerdown.stop="selectTemplate(template)"
                      @click.stop="selectTemplate(template)"
                    >
                      <span class="saved-template-item-header">
                        <strong>{{ template.name }}</strong>
                        <span>{{ template.status }}</span>
                      </span>
                      <small>{{ template.updatedAt }}</small>
                    </button>
                    <div class="template-binding-field" @click.stop @mousedown.stop @pointerdown.stop>
                      <span>绑定复制按钮</span>
                      <select :value="template.bindingTarget" :disabled="savingSettings" @change="updateTemplateBindingTarget(template, $event.target.value)">
                        <option value="">暂不绑定</option>
                        <option value="logistics-info">物流信息</option>
                        <option value="order-info">订单信息复制</option>
                      </select>
                    </div>
                    <div class="template-binding-users" @click.stop @mousedown.stop @pointerdown.stop>
                      <span class="template-binding-label">绑定人</span>
                      <button
                        type="button"
                        class="template-bind-user-button"
                        :class="{ active: templateBindingSearchOpen[template.id] }"
                        :disabled="savingSettings || !template.bindingTarget"
                        @click.stop="toggleBindingUserSearch(template)"
                      >
                        <svg viewBox="0 0 24 24" aria-hidden="true">
                          <path v-if="!templateBindingSearchOpen[template.id]" d="M12 5v14M5 12h14"></path>
                          <path v-else d="M6 6l12 12M18 6 6 18"></path>
                        </svg>
                        {{ templateBindingSearchOpen[template.id] ? '收起搜索' : '绑定用户' }}
                      </button>
                      <div v-if="templateBindingSearchOpen[template.id]" class="template-user-picker">
                        <input
                          v-model="templateBindingSearch[template.id]"
                          class="template-user-search"
                          type="search"
                          placeholder="搜索姓名或账号后添加"
                          :disabled="savingSettings"
                          @keydown.stop
                        >
                        <div
                          v-if="templateBindingSearch[template.id]?.trim()"
                          class="template-user-search-results"
                        >
                          <button
                            v-for="user in getFilteredBindingUsers(template)"
                            :key="user.id"
                            type="button"
                            class="template-user-search-result"
                            :title="`添加${user.name}`"
                            :disabled="savingSettings"
                            @click="addTemplateBindingUser(template, user.id)"
                          >
                            <span class="template-user-avatar">
                              <img v-if="user.avatarUrl" :src="user.avatarUrl" alt="">
                              <span v-else>{{ user.name.slice(0, 1) || '人' }}</span>
                            </span>
                            <span class="template-user-search-name">
                              {{ user.name }}
                              <small v-if="user.username">{{ user.username }}</small>
                            </span>
                            <span class="template-user-search-add" aria-hidden="true">+</span>
                          </button>
                          <span v-if="!getFilteredBindingUsers(template).length" class="template-users-empty">
                            没有找到匹配账号
                          </span>
                        </div>
                      </div>
                      <div class="template-selected-users">
                        <span v-if="!template.boundUserIds.length" class="template-users-empty">
                          暂未添加绑定人
                        </span>
                        <button
                          v-for="user in getSelectedBindingUsers(template)"
                          :key="user.id"
                          type="button"
                          class="template-user-avatar"
                          :class="{ active: true }"
                          :title="user.name"
                          :aria-label="`取消绑定${user.name}`"
                          :disabled="savingSettings"
                          @click="toggleTemplateBindingUser(template, user.id)"
                        >
                          <img v-if="user.avatarUrl" :src="user.avatarUrl" alt="">
                          <span v-else>{{ user.name.slice(0, 1) || '人' }}</span>
                        </button>
                      </div>
                    </div>
                  </article>
                </div>
                <div v-if="creatingTemplate" class="template-create-form">
                  <input
                    ref="newTemplateNameInput"
                    v-model="newTemplateName"
                    type="text"
                    maxlength="80"
                    placeholder="输入模板名称"
                    @keydown.enter.prevent="confirmAddTemplate"
                    @keydown.esc.prevent="cancelAddTemplate"
                  >
                  <div class="template-create-actions">
                    <button type="button" class="template-confirm-button" @click="confirmAddTemplate">确定</button>
                    <button type="button" class="template-cancel-button" @click="cancelAddTemplate">取消</button>
                  </div>
                  <span v-if="templateError" class="template-error">{{ templateError }}</span>
                </div>
                <div class="template-actions">
                  <button
                    type="button"
                    class="template-action-button"
                    @click="startAddTemplate"
                  >
                    <svg viewBox="0 0 24 24" aria-hidden="true">
                      <path d="M12 5v14M5 12h14"></path>
                    </svg>
                    新增模板
                  </button>
                  <button
                    type="button"
                    class="template-action-button template-delete-button"
                    :disabled="!selectedTemplateId"
                    @click="removeSelectedTemplate"
                  >
                    <svg viewBox="0 0 24 24" aria-hidden="true">
                      <path d="M5 7h14M10 11v6M14 11v6M8 7l1-3h6l1 3M7 7l1 14h8l1-14"></path>
                    </svg>
                    删除模板
                  </button>
                </div>
              </div>
            </aside>

            <section class="field-editor" aria-labelledby="copy-field-list-title">
              <div class="section-heading">
                <div>
                  <h3 id="copy-field-list-title">复制字段</h3>
                  <span>可关闭字段，也可以调整字段顺序。</span>
                </div>
                <strong>{{ enabledFieldCount }}/{{ draftFields.length }}</strong>
              </div>

              <div :key="selectedTemplateId || 'shared-fields'" class="field-list">
                <div
                  v-for="(field, index) in draftFields"
                  :key="field.key"
                  class="field-row"
                  :class="{ disabled: !field.enabled }"
                >
                  <label class="field-toggle" :title="field.enabled ? '隐藏字段' : '显示字段'">
                    <input v-model="field.enabled" type="checkbox" :disabled="loadingSettings || savingSettings">
                    <span class="toggle-box" aria-hidden="true"></span>
                  </label>

                  <div class="field-content">
                    <div class="field-title-row">
                      <strong>{{ field.name }}</strong>
                      <span v-if="field.custom" class="field-hint">自定义行</span>
                      <span v-else class="field-hint">内容模板</span>
                      <div class="field-order-actions">
                        <button
                          type="button"
                          title="上移"
                          aria-label="上移字段"
                          :disabled="index === 0"
                          @click="moveField(index, -1)"
                        >
                          <svg viewBox="0 0 24 24" aria-hidden="true">
                            <path d="m6 15 6-6 6 6"></path>
                          </svg>
                        </button>
                        <button
                          type="button"
                          title="下移"
                          aria-label="下移字段"
                          :disabled="index === draftFields.length - 1"
                          @click="moveField(index, 1)"
                        >
                          <svg viewBox="0 0 24 24" aria-hidden="true">
                            <path d="m6 9 6 6 6-6"></path>
                          </svg>
                        </button>
                        <button
                          class="field-delete-button"
                          type="button"
                          title="删除字段"
                          aria-label="删除字段"
                          @click="removeField(index)"
                        >
                          <svg viewBox="0 0 24 24" aria-hidden="true">
                            <path d="M5 7h14M10 11v6M14 11v6M8 7l1-3h6l1 3M7 7l1 14h8l1-14"></path>
                          </svg>
                        </button>
                      </div>
                    </div>
                    <textarea
                      :value="field.template"
                      class="field-input field-template-input"
                      rows="2"
                      :disabled="!field.enabled"
                      placeholder="输入文字，或把左侧变量拖到这里"
                      @focus="rememberTemplateTarget($event, field)"
                      @click="rememberTemplateTarget($event, field)"
                      @keyup="rememberTemplateTarget($event, field)"
                      @input="field.template = $event.target.value"
                      @dragover.prevent
                      @drop.prevent="handleTemplateDrop($event, field)"
                    ></textarea>
                  </div>

                </div>
              </div>

              <button
                type="button"
                class="add-field-button"
                @click="addCustomField()"
                @dragover.prevent
                @drop.prevent="handleNewFieldDrop"
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M12 5v14M5 12h14"></path>
                </svg>
                添加自定义行
              </button>
            </section>

            <aside class="copy-preview" aria-labelledby="copy-preview-title">
              <div class="section-heading">
                <div>
                  <h3 id="copy-preview-title">复制预览</h3>
                  <span>物流列表点击复制时将使用此格式。</span>
                </div>
              </div>
              <pre>{{ previewText }}</pre>
            </aside>
          </div>

          <footer class="settings-footer">
            <button type="button" class="reset-button" :disabled="loadingSettings || loadFailed || savingSettings" @click="resetFields">
              恢复默认
            </button>
            <div class="footer-actions">
              <button type="button" class="cancel-button" @click="handleClose">
                取消
              </button>
              <button type="button" class="save-button" :disabled="loadingSettings || loadFailed || savingSettings" @click="handleSave">
                {{ savingSettings ? '保存中...' : '保存设置' }}
              </button>
            </div>
          </footer>
        </section>
      </div>
    </Transition>

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
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, reactive, ref, watch } from 'vue'
import { getLogisticsCopySettings, putLogisticsCopySettings } from '@/api/logisticsCopy'
import {
  formatLogisticsOrderForCopy,
  getDefaultLogisticsCopyFields,
  getLogisticsCopyPreviewOrder,
  LOGISTICS_COPY_VARIABLE_GROUPS,
  normalizeLogisticsCopyFields
} from '@/utils/logisticsCopy'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'saved'])
const draftFields = ref(getDefaultLogisticsCopyFields())
const loadingSettings = ref(false)
const loadFailed = ref(false)
const savingSettings = ref(false)
const settingsError = ref('')
const notice = ref({
  visible: false,
  type: 'success',
  message: ''
})
let noticeTimer = null
let loadRequestId = 0
const variableGroups = LOGISTICS_COPY_VARIABLE_GROUPS
const activeVariablePanelTab = ref('variables')
const savedTemplates = ref([])
const bindingUsers = ref([])
const templateBindingSearch = reactive({})
const templateBindingSearchOpen = reactive({})
const selectedTemplateId = ref('')
const creatingTemplate = ref(false)
const newTemplateName = ref('')
const newTemplateNameInput = ref(null)
const templateError = ref('')

const getDefaultSavedTemplates = () => [
  {
    id: 'standard-logistics',
    name: '物流标准模板',
    description: '姓名、电话、地址、商品、重量、件数和服务',
    status: '示例模板',
    updatedAt: '最后更新：前端默认',
    bindingTarget: '',
    boundUserIds: [],
    fields: getDefaultLogisticsCopyFields()
  },
  {
    id: 'customer-delivery',
    name: '客户送货模板',
    description: '突出收货信息、配送服务和订单备注',
    status: '示例模板',
    updatedAt: '最后更新：前端默认',
    bindingTarget: '',
    boundUserIds: [],
    fields: getDefaultLogisticsCopyFields()
  },
  {
    id: 'warehouse-pickup',
    name: '仓库提货模板',
    description: '突出商品信息、包装、件数和发货方式',
    status: '示例模板',
    updatedAt: '最后更新：前端默认',
    bindingTarget: '',
    boundUserIds: [],
    fields: getDefaultLogisticsCopyFields()
  }
]

const normalizeSavedTemplates = templates => (
  Array.isArray(templates)
    ? templates
      .filter(template => template && template.id && template.name)
      .map(template => ({
        id: String(template.id),
        name: String(template.name).trim(),
        description: String(template.description || '').trim(),
        status: template.status || '已保存',
        updatedAt: template.updatedAt || '最后更新：服务器',
        bindingTarget: ['logistics-info', 'order-info'].includes(template.bindingTarget)
          ? template.bindingTarget : '',
        boundUserIds: Array.isArray(template.boundUserIds)
          ? [...new Set(template.boundUserIds.map(Number).filter(id => Number.isInteger(id) && id > 0))]
          : [],
        fields: normalizeLogisticsCopyFields(template.fields)
      }))
    : []
)
const activeTemplateFieldKey = ref('')
const activeTemplateElement = ref(null)
const activeSelectionStart = ref(0)
const activeSelectionEnd = ref(0)
const draggedVariableKey = ref('')

const hideNotice = () => {
  if (noticeTimer) {
    clearTimeout(noticeTimer)
    noticeTimer = null
  }
  notice.value = {
    ...notice.value,
    visible: false
  }
}

const showNotice = (type, message) => {
  if (noticeTimer) {
    clearTimeout(noticeTimer)
  }

  notice.value = {
    visible: true,
    type,
    message
  }

  noticeTimer = setTimeout(() => {
    notice.value = {
      ...notice.value,
      visible: false
    }
    noticeTimer = null
  }, type === 'error' ? 5000 : 3000)
}

onBeforeUnmount(hideNotice)

const enabledFieldCount = computed(() =>
  draftFields.value.filter(field => field.enabled).length
)

const previewText = computed(() => formatLogisticsOrderForCopy(
  getLogisticsCopyPreviewOrder(),
  {
    storeName: '伟杰',
    fields: draftFields.value,
    printVariables: {
      orderDate: '2026-09-24',
      warehouseName: '中国车间',
      contactPerson: '王哥哥',
      contactPhone: '18888888888',
      contactAddress: '北京天安门大楼上',
      spec: '30支/袋',
      unit: '公斤',
      totalQuantity: 50,
      totalPackages: 0,
      salesPerson: '示例业务员',
      creator: '示例制单人',
      orderRemark: '请送到一楼',
      settlementAccount: '示例账户',
      discountAmount: '100.00',
      otherFees: '0.00',
      totalAmount: '100.00',
      totalTaxAmount: '113.00',
      currentPayment: '50.00',
      currentDebt: '50.00',
      shouldReceive: '100.00',
      amountInWords: '壹佰元整'
    }
  }
))

const loadDraft = async () => {
  const requestId = ++loadRequestId
  loadingSettings.value = true
  loadFailed.value = false
  settingsError.value = ''
  hideNotice()
  activeVariablePanelTab.value = 'variables'
  try {
    const response = await getLogisticsCopySettings()
    if (!response?.success) throw new Error(response?.message || '读取复制字段设置失败')
    if (response.data?.fields !== null && !Array.isArray(response.data?.fields)) {
      throw new Error('复制字段设置数据格式不正确')
    }
    if (requestId !== loadRequestId || !props.visible) return
    draftFields.value = response.data?.fields === null
      ? getDefaultLogisticsCopyFields()
      : normalizeLogisticsCopyFields(response.data?.fields)
    savedTemplates.value = response.data?.templates === null
      ? getDefaultSavedTemplates()
      : normalizeSavedTemplates(response.data?.templates)
    bindingUsers.value = (response.data?.bindingUsers || []).map(user => ({
      id: Number(user.id),
      name: user.name || user.username || '用户',
      avatarUrl: user.avatarUrl || ''
    }))
    selectedTemplateId.value = ''
    creatingTemplate.value = false
    newTemplateName.value = ''
    templateError.value = ''
  } catch (error) {
    if (requestId === loadRequestId && props.visible) {
      loadFailed.value = true
      settingsError.value = error.response?.data?.message || error.message || '读取复制字段设置失败'
    }
  } finally {
    if (requestId === loadRequestId) loadingSettings.value = false
  }
}

watch(
  () => props.visible,
  visible => {
    if (visible) {
      loadDraft()
    } else {
      loadRequestId++
    }
  }
)

const moveField = (index, offset) => {
  const targetIndex = index + offset
  if (targetIndex < 0 || targetIndex >= draftFields.value.length) {
    return
  }

  const nextFields = [...draftFields.value]
  const [field] = nextFields.splice(index, 1)
  nextFields.splice(targetIndex, 0, field)
  draftFields.value = nextFields
}

const resetFields = () => {
  draftFields.value = getDefaultLogisticsCopyFields()
}

const saveActiveTemplateDraft = () => {
  if (!selectedTemplateId.value) return
  const activeTemplate = savedTemplates.value.find(
    item => item.id === selectedTemplateId.value
  )
  if (activeTemplate) {
    activeTemplate.fields = normalizeLogisticsCopyFields(draftFields.value)
  }
}

const handleTemplatePointerDown = (event, template) => {
  if (event.button !== undefined && event.button !== 0) return
  selectTemplate(template)
}

const selectTemplate = template => {
  if (loadingSettings.value || savingSettings.value || creatingTemplate.value) return
  if (selectedTemplateId.value === template.id) return
  saveActiveTemplateDraft()
  selectedTemplateId.value = template.id
  draftFields.value = normalizeLogisticsCopyFields(template.fields)
  activeTemplateFieldKey.value = ''
  activeTemplateElement.value = null
}

const updateTemplateBindingTarget = (template, target) => {
  if (template.bindingTarget === target) return
  template.bindingTarget = target
  template.boundUserIds = []
  templateBindingSearch[template.id] = ''
  templateBindingSearchOpen[template.id] = false
}

const toggleBindingUserSearch = template => {
  if (!template.bindingTarget || savingSettings.value) return
  templateBindingSearchOpen[template.id] = !templateBindingSearchOpen[template.id]
  if (!templateBindingSearchOpen[template.id]) {
    templateBindingSearch[template.id] = ''
  }
}

const getFilteredBindingUsers = template => {
  const keyword = String(templateBindingSearch[template.id] || '').trim().toLowerCase()
  if (!keyword || !template.bindingTarget) return []

  return bindingUsers.value
    .filter(user => !template.boundUserIds.includes(user.id))
    .filter(user => [
      user.name,
      user.username,
      user.id
    ].some(value => String(value || '').toLowerCase().includes(keyword)))
    .slice(0, 8)
}

const getSelectedBindingUsers = template => (
  template.boundUserIds
    .map(userId => bindingUsers.value.find(user => user.id === userId))
    .filter(Boolean)
)

const addTemplateBindingUser = (template, userId) => {
  toggleTemplateBindingUser(template, userId)
  templateBindingSearch[template.id] = ''
}

const toggleTemplateBindingUser = (template, userId) => {
  if (!template.bindingTarget) return
  if (template.boundUserIds.includes(userId)) {
    template.boundUserIds = template.boundUserIds.filter(id => id !== userId)
    return
  }
  savedTemplates.value.forEach(item => {
    if (item.bindingTarget === template.bindingTarget) {
      item.boundUserIds = item.boundUserIds.filter(id => id !== userId)
    }
  })
  template.boundUserIds.push(userId)
}

const startAddTemplate = async () => {
  if (loadingSettings.value || savingSettings.value) return
  creatingTemplate.value = true
  newTemplateName.value = ''
  templateError.value = ''
  await nextTick()
  newTemplateNameInput.value?.focus()
}

const cancelAddTemplate = () => {
  creatingTemplate.value = false
  newTemplateName.value = ''
  templateError.value = ''
}

const confirmAddTemplate = () => {
  const name = newTemplateName.value.trim()
  if (!name) {
    templateError.value = '请输入模板名称'
    return
  }

  const template = {
    id: `template_${Date.now()}`,
    name,
    description: '自定义物流复制模板',
    status: '待保存',
    updatedAt: '保存设置后写入服务器',
    bindingTarget: '',
    boundUserIds: [],
    fields: normalizeLogisticsCopyFields(draftFields.value)
  }
  savedTemplates.value.push(template)
  selectedTemplateId.value = template.id
  creatingTemplate.value = false
  newTemplateName.value = ''
  templateError.value = ''
}

const removeSelectedTemplate = () => {
  if (!selectedTemplateId.value || savingSettings.value) return
  const index = savedTemplates.value.findIndex(
    template => template.id === selectedTemplateId.value
  )
  if (index < 0) return

  savedTemplates.value.splice(index, 1)
  selectedTemplateId.value = ''
  templateError.value = ''
}

const getFieldByKey = key => draftFields.value.find(field => field.key === key)

const rememberTemplateTarget = (event, field) => {
  activeTemplateFieldKey.value = field.key
  activeTemplateElement.value = event.target
  activeSelectionStart.value = event.target.selectionStart ?? field.template.length
  activeSelectionEnd.value = event.target.selectionEnd ?? activeSelectionStart.value
}

const insertVariableIntoField = (field, variableKey, element = null) => {
  const token = `@${variableKey}`
  const targetElement = element || activeTemplateElement.value
  const isActiveField = activeTemplateFieldKey.value === field.key
  const template = String(field.template || '')
  const start = isActiveField
    ? activeSelectionStart.value
    : template.length
  const end = isActiveField
    ? activeSelectionEnd.value
    : template.length

  field.template = `${template.slice(0, start)}${token}${template.slice(end)}`

  if (targetElement && isActiveField) {
    window.requestAnimationFrame(() => {
      const nextPosition = start + token.length
      targetElement.focus()
      targetElement.setSelectionRange(nextPosition, nextPosition)
      activeSelectionStart.value = nextPosition
      activeSelectionEnd.value = nextPosition
    })
  }
}

const insertVariable = variableKey => {
  const field = getFieldByKey(activeTemplateFieldKey.value) ||
    draftFields.value.find(item => item.enabled)
  if (field) {
    insertVariableIntoField(field, variableKey)
  }
}

const handleVariableDragStart = (event, variableKey) => {
  draggedVariableKey.value = variableKey
  event.dataTransfer.effectAllowed = 'copy'
  event.dataTransfer.setData('text/plain', variableKey)
}

const handleVariableDragEnd = () => {
  draggedVariableKey.value = ''
}

const handleTemplateDrop = (event, field) => {
  const variableKey = event.dataTransfer.getData('text/plain') || draggedVariableKey.value
  if (!variableKey) {
    return
  }

  activeTemplateFieldKey.value = field.key
  activeTemplateElement.value = event.target
  activeSelectionStart.value = event.target.selectionStart ?? field.template.length
  activeSelectionEnd.value = event.target.selectionEnd ?? activeSelectionStart.value
  insertVariableIntoField(field, variableKey, event.target)
  draggedVariableKey.value = ''
}

const addCustomField = (template = '') => {
  const field = {
    key: `custom_${Date.now()}`,
    name: '自定义字段',
    template,
    enabled: true,
    custom: true
  }
  draftFields.value.push(field)
  activeTemplateFieldKey.value = field.key
}

const handleNewFieldDrop = event => {
  const variableKey = event.dataTransfer.getData('text/plain') || draggedVariableKey.value
  if (variableKey) {
    addCustomField(`@${variableKey}`)
  }
  draggedVariableKey.value = ''
}

const removeField = index => {
  const [removedField] = draftFields.value.splice(index, 1)
  if (removedField?.key === activeTemplateFieldKey.value) {
    activeTemplateFieldKey.value = ''
    activeTemplateElement.value = null
  }
  if (!draftFields.value.some(field => field.key === activeTemplateFieldKey.value)) {
    activeTemplateFieldKey.value = ''
    activeTemplateElement.value = null
  }
}

const handleClose = () => {
  if (savingSettings.value) return
  emit('close')
}

const handleSave = async () => {
  if (loadingSettings.value || loadFailed.value || savingSettings.value) return
  settingsError.value = ''
  savingSettings.value = true
  try {
    const normalizedFields = normalizeLogisticsCopyFields(draftFields.value)
    const templates = savedTemplates.value.map(template => ({
      id: template.id,
      name: template.name,
      description: template.description,
      bindingTarget: template.bindingTarget,
      boundUserIds: template.boundUserIds,
      fields: normalizeLogisticsCopyFields(
        template.id === selectedTemplateId.value
          ? normalizedFields
          : template.fields
      )
    }))
    const response = await putLogisticsCopySettings(normalizedFields, templates)
    if (!response?.success) throw new Error(response?.message || '保存复制字段设置失败')
    draftFields.value = normalizeLogisticsCopyFields(response.data?.fields)
    savedTemplates.value = normalizeSavedTemplates(response.data?.templates)
    emit('saved', {
      fields: draftFields.value,
      templates: savedTemplates.value
    })
    showNotice('success', '复制字段设置保存成功')
    emit('close')
  } catch (error) {
    const message = error.response?.data?.message || error.message || '保存复制字段设置失败'
    settingsError.value = message
    showNotice('error', `保存失败：${message}`)
  } finally {
    savingSettings.value = false
  }
}
</script>

<style scoped>
.logistics-copy-settings-overlay {
  position: fixed;
  inset: 0;
  z-index: 100000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  background: rgba(15, 23, 42, 0.48);
  backdrop-filter: blur(2px);
}

.logistics-copy-settings-dialog {
  width: min(1440px, calc(100vw - 32px));
  max-height: min(900px, calc(100vh - 32px));
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #fff;
  border: 1px solid #dbe4ec;
  border-radius: 8px;
  box-shadow: 0 18px 48px rgba(15, 23, 42, 0.2);
}

.settings-header,
.settings-footer {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 20px 24px;
}

.settings-header {
  border-bottom: 1px solid #e4ebf1;
}

.settings-error {
  padding: 10px 24px;
  color: #b42318;
  background: #fff5f5;
  border-bottom: 1px solid #f3b4b4;
  font-size: 13px;
}

.settings-body-disabled {
  opacity: 0.55;
}

.reset-button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.save-button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.settings-eyebrow {
  color: #0f9f78;
  font-size: 12px;
  font-weight: 700;
}

.settings-header h2 {
  margin: 5px 0 4px;
  color: #172033;
  font-size: 20px;
}

.settings-header p,
.section-heading span {
  margin: 0;
  color: #7b8798;
  font-size: 12px;
}

.icon-close,
.field-order-actions button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  padding: 0;
  color: #64748b;
  background: #fff;
  border: 1px solid #cbd5e1;
  border-radius: 5px;
  cursor: pointer;
}

.icon-close:hover,
.field-order-actions button:hover:not(:disabled) {
  color: #08745a;
  border-color: #9bdcc8;
  background: #effaf6;
}

.icon-close svg {
  width: 18px;
  height: 18px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
  stroke-linecap: round;
}

.settings-body {
  min-height: 0;
  display: grid;
  grid-template-columns: minmax(340px, 0.75fr) minmax(330px, 1.1fr) minmax(280px, 0.65fr);
  gap: 16px;
  padding: 18px 24px;
  overflow: hidden;
  background: #f7fafb;
}

.field-editor,
.variable-panel,
.copy-preview {
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: #fff;
  border: 1px solid #dfe8ef;
  border-radius: 6px;
}

.section-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 16px;
  border-bottom: 1px solid #e8eef3;
}

.section-heading h3 {
  margin: 0 0 4px;
  color: #1f2937;
  font-size: 15px;
}

.section-heading strong {
  color: #0f9f78;
  font-size: 13px;
  white-space: nowrap;
}

.field-list {
  min-height: 0;
  flex: 1;
  padding: 8px 12px 12px;
  overflow: auto;
}

.field-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 4px;
  border-bottom: 1px solid #eef2f5;
}

.field-row:last-child {
  border-bottom: 0;
}

.field-row.disabled {
  opacity: 0.56;
}

.field-toggle {
  flex: 0 0 auto;
  position: relative;
  display: inline-flex;
  width: 20px;
  height: 20px;
  cursor: pointer;
}

.field-toggle input {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
}

.toggle-box {
  width: 18px;
  height: 18px;
  border: 1px solid #b8c6d2;
  border-radius: 4px;
  background: #fff;
}

.field-toggle input:checked + .toggle-box {
  border-color: #0f9f78;
  background: #0f9f78;
  box-shadow: inset 0 0 0 3px #fff;
}

.field-content {
  flex: 1;
  min-width: 0;
}

.field-title-row,
.field-label-input {
  display: flex;
  align-items: center;
  gap: 8px;
}

.field-title-row {
  margin-bottom: 6px;
}

.field-title-row strong {
  color: #334155;
  font-size: 13px;
}

.field-hint {
  color: #0f9f78;
  font-size: 11px;
}

.field-label-input span {
  flex: 0 0 auto;
  color: #8a96a6;
  font-size: 12px;
}

.field-input {
  width: 100%;
  min-width: 0;
  height: 32px;
  padding: 0 9px;
  color: #334155;
  background: #fff;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  outline: none;
  font-size: 13px;
}

.field-template-input {
  height: auto;
  min-height: 48px;
  resize: vertical;
  line-height: 1.55;
  font-family: Consolas, 'Microsoft YaHei', sans-serif;
}

.field-input:focus {
  border-color: #0f9f78;
  box-shadow: 0 0 0 2px rgba(15, 159, 120, 0.12);
}

.field-order-actions {
  display: flex;
  flex: 0 0 auto;
  margin-left: auto;
  gap: 4px;
}

.field-order-actions .field-delete-button {
  color: #dc6b6b;
}

.field-order-actions .field-delete-button:hover:not(:disabled) {
  color: #b42318;
  border-color: #f3b4b4;
  background: #fff5f5;
}

.field-order-actions button {
  width: 26px;
  height: 24px;
}

.field-order-actions svg {
  width: 14px;
  height: 14px;
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.field-order-actions button:disabled {
  color: #cbd5e1;
  cursor: not-allowed;
}

.add-field-button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin: 0 16px 16px;
  padding: 0;
  color: #08745a;
  background: transparent;
  border: 0;
  font-size: 12px;
  font-weight: 650;
  cursor: pointer;
}

.add-field-button:hover {
  color: #0f9f78;
}

.add-field-button svg {
  width: 15px;
  height: 15px;
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
  stroke-linecap: round;
}

.copy-preview {
  display: flex;
  flex-direction: column;
}

.variable-panel-tabs {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6px;
  margin: 12px 16px 0;
  padding: 4px;
  background: #f4f7f9;
  border: 1px solid #e1e9ee;
  border-radius: 5px;
}

.variable-panel-tab {
  min-height: 32px;
  padding: 0 10px;
  color: #64748b;
  background: transparent;
  border: 0;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}

.variable-panel-tab:hover:not(.active) {
  color: #08745a;
}

.variable-panel-tab.active {
  color: #08745a;
  background: #fff;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
}

.variable-library {
  min-height: 0;
  flex: 1;
  padding: 14px 16px 4px;
  border-bottom: 1px solid #e8eef3;
  overflow: auto;
}

.saved-template-panel {
  min-height: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.saved-template-list {
  min-height: 0;
  flex: 1;
  padding: 14px 16px;
  overflow: auto;
}

.saved-template-empty {
  padding: 18px 10px;
  color: #8a96a6;
  font-size: 12px;
  line-height: 1.6;
  text-align: center;
}

.saved-template-item {
  margin: 0 0 10px;
  padding: 12px;
  color: #334155;
  background: #fbfdfe;
  border: 1px solid #dfe8ef;
  border-radius: 5px;
  outline: none;
}

.saved-template-item:hover,
.saved-template-item:focus-visible {
  border-color: #9bdcc8;
  background: #f5fcf9;
}

.saved-template-item.active {
  border-color: #0f9f78;
  background: #effaf6;
  box-shadow: inset 3px 0 0 #0f9f78;
}

.saved-template-item:last-child {
  margin-bottom: 0;
}

.saved-template-item-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.template-select-button {
  display: block;
  width: 100%;
  padding: 0;
  color: inherit;
  text-align: left;
  background: transparent;
  border: 0;
  cursor: pointer;
}

.template-select-button:focus-visible {
  outline: 2px solid #0f9f78;
  outline-offset: 3px;
  border-radius: 3px;
}

.template-select-button small {
  display: block;
  margin-top: 5px;
}

.saved-template-item-header strong {
  min-width: 0;
  color: #334155;
  font-size: 13px;
}

.saved-template-item-header span {
  flex: 0 0 auto;
  color: #0f9f78;
  font-size: 11px;
}

.saved-template-item p {
  margin: 6px 0 8px;
  color: #7b8798;
  font-size: 12px;
  line-height: 1.55;
}

.saved-template-item small {
  color: #94a3b8;
  font-size: 11px;
}

.template-binding-field {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-top: 10px;
  color: #596579;
  font-size: 11px;
  font-weight: 600;
}

.template-binding-field select {
  width: 150px;
  min-width: 0;
  height: 32px;
  padding: 0 8px;
  color: #334155;
  background: #fff;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  font-size: 12px;
}

.template-binding-users {
  margin-top: 10px;
  color: #596579;
  font-size: 11px;
  font-weight: 600;
}

.template-binding-label {
  display: block;
  margin-bottom: 6px;
}

.template-bind-user-button {
  display: inline-flex;
  min-height: 30px;
  align-items: center;
  justify-content: center;
  gap: 5px;
  padding: 0 9px;
  color: #08745a;
  background: #effaf6;
  border: 1px solid #b8ead8;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}

.template-bind-user-button:hover:not(:disabled),
.template-bind-user-button.active {
  background: #e0f6ed;
  border-color: #79d6ba;
}

.template-bind-user-button svg {
  width: 14px;
  height: 14px;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-width: 2;
}

.template-bind-user-button:disabled {
  color: #aab6c3;
  background: #f8fafc;
  border-color: #e2e8f0;
  cursor: not-allowed;
}

.template-user-picker {
  margin-top: 6px;
}

.template-user-search {
  width: 100%;
  height: 32px;
  padding: 0 9px;
  color: #334155;
  background: #fff;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  outline: none;
  font-size: 12px;
}

.template-user-search:focus {
  border-color: #0f9f78;
  box-shadow: 0 0 0 2px rgba(15, 159, 120, 0.12);
}

.template-user-search:disabled {
  background: #f8fafc;
  cursor: not-allowed;
}

.template-user-search-results {
  display: grid;
  max-height: 168px;
  gap: 4px;
  margin-top: 6px;
  padding: 5px;
  overflow-y: auto;
  background: #fbfdfe;
  border: 1px solid #dfe8ef;
  border-radius: 4px;
}

.template-user-search-result {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 8px;
  min-height: 36px;
  padding: 3px 5px;
  color: #334155;
  background: #fff;
  border: 1px solid transparent;
  border-radius: 4px;
  text-align: left;
  cursor: pointer;
}

.template-user-search-result:hover:not(:disabled) {
  background: #effaf6;
  border-color: #b8ead8;
}

.template-user-search-result:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.template-user-search-name {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 12px;
  font-weight: 600;
}

.template-user-search-name small {
  margin-left: 6px;
  color: #8a96a6;
  font-size: 10px;
  font-weight: 400;
}

.template-user-search-add {
  margin-left: auto;
  color: #0f9f78;
  font-size: 18px;
  font-weight: 400;
  line-height: 1;
}

.template-selected-users {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 6px;
  min-height: 30px;
  align-items: center;
}

.template-user-avatar {
  display: inline-flex;
  width: 30px;
  height: 30px;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  padding: 0;
  color: #08745a;
  background: #e9f8f3;
  border: 2px solid #dfe8ef;
  border-radius: 50%;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}

.template-user-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.template-user-avatar.active {
  border-color: #0f9f78;
  box-shadow: 0 0 0 2px #b8ead8;
}

.template-user-avatar:focus-visible,
.template-binding-field select:focus-visible {
  outline: 2px solid #0f9f78;
  outline-offset: 2px;
}

.template-user-avatar:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.template-users-empty {
  color: #8a96a6;
  font-weight: 400;
}

.template-create-form {
  display: grid;
  gap: 8px;
  margin: 0 16px 10px;
  padding: 10px;
  background: #f7fafb;
  border: 1px solid #dfe8ef;
  border-radius: 5px;
}

.template-create-form input {
  width: 100%;
  height: 32px;
  padding: 0 9px;
  color: #334155;
  background: #fff;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  outline: none;
  font-size: 12px;
}

.template-create-form input:focus {
  border-color: #0f9f78;
  box-shadow: 0 0 0 2px rgba(15, 159, 120, 0.12);
}

.template-create-actions,
.template-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.template-create-actions button,
.template-action-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  min-height: 30px;
  padding: 0 9px;
  color: #08745a;
  background: #fff;
  border: 1px solid #b8ead8;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
}

.template-create-actions button:hover,
.template-action-button:hover:not(:disabled) {
  background: #effaf6;
  border-color: #79d6ba;
}

.template-cancel-button {
  color: #64748b !important;
  border-color: #cbd5e1 !important;
}

.template-error {
  color: #b42318;
  font-size: 11px;
}

.template-actions {
  flex: 0 0 auto;
  padding: 10px 16px 14px;
  border-top: 1px solid #e8eef3;
}

.template-action-button svg {
  width: 14px;
  height: 14px;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-width: 2;
}

.template-delete-button {
  color: #c94f4f;
  border-color: #f3b4b4;
}

.template-delete-button:hover:not(:disabled) {
  color: #b42318;
  background: #fff5f5;
  border-color: #e38d8d;
}

.template-action-button:disabled {
  color: #cbd5e1;
  background: #f8fafc;
  border-color: #e2e8f0;
  cursor: not-allowed;
}

.variable-library-heading {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 10px;
}

.variable-library-heading strong {
  color: #334155;
  font-size: 13px;
}

.variable-library-heading span {
  color: #8a96a6;
  font-size: 11px;
}

.variable-group {
  margin-bottom: 11px;
}

.variable-group-title {
  display: flex;
  align-items: center;
  margin: 0 0 6px;
  color: #8a96a6;
  text-align: left;
}

.variable-group-label {
  display: inline-block;
  font-size: 11px;
}

.variable-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.variable-chip {
  min-height: 28px;
  padding: 0 8px;
  color: #08745a;
  background: #effaf6;
  border: 1px solid #b8ead8;
  border-radius: 4px;
  font-size: 12px;
  cursor: grab;
}

.variable-chip:hover {
  background: #e0f6ed;
  border-color: #79d6ba;
}

.variable-chip:active {
  cursor: grabbing;
}

.copy-preview pre {
  flex: 1;
  min-height: 0;
  margin: 0;
  padding: 18px;
  color: #243244;
  background: #fbfdfe;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-word;
  font: 13px/1.85 Consolas, 'Microsoft YaHei', sans-serif;
}

.settings-footer {
  border-top: 1px solid #e4ebf1;
}

.footer-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.reset-button,
.cancel-button,
.save-button {
  height: 36px;
  padding: 0 18px;
  border-radius: 5px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}

.reset-button,
.cancel-button {
  color: #596579;
  background: #fff;
  border: 1px solid #cbd5e1;
}

.reset-button:hover,
.cancel-button:hover {
  color: #08745a;
  border-color: #9bdcc8;
  background: #effaf6;
}

.save-button {
  color: #fff;
  background: #0f9f78;
  border: 1px solid #0f9f78;
}

.save-button:hover {
  background: #08745a;
  border-color: #08745a;
}

.page-notice {
  position: fixed;
  top: 24px;
  left: 50%;
  z-index: 100001;
  display: flex;
  align-items: center;
  gap: 9px;
  min-width: 0;
  max-width: min(520px, calc(100vw - 32px));
  min-height: 44px;
  padding: 10px 16px;
  color: #172033;
  background: #fff;
  border: 1px solid #dfe5ec;
  border-radius: 6px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.16);
  transform: translateX(-50%);
  box-sizing: border-box;
  font-size: 13px;
  font-weight: 600;
  line-height: 1.5;
  overflow-wrap: anywhere;
}

.page-notice svg {
  flex: 0 0 19px;
  width: 19px;
  height: 19px;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
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

@media (max-width: 1060px) {
  .settings-body {
    grid-template-columns: minmax(320px, 0.9fr) minmax(240px, 1fr);
    overflow: auto;
  }

  .variable-panel {
    grid-column: 1;
    grid-row: 1;
  }

  .field-editor {
    grid-column: 2;
    grid-row: 1 / span 2;
  }

  .copy-preview {
    grid-column: 1;
    grid-row: 2;
    min-height: 280px;
  }
}

@media (max-width: 760px) {
  .logistics-copy-settings-overlay {
    align-items: flex-start;
    padding: 12px;
  }

  .logistics-copy-settings-dialog {
    max-height: calc(100vh - 24px);
  }

  .settings-body {
    grid-template-columns: 1fr;
    padding: 12px;
    overflow: auto;
  }

  .field-editor,
  .variable-panel,
  .copy-preview {
    grid-column: auto;
    grid-row: auto;
  }

  .field-editor,
  .variable-panel,
  .copy-preview {
    min-height: 220px;
  }

  .copy-preview pre {
    min-height: 180px;
  }

  .settings-header,
  .settings-footer {
    padding: 16px;
  }

  .page-notice {
    top: 12px;
    max-width: calc(100vw - 32px);
  }
}

@media (prefers-reduced-motion: reduce) {
  .notice-enter-active,
  .notice-leave-active {
    transition: none;
  }
}
</style>
