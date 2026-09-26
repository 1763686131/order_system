<template>
  <Teleport to="body">
    <Transition name="logistics-copy-settings">
      <div
        v-if="visible && canViewSettings"
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
              <p>自定义物流列表复制内容和变量排版。</p>
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
                  历史模板
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
                      :disabled="!canEditContent"
                      :draggable="canEditContent"
                      :title="`插入 @${variable.key}`"
                      @dragstart="handleVariableDragStart($event, variable.key)"
                      @dragend="handleVariableDragEnd"
                      @click="insertVariable(variable.key)"
                    >
                      {{ variable.label }}
                    </button>
                    <button
                      v-if="group.id === 'goods'"
                      type="button"
                      class="variable-chip row-separator-chip"
                      :disabled="!canEditContent"
                      title="放在全部商品、全部规格、全部数量和合计单位之间；同一行按商品逐件换行"
                      @click="insertVariable(' | ', true)"
                    >
                      逐件分列 |
                    </button>
                    <button
                      v-if="group.id === 'goods'"
                      type="button"
                      class="variable-chip row-separator-chip"
                      :disabled="!canEditContent"
                      title="在变量后插入 ～ 连接文字，如 @allQuantity～kg"
                      @click="insertVariable('～', true)"
                    >
                      变量拼接 ～
                    </button>
                  </div>
                </div>
              </div>
              <div v-else class="saved-template-panel" role="tabpanel">
                <div class="saved-template-list">
                  <div v-if="!savedTemplates.length" class="saved-template-empty">
                    暂无历史模板
                  </div>
                  <article
                    v-for="template in savedTemplates"
                    :key="template.id"
                    class="saved-template-item"
                    :class="{ active: selectedTemplateId === template.id }"
                    role="button"
                    tabindex="0"
                    :aria-label="`选择模板：${template.name}`"
                    :aria-pressed="selectedTemplateId === template.id"
                    @click="selectTemplate(template)"
                    @keydown.enter.self.prevent="selectTemplate(template)"
                    @keydown.space.self.prevent="selectTemplate(template)"
                  >
                    <div class="saved-template-item-header">
                      <strong :title="template.name">{{ template.name }}</strong>
                      <select
                        class="template-binding-select"
                        :value="template.bindingTarget"
                        :aria-label="`${template.name}绑定的复制按钮`"
                        :disabled="savingSettings || !canEditTemplate(template)"
                        @click.stop
                        @mousedown.stop
                        @pointerdown.stop
                        @keydown.enter.stop
                        @keydown.space.stop
                        @change="updateTemplateBindingTarget(template, $event.target.value)"
                      >
                        <option value="">暂不绑定</option>
                        <option value="logistics-info">物流信息</option>
                        <option value="order-info">订单信息复制</option>
                      </select>
                    </div>
                    <div class="template-binding-users">
                      <span class="template-binding-label">绑定人</span>
                      <div class="template-selected-users">
                        <button
                          v-for="user in getSelectedBindingUsers(template)"
                          :key="user.id"
                          type="button"
                          class="template-user-avatar active"
                          :title="user.name"
                          :aria-label="`取消绑定${user.name}`"
                          :disabled="savingSettings || !canEditTemplate(template)"
                          @click.stop="toggleTemplateBindingUser(template, user.id)"
                        >
                          <img v-if="user.avatarUrl" :src="user.avatarUrl" alt="">
                          <span v-else>{{ user.name.slice(0, 1) || '人' }}</span>
                        </button>
                        <button
                          v-if="canEditTemplate(template)"
                          type="button"
                          class="template-user-avatar template-add-user-button"
                          :class="{ open: templateBindingSearchOpen[template.id] }"
                          :title="!template.bindingTarget ? '请先选择绑定的复制按钮' : templateBindingSearchOpen[template.id] ? '收起搜索' : '绑定用户'"
                          :aria-label="templateBindingSearchOpen[template.id] ? `收起${template.name}的绑定用户搜索` : `为${template.name}绑定用户`"
                          :aria-expanded="!!templateBindingSearchOpen[template.id]"
                          :aria-controls="`template-user-picker-${template.id}`"
                          :disabled="savingSettings || !template.bindingTarget"
                          @click.stop="toggleBindingUserSearch(template)"
                        >
                          <span aria-hidden="true">＋</span>
                        </button>
                      </div>
                      <div v-if="templateBindingSearchOpen[template.id]" :id="`template-user-picker-${template.id}`" class="template-user-picker" @click.stop>
                        <input
                          v-model="templateBindingSearch[template.id]"
                          class="template-user-search"
                          type="search"
                          placeholder="搜索姓名或账号后添加"
                          :disabled="savingSettings || !canEditTemplate(template)"
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
                            :disabled="savingSettings || !canEditTemplate(template)"
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
                    </div>
                  </article>
                </div>
                <div v-if="creatingTemplate && canCreateTemplate" class="template-create-form">
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
                <div v-if="canCreateTemplate || canDeleteTemplate" class="template-actions">
                  <button
                    v-if="canCreateTemplate"
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
                    v-if="canDeleteTemplate || canDiscardNewTemplate"
                    type="button"
                    class="template-action-button template-delete-button"
                    :disabled="!canRemoveSelectedTemplate"
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
                  <h3 id="copy-field-list-title">
                    编辑内容
                    <span class="current-template-name">{{ selectedTemplateName }}</span>
                  </h3>
                  <span>直接编辑复制内容，也可以拖入变量。</span>
                </div>
                <strong>{{ editorLineCount }} 行</strong>
              </div>

              <div :key="selectedTemplateId || 'shared-fields'" class="field-list">
                <textarea
                  ref="editorElement"
                  :value="draftText"
                  class="copy-editor-input"
                  :disabled="loadingSettings || loadFailed || savingSettings"
                  :readonly="!canEditContent"
                  aria-label="编辑模板内容"
                  maxlength="4000"
                  placeholder="在这里编辑复制内容，或把左侧变量拖进来"
                  @focus="rememberEditorTarget"
                  @click="rememberEditorTarget"
                  @keyup="rememberEditorTarget"
                  @select="rememberEditorTarget"
                  @input="handleEditorInput"
                  @dragover.prevent
                  @drop.prevent="handleEditorDrop"
                ></textarea>
              </div>
            </section>

            <aside class="copy-preview" aria-labelledby="copy-preview-title">
              <div class="section-heading">
                <div>
                  <h3 id="copy-preview-title">复制预览</h3>
                  <span>输入内容和变量后会实时生成复制结果。</span>
                </div>
              </div>
              <pre>{{ previewText }}</pre>
            </aside>
          </div>

          <footer class="settings-footer">
            <button v-if="canEditContent" type="button" class="reset-button" :disabled="loadingSettings || loadFailed || savingSettings" @click="resetFields">
              恢复默认
            </button>
            <div class="footer-actions">
              <button type="button" class="cancel-button" @click="handleClose">
                取消
              </button>
              <button v-if="canSaveSettings" type="button" class="save-button" :disabled="loadingSettings || loadFailed || savingSettings" @click="handleSave">
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
import { useUserStore } from '@/stores/user'
import { ADMIN_LOGISTICS_COPY_PERMISSIONS } from '@/utils/accessControl'
import {
  formatLogisticsOrderForCopy,
  getDefaultLogisticsCopyFields,
  getLogisticsCopyPreviewOrder,
  LOGISTICS_COPY_EDITOR_KEY,
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
const userStore = useUserStore()
const canViewSettings = computed(() =>
  userStore.canAccessAdmin &&
  userStore.hasPerm(ADMIN_LOGISTICS_COPY_PERMISSIONS.ENTRY) &&
  userStore.hasPerm(ADMIN_LOGISTICS_COPY_PERMISSIONS.READ)
)
const canCreateTemplate = computed(() =>
  canViewSettings.value && userStore.hasPerm(ADMIN_LOGISTICS_COPY_PERMISSIONS.CREATE)
)
const canEditSettings = computed(() =>
  canViewSettings.value && userStore.hasPerm(ADMIN_LOGISTICS_COPY_PERMISSIONS.EDIT)
)
const canDeleteTemplate = computed(() =>
  canViewSettings.value && userStore.hasPerm(ADMIN_LOGISTICS_COPY_PERMISSIONS.DELETE)
)
const canSaveSettings = computed(() =>
  canCreateTemplate.value || canEditSettings.value || canDeleteTemplate.value
)
const draftText = ref(
  getDefaultLogisticsCopyFields()
    .filter(field => field.enabled)
    .map(field => field.template)
    .join('\n')
)
const editorElement = ref(null)
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
const activeVariablePanelTab = ref('templates')
const savedTemplates = ref([])
const bindingUsers = ref([])
const templateBindingSearch = reactive({})
const templateBindingSearchOpen = reactive({})
const selectedTemplateId = ref('')
const persistedTemplateIds = ref(new Set())
const sharedDraftText = ref('')
const initialSharedText = ref('')
const creatingTemplate = ref(false)
const newTemplateName = ref('')
const newTemplateNameInput = ref(null)
const templateError = ref('')

const fieldsToEditorText = fields => normalizeLogisticsCopyFields(fields)
  .filter(field => field.enabled)
  .map(field => String(field.template || ''))
  .join('\n')

const editorTextToFields = text => [{
  key: LOGISTICS_COPY_EDITOR_KEY,
  name: '复制内容',
  template: String(text || ''),
  enabled: true,
  custom: true
}]

const getDefaultSavedTemplates = () => [
  {
    id: 'standard-logistics',
    name: '物流标准模板',
    description: '姓名、电话、地址、商品、重量、件数和服务',
    bindingTarget: '',
    boundUserIds: [],
    fields: getDefaultLogisticsCopyFields()
  },
  {
    id: 'customer-delivery',
    name: '客户送货模板',
    description: '突出收货信息、配送服务和订单备注',
    bindingTarget: '',
    boundUserIds: [],
    fields: getDefaultLogisticsCopyFields()
  },
  {
    id: 'warehouse-pickup',
    name: '仓库提货模板',
    description: '突出商品信息、包装、件数和发货方式',
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
        bindingTarget: ['logistics-info', 'order-info'].includes(template.bindingTarget)
          ? template.bindingTarget : '',
        boundUserIds: Array.isArray(template.boundUserIds)
          ? [...new Set(template.boundUserIds.map(Number).filter(id => Number.isInteger(id) && id > 0))]
          : [],
        fields: Array.isArray(template.fields)
          ? template.fields.map(field => ({ ...field }))
          : getDefaultLogisticsCopyFields()
      }))
    : []
)
const activeSelectionStart = ref(draftText.value.length)
const activeSelectionEnd = ref(draftText.value.length)
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

const editorLineCount = computed(() =>
  draftText.value ? draftText.value.split('\n').length : 0
)
const selectedTemplateName = computed(() =>
  savedTemplates.value.find(template => template.id === selectedTemplateId.value)?.name || '默认配置'
)
const canEditTemplate = template => persistedTemplateIds.value.has(template.id)
  ? canEditSettings.value
  : canCreateTemplate.value
const canEditContent = computed(() => {
  const template = savedTemplates.value.find(item => item.id === selectedTemplateId.value)
  return template ? canEditTemplate(template) : canEditSettings.value
})
const canDiscardNewTemplate = computed(() =>
  Boolean(selectedTemplateId.value) &&
  !persistedTemplateIds.value.has(selectedTemplateId.value) &&
  canCreateTemplate.value
)
const canRemoveSelectedTemplate = computed(() =>
  Boolean(selectedTemplateId.value) &&
  (persistedTemplateIds.value.has(selectedTemplateId.value)
    ? canDeleteTemplate.value : canDiscardNewTemplate.value)
)

const previewText = computed(() => formatLogisticsOrderForCopy(
  getLogisticsCopyPreviewOrder(),
  {
    storeName: '伟杰',
    fields: editorTextToFields(draftText.value),
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
  if (!canViewSettings.value) return
  const requestId = ++loadRequestId
  loadingSettings.value = true
  loadFailed.value = false
  settingsError.value = ''
  hideNotice()
  activeVariablePanelTab.value = 'templates'
  try {
    const response = await getLogisticsCopySettings()
    if (!response?.success) throw new Error(response?.message || '读取复制字段设置失败')
    if (response.data?.fields !== null && !Array.isArray(response.data?.fields)) {
      throw new Error('复制字段设置数据格式不正确')
    }
    if (requestId !== loadRequestId || !props.visible) return
    draftText.value = fieldsToEditorText(
      response.data?.fields === null
        ? getDefaultLogisticsCopyFields()
        : response.data?.fields
    )
    activeSelectionStart.value = draftText.value.length
    activeSelectionEnd.value = draftText.value.length
    sharedDraftText.value = draftText.value
    initialSharedText.value = draftText.value
    const hasSavedTemplates = response.data?.templates !== null
    savedTemplates.value = hasSavedTemplates
      ? normalizeSavedTemplates(response.data?.templates)
      : getDefaultSavedTemplates()
    persistedTemplateIds.value = hasSavedTemplates
      ? new Set(savedTemplates.value.map(template => template.id))
      : new Set()
    bindingUsers.value = (response.data?.bindingUsers || []).map(user => ({
      id: Number(user.id),
      name: user.name || user.username || '用户',
      username: user.username || '',
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
  [() => props.visible, canViewSettings],
  ([visible, allowed]) => {
    if (visible && allowed) {
      loadDraft()
    } else {
      loadRequestId++
    }
  },
  { immediate: true }
)

const resetFields = () => {
  if (!canEditContent.value) return
  draftText.value = fieldsToEditorText(getDefaultLogisticsCopyFields())
  activeSelectionStart.value = draftText.value.length
  activeSelectionEnd.value = draftText.value.length
}

const saveActiveTemplateDraft = () => {
  if (!canEditContent.value) return
  if (!selectedTemplateId.value) {
    sharedDraftText.value = draftText.value
    return
  }
  const activeTemplate = savedTemplates.value.find(
    item => item.id === selectedTemplateId.value
  )
  if (activeTemplate && fieldsToEditorText(activeTemplate.fields) !== draftText.value) {
    activeTemplate.fields = editorTextToFields(draftText.value)
  }
}

const selectTemplate = template => {
  if (!canViewSettings.value || loadingSettings.value || savingSettings.value) return
  if (selectedTemplateId.value === template.id) return
  saveActiveTemplateDraft()
  cancelAddTemplate()
  selectedTemplateId.value = template.id
  draftText.value = fieldsToEditorText(template.fields)
  activeSelectionStart.value = draftText.value.length
  activeSelectionEnd.value = draftText.value.length
}

const updateTemplateBindingTarget = (template, target) => {
  if (!canEditTemplate(template) || savingSettings.value) return
  if (template.bindingTarget === target) return
  template.bindingTarget = target
  template.boundUserIds = []
  templateBindingSearch[template.id] = ''
  templateBindingSearchOpen[template.id] = false
}

const toggleBindingUserSearch = template => {
  if (!canEditTemplate(template) || !template.bindingTarget || savingSettings.value) return
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
  if (!canEditTemplate(template) || !template.bindingTarget || savingSettings.value) return
  if (template.boundUserIds.includes(userId)) {
    template.boundUserIds = template.boundUserIds.filter(id => id !== userId)
    return
  }
  const conflictingTemplate = savedTemplates.value.find(item =>
    item.id !== template.id &&
    item.bindingTarget === template.bindingTarget &&
    item.boundUserIds.includes(userId) &&
    !canEditTemplate(item)
  )
  if (conflictingTemplate) {
    showNotice('error', '此用户已绑定其他模板，需要修改权限才能更换绑定')
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
  if (!canCreateTemplate.value || loadingSettings.value || savingSettings.value) return
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
  if (!canCreateTemplate.value || savingSettings.value) return
  const name = newTemplateName.value.trim()
  if (!name) {
    templateError.value = '请输入模板名称'
    return
  }

  saveActiveTemplateDraft()
  const template = {
    id: `template_${Date.now()}`,
    name,
    description: '自定义物流复制模板',
    bindingTarget: '',
    boundUserIds: [],
    fields: editorTextToFields(draftText.value)
  }
  savedTemplates.value.push(template)
  selectedTemplateId.value = template.id
  creatingTemplate.value = false
  newTemplateName.value = ''
  templateError.value = ''
}

const removeSelectedTemplate = () => {
  if (!canRemoveSelectedTemplate.value || savingSettings.value) return
  const index = savedTemplates.value.findIndex(
    template => template.id === selectedTemplateId.value
  )
  if (index < 0) return

  savedTemplates.value.splice(index, 1)
  selectedTemplateId.value = ''
  draftText.value = sharedDraftText.value
  activeSelectionStart.value = draftText.value.length
  activeSelectionEnd.value = draftText.value.length
  templateError.value = ''
}

const rememberEditorTarget = event => {
  editorElement.value = event.target
  activeSelectionStart.value = event.target.selectionStart ?? draftText.value.length
  activeSelectionEnd.value = event.target.selectionEnd ?? activeSelectionStart.value
}

const insertVariableIntoEditor = (token, element = editorElement.value) => {
  if (!canEditContent.value || savingSettings.value) return
  const text = draftText.value
  const start = Math.min(activeSelectionStart.value, text.length)
  const end = Math.min(activeSelectionEnd.value, text.length)
  if (text.length - (end - start) + token.length > 4000) return
  draftText.value = `${text.slice(0, start)}${token}${text.slice(end)}`

  if (element) {
    window.requestAnimationFrame(() => {
      const nextPosition = start + token.length
      element.focus()
      element.setSelectionRange(nextPosition, nextPosition)
      activeSelectionStart.value = nextPosition
      activeSelectionEnd.value = nextPosition
    })
  }
}

const insertVariable = (variableKey, isLiteral = false) => {
  insertVariableIntoEditor(isLiteral ? variableKey : `@${variableKey}`)
}

const handleVariableDragStart = (event, variableKey) => {
  if (!canEditContent.value) {
    event.preventDefault()
    return
  }
  draggedVariableKey.value = variableKey
  event.dataTransfer.effectAllowed = 'copy'
  event.dataTransfer.setData('text/plain', variableKey)
}

const handleVariableDragEnd = () => {
  draggedVariableKey.value = ''
}

const handleEditorInput = event => {
  if (!canEditContent.value) return
  draftText.value = event.target.value
  rememberEditorTarget(event)
}

const handleEditorDrop = event => {
  if (!canEditContent.value || savingSettings.value) return
  const variableKey = event.dataTransfer.getData('text/plain') || draggedVariableKey.value
  if (!variableKey) {
    return
  }

  activeSelectionStart.value = event.target.selectionStart ?? draftText.value.length
  activeSelectionEnd.value = event.target.selectionEnd ?? activeSelectionStart.value
  insertVariableIntoEditor(`@${variableKey}`, event.target)
  draggedVariableKey.value = ''
}

const handleClose = () => {
  if (savingSettings.value) return
  emit('close')
}

const handleSave = async () => {
  if (!canSaveSettings.value || loadingSettings.value || loadFailed.value || savingSettings.value) return
  settingsError.value = ''
  savingSettings.value = true
  try {
    saveActiveTemplateDraft()
    const normalizedFields = sharedDraftText.value !== initialSharedText.value
      ? editorTextToFields(sharedDraftText.value)
      : undefined
    const templates = savedTemplates.value.map(template => ({
      id: template.id,
      name: template.name,
      description: template.description,
      bindingTarget: template.bindingTarget,
      boundUserIds: template.boundUserIds,
      fields: template.fields
    }))
    const response = await putLogisticsCopySettings(normalizedFields, templates)
    if (!response?.success) throw new Error(response?.message || '保存复制字段设置失败')
    draftText.value = fieldsToEditorText(response.data?.fields)
    sharedDraftText.value = draftText.value
    initialSharedText.value = draftText.value
    savedTemplates.value = normalizeSavedTemplates(response.data?.templates)
    persistedTemplateIds.value = new Set(savedTemplates.value.map(template => template.id))
    selectedTemplateId.value = ''
    emit('saved', {
      fields: response.data?.fields,
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
  height: min(820px, calc(100dvh - 32px));
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

.icon-close {
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

.icon-close:hover {
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
  flex: 1;
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
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 8px;
  margin: 0 0 4px;
  color: #1f2937;
  font-size: 15px;
}

.section-heading .current-template-name {
  color: #d44b51;
  font-size: 13px;
  font-weight: 600;
  overflow-wrap: anywhere;
}

.section-heading strong {
  color: #0f9f78;
  font-size: 13px;
  white-space: nowrap;
}

.field-list {
  min-height: 0;
  flex: 1;
  display: flex;
  padding: 14px;
  overflow: hidden;
}

.copy-editor-input {
  width: 100%;
  min-height: 0;
  flex: 1;
  padding: 16px;
  color: #243244;
  background: #fbfdfe;
  border: 1px solid #cbd5e1;
  border-radius: 5px;
  outline: none;
  resize: none;
  font: 14px/1.8 Consolas, 'Microsoft YaHei', sans-serif;
  white-space: pre-wrap;
  overflow: auto;
}

.copy-editor-input:focus {
  border-color: #0f9f78;
  box-shadow: 0 0 0 3px rgba(15, 159, 120, 0.12);
}

.copy-editor-input:disabled {
  background: #f8fafc;
  cursor: not-allowed;
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
  position: relative;
  margin: 0 0 10px;
  padding: 12px 12px 12px 16px;
  color: #172033;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 7px;
  outline: none;
  cursor: pointer;
  transition: background .18s ease, border-color .18s ease, box-shadow .18s ease;
}

.saved-template-item::before {
  position: absolute;
  top: 10px;
  bottom: 10px;
  left: 0;
  width: 4px;
  border-radius: 0 3px 3px 0;
  background: transparent;
  content: '';
}

.saved-template-item:hover {
  border-color: #a9e5d2;
  background: #f5fcf9;
}

.saved-template-item:focus-visible {
  outline: 2px solid #0f9f78;
  outline-offset: 2px;
}

.saved-template-item.active {
  border-color: #0f9f78;
  background: #e9f8f3;
  box-shadow: 0 0 0 2px rgba(15, 159, 120, .12);
}

.saved-template-item.active::before {
  background: #0f9f78;
}

.saved-template-item:last-child {
  margin-bottom: 0;
}

.saved-template-item-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  min-height: 36px;
}

.saved-template-item-header strong {
  min-width: 0;
  color: #172033;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.saved-template-item.active .saved-template-item-header strong {
  color: #08745a;
}

.saved-template-item.active .saved-template-item-header strong::before {
  margin-right: 6px;
  content: '✓';
}

.saved-template-item p {
  margin: 6px 0 8px;
  color: #7b8798;
  font-size: 12px;
  line-height: 1.55;
}

.template-binding-select {
  flex: 0 1 150px;
  width: min(150px, 50%);
  min-width: 0;
  height: 32px;
  padding: 0 8px;
  color: #334155;
  background: #fff;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  font-size: 12px;
}

.template-binding-select:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.template-binding-users {
  margin-top: 8px;
  color: #596579;
  font-size: 11px;
  font-weight: 600;
}

.template-binding-label {
  display: block;
  margin-bottom: 6px;
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

.template-add-user-button {
  color: #08745a;
  background: #fff;
  border: 1px dashed #79d6ba;
  font-size: 19px;
  font-weight: 400;
}

.template-add-user-button:hover:not(:disabled),
.template-add-user-button.open {
  background: #e0f6ed;
  border-color: #0f9f78;
}

.template-add-user-button span {
  line-height: 1;
  transition: transform 0.15s ease;
}

.template-add-user-button.open span {
  transform: rotate(45deg);
}

.template-user-avatar:focus-visible,
.template-binding-select:focus-visible {
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

.variable-chip:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.row-separator-chip {
  color: #8a5a03;
  background: #fffaf0;
  border-color: #e9cf92;
  cursor: pointer;
}

.row-separator-chip:hover {
  background: #fff2d5;
  border-color: #d9b45c;
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
  margin-left: auto;
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
    height: clamp(300px, 55dvh, 520px);
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
    height: min(820px, calc(100dvh - 24px));
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

  .variable-panel {
    height: clamp(240px, 55dvh, 480px);
  }

  .copy-editor-input {
    min-height: 260px;
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
