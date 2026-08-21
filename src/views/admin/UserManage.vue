<template>
  <teleport to="body">
    <div
      v-if="visible"
      id="viewUserModal"
      class="old-modal-mask"
    >
      <div class="old-modal-box" style="max-width: 900px; width: 92%;">
        <div class="old-modal-header">
          <span>系统账户与权限管理控制台</span>
          <span class="old-close-x" @click="handleClose">&times;</span>
        </div>

        <div class="old-modal-body" style="padding: 24px; display: flex; gap: 24px; min-height: 400px;">
          <!-- 左侧用户列表 -->
          <div style="flex: 1; border-right: 1px solid #f0f0f0; padding-right: 24px;">
            <div style="margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center;">
              <h3 style="margin: 0; font-size: 16px; color: #333;">账户列表</h3>
              <button class="btn-success" @click="prepareCreateUser" style="padding: 6px 12px; font-size: 13px;">+ 新建账户</button>
            </div>
            <div id="userListContainer" style="max-height: 450px; overflow-y: auto;">
              <div
                v-for="user in users"
                :key="user.username"
                class="user-list-item"
                :class="{ active: currentEditUser?.username === user.username }"
                @click="loadUserDetail(user)"
              >
                <div style="display:flex; justify-content:space-between; align-items:center;">
                  <span style="font-size: 15px; font-weight: bold; color: #333;">
                    {{ user.name || user.username }}
                    <span style="font-size:12px;color:#999;font-weight:normal;">({{ user.username }})</span>
                  </span>
                  <span
                    :style="{
                      fontSize: '12px',
                      background: getRoleColor(user.role) + '20',
                      color: getRoleColor(user.role),
                      padding: '2px 8px',
                      borderRadius: '12px',
                      fontWeight: 'bold'
                    }"
                  >
                    {{ getRoleName(user.role) }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- 右侧详情面板 -->
          <div id="userDetailPanel" v-show="showDetailPanel" style="flex: 1.5;">
            <h3 id="detailTitle" style="margin: 0 0 20px 0; font-size: 18px; color: #1890ff;">{{ detailTitle }}</h3>

            <div class="form-item" style="margin-bottom: 16px;">
              <label style="font-weight: bold; color: #555; margin-bottom: 6px; display: block;">登录账号:</label>
              <input
                v-model="formData.username"
                id="detailUsername"
                :disabled="isEditMode"
                placeholder="用于登录的唯一标识"
                style="width: 100%; padding: 8px 12px; border: 1px solid #d9d9d9; border-radius: 6px;"
              />
            </div>

            <div class="form-item" style="margin-bottom: 16px;">
              <label style="font-weight: bold; color: #555; margin-bottom: 6px; display: block;">显示姓名:</label>
              <input
                v-model="formData.name"
                id="detailName"
                placeholder="在系统中展示的真实姓名"
                style="width: 100%; padding: 8px 12px; border: 1px solid #d9d9d9; border-radius: 6px;"
              />
            </div>

            <div class="form-item" style="margin-bottom: 16px;">
              <label style="font-weight: bold; color: #555; margin-bottom: 6px; display: block;">登录密码:</label>
              <input
                v-model="formData.password"
                id="detailPassword"
                type="password"
                :placeholder="isEditMode ? '留空则不修改密码' : '设置初始密码'"
                style="width: 100%; padding: 8px 12px; border: 1px solid #d9d9d9; border-radius: 6px;"
              />
            </div>

            <div class="form-item" style="margin-bottom: 16px;">
              <label style="font-weight: bold; color: #555; margin-bottom: 6px; display: block;">账户角色:</label>
              <select
                v-model="formData.role"
                id="detailRole"
                :disabled="!userStore.hasPerm('system.user_manage')"
                style="width: 100%; padding: 8px 12px; border: 1px solid #d9d9d9; border-radius: 6px;"
              >
                <option value="employee">员工（只读）</option>
                <option value="operator">操作员（编辑）</option>
                <option value="admin">管理员（全部）</option>
                <option v-if="userStore.role === 'super_admin'" value="super_admin">超级管理员</option>
              </select>
            </div>

            <div class="form-item">
              <label style="font-weight: bold; color: #555; margin-bottom: 8px; display: block;">细粒度权限:</label>
              <div style="font-size: 12px; color: #999; margin-bottom: 12px;">（仅当角色为"员工"或"操作员"时生效）</div>
              <div style="max-height: 200px; overflow-y: auto; border: 1px solid #f0f0f0; border-radius: 6px; padding: 12px;">
                <div v-for="group in permissionsConfig" :key="group.group" style="margin-bottom: 16px;">
                  <div style="font-weight: bold; color: #333; margin-bottom: 8px;">{{ group.label }}</div>
                  <div v-for="perm in group.children" :key="perm.key" style="margin-bottom: 6px;">
                    <label style="cursor: pointer; display: flex; align-items: center;">
                      <input
                        type="checkbox"
                        :value="perm.key"
                        v-model="formData.permissions"
                        style="margin-right: 8px;"
                      />
                      <span style="font-size: 13px; color: #666;">{{ perm.label }}</span>
                    </label>
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
const detailTitle = computed(() => (isEditMode.value ? '编辑账户信息' : '新建系统账户'))

// 获取角色名称
const getRoleName = (role) => {
  const roleMap = {
    super_admin: '超级管理员',
    admin: '管理员',
    operator: '操作员',
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
  if (!formData.value.username.trim()) {
    return alert('登录账号不能为空')
  }

  if (!isEditMode.value && !formData.value.password.trim()) {
    return alert('新建账户必须设置初始密码')
  }

  loading.value = true

  try {
    const payload = {
      username: formData.value.username,
      name: formData.value.name,
      role: formData.value.role,
      permissions: formData.value.permissions
    }

    if (formData.value.password.trim()) {
      payload.password = formData.value.password
    }

    if (isEditMode.value) {
      await request({ url: `/users/${formData.value.username}`, method: 'PUT', data: payload })
    } else {
      await request({ url: '/users', method: 'POST', data: payload })
    }

    alert('保存成功')
    showDetailPanel.value = false
    await refreshUserList()
  } catch (error) {
    alert('保存失败')
  } finally {
    loading.value = false
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
.user-list-item {
  padding: 14px;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  transition: background 0.2s;
}

.user-list-item:hover {
  background: #f5f5f5;
}

.user-list-item.active {
  background: #e6f4ff;
  border-left: 3px solid #1890ff;
}
</style>
