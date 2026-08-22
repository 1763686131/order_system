<template>
  <teleport to="body">
    <div
      v-if="visible"
      id="viewUserModal"
      class="old-modal-mask"
      :class="{ hidden: !visible }"
    >
      <div class="old-modal-box" style="width: 850px; max-width: 95%;">
        <div class="old-modal-header">
          <span>系统账户与权限管理控制台</span>
          <span class="old-close-x" @click="handleClose">&times;</span>
        </div>

        <div class="old-modal-body" style="padding: 20px;">
          <div class="user-manage-container">
            <!-- 左侧用户列表 -->
            <div class="user-list-panel">
              <div style="display:flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <strong style="color:#606266; font-size: 15px;">员工名单</strong>
                <button class="btn-primary" style="padding: 6px 12px; font-size: 12px;" @click="prepareCreateUser">+ 新增员工</button>
              </div>
              <div id="userListContainer">
                <div
                  v-for="user in users"
                  :key="user.username"
                  class="user-list-item"
                  :class="{ active: currentEditUser?.username === user.username }"
                  @click="loadUserDetail(user)"
                >
                  <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 4px;">
                    <strong style="color:#303133; font-size: 15px;">{{ user.name || user.username }}</strong>
                    <span
                      :style="{
                        fontSize: '11px',
                        background: getRoleColor(user.role) + '15',
                        color: getRoleColor(user.role),
                        padding: '3px 8px',
                        borderRadius: '10px',
                        fontWeight: 'bold'
                      }"
                    >
                      {{ getRoleName(user.role) }}
                    </span>
                  </div>
                  <div style="font-size:12px; color:#909399;">账号: {{ user.username }}</div>
                </div>
              </div>
            </div>

            <!-- 右侧详情面板 -->
            <div class="user-detail-panel" id="userDetailPanel" v-show="showDetailPanel">
              <h4 id="detailTitle" style="margin-top:0; color:#303133; border-bottom: 1px solid #ebeef5; padding-bottom:12px; margin-bottom: 15px;">
                {{ detailTitle }}
              </h4>

              <div class="form-item" id="createUsernameGroup">
                <label>系统登录账号:</label>
                <input
                  v-model="formData.username"
                  id="detailUsername"
                  :disabled="isEditMode"
                  placeholder="输入账号名称"
                />
              </div>

              <div class="form-item" style="margin-top: 16px;">
                <label>员工真实姓名:</label>
                <input
                  v-model="formData.name"
                  id="detailName"
                  placeholder="输入员工的中文全名"
                />
              </div>

              <div class="form-item">
                <label>账户安全密码:</label>
                <div style="display:flex; gap:10px;">
                  <input
                    v-model="formData.password"
                    id="detailPassword"
                    type="password"
                    :placeholder="isEditMode ? '留空则不修改密码' : '输入登录密码'"
                    style="flex:1;"
                  />
                </div>
              </div>

              <div class="form-item">
                <label>系统岗位级别:</label>
                <select
                  v-model="formData.role"
                  id="detailRole"
                  :disabled="!userStore.hasPerm('system.user_manage')"
                >
                  <option value="employee">普通员工</option>
                  <option value="operator">操作员</option>
                  <option value="admin">管理员</option>
                  <option v-if="userStore.role === 'super_admin'" value="super_admin">超级管理员</option>
                </select>
              </div>

              <div id="permissionsWrapper">
                <label style="font-weight: bold; display:block; margin-top:15px; color:#606266;">
                  模块功能权限分配 (勾选即刻赋权):
                </label>
                <div class="perm-tree" id="permTreeContainer">
                  <div
                    v-for="group in permissionsConfig"
                    :key="group.group"
                    class="perm-group"
                  >
                    <label>
                      <input
                        type="checkbox"
                        :checked="isGroupChecked(group)"
                        @change="toggleGroupPerms(group, $event)"
                      />
                      {{ group.label }}
                    </label>
                    <div class="perm-children">
                      <label
                        v-for="perm in group.children"
                        :key="perm.key"
                      >
                        <input
                          type="checkbox"
                          :value="perm.key"
                          v-model="formData.permissions"
                        />
                        {{ perm.label }}
                      </label>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="old-modal-footer">
          <button
            v-if="isEditMode && userStore.hasPerm('system.user_manage')"
            class="btn-danger"
            id="btnDeleteUser"
            style="float:left;"
            @click="deleteCurrentUser"
          >
            物理注销该账户
          </button>
          <button class="btn-default" @click="handleClose">关闭</button>
          <button
            v-if="showDetailPanel"
            class="btn-success"
            id="btnSaveUser"
            @click="saveUserData"
            :disabled="loading"
          >
            {{ loading ? '保存中...' : '保存账户与权限' }}
          </button>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import request from '@/api/request'

const userStore = useUserStore()

const visible = ref(false)
const loading = ref(false)
const users = ref([])
const currentEditUser = ref(null)
const showDetailPanel = ref(false)

const formData = ref({
  username: '',
  name: '',
  password: '',
  role: 'employee',
  permissions: []
})

const permissionsConfig = [
  {
    group: 'pending_order',
    label: '未完成订单 (车间看板)',
    children: [
      { key: 'pending.add', label: '显示：发布新订单 (悬浮球)' },
      { key: 'pending.view_detail', label: '显示：卡片翻转与详情页面' },
      { key: 'pending.complete', label: '操作：确定完成业务' },
      { key: 'pending.edit', label: '操作：修改订单信息' },
      { key: 'pending.copy', label: '显示：复制物流信息' },
      { key: 'pending.delete', label: '操作：物理删除订单' }
    ]
  },
  {
    group: 'completed_order',
    label: '已完成订单 (核对发货)',
    children: [
      { key: 'completed.ship', label: '操作：发货并出库' },
      { key: 'completed.uncomplete', label: '操作：撤销回未完成' },
      { key: 'completed.copy', label: '显示：复制物流信息' },
      { key: 'completed.delete', label: '操作：物理删除订单' }
    ]
  },
  {
    group: 'shipped',
    label: '已出库订单栏目',
    children: [
      { key: 'shipped.audit', label: '发货方式标签（出库审核与撤销）' },
      { key: 'shipped.view_receipt', label: '回单标签（查看与下载凭证）' },
      { key: 'shipped.upload_receipt', label: '单号标签（上传与管理回单图片）' },
      { key: 'shipped.delete_receipt', label: '弹窗操作：允许删除回单图片' }
    ]
  },
  {
    group: 'material',
    label: '原材料数据模块',
    children: [
      { key: 'material.add', label: '录入原材料数据' },
      { key: 'material.edit', label: '行内就地修改数据' },
      { key: 'material.delete', label: '物理删除流水记录' }
    ]
  },
  {
    group: 'system',
    label: '系统管理模块',
    children: [{ key: 'system.user_manage', label: '账户与权限控制台' }]
  }
]

const isEditMode = computed(() => currentEditUser.value !== null)
const detailTitle = computed(() => (isEditMode.value ? '用户信息配置' : '用户信息配置'))

// 检查分组是否全选
const isGroupChecked = (group) => {
  return group.children.every(perm => formData.value.permissions.includes(perm.key))
}

// 切换分组权限
const toggleGroupPerms = (group, event) => {
  const checked = event.target.checked
  if (checked) {
    group.children.forEach(perm => {
      if (!formData.value.permissions.includes(perm.key)) {
        formData.value.permissions.push(perm.key)
      }
    })
  } else {
    group.children.forEach(perm => {
      const index = formData.value.permissions.indexOf(perm.key)
      if (index > -1) {
        formData.value.permissions.splice(index, 1)
      }
    })
  }
}

// 获取角色名称
const getRoleName = (role) => {
  const roleMap = {
    super_admin: '超管',
    admin: '管理',
    operator: '操作',
    employee: '员工'
  }
  return roleMap[role] || '未知'
}

// 获取角色颜色
const getRoleColor = (role) => {
  const colorMap = {
    super_admin: '#ff4d4f',
    admin: '#faad14',
    operator: '#1890ff',
    employee: '#52c41a'
  }
  return colorMap[role] || '#999'
}

// 刷新用户列表
const refreshUserList = async () => {
  try {
    const response = await request({ url: '/users', method: 'GET' })
    users.value = response || []
  } catch (error) {
    console.error('获取用户列表失败:', error)
  }
}

// 准备创建用户
const prepareCreateUser = () => {
  currentEditUser.value = null
  showDetailPanel.value = true
  formData.value = {
    username: '',
    name: '',
    password: '',
    role: 'employee',
    permissions: []
  }
}

// 加载用户详情
const loadUserDetail = (user) => {
  currentEditUser.value = user
  showDetailPanel.value = true
  formData.value = {
    username: user.username,
    name: user.name || '',
    password: '',
    role: user.role,
    permissions: user.permissions || []
  }
}

// 保存用户数据
const saveUserData = async () => {
  if (!isEditMode.value) {
    // 新建用户
    const username = formData.value.username.trim()
    const password = formData.value.password.trim()
    if (!username || !password) {
      return alert('账号密码不能为空！')
    }

    const payload = {
      username: username,
      name: formData.value.name.trim(),
      password: password,
      role: formData.value.role,
      permissions: formData.value.permissions
    }

    loading.value = true
    try {
      const res = await request({ url: '/users', method: 'POST', data: payload })
      if (res) {
        window.location.reload()
      }
    } catch (error) {
      alert('账号已存在或无权限！')
    } finally {
      loading.value = false
    }
  } else {
    // 编辑现有用户权限
    const payload = {
      name: formData.value.name.trim(),
      permissions: formData.value.permissions,
      role: formData.value.role
    }

    loading.value = true
    try {
      const res = await request({
        url: `/users/${currentEditUser.value.username}/permissions`,
        method: 'PUT',
        data: payload
      })
      if (res) {
        window.location.reload()
      }
    } catch (error) {
      alert('更新失败，权限不足')
    } finally {
      loading.value = false
    }
  }
}

// 删除当前用户
const deleteCurrentUser = async () => {
  if (!currentEditUser.value) return

  if (!confirm(`确定要物理删除账户 "${currentEditUser.value.username}" 吗？此操作无法撤销！`)) {
    return
  }

  try {
    await request({ url: `/users/${currentEditUser.value.username}`, method: 'DELETE' })
    alert('账户已删除')
    showDetailPanel.value = false
    currentEditUser.value = null
    await refreshUserList()
  } catch (error) {
    alert('删除失败')
  }
}

// 打开弹窗
const open = async () => {
  visible.value = true
  showDetailPanel.value = false
  await refreshUserList()
}

// 关闭弹窗
const handleClose = () => {
  visible.value = false
}

// 暴露方法
defineExpose({
  open
})

// 监听全局事件
onMounted(() => {
  window.addEventListener('open-user-manage-modal', () => {
    open()
  })
})
</script>

<style scoped>
/* 通用隐藏类 */
.hidden {
  display: none !important;
}

/* 弹窗遮罩层 */
.old-modal-mask {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 100000;
}

/* 弹窗容器 */
.old-modal-box {
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  max-height: 90vh;
  width: 95%;
  max-width: 700px;
  animation: scaleUp 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes scaleUp {
  from {
    transform: scale(0.95);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}

/* 弹窗头部 */
.old-modal-header {
  padding: 20px 32px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 20px;
  font-weight: bold;
  background: #fafafa;
}

/* 关闭按钮 */
.old-close-x {
  cursor: pointer;
  font-size: 28px;
  color: #999;
  line-height: 1;
  transition: color 0.2s;
}

.old-close-x:hover {
  color: #ff4d4f;
}

/* 弹窗内容区 */
.old-modal-body {
  overflow-y: auto;
  padding: 32px;
}

/* 弹窗底部 */
.old-modal-footer {
  padding: 20px 32px;
  border-top: 1px solid #f0f0f0;
  display: flex;
  justify-content: flex-end;
  gap: 16px;
  background: #fafafa;
}

/* 用户管理容器 */
.user-manage-container {
  display: flex;
  gap: 24px;
  min-height: 450px;
}

/* 左侧用户列表面板 */
.user-list-panel {
  width: 35%;
  border-right: 1px solid #eee;
  padding-right: 20px;
  overflow-y: auto;
  max-height: 500px;
}

/* 右侧用户详情面板 */
.user-detail-panel {
  width: 65%;
  padding-left: 10px;
}

/* 用户列表项 */
.user-list-item {
  padding: 16px;
  border: 1px solid #eee;
  border-radius: 8px;
  margin-bottom: 12px;
  cursor: pointer;
  transition: 0.2s;
  background: #fff;
}

.user-list-item:hover {
  border-color: #1890ff;
  background: #f0f7ff;
}

.user-list-item.active {
  border-color: #1890ff;
  background: #e6f7ff;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.1);
}

/* 表单项 */
.form-item {
  margin-bottom: 20px;
  width: 100%;
  text-align: left;
}

.form-item label {
  display: block;
  margin-bottom: 8px;
  font-size: 16px;
  color: #555;
  font-weight: bold;
}

.form-item input,
.form-item select,
.form-item textarea {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  outline: none;
  font-size: 16px;
  font-family: inherit;
}

.form-item input:focus,
.form-item select:focus {
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.1);
}

/* 权限树 */
.perm-tree {
  margin-top: 20px;
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 20px;
  background: #f9f9f9;
  max-height: 300px;
  overflow-y: auto;
}

/* 权限分组 */
.perm-group {
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px dashed #e4e7ed;
}

.perm-group:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.perm-group > label {
  font-weight: bold;
  color: #333;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  margin-bottom: 12px;
  cursor: pointer;
}

/* 权限子项 */
.perm-children {
  margin-left: 32px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.perm-children label {
  font-size: 15px;
  color: #666;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

/* 按钮样式 */
.btn-primary {
  background: #1890ff;
  color: #fff;
  border: none;
  padding: 10px 24px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: bold;
  transition: background 0.2s;
}

.btn-primary:hover {
  background: #40a9ff;
}

.btn-default {
  background: #f0f2f5;
  color: #666;
  border: none;
  padding: 10px 24px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.btn-default:hover {
  background: #e4e7ed;
  color: #333;
}

.btn-success {
  background: #52c41a;
  color: #fff;
  border: none;
  padding: 10px 24px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: bold;
  transition: background 0.2s;
}

.btn-success:hover {
  background: #73d13d;
}

.btn-success:disabled {
  background: #d9d9d9;
  color: #999;
  cursor: not-allowed;
}

.btn-danger {
  background: #fdecee;
  color: #f46e83;
  border: none;
  padding: 10px 24px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: bold;
  transition: background 0.2s;
}

.btn-danger:hover {
  background: #fbcdd1;
}

/* 响应式 */
@media (max-width: 768px) {
  .user-manage-container {
    flex-direction: column;
  }

  .user-list-panel {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid #eee;
    padding-right: 0;
    padding-bottom: 20px;
    margin-bottom: 20px;
    max-height: 250px;
  }

  .user-detail-panel {
    width: 100%;
    padding-left: 0;
  }
}
</style>
