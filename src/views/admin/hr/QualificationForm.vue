<template>
  <div class="qualification-container">
    <header class="toolbar">
      <div class="heading">
        <button class="back-button" type="button" aria-label="返回公司资质" title="返回公司资质" @click="backToList">
          <ArrowLeft :size="20" aria-hidden="true" />
        </button>
        <h2 class="page-title">{{ pageTitle }}</h2>
      </div>
      <button v-if="isViewing && loaded" class="primary-button" type="button" @click="editQualification">
        <Pencil :size="16" aria-hidden="true" />
        编辑文件
      </button>
    </header>

    <nav class="breadcrumb" aria-label="当前位置">
      <RouterLink :to="{ name: 'admin-hr-qualifications' }">公司资质</RouterLink>
      <template v-if="form.folderId && selectedFolderName">
        <ChevronRight :size="14" aria-hidden="true" />
        <RouterLink :to="{ name: 'admin-hr-qualifications', query: { folderId: form.folderId } }">
          {{ selectedFolderName }}
        </RouterLink>
      </template>
      <ChevronRight :size="14" aria-hidden="true" />
      <span>{{ isViewing ? form.certificateNo || '资质文件' : pageTitle }}</span>
    </nav>

    <div v-if="loading" class="state-message" role="status">正在加载资质文件...</div>
    <div v-else-if="!loaded" class="state-message error-message" role="alert">
      <span>{{ loadError }}</span>
      <button class="text-button" type="button" @click="loadForm">重新加载</button>
    </div>

    <section v-else-if="isViewing" class="details-section" aria-label="资质文件详情">
      <dl class="certificate-details">
        <div v-for="field in detailFields" :key="field.key" class="detail-row">
          <dt>{{ field.label }}：</dt>
          <dd>{{ field.date ? formatDate(form[field.key]) : form[field.key] }}</dd>
        </div>
      </dl>
    </section>

    <form v-else class="qualification-form" @submit.prevent="saveQualification">
      <fieldset :disabled="saving">
        <h3 class="section-title">资质文件信息</h3>
        <div class="form-fields">
          <div class="form-field full-width">
            <label for="folder-id">所属文件夹 <span class="required">*</span></label>
            <select id="folder-id" v-model="form.folderId" required>
              <option value="" disabled>请选择文件夹</option>
              <option v-for="folder in folders" :key="folder.id" :value="folder.id">{{ folder.name }}</option>
            </select>
            <span v-if="!folders.length" class="field-hint">暂无文件夹，请先返回公司资质新建文件夹</span>
          </div>
          <div class="form-field">
            <label for="certificate-no">证书编号 <span class="required">*</span></label>
            <input id="certificate-no" v-model="form.certificateNo" type="text" maxlength="100" required placeholder="请输入证书编号" />
          </div>
          <div class="form-field">
            <label for="company-name">中文名称 <span class="required">*</span></label>
            <input id="company-name" v-model="form.companyName" type="text" maxlength="200" required placeholder="请输入公司中文名称" />
          </div>
          <div class="form-field full-width">
            <label for="certification-basis">认证依据 <span class="required">*</span></label>
            <input id="certification-basis" v-model="form.certificationBasis" type="text" maxlength="500" required placeholder="请输入认证标准或依据" />
          </div>
          <div class="form-field full-width">
            <label for="registered-address">注册地址 <span class="required">*</span></label>
            <textarea id="registered-address" v-model="form.registeredAddress" rows="2" maxlength="1000" required placeholder="请输入注册地址"></textarea>
          </div>
          <div class="form-field full-width">
            <label for="audit-address">审核地址 <span class="required">*</span></label>
            <textarea id="audit-address" v-model="form.auditAddress" rows="2" maxlength="1000" required placeholder="请输入审核地址"></textarea>
          </div>
          <div class="form-field full-width">
            <label for="certification-scope">认证范围 <span class="required">*</span></label>
            <textarea id="certification-scope" v-model="form.certificationScope" rows="3" maxlength="5000" required placeholder="请输入认证范围"></textarea>
          </div>
          <div class="form-field">
            <label for="issue-date">发证日期 <span class="required">*</span></label>
            <input id="issue-date" v-model="form.issueDate" type="date" max="9999-12-31" required />
          </div>
          <div class="form-field">
            <label for="valid-until">有效日期 <span class="required">*</span></label>
            <input id="valid-until" v-model="form.validUntil" type="date" :min="form.issueDate || undefined" max="9999-12-31" required />
          </div>
          <div class="form-field">
            <label for="certificate-status">证书状态 <span class="required">*</span></label>
            <select id="certificate-status" v-model="form.certificateStatus" required>
              <option v-for="status in certificateStatuses" :key="status" :value="status">{{ status }}</option>
            </select>
          </div>
        </div>
        <p v-if="saveError" class="save-error" role="alert">{{ saveError }}</p>
        <footer class="form-actions">
          <button class="secondary-button" type="button" @click="cancel">取消</button>
          <button class="primary-button" type="submit" :disabled="!folders.length">
            <Save :size="16" aria-hidden="true" />
            {{ saving ? '保存中...' : '保存文件' }}
          </button>
        </footer>
      </fieldset>
    </form>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { ArrowLeft, ChevronRight, Pencil, Save } from '@lucide/vue'
import request from '@/api/request'

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
const folders = ref([])
const certificateStatuses = ['有效', '暂停', '撤销', '注销', '过期']
const detailFields = [
  { key: 'certificateNo', label: '证书编号' },
  { key: 'companyName', label: '中文名称' },
  { key: 'certificationBasis', label: '认证依据' },
  { key: 'registeredAddress', label: '注册地址' },
  { key: 'auditAddress', label: '审核地址' },
  { key: 'certificationScope', label: '认证范围' },
  { key: 'issueDate', label: '发证日期', date: true },
  { key: 'validUntil', label: '有效日期', date: true },
  { key: 'certificateStatus', label: '证书状态' }
]

const emptyForm = () => ({
  folderId: props.folderId ? Number(props.folderId) : '',
  folderName: '',
  certificateNo: '',
  companyName: '',
  certificationBasis: '',
  registeredAddress: '',
  auditAddress: '',
  certificationScope: '',
  issueDate: '',
  validUntil: '',
  certificateStatus: '有效'
})
const form = reactive(emptyForm())
const isViewing = computed(() => props.mode === 'view')
const pageTitle = computed(() => ({ create: '新建文件', edit: '编辑文件', view: '文件预览' })[props.mode])
const selectedFolderName = computed(() => folders.value.find(folder => folder.id === form.folderId)?.name || form.folderName)

const folderPath = () => form.folderId
  ? { name: 'admin-hr-qualifications', query: { folderId: form.folderId } }
  : { name: 'admin-hr-qualifications' }
const backToList = () => router.push(folderPath())
const editQualification = () => router.push({ name: 'admin-hr-qualification-edit', params: { id: props.qualificationId } })
const cancel = () => props.mode === 'edit'
  ? router.push({ name: 'admin-hr-qualification-view', params: { id: props.qualificationId } })
  : backToList()
const formatDate = value => {
  if (!value) return ''
  const [year, month, day] = value.split('-')
  return `${year}年${Number(month)}月${Number(day)}日`
}

let loadVersion = 0
async function loadForm() {
  const version = ++loadVersion
  loading.value = true
  loaded.value = false
  saveError.value = ''
  loadError.value = ''
  try {
    const folderResponse = await request.get('/hr/qualifications/folders')
    if (!folderResponse.success) throw new Error(folderResponse.message || '加载文件夹失败')
    if (version !== loadVersion) return
    folders.value = folderResponse.data
    Object.assign(form, emptyForm())

    if (props.mode !== 'create') {
      const response = await request.get(`/hr/qualifications/${props.qualificationId}`)
      if (!response.success) throw new Error(response.message || '加载资质文件失败')
      if (version !== loadVersion) return
      Object.keys(form).forEach(key => {
        if (response.data[key] !== undefined) form[key] = response.data[key]
      })
    } else if (form.folderId && !folders.value.some(folder => folder.id === form.folderId)) {
      form.folderId = ''
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
    ...Object.fromEntries(
      Object.entries(form)
        .filter(([key]) => !['folderId', 'folderName'].includes(key))
        .map(([key, value]) => [key, value.trim()])
    )
  }
  if (!payload.folderId || Object.values(payload).some(value => !value)) {
    saveError.value = '请完整填写所有必填项'
    return
  }
  if (payload.validUntil < payload.issueDate) {
    saveError.value = '有效日期不能早于发证日期'
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
.heading {
  display: flex;
  align-items: center;
  gap: 12px;
}

.toolbar {
  justify-content: space-between;
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

.qualification-form,
.details-section {
  max-width: 960px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fff;
  overflow: hidden;
}

.details-section { max-width: 760px; }

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
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 22px 24px;
  padding: 24px;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 0;
}

.full-width { grid-column: 1 / -1; }

.form-field label {
  color: #374151;
  font-size: 14px;
  font-weight: 500;
}

.required { color: #dc2626; }

.form-field input,
.form-field textarea,
.form-field select {
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

.form-field textarea { resize: vertical; }

.form-field input:focus,
.form-field textarea:focus,
.form-field select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgb(59 130 246 / 10%);
}

.field-hint {
  color: #b45309;
  font-size: 12px;
}

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

.certificate-details { margin: 0; }

.detail-row {
  padding: 12px 18px;
  border-bottom: 1px solid #e5e7eb;
  color: #374151;
  font-size: 16px;
  line-height: 1.65;
  overflow-wrap: anywhere;
}

.detail-row:last-child { border-bottom: 0; }
.detail-row dt { display: inline; font-weight: 600; }
.detail-row dd { display: inline; margin: 0; white-space: pre-wrap; }

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
  .primary-button,
  .secondary-button { padding: 10px 12px; }
  .form-fields { grid-template-columns: minmax(0, 1fr); padding: 20px 16px; }
  .section-title,
  .form-actions { padding: 16px; }
  .detail-row { padding: 12px 16px; }
  .save-error { padding: 0 16px 16px; }
}
</style>
