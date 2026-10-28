<template>
  <div class="qualifications-container">
    <header class="toolbar">
      <div class="heading">
        <button
          v-if="currentFolder"
          class="icon-button"
          type="button"
          aria-label="返回根目录"
          title="返回根目录"
          @click="openRoot"
        >
          <ArrowLeft :size="20" aria-hidden="true" />
        </button>
        <h2 class="page-title">{{ currentFolder ? currentFolder.name : '公司资质' }}</h2>
      </div>
      <div class="toolbar-actions">
        <button v-if="!folderId" class="secondary-button" type="button" @click="showFolderModal = true">
          <FolderPlus :size="18" aria-hidden="true" />
          新建文件夹
        </button>
        <button class="primary-button" type="button" @click="createFile">
          <FilePlus :size="18" aria-hidden="true" />
          新建文件
        </button>
      </div>
    </header>

    <nav class="breadcrumb" aria-label="当前位置">
      <button type="button" @click="openRoot">公司资质</button>
      <template v-if="currentFolder">
        <ChevronRight :size="14" aria-hidden="true" />
        <span>{{ currentFolder.name }}</span>
      </template>
    </nav>

    <div class="list-toolbar">
      <span class="folder-total">
        {{ currentFolder ? `当前文件夹 · ${files.length} 个文件` : `全部目录 · ${folders.length} 个文件夹` }}
      </span>
      <label class="search-box">
        <Search :size="16" aria-hidden="true" />
        <input
          v-model="search"
          type="search"
          :aria-label="currentFolder ? '搜索资质文件' : '搜索文件夹'"
          :placeholder="currentFolder ? '搜索证书编号或中文名称' : '搜索文件夹'"
        />
      </label>
    </div>

    <div v-if="loading" class="state-message" role="status">正在加载公司资质...</div>
    <div v-else-if="loadError" class="state-message error-message" role="alert">
      <span>{{ loadError }}</span>
      <button class="retry-button" type="button" @click="loadCurrentView">重新加载</button>
    </div>
    <template v-else>
      <div v-if="!currentFolder && !filteredFolders.length" class="empty-state">
        <FolderOpen :size="42" stroke-width="1.5" aria-hidden="true" />
        <span>{{ search ? '未找到匹配的文件夹' : '暂无文件夹，请先新建文件夹' }}</span>
      </div>
      <div v-if="currentFolder && !filteredFiles.length" class="empty-state">
        <FileText :size="42" stroke-width="1.5" aria-hidden="true" />
        <span>{{ search ? '未找到匹配的资质文件' : '当前文件夹暂无文件' }}</span>
      </div>

      <div v-if="!currentFolder" class="folders-grid">
        <button
          v-for="folder in filteredFolders"
          :key="folder.id"
          class="folder-card"
          type="button"
          :aria-label="`打开${folder.name}`"
          @click="openFolder(folder)"
        >
          <Folder class="folder-icon" :size="80" :stroke-width="1.5" fill="#ffa500" stroke="#ff8c00" aria-hidden="true" />
          <span class="folder-name" :title="folder.name">{{ folder.name }}</span>
          <span class="folder-count">{{ folder.fileCount }} 个文件</span>
        </button>
      </div>

      <div v-else class="files-grid">
        <button
          v-for="file in filteredFiles"
          :key="file.id"
          class="file-card"
          type="button"
          :aria-label="`打开${file.certificateNo}`"
          @click="openFile(file)"
        >
          <FileText class="file-icon" :size="62" stroke-width="1.5" aria-hidden="true" />
          <span class="file-name" :title="file.certificateNo">{{ file.certificateNo }}</span>
          <span class="file-company" :title="file.companyName">{{ file.companyName }}</span>
          <span class="file-status" :class="statusClass(file.certificateStatus)">{{ file.certificateStatus }}</span>
        </button>
        <button class="file-card add-file" type="button" @click="createFile">
          <FilePlus class="file-icon" :size="62" stroke-width="1.25" aria-hidden="true" />
          <span class="file-name">新建文件</span>
        </button>
      </div>
    </template>

    <Teleport to="body">
      <div v-if="showFolderModal" class="modal-overlay" @click.self="closeFolderModal" @keydown.esc="closeFolderModal">
        <form class="modal-content" role="dialog" aria-modal="true" aria-labelledby="new-folder-title" @submit.prevent="createFolder">
          <h3 id="new-folder-title" class="modal-title">新建文件夹</h3>
          <fieldset :disabled="creatingFolder">
            <label class="modal-field">
              <span>文件夹名称</span>
              <input
                ref="folderInput"
                v-model="newFolderName"
                type="text"
                maxlength="100"
                required
                placeholder="请输入文件夹名称"
              />
            </label>
            <p v-if="folderError" class="form-error" role="alert">{{ folderError }}</p>
            <div class="modal-actions">
              <button class="secondary-button" type="button" @click="closeFolderModal">取消</button>
              <button class="primary-button" type="submit" :disabled="creatingFolder">
                {{ creatingFolder ? '创建中...' : '创建' }}
              </button>
            </div>
          </fieldset>
        </form>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, ChevronRight, FilePlus, FileText, Folder, FolderOpen, FolderPlus, Search } from '@lucide/vue'
import request from '@/api/request'

const route = useRoute()
const router = useRouter()
const folders = ref([])
const files = ref([])
const currentFolder = ref(null)
const search = ref('')
const loading = ref(true)
const loadError = ref('')
const showFolderModal = ref(false)
const newFolderName = ref('')
const folderError = ref('')
const creatingFolder = ref(false)
const folderInput = ref(null)

const folderId = computed(() => {
  const value = Number(route.query.folderId)
  return Number.isInteger(value) && value > 0 ? value : null
})

const filteredFolders = computed(() => {
  const keyword = search.value.trim().toLocaleLowerCase()
  return folders.value.filter(folder => folder.name.toLocaleLowerCase().includes(keyword))
})

const filteredFiles = computed(() => {
  const keyword = search.value.trim().toLocaleLowerCase()
  return files.value.filter(file =>
    [file.certificateNo, file.companyName, file.certificationBasis]
      .some(value => value.toLocaleLowerCase().includes(keyword))
  )
})

const statusClass = status => status === '有效' ? 'status-valid' : status === '暂停' ? 'status-paused' : 'status-inactive'

function openRoot() {
  router.push({ name: 'admin-hr-qualifications' })
}

function openFolder(folder) {
  router.push({ name: 'admin-hr-qualifications', query: { folderId: folder.id } })
}

function createFile() {
  router.push({
    name: 'admin-hr-qualification-create',
    query: folderId.value ? { folderId: folderId.value } : undefined
  })
}

function openFile(file) {
  router.push({ name: 'admin-hr-qualification-view', params: { id: file.id } })
}

function closeFolderModal() {
  if (creatingFolder.value) return
  showFolderModal.value = false
  newFolderName.value = ''
  folderError.value = ''
}

async function createFolder() {
  if (creatingFolder.value) return
  folderError.value = ''
  const name = newFolderName.value.trim()
  if (!name) {
    folderError.value = '文件夹名称不能为空'
    return
  }
  creatingFolder.value = true
  try {
    const response = await request.post('/hr/qualifications/folders', { name })
    if (!response.success) throw new Error(response.message || '新建文件夹失败')
    creatingFolder.value = false
    closeFolderModal()
    await loadCurrentView()
  } catch (error) {
    folderError.value = error.response?.data?.message || error.message || '新建文件夹失败，请稍后重试'
  } finally {
    creatingFolder.value = false
  }
}

let loadVersion = 0
async function loadCurrentView() {
  const version = ++loadVersion
  const requestedFolderId = folderId.value
  loading.value = true
  loadError.value = ''
  try {
    const folderResponse = await request.get('/hr/qualifications/folders')
    if (!folderResponse.success) throw new Error(folderResponse.message || '加载文件夹失败')
    if (version !== loadVersion) return
    folders.value = folderResponse.data
    currentFolder.value = requestedFolderId
      ? folders.value.find(folder => folder.id === requestedFolderId) || null
      : null
    if (requestedFolderId && !currentFolder.value) {
      openRoot()
      return
    }
    if (requestedFolderId) {
      const fileResponse = await request.get('/hr/qualifications', { params: { folder_id: requestedFolderId } })
      if (!fileResponse.success) throw new Error(fileResponse.message || '加载资质文件失败')
      if (version !== loadVersion) return
      files.value = fileResponse.data
    } else {
      files.value = []
    }
  } catch (error) {
    if (version === loadVersion) loadError.value = error.response?.data?.message || error.message || '加载公司资质失败，请稍后重试'
  } finally {
    if (version === loadVersion) loading.value = false
  }
}

watch(folderId, () => {
  search.value = ''
  loadCurrentView()
})

watch(showFolderModal, async visible => {
  if (visible) {
    await nextTick()
    folderInput.value?.focus()
  }
})

onMounted(loadCurrentView)
</script>

<style scoped>
.qualifications-container {
  padding: 20px;
  min-height: calc(100vh - 100px);
}

.toolbar,
.heading,
.toolbar-actions,
.list-toolbar,
.breadcrumb {
  display: flex;
  align-items: center;
}

.toolbar {
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.heading,
.toolbar-actions {
  gap: 10px;
}

.heading { min-width: 0; }

.page-title {
  margin: 0;
  color: #1f2937;
  font-size: 24px;
  font-weight: 600;
}

.icon-button,
.primary-button,
.secondary-button,
.retry-button {
  cursor: pointer;
}

.icon-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fff;
  color: #374151;
}

.icon-button:hover {
  border-color: #3b82f6;
  color: #2563eb;
}

.primary-button,
.secondary-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 40px;
  padding: 10px 16px;
  border: 1px solid transparent;
  border-radius: 8px;
  font: inherit;
  font-size: 14px;
  white-space: nowrap;
}

.primary-button {
  background: #3b82f6;
  color: #fff;
}

.primary-button:hover:not(:disabled) { background: #2563eb; }
.primary-button:disabled { cursor: wait; opacity: 0.7; }

.secondary-button {
  border-color: #d1d5db;
  background: #fff;
  color: #374151;
}

.secondary-button:hover:not(:disabled) {
  border-color: #3b82f6;
  color: #2563eb;
}

.breadcrumb {
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 20px;
  color: #6b7280;
  font-size: 14px;
}

.breadcrumb button {
  padding: 0;
  border: 0;
  background: transparent;
  color: #2563eb;
  font: inherit;
  cursor: pointer;
}

.list-toolbar {
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 24px;
}

.folder-total {
  color: #6b7280;
  font-size: 14px;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 320px;
  max-width: 100%;
  padding: 9px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fff;
  color: #9ca3af;
  box-sizing: border-box;
}

.search-box:focus-within { border-color: #3b82f6; }

.search-box input {
  width: 100%;
  min-width: 0;
  border: 0;
  outline: 0;
  background: transparent;
  color: #374151;
  font: inherit;
  font-size: 14px;
}

.folders-grid,
.files-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 20px;
}

.folder-card,
.file-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 0;
  min-height: 210px;
  padding: 20px;
  border: 2px solid #f3f4f6;
  border-radius: 8px;
  background: #fff;
  font: inherit;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.2s, box-shadow 0.2s, transform 0.2s;
}

.folder-card:hover,
.file-card:hover {
  transform: translateY(-4px);
  border-color: #3b82f6;
  box-shadow: 0 8px 20px rgb(0 0 0 / 8%);
}

.folder-icon,
.file-icon {
  flex-shrink: 0;
  margin-bottom: 14px;
}

.file-icon {
  padding: 8px;
  border-radius: 8px;
  background: #eff6ff;
  color: #2563eb;
}

.folder-name,
.file-name,
.file-company {
  width: 100%;
  overflow-wrap: anywhere;
}

.folder-name,
.file-name {
  color: #1f2937;
  font-size: 14px;
  font-weight: 600;
  line-height: 1.5;
}

.folder-count,
.file-company,
.file-status {
  margin-top: 6px;
  color: #6b7280;
  font-size: 12px;
}

.file-company {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-status { margin-top: auto; }
.status-valid { color: #15803d; }
.status-paused { color: #b45309; }
.status-inactive { color: #b91c1c; }

.add-file {
  border: 2px dashed #9ca3af;
  background: #f9fafb;
  color: #6b7280;
}

.add-file:hover { background: #f0f9ff; }

.empty-state,
.state-message {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 12px;
  min-height: 180px;
  color: #9ca3af;
  font-size: 14px;
  text-align: center;
}

.error-message,
.form-error { color: #b91c1c; }

.retry-button {
  border: 0;
  background: transparent;
  color: #2563eb;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: rgb(17 24 39 / 45%);
}

.modal-content {
  width: min(100%, 460px);
  padding: 24px;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 20px 60px rgb(0 0 0 / 25%);
  box-sizing: border-box;
}

.modal-title {
  margin: 0 0 20px;
  color: #1f2937;
  font-size: 18px;
}

fieldset {
  min-width: 0;
  margin: 0;
  padding: 0;
  border: 0;
}

.modal-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
  color: #374151;
  font-size: 14px;
}

.modal-field input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  outline: 0;
  font: inherit;
  box-sizing: border-box;
}

.modal-field input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgb(59 130 246 / 10%);
}

.form-error {
  margin: 12px 0 0;
  font-size: 13px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 24px;
}

button:focus-visible,
input:focus-visible {
  outline: 2px solid #2563eb;
  outline-offset: 3px;
}

@media (max-width: 600px) {
  .qualifications-container { padding: 16px; }
  .toolbar { align-items: flex-start; flex-direction: column; }
  .toolbar-actions { width: 100%; }
  .toolbar-actions button { flex: 1; padding-inline: 10px; }
  .page-title { font-size: 22px; }
  .list-toolbar { align-items: stretch; flex-direction: column; }
  .search-box { width: 100%; }
  .folders-grid,
  .files-grid { grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 12px; }
  .folder-card,
  .file-card { padding: 16px 12px; }
}
</style>
