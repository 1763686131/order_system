<template>
  <div class="reports-container">
    <!-- 文件夹视图 -->
    <div v-if="!selectedFolder" class="folders-view">
      <h2 class="page-title">检测报告</h2>
      <div class="folders-grid">
        <div
          v-for="folder in folders"
          :key="folder.id"
          class="folder-card"
          @click="openFolder(folder)"
          @contextmenu.prevent="showFolderContextMenu($event, folder)"
        >
          <div class="folder-icon">
            <svg width="80" height="80" viewBox="0 0 24 24" fill="none">
              <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" fill="#FFA500" stroke="#FF8C00" stroke-width="1.5"/>
            </svg>
          </div>
          <div class="folder-name">{{ folder.name }}</div>
          <div class="folder-count">{{ folder.fileCount }} 个文件</div>
        </div>

        <!-- 新增文件夹按钮 -->
        <div class="folder-card add-folder" @click="showAddFolderModal = true">
          <div class="folder-icon">
            <svg width="80" height="80" viewBox="0 0 24 24" fill="none">
              <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" fill="#e5e7eb" stroke="#9ca3af" stroke-width="1.5" stroke-dasharray="4 4"/>
              <circle cx="12" cy="13" r="4" fill="#3b82f6"/>
              <path d="M12 11v4M10 13h4" stroke="white" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
          </div>
          <div class="folder-name">新建文件夹</div>
        </div>
      </div>
    </div>

    <!-- PDF 文件书架视图 -->
    <div v-else class="files-view">
      <div class="files-header">
        <button class="back-btn" @click="closeFolder">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M19 12H5M12 19l-7-7 7-7"/>
          </svg>
          返回
        </button>
        <h2 class="folder-title">{{ selectedFolder.name }}</h2>
      </div>

      <div class="files-shelf">
        <div
          v-for="file in selectedFolder.files"
          :key="file.id"
          class="file-book"
          @click="openPDF(file)"
          @contextmenu.prevent="showFileContextMenu($event, file)"
        >
          <div class="book-cover">
            <div class="book-icon">PDF</div>
            <div class="book-title">{{ file.name }}</div>
          </div>
          <div class="book-spine"></div>
        </div>

        <!-- 上传文件按钮 -->
        <div class="file-book add-file" @click="triggerFileUpload">
          <div class="book-cover add-cover">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <path d="M12 8v8M8 12h8"/>
            </svg>
            <div class="add-text">上传PDF</div>
          </div>
          <div class="book-spine"></div>
        </div>
      </div>

      <input
        ref="fileInput"
        type="file"
        accept="application/pdf"
        multiple
        style="display: none"
        @change="handleFileUpload"
      />
    </div>

    <!-- 右键菜单 -->
    <teleport to="body">
      <div
        v-if="contextMenu.visible"
        class="context-menu"
        :style="{ top: contextMenu.y + 'px', left: contextMenu.x + 'px' }"
        @click="hideContextMenu"
      >
        <div class="context-menu-item" @click="handleRename">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
          </svg>
          重命名
        </div>
        <div v-if="contextMenu.type === 'file'" class="context-menu-item" @click="handleMove">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/>
            <polyline points="13 2 13 9 20 9"/>
          </svg>
          移动
        </div>
        <div class="context-menu-item danger" @click="handleDelete">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="3 6 5 6 21 6"/>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
          </svg>
          删除
        </div>
        <div class="context-menu-divider"></div>
        <div class="context-menu-item" @click="hideContextMenu">取消</div>
      </div>
    </teleport>

    <!-- 新增文件夹弹窗 -->
    <teleport to="body">
      <div v-if="showAddFolderModal" class="modal-overlay" @click.self="showAddFolderModal = false">
        <div class="modal-content">
          <h3 class="modal-title">新建文件夹</h3>
          <input
            v-model="newFolderName"
            type="text"
            class="folder-input"
            placeholder="请输入文件夹名称"
            @keyup.enter="createFolder"
          />
          <div class="modal-actions">
            <button class="btn-cancel" @click="showAddFolderModal = false">取消</button>
            <button class="btn-confirm" @click="createFolder">确定</button>
          </div>
        </div>
      </div>
    </teleport>

    <!-- 重命名弹窗 -->
    <teleport to="body">
      <div v-if="showRenameModal" class="modal-overlay" @click.self="showRenameModal = false">
        <div class="modal-content">
          <h3 class="modal-title">重命名</h3>
          <input
            v-model="renameValue"
            type="text"
            class="folder-input"
            placeholder="请输入新名称"
            @keyup.enter="confirmRename"
          />
          <div class="modal-actions">
            <button class="btn-cancel" @click="showRenameModal = false">取消</button>
            <button class="btn-confirm" @click="confirmRename">确定</button>
          </div>
        </div>
      </div>
    </teleport>

    <!-- 移动文件弹窗 -->
    <teleport to="body">
      <div v-if="showMoveModal" class="modal-overlay" @click.self="showMoveModal = false">
        <div class="modal-content">
          <h3 class="modal-title">移动到</h3>
          <div class="folder-list">
            <div
              v-for="folder in folders.filter(f => f.id !== selectedFolder.id)"
              :key="folder.id"
              class="folder-list-item"
              @click="moveFileToFolder(folder)"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" fill="#FFA500" stroke="#FF8C00" stroke-width="1.5"/>
              </svg>
              {{ folder.name }}
            </div>
          </div>
          <div class="modal-actions">
            <button class="btn-cancel" @click="showMoveModal = false">取消</button>
          </div>
        </div>
      </div>
    </teleport>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const selectedFolder = ref(null)
const showAddFolderModal = ref(false)
const showRenameModal = ref(false)
const showMoveModal = ref(false)
const newFolderName = ref('')
const renameValue = ref('')
const fileInput = ref(null)

// 右键菜单状态
const contextMenu = ref({
  visible: false,
  x: 0,
  y: 0,
  type: '', // 'folder' or 'file'
  target: null
})

// 模拟文件夹数据
const folders = ref([
  { id: 1, name: '产品检测报告', fileCount: 5, files: [
    { id: 1, name: '2024年度产品质检报告.pdf', url: '' },
    { id: 2, name: '原材料检测报告-Q1.pdf', url: '' },
    { id: 3, name: '成品质量检验报告.pdf', url: '' }
  ]},
  { id: 2, name: '环境检测报告', fileCount: 3, files: [
    { id: 4, name: '车间环境检测-2024.pdf', url: '' },
    { id: 5, name: '空气质量检测报告.pdf', url: '' }
  ]},
  { id: 3, name: '安全检测报告', fileCount: 2, files: [
    { id: 6, name: '消防安全检测报告.pdf', url: '' }
  ]}
])

const openFolder = (folder) => {
  selectedFolder.value = folder
}

const closeFolder = () => {
  selectedFolder.value = null
}

const createFolder = () => {
  if (newFolderName.value.trim()) {
    folders.value.push({
      id: Date.now(),
      name: newFolderName.value,
      fileCount: 0,
      files: []
    })
    newFolderName.value = ''
    showAddFolderModal.value = false
  }
}

const triggerFileUpload = () => {
  fileInput.value?.click()
}

const handleFileUpload = (event) => {
  const files = Array.from(event.target.files)
  files.forEach(file => {
    if (file.type === 'application/pdf') {
      selectedFolder.value.files.push({
        id: Date.now() + Math.random(),
        name: file.name,
        url: URL.createObjectURL(file)
      })
      selectedFolder.value.fileCount++
    }
  })
  event.target.value = ''
}

const openPDF = (file) => {
  if (file.url) {
    window.open(file.url, '_blank')
  } else {
    alert('PDF文件尚未上传')
  }
}

// 显示文件夹右键菜单
const showFolderContextMenu = (event, folder) => {
  contextMenu.value = {
    visible: true,
    x: event.clientX,
    y: event.clientY,
    type: 'folder',
    target: folder
  }
}

// 显示文件右键菜单
const showFileContextMenu = (event, file) => {
  contextMenu.value = {
    visible: true,
    x: event.clientX,
    y: event.clientY,
    type: 'file',
    target: file
  }
}

// 隐藏右键菜单
const hideContextMenu = () => {
  contextMenu.value.visible = false
}

// 处理重命名
const handleRename = () => {
  renameValue.value = contextMenu.value.target.name.replace('.pdf', '')
  showRenameModal.value = true
  hideContextMenu()
}

// 确认重命名
const confirmRename = () => {
  if (renameValue.value.trim()) {
    if (contextMenu.value.type === 'folder') {
      contextMenu.value.target.name = renameValue.value
    } else {
      contextMenu.value.target.name = renameValue.value + (renameValue.value.endsWith('.pdf') ? '' : '.pdf')
    }
    showRenameModal.value = false
    renameValue.value = ''
  }
}

// 处理删除
const handleDelete = () => {
  if (confirm(`确定要删除"${contextMenu.value.target.name}"吗？`)) {
    if (contextMenu.value.type === 'folder') {
      const index = folders.value.findIndex(f => f.id === contextMenu.value.target.id)
      if (index > -1) {
        folders.value.splice(index, 1)
      }
    } else {
      const index = selectedFolder.value.files.findIndex(f => f.id === contextMenu.value.target.id)
      if (index > -1) {
        selectedFolder.value.files.splice(index, 1)
        selectedFolder.value.fileCount--
      }
    }
  }
  hideContextMenu()
}

// 处理移动
const handleMove = () => {
  showMoveModal.value = true
  hideContextMenu()
}

// 移动文件到目标文件夹
const moveFileToFolder = (targetFolder) => {
  const fileToMove = contextMenu.value.target
  const sourceFolder = selectedFolder.value

  // 从原文件夹移除
  const index = sourceFolder.files.findIndex(f => f.id === fileToMove.id)
  if (index > -1) {
    sourceFolder.files.splice(index, 1)
    sourceFolder.fileCount--
  }

  // 添加到目标文件夹
  targetFolder.files.push(fileToMove)
  targetFolder.fileCount++

  showMoveModal.value = false
  alert(`已将"${fileToMove.name}"移动到"${targetFolder.name}"`)
}

// 点击其他地方隐藏右键菜单
const handleClickOutside = (event) => {
  if (contextMenu.value.visible) {
    hideContextMenu()
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.reports-container {
  padding: 20px;
  min-height: calc(100vh - 100px);
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 24px;
}

/* 文件夹网格视图 */
.folders-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 24px;
}

.folder-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid #f3f4f6;
}

.folder-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
  border-color: #3b82f6;
}

.folder-card.add-folder:hover {
  border-color: #3b82f6;
  background: #f0f9ff;
}

.folder-icon {
  margin-bottom: 12px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.folder-name {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 8px;
}

.folder-count {
  font-size: 14px;
  color: #6b7280;
}

/* 文件书架视图 */
.files-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 32px;
}

.back-btn {
  padding: 8px 16px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 14px;
  color: #374151;
  transition: all 0.2s;
}

.back-btn:hover {
  background: #f9fafb;
  border-color: #3b82f6;
  color: #3b82f6;
}

.folder-title {
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.files-shelf {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 24px;
  perspective: 1000px;
}

.file-book {
  position: relative;
  height: 200px;
  cursor: pointer;
  transition: all 0.3s ease;
  transform-style: preserve-3d;
}

.file-book:hover {
  transform: translateY(-12px) rotateY(-5deg);
}

.book-cover {
  position: absolute;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 4px 8px 8px 4px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 16px;
  color: white;
  transform: translateZ(10px);
}

.book-cover.add-cover {
  background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
  color: #6b7280;
  border: 2px dashed #9ca3af;
}

.book-icon {
  font-size: 32px;
  font-weight: bold;
  margin-bottom: 12px;
  opacity: 0.9;
}

.book-title {
  font-size: 12px;
  text-align: center;
  line-height: 1.4;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}

.add-text {
  font-size: 14px;
  margin-top: 8px;
  font-weight: 600;
}

.book-spine {
  position: absolute;
  right: -4px;
  top: 0;
  width: 8px;
  height: 100%;
  background: linear-gradient(to right, rgba(0, 0, 0, 0.3), transparent);
  border-radius: 0 4px 4px 0;
}

/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  padding: 24px;
  width: 400px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.modal-title {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 16px;
}

.folder-input {
  width: 100%;
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
  transition: all 0.2s;
  box-sizing: border-box;
}

.folder-input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.modal-actions {
  display: flex;
  gap: 12px;
  margin-top: 20px;
  justify-content: flex-end;
}

.btn-cancel,
.btn-confirm {
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn-cancel {
  background: #f3f4f6;
  color: #374151;
}

.btn-cancel:hover {
  background: #e5e7eb;
}

.btn-confirm {
  background: #3b82f6;
  color: white;
}

.btn-confirm:hover {
  background: #2563eb;
}

/* 右键菜单样式 */
.context-menu {
  position: fixed;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  padding: 4px;
  min-width: 160px;
  z-index: 9999;
  animation: fadeIn 0.15s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.context-menu-item {
  padding: 10px 16px;
  font-size: 14px;
  color: #374151;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 10px;
}

.context-menu-item:hover {
  background: #f3f4f6;
  color: #1f2937;
}

.context-menu-item.danger {
  color: #ef4444;
}

.context-menu-item.danger:hover {
  background: #fee2e2;
  color: #dc2626;
}

.context-menu-item svg {
  flex-shrink: 0;
}

.context-menu-divider {
  height: 1px;
  background: #e5e7eb;
  margin: 4px 0;
}

/* 文件夹列表样式 */
.folder-list {
  max-height: 300px;
  overflow-y: auto;
  margin: 16px 0;
}

.folder-list-item {
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  color: #374151;
}

.folder-list-item:hover {
  background: #f0f9ff;
  border-color: #3b82f6;
  color: #1f2937;
}
</style>
