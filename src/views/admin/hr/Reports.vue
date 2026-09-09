<template>
  <div class="reports-container">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <h2 class="page-title">检测报告</h2>
      <button class="sync-btn" @click="syncFiles" :disabled="syncing">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :class="{ spinning: syncing }">
          <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/>
        </svg>
        {{ syncing ? '同步中...' : '同步文件' }}
      </button>
    </div>

    <!-- 面包屑导航 -->
    <div v-if="currentPath.length > 0" class="breadcrumb">
      <span class="breadcrumb-item" @click="navigateToRoot">根目录</span>
      <span v-for="(folder, index) in currentPath" :key="index" class="breadcrumb-item">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M9 18l6-6-6-6"/>
        </svg>
        <span @click="navigateToFolder(index)">{{ folder.name }}</span>
      </span>
    </div>

    <!-- 文件夹视图 -->
    <div v-if="!selectedFolder" class="folders-view">
      <div class="folders-grid">
        <div
          v-for="folder in currentFolders"
          :key="folder.path"
          class="folder-card"
          @click="openFolder(folder)"
          @contextmenu.prevent="showFolderContextMenu($event, folder)"
        >
          <div class="folder-icon">
            <svg width="80" height="80" viewBox="0 0 24 24" fill="none">
              <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" fill="#FFA500" stroke="#FF8C00" stroke-width="1.5"/>
            </svg>
          </div>
          <div class="folder-name" :title="folder.name">{{ folder.name }}</div>
          <div class="folder-count">{{ folder.fileCount }} 个文件</div>
        </div>

        <!-- 当前文件 -->
        <div
          v-for="file in currentFiles"
          :key="file.id"
          class="file-card"
          @click="openFile(file)"
          @contextmenu.prevent="showFileContextMenu($event, file)"
        >
          <div class="file-icon" :class="`file-type-${file.type}`">
            <template v-if="file.type === 'pdf'">PDF</template>
            <template v-else-if="file.type === 'image'">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                <circle cx="8.5" cy="8.5" r="1.5"/>
                <polyline points="21 15 16 10 5 21"/>
              </svg>
            </template>
            <template v-else-if="file.type === 'excel'">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
                <line x1="9" y1="15" x2="15" y2="15"/>
              </svg>
            </template>
            <template v-else-if="file.type === 'word'">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
              </svg>
            </template>
            <template v-else>FILE</template>
          </div>
          <div class="file-name" :title="file.name">{{ file.name }}</div>
          <div class="file-size">{{ formatFileSize(file.size) }}</div>
        </div>

        <!-- 上传文件按钮 -->
        <div class="file-card add-file" @click="triggerFileUpload">
          <div class="file-icon add-icon">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <path d="M12 8v8M8 12h8"/>
            </svg>
          </div>
          <div class="file-name">上传文件</div>
        </div>
      </div>

      <input
        ref="fileInput"
        type="file"
        accept=".pdf,.jpg,.jpeg,.png,.gif,.xlsx,.xls,.doc,.docx"
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
        <!-- 文件菜单 -->
        <template v-if="contextMenu.type === 'file'">
          <div class="context-menu-item" @click="handleDownload">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="7 10 12 15 17 10"/>
              <line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
            下载
          </div>
          <div class="context-menu-item" @click="handleMove">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/>
              <polyline points="13 2 13 9 20 9"/>
            </svg>
            移动
          </div>
          <div class="context-menu-item" @click="handleShare">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="18" cy="5" r="3"/>
              <circle cx="6" cy="12" r="3"/>
              <circle cx="18" cy="19" r="3"/>
              <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/>
              <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>
            </svg>
            分享
          </div>
          <div class="context-menu-item danger" @click="handleDelete">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="3 6 5 6 21 6"/>
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
            </svg>
            删除
          </div>
        </template>

        <!-- 文件夹菜单 -->
        <template v-if="contextMenu.type === 'folder'">
          <div class="context-menu-item" @click="handleRenameFolder">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
            重命名
          </div>
          <div class="context-menu-item danger" @click="handleDeleteFolder">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="3 6 5 6 21 6"/>
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
            </svg>
            删除文件夹
          </div>
        </template>

        <div class="context-menu-divider"></div>
        <div class="context-menu-item" @click="hideContextMenu">取消</div>
      </div>
    </teleport>

    <!-- 分享弹窗 -->
    <teleport to="body">
      <div v-if="showShareModal" class="modal-overlay" @click.self="showShareModal = false">
        <div class="modal-content">
          <h3 class="modal-title">分享文件</h3>
          <div class="share-info">
            <p>文件名: <strong>{{ shareFile?.name }}</strong></p>
            <div class="expire-selector">
              <label>有效期:</label>
              <select v-model="shareExpireDays">
                <option :value="7">7天</option>
                <option :value="30">30天</option>
                <option :value="365">365天</option>
              </select>
            </div>
          </div>
          <div v-if="shareLink" class="share-link-box">
            <input
              ref="shareLinkInput"
              type="text"
              :value="shareLink"
              readonly
              class="share-link-input"
            />
            <button class="copy-btn" @click="copyShareLink">
              {{ copied ? '已复制' : '复制链接' }}
            </button>
          </div>
          <div class="modal-actions">
            <button class="btn-cancel" @click="showShareModal = false">取消</button>
            <button v-if="!shareLink" class="btn-confirm" @click="generateShareLink">生成链接</button>
          </div>
        </div>
      </div>
    </teleport>

    <!-- 重命名文件夹弹窗 -->
    <teleport to="body">
      <div v-if="showRenameFolderModal" class="modal-overlay" @click.self="showRenameFolderModal = false">
        <div class="modal-content">
          <h3 class="modal-title">重命名文件夹</h3>
          <input
            v-model="renameFolderValue"
            type="text"
            class="folder-input"
            placeholder="请输入新名称"
            @keyup.enter="confirmRenameFolder"
          />
          <div class="modal-actions">
            <button class="btn-cancel" @click="showRenameFolderModal = false">取消</button>
            <button class="btn-confirm" @click="confirmRenameFolder">确定</button>
          </div>
        </div>
      </div>
    </teleport>

    <!-- 移动文件弹窗 -->
    <teleport to="body">
      <div v-if="showMoveModal" class="modal-overlay" @click.self="showMoveModal = false">
        <div class="modal-content">
          <h3 class="modal-title">移动文件到</h3>
          <div class="folder-list">
            <div
              class="folder-list-item"
              :class="{ 'selected': selectedTargetFolder === '' }"
              @click="selectTargetFolder('')"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" fill="#3b82f6" stroke="#2563eb" stroke-width="1.5"/>
              </svg>
              根目录
            </div>
            <div
              v-for="folder in allFolders"
              :key="folder.path"
              class="folder-list-item"
              :class="{ 'selected': selectedTargetFolder === folder.path }"
              @click="selectTargetFolder(folder.path)"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" fill="#FFA500" stroke="#FF8C00" stroke-width="1.5"/>
              </svg>
              {{ folder.path }}
            </div>
          </div>
          <div class="modal-actions">
            <button class="btn-cancel" @click="showMoveModal = false">取消</button>
            <button
              class="btn-confirm"
              :disabled="selectedTargetFolder === null"
              @click="confirmMoveFile"
            >
              确定
            </button>
          </div>
        </div>
      </div>
    </teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import request from '@/api/request'

const API_BASE = '/hr/reports'

const syncing = ref(false)
const fileTree = ref({ folders: [], files: [] })
const currentPath = ref([])
const fileInput = ref(null)
const showShareModal = ref(false)
const showRenameFolderModal = ref(false)
const showMoveModal = ref(false)
const shareFile = ref(null)
const shareLink = ref('')
const shareExpireDays = ref(7)
const copied = ref(false)
const shareLinkInput = ref(null)
const renameFolderValue = ref('')
const renameFolderTarget = ref(null)
const moveFileTarget = ref(null)
const selectedTargetFolder = ref(null)  // 选中的目标文件夹

// 右键菜单状态
const contextMenu = ref({
  visible: false,
  x: 0,
  y: 0,
  type: '', // 'folder' or 'file'
  target: null
})

// 当前显示的文件夹和文件
const currentFolders = computed(() => {
  let current = fileTree.value
  for (const folder of currentPath.value) {
    const found = current.folders.find(f => f.name === folder.name)
    if (found) {
      current = found
    } else {
      return []
    }
  }
  return current.folders.map(f => ({
    ...f,
    fileCount: countFiles(f)
  }))
})

const currentFiles = computed(() => {
  let current = fileTree.value
  for (const folder of currentPath.value) {
    const found = current.folders.find(f => f.name === folder.name)
    if (found) {
      current = found
    } else {
      return []
    }
  }
  return current.files || []
})

// 递归计算文件夹内文件数量
const countFiles = (folder) => {
  let count = folder.files ? folder.files.length : 0
  if (folder.folders) {
    folder.folders.forEach(f => {
      count += countFiles(f)
    })
  }
  return count
}

// 递归获取所有文件夹路径（用于移动文件时选择目标）
const allFolders = computed(() => {
  const folders = []

  const collectFolders = (node, prefix = '') => {
    if (node.folders) {
      node.folders.forEach(folder => {
        const path = prefix ? `${prefix}/${folder.name}` : folder.name
        folders.push({ name: folder.name, path })
        collectFolders(folder, path)
      })
    }
  }

  collectFolders(fileTree.value)
  return folders
})

// 同步文件
const syncFiles = async () => {
  syncing.value = true
  try {
    const response = await request.post(`${API_BASE}/sync`)
    if (response.success) {
      alert(response.message)
      await loadFileList()
    } else {
      alert('同步失败: ' + response.message)
    }
  } catch (error) {
    alert('同步失败: ' + error.message)
  } finally {
    syncing.value = false
  }
}

// 加载文件列表
const loadFileList = async () => {
  try {
    const response = await request.get(`${API_BASE}/list`)
    if (response.success) {
      fileTree.value = response.data
    }
  } catch (error) {
    console.error('加载文件列表失败:', error)
  }
}

// 导航到根目录
const navigateToRoot = () => {
  currentPath.value = []
}

// 导航到指定层级
const navigateToFolder = (index) => {
  currentPath.value = currentPath.value.slice(0, index + 1)
}

// 打开文件夹
const openFolder = (folder) => {
  currentPath.value.push({ name: folder.name })
}

// 打开文件
const openFile = (file) => {
  // PDF 和图片直接在新标签页预览，其他文件会触发下载
  // 使用完整的 API 路径
  window.open(`/api/hr/reports/download/${file.id}`, '_blank')
}

// 触发文件上传
const triggerFileUpload = () => {
  fileInput.value?.click()
}

// 处理文件上传
const handleFileUpload = async (event) => {
  const files = Array.from(event.target.files)

  for (const file of files) {
    const formData = new FormData()
    formData.append('file', file)

    // 构建当前路径
    const folderPath = currentPath.value.map(p => p.name).join('/')
    if (folderPath) {
      formData.append('folder_path', folderPath)
    }

    try {
      const response = await request.post(`${API_BASE}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Username': localStorage.getItem('username') || 'unknown'
        }
      })

      if (response.success) {
        console.log('上传成功:', file.name)
      }
    } catch (error) {
      alert(`上传失败 ${file.name}: ${error.message}`)
    }
  }

  // 重新加载列表
  await loadFileList()
  event.target.value = ''
}

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
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

// 隐藏右键菜单
const hideContextMenu = () => {
  contextMenu.value.visible = false
}

// 处理下载
const handleDownload = () => {
  if (contextMenu.value.type === 'file') {
    window.open(`${API_BASE}/download/${contextMenu.value.target.id}`, '_blank')
  }
  hideContextMenu()
}

// 处理移动
const handleMove = () => {
  moveFileTarget.value = contextMenu.value.target
  selectedTargetFolder.value = null  // 重置选择
  showMoveModal.value = true
  hideContextMenu()
}

// 选择目标文件夹
const selectTargetFolder = (folderPath) => {
  selectedTargetFolder.value = folderPath
}

// 确认移动文件
const confirmMoveFile = async () => {
  if (selectedTargetFolder.value === null) {
    return
  }

  try {
    const response = await request.post(`${API_BASE}/move`, {
      file_id: moveFileTarget.value.id,
      target_folder: selectedTargetFolder.value
    })

    if (response.success) {
      alert('移动成功')
      await loadFileList()
      showMoveModal.value = false
      selectedTargetFolder.value = null
    } else {
      alert('移动失败: ' + response.message)
    }
  } catch (error) {
    alert('移动失败: ' + error.message)
  }
}

// 移动文件到目标文件夹（废弃，改用 confirmMoveFile）
const moveFileToFolder = async (targetFolderPath) => {
  try {
    const response = await axios.post(`${API_BASE}/move`, {
      file_id: moveFileTarget.value.id,
      target_folder: targetFolderPath
    })

    if (response.data.success) {
      alert('移动成功')
      await loadFileList()
      showMoveModal.value = false
    } else {
      alert('移动失败: ' + response.data.message)
    }
  } catch (error) {
    alert('移动失败: ' + error.message)
  }
}

// 处理分享
const handleShare = () => {
  shareFile.value = contextMenu.value.target
  showShareModal.value = true
  shareLink.value = ''
  copied.value = false
  hideContextMenu()
}

// 生成分享链接
const generateShareLink = async () => {
  try {
    const response = await request.post(`${API_BASE}/share/${shareFile.value.id}`, {
      expire_days: shareExpireDays.value
    })

    if (response.success) {
      shareLink.value = `${window.location.origin}/api/hr/reports/share/${response.share_token}`
    } else {
      alert('生成分享链接失败: ' + response.message)
    }
  } catch (error) {
    alert('生成分享链接失败: ' + error.message)
  }
}

// 复制分享链接
const copyShareLink = () => {
  shareLinkInput.value?.select()
  document.execCommand('copy')
  copied.value = true
  setTimeout(() => {
    copied.value = false
  }, 2000)
}

// 处理文件删除
const handleDelete = async () => {
  if (confirm(`确定要删除"${contextMenu.value.target.name}"吗？此操作将永久删除文件！`)) {
    try {
      const response = await request.delete(`${API_BASE}/delete/${contextMenu.value.target.id}`)

      if (response.success) {
        alert('删除成功')
        await loadFileList()
      } else {
        alert('删除失败: ' + response.message)
      }
    } catch (error) {
      alert('删除失败: ' + error.message)
    }
  }
  hideContextMenu()
}

// 处理文件夹重命名
const handleRenameFolder = () => {
  renameFolderTarget.value = contextMenu.value.target
  renameFolderValue.value = contextMenu.value.target.name
  showRenameFolderModal.value = true
  hideContextMenu()
}

// 确认重命名文件夹
const confirmRenameFolder = async () => {
  if (!renameFolderValue.value.trim()) {
    alert('文件夹名称不能为空')
    return
  }

  try {
    const response = await request.post(`${API_BASE}/folder/rename`, {
      old_path: renameFolderTarget.value.path,
      new_name: renameFolderValue.value
    })

    if (response.success) {
      alert('重命名成功')
      await loadFileList()
      showRenameFolderModal.value = false
    } else {
      alert('重命名失败: ' + response.message)
    }
  } catch (error) {
    alert('重命名失败: ' + error.message)
  }
}

// 处理文件夹删除
const handleDeleteFolder = async () => {
  if (confirm(`确定要删除文件夹"${contextMenu.value.target.name}"吗？此操作将永久删除文件夹及其所有内容！`)) {
    try {
      const response = await request.delete(`${API_BASE}/folder/delete`, {
        data: { folder_path: contextMenu.value.target.path }
      })

      if (response.success) {
        alert(response.message)
        await loadFileList()
      } else {
        alert('删除失败: ' + response.message)
      }
    } catch (error) {
      alert('删除失败: ' + error.message)
    }
  }
  hideContextMenu()
}

// 点击其他地方隐藏右键菜单
const handleClickOutside = (event) => {
  if (contextMenu.value.visible) {
    hideContextMenu()
  }
}

onMounted(() => {
  loadFileList()
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

// 兼容旧代码（如果需要）
const selectedFolder = ref(null)
</script>

<style scoped>
.reports-container {
  padding: 20px;
  min-height: calc(100vh - 100px);
}

/* 顶部工具栏 */
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.sync-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.sync-btn:hover:not(:disabled) {
  background: #2563eb;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.sync-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.sync-btn svg.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 面包屑导航 */
.breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
  font-size: 14px;
  color: #6b7280;
}

.breadcrumb-item {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  transition: color 0.2s;
}

.breadcrumb-item:hover {
  color: #3b82f6;
}

.breadcrumb-item span {
  cursor: pointer;
}

/* 文件夹和文件网格视图 */
.folders-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 20px;
}

.folder-card,
.file-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid #f3f4f6;
}

.folder-card:hover,
.file-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
  border-color: #3b82f6;
}

.file-card.add-file {
  border: 2px dashed #9ca3af;
  background: #f9fafb;
}

.file-card.add-file:hover {
  border-color: #3b82f6;
  background: #f0f9ff;
}

.folder-icon {
  margin-bottom: 12px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.file-icon {
  width: 80px;
  height: 80px;
  margin: 0 auto 12px;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 18px;
  font-weight: bold;
  border-radius: 8px;
  color: white;
}

.file-icon.file-type-pdf {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
}

.file-icon.file-type-image {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.file-icon.file-type-excel {
  background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
}

.file-icon.file-type-word {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
}

.file-icon.file-type-other {
  background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
}

.file-icon.add-icon {
  background: none;
  color: #9ca3af;
}

.folder-name,
.file-name {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 6px;
  word-wrap: break-word;
  word-break: break-all;
  line-height: 1.4;
  max-height: 3.6em;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.folder-count,
.file-size {
  font-size: 12px;
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
  width: 90%;
  max-width: 500px;
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

.share-info {
  margin-bottom: 16px;
}

.share-info p {
  margin-bottom: 12px;
  color: #374151;
  font-size: 14px;
}

.expire-selector {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
}

.expire-selector label {
  font-size: 14px;
  color: #374151;
  font-weight: 500;
}

.expire-selector select {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  cursor: pointer;
}

.share-link-box {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.share-link-input {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 13px;
  background: #f9fafb;
  font-family: monospace;
}

.copy-btn {
  padding: 10px 16px;
  background: #10b981;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.copy-btn:hover {
  background: #059669;
}

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

.folder-list-item.selected {
  background: #dbeafe;
  border-color: #3b82f6;
  color: #1e40af;
  font-weight: 600;
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

.btn-confirm:hover:not(:disabled) {
  background: #2563eb;
}

.btn-confirm:disabled {
  background: #9ca3af;
  cursor: not-allowed;
  opacity: 0.5;
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
</style>
