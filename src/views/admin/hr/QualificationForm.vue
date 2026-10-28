<template>
  <div class="qualification-container">
    <header class="toolbar">
      <div class="heading">
        <button class="back-button" type="button" aria-label="返回公司资质" title="返回公司资质" @click="backToList">
          <ArrowLeft :size="20" aria-hidden="true" />
        </button>
        <h2 class="page-title">{{ pageTitle }}</h2>
      </div>
      <div v-if="isViewing && loaded" class="toolbar-actions">
        <button class="secondary-button" type="button" @click="showShareDialog = true">
          <QrCode :size="16" aria-hidden="true" />
          分享二维码
        </button>
        <button class="primary-button" type="button" @click="editQualification">
          <Pencil :size="16" aria-hidden="true" />
          编辑文件
        </button>
      </div>
    </header>

    <nav class="breadcrumb" aria-label="当前位置">
      <RouterLink :to="{ name: 'admin-hr-qualifications' }">公司资质</RouterLink>
      <template v-if="form.folderId && form.folderName">
        <ChevronRight :size="14" aria-hidden="true" />
        <RouterLink :to="{ name: 'admin-hr-qualifications', query: { folderId: form.folderId } }">
          {{ form.folderName }}
        </RouterLink>
      </template>
      <ChevronRight :size="14" aria-hidden="true" />
      <span>{{ isViewing ? form.title || '资质文件' : pageTitle }}</span>
    </nav>

    <div v-if="loading" class="state-message" role="status">正在加载资质文件...</div>
    <div v-else-if="!loaded" class="state-message error-message" role="alert">
      <span>{{ loadError }}</span>
      <button class="text-button" type="button" @click="loadForm">重新加载</button>
    </div>

    <QualificationDetails v-else-if="isViewing" :title="form.title" :fields="form.fields" />

    <form v-else class="qualification-form" @submit.prevent="saveQualification">
      <fieldset :disabled="saving">
        <h3 class="section-title">文件信息</h3>
        <div class="form-fields">
          <div class="form-field">
            <label for="file-title">文件名称 <span class="required">*</span></label>
            <input id="file-title" v-model="form.title" type="text" maxlength="200" required placeholder="请输入文件名称" />
          </div>
          <div class="custom-fields">
            <div class="field-column-headings" aria-hidden="true">
              <span>字段标题</span>
              <span>字段内容</span>
            </div>
            <div v-for="(field, index) in form.fields" :key="field.id" class="custom-field-row">
              <input
                :id="`field-label-${field.id}`"
                v-model="field.label"
                :aria-label="`第${index + 1}项字段标题`"
                type="text"
                maxlength="100"
                required
                placeholder="请输入标题"
              />
              <textarea
                :id="`field-value-${field.id}`"
                v-model="field.value"
                :aria-label="`${field.label || `第${index + 1}项`}的内容`"
                rows="2"
                maxlength="5000"
                required
                placeholder="请输入内容"
              ></textarea>
              <button
                class="remove-field-button"
                type="button"
                :aria-label="`删除第${index + 1}项字段`"
                title="删除字段"
                :disabled="form.fields.length === 1"
                @click="removeField(index)"
              >
                <Trash2 :size="18" aria-hidden="true" />
              </button>
            </div>
            <button class="text-button add-field-button" type="button" :disabled="form.fields.length >= 50" @click="addField">
              <Plus :size="16" aria-hidden="true" />
              添加字段
            </button>
          </div>
        </div>
        <p v-if="saveError" class="save-error" role="alert">{{ saveError }}</p>
        <footer class="form-actions">
          <button class="secondary-button" type="button" @click="cancel">取消</button>
          <button class="primary-button" type="submit">
            <Save :size="16" aria-hidden="true" />
            {{ saving ? '保存中...' : '保存文件' }}
          </button>
        </footer>
      </fieldset>
    </form>
    <QualificationShareDialog
      v-if="showShareDialog && isViewing && loaded"
      :key="qualificationId"
      :qualification-id="qualificationId"
      :title="form.title"
      @close="showShareDialog = false"
    />
  </div>
</template>

<script setup>
import { computed, nextTick, reactive, ref, watch } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { ArrowLeft, ChevronRight, Pencil, Plus, QrCode, Save, Trash2 } from '@lucide/vue'
import request from '@/api/request'
import QualificationDetails from '@/components/qualifications/QualificationDetails.vue'
import QualificationShareDialog from '@/components/qualifications/QualificationShareDialog.vue'

const props = defineProps({
  mode: { type: String, default: 'create' },
  qualificationId: { type: String, default: '' },
  folderId: { type: String, default: '' }
})
const router = useRouter()
const loading = ref(false)
const loaded = ref(false)
const saving = ref(false)
const loadError = ref('')
const saveError = ref('')
const showShareDialog = ref(false)
const defaultLabels = ['证书编号', '中文名称', '认证依据', '注册地址', '审核地址', '认证范围', '发证日期', '有效日期', '证书状态']
let nextFieldId = 0
const createField = (label = '', value = '') => ({ id: ++nextFieldId, label, value })

const emptyForm = () => ({
  folderId: props.folderId ? Number(props.folderId) : '',
  folderName: '',
  title: '',
  fields: defaultLabels.map(label => createField(label))
})
const form = reactive(emptyForm())
const isViewing = computed(() => props.mode === 'view')
const pageTitle = computed(() => ({ create: '新建文件', edit: '编辑文件', view: '文件预览' })[props.mode])

const folderPath = () => form.folderId
  ? { name: 'admin-hr-qualifications', query: { folderId: form.folderId } }
  : { name: 'admin-hr-qualifications' }
const backToList = () => router.push(folderPath())
const editQualification = () => router.push({ name: 'admin-hr-qualification-edit', params: { id: props.qualificationId } })
const cancel = () => props.mode === 'edit'
  ? router.push({ name: 'admin-hr-qualification-view', params: { id: props.qualificationId } })
  : backToList()
async function addField() {
  if (form.fields.length >= 50) return
  const field = createField()
  form.fields.push(field)
  await nextTick()
  document.getElementById(`field-label-${field.id}`)?.focus()
}

function removeField(index) {
  if (form.fields.length > 1) form.fields.splice(index, 1)
}

let loadVersion = 0
async function loadForm() {
  const version = ++loadVersion
  loading.value = true
  loaded.value = false
  saveError.value = ''
  loadError.value = ''
  showShareDialog.value = false
  try {
    Object.assign(form, emptyForm())

    if (props.mode !== 'create') {
      const response = await request.get(`/hr/qualifications/${props.qualificationId}`)
      if (!response.success) throw new Error(response.message || '加载资质文件失败')
      if (version !== loadVersion) return
      const data = response.data
      Object.assign(form, {
        folderId: data.folderId,
        folderName: data.folderName,
        title: data.title,
        fields: data.fields.map(field => createField(field.label, field.value))
      })
    } else {
      if (!Number.isSafeInteger(form.folderId) || form.folderId <= 0) {
        await router.replace({ name: 'admin-hr-qualifications' })
        return
      }
      const folderResponse = await request.get('/hr/qualifications/folders')
      if (!folderResponse.success) throw new Error(folderResponse.message || '加载文件夹失败')
      if (version !== loadVersion) return
      const folder = folderResponse.data.find(folder => folder.id === form.folderId)
      if (!folder) throw new Error('当前文件夹不存在，请返回公司资质选择文件夹')
      form.folderName = folder.name
    }
    loaded.value = true
  } catch (error) {
    if (version === loadVersion) loadError.value = error.response?.data?.message || error.message || '加载资质文件失败'
  } finally {
    if (version === loadVersion) loading.value = false
  }
}

async function saveQualification() {
  if (saving.value) return
  saveError.value = ''
  const payload = {
    folderId: Number(form.folderId),
    title: form.title.trim(),
    fields: form.fields.map(field => ({ label: field.label.trim(), value: field.value.trim() }))
  }
  if (!payload.folderId || !payload.title) {
    saveError.value = '请填写文件名称，并从有效的文件夹内新建文件'
    return
  }
  if (!payload.fields.length || payload.fields.some(field => !field.label || !field.value)) {
    saveError.value = '请填写每项字段的标题和内容'
    return
  }
  saving.value = true
  try {
    const response = props.mode === 'edit'
      ? await request.put(`/hr/qualifications/${props.qualificationId}`, payload)
      : await request.post('/hr/qualifications', payload)
    if (!response.success) throw new Error(response.message || '保存资质文件失败')
    await router.push({ name: 'admin-hr-qualification-view', params: { id: response.data.id } })
  } catch (error) {
    saveError.value = error.response?.data?.message || error.message || '保存资质文件失败，请稍后重试'
  } finally {
    saving.value = false
  }
}

watch(() => [props.mode, props.qualificationId, props.folderId], loadForm, { immediate: true })
</script>

<style scoped>
.qualification-container {
  padding: 20px;
  min-height: calc(100vh - 100px);
}

.toolbar,
.heading,
.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.toolbar {
  justify-content: space-between;
  flex-wrap: wrap;
  margin-bottom: 20px;
}

.heading { min-width: 0; }

.page-title {
  margin: 0;
  color: #1f2937;
  font-size: 24px;
  font-weight: 600;
}

.back-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fff;
  color: #374151;
  cursor: pointer;
}

.back-button:hover { color: #2563eb; border-color: #3b82f6; }

.breadcrumb {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 24px;
  color: #6b7280;
  font-size: 14px;
  overflow-wrap: anywhere;
}

.breadcrumb a,
.text-button {
  color: #2563eb;
  text-decoration: none;
}

.qualification-form {
  max-width: 960px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fff;
  overflow: hidden;
}

fieldset {
  min-width: 0;
  margin: 0;
  padding: 0;
  border: 0;
}

.section-title {
  margin: 0;
  padding: 20px 24px;
  border-bottom: 1px solid #e5e7eb;
  color: #1f2937;
  font-size: 16px;
  font-weight: 600;
  overflow-wrap: anywhere;
}

.form-fields {
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 24px;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 0;
}

.form-field label {
  color: #374151;
  font-size: 14px;
  font-weight: 500;
}

.required { color: #dc2626; }

.form-field input,
.custom-field-row input,
.custom-field-row textarea {
  width: 100%;
  min-width: 0;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: #fff;
  color: #374151;
  font: inherit;
  font-size: 14px;
  line-height: 1.5;
  box-sizing: border-box;
}

.custom-field-row textarea { resize: vertical; }

.form-field input:focus,
.custom-field-row input:focus,
.custom-field-row textarea:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgb(59 130 246 / 10%);
}

.field-column-headings,
.custom-field-row {
  display: grid;
  grid-template-columns: minmax(140px, 1fr) minmax(0, 3fr) 36px;
  align-items: start;
  gap: 12px;
}

.field-column-headings { margin-bottom: 10px; color: #374151; font-size: 14px; font-weight: 500; }
.custom-field-row { margin-bottom: 16px; }
.remove-field-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 42px;
  padding: 0;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: #6b7280;
  cursor: pointer;
}
.remove-field-button:hover:not(:disabled) { background: #fef2f2; color: #b91c1c; }
.remove-field-button:disabled { cursor: not-allowed; opacity: 0.35; }
.add-field-button { display: inline-flex; align-items: center; gap: 6px; padding: 8px 0; font: inherit; font-size: 14px; }
.add-field-button:disabled { cursor: not-allowed; opacity: 0.5; }

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 24px;
  border-top: 1px solid #e5e7eb;
}

.primary-button,
.secondary-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 40px;
  padding: 10px 20px;
  border: 1px solid transparent;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
}

.primary-button { background: #3b82f6; color: #fff; }
.primary-button:hover:not(:disabled) { background: #2563eb; }
.primary-button:disabled { cursor: not-allowed; opacity: 0.6; }
.secondary-button { border-color: #d1d5db; background: #fff; color: #374151; }
.secondary-button:hover:not(:disabled) { background: #f9fafb; }
fieldset:disabled { opacity: 0.7; }
fieldset:disabled button { cursor: wait; }

button:focus-visible,
a:focus-visible {
  outline: 2px solid #2563eb;
  outline-offset: 3px;
}

.state-message {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 12px;
  padding: 40px 16px;
  color: #6b7280;
  font-size: 14px;
}

.error-message,
.save-error { color: #b91c1c; }
.save-error { margin: 0; padding: 0 24px 20px; font-size: 14px; }
.text-button { border: 0; background: transparent; cursor: pointer; }

@media (max-width: 600px) {
  .qualification-container { padding: 16px; }
  .page-title { font-size: 22px; }
  .toolbar-actions { flex-wrap: wrap; }
  .primary-button,
  .secondary-button { padding: 10px 12px; }
  .form-fields { padding: 20px 16px; }
  .field-column-headings { display: none; }
  .custom-field-row { grid-template-columns: minmax(0, 1fr) 36px; gap: 8px; }
  .custom-field-row input { grid-column: 1; }
  .custom-field-row textarea { grid-column: 1; }
  .remove-field-button { grid-column: 2; grid-row: 1 / 3; }
  .section-title,
  .form-actions { padding: 16px; }
  .save-error { padding: 0 16px 16px; }
}
</style>
